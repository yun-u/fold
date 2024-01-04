from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import numpy as np
import transformers
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FileUrl,
    HttpUrl,
    PrivateAttr,
    TypeAdapter,
    field_serializer,
    field_validator,
)
from redis import WatchError
from redis.client import Redis
from ulid import ULID
from ulid import monotonic as ulid

from app import redis_pool
from app.pipeline.embed.model import Pipeline
from app.utils.pydantic_utils import instance_from_dict
from app.utils.redis_utils import keyjoin, zadd_with_timestamps


class DocumentIdGenerator:
    lock = threading.Lock()

    @classmethod
    def generate(cls, url: str, redis_client: Redis) -> str:
        with cls.lock:
            with redis_client.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(keyjoin("mapping", "url", "id"))

                        if document_id := pipe.hget(
                            keyjoin("mapping", "url", "id"), url
                        ):
                            logging.info(f"[EXISTING] ID: {document_id}, URL: '{url}'")
                            pipe.unwatch()
                            return document_id

                        document_id = str(ulid.new())

                        pipe.multi()
                        pipe.hset(keyjoin("mapping", "url", "id"), url, document_id)
                        pipe.hset(keyjoin("mapping", "id", "url"), document_id, url)
                        pipe.execute()

                        logging.info(f"[NEW] ID: {document_id}, URL: '{url}'")

                        return document_id
                    except WatchError:
                        continue


def generate_document_id(url: str, redis_client: Redis) -> str:
    if document_id := redis_client.hget(keyjoin("mapping", "url", "id"), url):
        logging.info(f"[EXISTING] ID: {document_id}, URL: '{url}'")
        return str(document_id)

    document_id = str(ulid.new())
    redis_client.hset(keyjoin("mapping", "url", "id"), url, document_id)
    redis_client.hset(keyjoin("mapping", "id", "url"), document_id, url)
    logging.info(f"[NEW] ID: {document_id}, URL: '{url}'")
    return document_id


def generate_tokenizer_key(tokenizer: transformers.PreTrainedTokenizerBase) -> str:
    return f"{tokenizer.__class__}-{tokenizer.max_len_single_sentence}"


def process_arxiv_url(redis_client: Redis, url: str) -> str:
    """Process an ArXiv URL and return the versioned ArXiv ID if matched.

    This function checks if the given URL corresponds to an ArXiv URL, and if so, extracts the versioned
    ArXiv ID and returns the complete URL with the versioned ArXiv ID. If the URL is not recognized as
    an ArXiv URL, it returns the original URL.

    Args:
        redis_client (`Redis`): The Redis client used for caching ArXiv information.
        url (`str`): The URL to process.

    Returns:
        `str`: The processed URL with the versioned ArXiv ID, or the original URL if it is not an ArXiv URL.
    """
    # to prevent circular import
    from app.pipeline.fetch.sources.arxiv import Arxiv

    # check if the given URL matches the Arxiv pattern.
    if (arxiv := Arxiv(redis_client)).match(url):
        return urljoin(Arxiv._ABS_URL, arxiv.get_arxiv_id_versioned(url))

    # if it does not match, return the original URL.
    return url


class Document(BaseModel):
    """
    A class representing a document.

    Attributes:
        id (`str`): The ID of the document.
        url (`Union[HttpUrl, FileUrl]`): The URL of the document.
        category (`str`): The category of the document.
        metadata (`Dict[str, Any]`): Additional metadata associated with the document.
        links (`List[Union[HttpUrl, FileUrl]]`): A list of URLs of documents that this document links to.
        text (`str`): The raw text content of the document.
        embeddings (`Dict[str, List[List[str]]]`): A dictionary that maps model IDs to embeddings of the document.
        is_read (`bool`): Indicates whether the document has been read (default is False).
        is_bookmarked (`bool`): Indicates whether the document has been bookmarked (default is False).

    NOTE: The backlink must be generated automatically by other document's link.
    NOTE: Casting a Boolean type variable to an Int type for use in Redis Search.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = None
    url: Union[HttpUrl, FileUrl]
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    links: List[Union[HttpUrl, FileUrl]] = Field(default_factory=list)
    text: str = ""
    embeddings: Dict[str, List[List[float]]] = Field(default_factory=dict)
    is_read: bool = False
    is_bookmarked: bool = False

    _link_ids: List[str] = PrivateAttr(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return str(ulid.parse(value))

    @field_serializer("url")
    def serialize_url(self, url: Union[HttpUrl, FileUrl], _info) -> str:
        return str(url)

    @field_serializer("links")
    def serialize_links(self, links: List[Union[HttpUrl, FileUrl]], _info) -> List[str]:
        return [str(link) for link in links]

    # casting a Boolean type variable to an Int type for use in Redis Search.
    @field_serializer("is_read", "is_bookmarked")
    def serialize_boolean(self, value: bool, _info) -> int:
        return int(value)

    @property
    def created_at(self) -> str:
        return ulid.parse(self.id).timestamp().datetime.isoformat()

    def model_post_init(self, __context: Any) -> None:
        redis_client = Redis(connection_pool=redis_pool.pool)

        self._process_links(redis_client)

        self._generate_document_id(redis_client)

    def _process_links(self, redis_client: Redis) -> None:
        self.links = [
            TypeAdapter(Union[HttpUrl, FileUrl]).validate_python(
                process_arxiv_url(redis_client, str(link))
            )
            for link in self.links
        ]

    def _generate_document_id(self, redis_client: Redis) -> None:
        if self.id is None:
            self.id = DocumentIdGenerator.generate(str(self.url), redis_client)
        for link in self.links:
            self._link_ids.append(DocumentIdGenerator.generate(str(link), redis_client))

    def is_empty_text(self) -> bool:
        return self.text == ""

    def is_empty_metadata(self) -> bool:
        return len(self.metadata) == 0

    def is_empty_embedding(self, model_id: str) -> bool:
        return not bool(self.embeddings.get(model_id))

    def is_new(self) -> bool:
        # Even though fetched, the text may be empty. e.g. Youtube
        return self.is_empty_text() and self.is_empty_metadata()

    def is_fetched(self, model_id: str) -> bool:
        return not self.is_new() and self.is_empty_embedding(model_id)

    def is_embedded(self, model_id: str) -> bool:
        return not self.is_new() and not self.is_empty_embedding(model_id)

    def create_and_store_embedding(
        self, pipeline: Pipeline, redis_client: Optional[Redis] = None
    ) -> None:
        if self.is_empty_text():
            logging.error(f"Empty content: {self.model_dump_json()}")
            return None

        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        try:
            embeddings = pipeline(self.text).astype(np.float32).tolist()

            self.embeddings[pipeline.model_id] = embeddings

            # set embedding value
            document_id = keyjoin("document", self.id)

            if redis_client.json().objkeys(document_id, "$.embeddings") == []:
                redis_client.json().set(document_id, "$.embeddings", {})

            redis_client.json().set(
                document_id,
                f"$.embeddings.{pipeline.model_id}",
                embeddings,
            )
        except Exception as e:
            logging.error(e)

    @staticmethod
    def exists(url: str, redis_client: Optional[Redis] = None) -> bool:
        """Check if the document data exists in Redis based on the given URL.

        This function checks whether the document associated with the provided URL exists in Redis or not.

        Args:
            url (`str`): The URL of the document.
            redis_client (`Redis`, optional): The Redis client used to check for the document.
                If not provided, a default client will be created.

        Returns:
            `bool`: True if the document data is found in Redis, False otherwise.
        """
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        if document_id := redis_client.hget(keyjoin("mapping", "url", "id"), url):
            if redis_client.exists(keyjoin("document", document_id)):
                logging.info(f"Document data for URL '{url}' exists in Redis.")
                return True
        return False

    def store(self, redis_client: Optional[Redis] = None) -> None:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        if self.exists(str(self.url), redis_client):
            return

        pipe = redis_client.pipeline(transaction=False)

        # store the document as JSON format
        pipe.json().set(keyjoin("document", self.id), "$", self.model_dump())

        # store the document
        zadd_with_timestamps(pipe, "document", self.id)

        # store the document key and its associated data.
        zadd_with_timestamps(pipe, keyjoin("category", self.category), self.id)

        if self._link_ids:
            # store the links associated with the document.
            zadd_with_timestamps(pipe, keyjoin("link", self.id), *self._link_ids)

            # store the backlink list associated with the document.
            for link_id in self._link_ids:
                zadd_with_timestamps(pipe, keyjoin("backlink", link_id), self.id)

        pipe.execute()

    def delete(self, redis_client: Optional[Redis] = None) -> None:
        """Delete the document from Redis.

        This function removes all the keys associated with the document from Redis, including the
        document itself and its backlink relationships.

        Args:
            redis_client (`Optional[Redis]`): The Redis client used to delete the document.
        """

        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        def delete_in_backlink():
            for backlink_id in redis_client.zrange(keyjoin("backlink", self.id), 0, -1):
                document_name = keyjoin("document", backlink_id)
                if (
                    arr_index := redis_client.json().arrindex(
                        document_name, "$.links", str(self.url)
                    )[0]
                ) != -1:
                    redis_client.json().arrpop(document_name, "$.links", arr_index)

                redis_client.zrem(keyjoin("link", backlink_id), self.id)

        def delete_in_link():
            for link_id in self._link_ids:
                redis_client.zrem(keyjoin("backlink", link_id), self.id)

        delete_in_link()
        delete_in_backlink()

        pipe = redis_client.pipeline(transaction=False)

        pipe.hdel(keyjoin("mapping", "id", "url"), self.id)
        pipe.hdel(keyjoin("mapping", "url", "id"), str(self.url))

        pipe.delete(keyjoin("backlink", self.id))
        pipe.delete(keyjoin("link", self.id))

        # delete the document key and its associated data.
        pipe.zrem(keyjoin("category", self.category), self.id)

        # delete the document
        pipe.zrem("document", self.id)

        # delete the document JSON
        pipe.delete(keyjoin("document", self.id))

        pipe.execute()

    @staticmethod
    def from_url(url: str, redis_client: Optional[Redis] = None) -> Optional[Document]:
        """
        Create a Document instance from a given URL.

        This function fetches the document information associated with the given URL from Redis and
        creates a new Document instance with the retrieved data.

        Args:
            url (`str`): The URL of the document.

        Returns:
            `Optional[Document]`: A new Document instance if the document with the provided URL is
            found in Redis, otherwise returns None.
        """
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        # query Redis to find the document ID associated with the given URL.
        if document_id := Document.url_to_id(url, redis_client):
            return Document.from_id(document_id, redis_client)

        return None

    @staticmethod
    def from_id(
        document_id: Union[str, ULID],
        redis_client: Optional[Redis] = None,
    ) -> Optional[Document]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        # fetch the document data associated with the ID from Redis.
        if document_data := redis_client.json().get(
            keyjoin("document", str(document_id))
        ):
            document = instance_from_dict(Document, document_data)
            document._link_ids = redis_client.zrange(
                keyjoin("link", document.id), 0, -1, desc=False
            )
            return document

        return None

    @staticmethod
    def url_to_id(url: str, redis_client: Optional[Redis] = None) -> Optional[str]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        return redis_client.hget(keyjoin("mapping", "url", "id"), url)

    @staticmethod
    def id_to_url(
        document_id: str, redis_client: Optional[Redis] = None
    ) -> Optional[str]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        return redis_client.hget(keyjoin("mapping", "id", "url"), document_id)
