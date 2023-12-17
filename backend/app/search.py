from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import numpy as np
from pydantic import BaseModel, Field, PositiveInt, PrivateAttr, model_validator
from redis.client import Redis
from redis.commands.search.field import NumericField, TagField, TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from typing_extensions import TypedDict

from app import redis_pool
from app.document import Document
from app.embedding_pipeline.pipeline import Pipeline
from app.embedding_pipeline.utils import extract_model_id
from app.sources.twitter import Twitter
from app.utils.redis_utils import keyjoin


def create_index(
    index_name: str,
    model_path: Union[str, Path],
    embedding_dimensions: int,
    redis_client: Optional[Redis] = None,
) -> None:
    if redis_client is None:
        redis_client = Redis(connection_pool=redis_pool.pool)

    schema = (
        VectorField(
            f"$.embeddings['{extract_model_id(model_path)}'][*]",
            "HNSW",
            {
                "TYPE": "FLOAT32",
                "DIM": embedding_dimensions,
                "DISTANCE_METRIC": "IP",
            },
            as_name="embeddings",
        ),
        TagField("$.category", as_name="category"),
        TextField("$.id", as_name="document_id", sortable=True, no_stem=True),
        TextField("$.text", as_name="text", no_stem=True),
        TextField("$.metadata.title", as_name="title", no_stem=True),
        TextField("$.metadata.user_id", as_name="user", no_stem=True),
        TextField("$.metadata.author", as_name="author", no_stem=True),
        TextField("$.metadata.authors", as_name="authors", no_stem=True),
        NumericField("$.is_read", as_name="unread"),
        NumericField("$.is_bookmarked", as_name="bookmarked"),
    )

    redis_client.ft(index_name).create_index(
        schema,
        definition=IndexDefinition(prefix=["document:"], index_type=IndexType.JSON),
    )
    redis_client.ft(index_name).config_set("default_dialect", 2)

    logging.info(
        f"Create '{index_name}' index ({redis_client.ft(index_name).info()['num_docs']})"
    )


class SearchResult(BaseModel):
    id: str
    op: OriginalPost
    score: Union[float, None] = Field(None, ge=0.0, le=1.0)

    @property
    def is_op(self) -> bool:
        return self.op["id"] == self.id

    @property
    def url(self) -> str:
        return self.op["url"]


class QueryModel(BaseModel):
    author: str = ""
    bookmarked: bool = False
    category: List[str] = Field(default_factory=list)
    desc: bool = True  # Sort in descending order by created timestamp
    text: str = ""
    title: str = ""
    unread: bool = False
    vector_search: str = ""
    vector_search_document: str = ""
    offset: int = 0
    count: PositiveInt = 10

    _pipeline: Union[Pipeline, None] = PrivateAttr(None)
    _embedding: Union[np.ndarray, None] = PrivateAttr(None)

    @model_validator(mode="after")
    def check_vector_search(self) -> QueryModel:
        if self.vector_search and self.vector_search_document:
            raise ValueError
        return self

    @property
    def exclusive_end(self) -> int:
        return self.offset + self.count

    def embedding(self, redis_client: Optional[Redis] = None) -> Optional[np.ndarray]:
        if self._embedding is not None:
            return self._embedding

        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        assert self._pipeline is not None

        if self.vector_search:
            self._embedding = (
                self._pipeline(self.vector_search)[0].numpy().astype(np.float32)
            )

        if self.vector_search_document:
            if document := Document.from_id(self.vector_search_document, redis_client):
                if embedding := document.embeddings.get(self._pipeline.model_id):
                    embedding = np.asarray(embedding).mean(axis=0).astype(np.float32)
                    self._embedding = embedding / np.linalg.norm(embedding, ord=2)

        return self._embedding

    def query_string(self) -> str:
        queries = []

        if self.author:
            queries.append(f"@author|authors|user:{self.author}")

        if self.bookmarked:
            queries.append("@bookmarked:[1 inf]")

        if self.category:
            queries.append(f"@category:{{{'|'.join(self.category)}}}")

        if self.text:
            queries.append(f"@text:{self.text}")

        if self.title:
            queries.append(f"@title:{self.title}")

        if self.unread:
            queries.append("@unread:[0 0]")

        result = " ".join(queries) if queries else "*"

        if self.embedding() is not None:
            result = f"({result})=>[KNN {self.offset + self.count} @embeddings $query_embedding AS distance]"

        return result

    def query(self) -> Query:
        query: Query = Query(self.query_string()).paging(self.offset, self.count)

        if self.embedding() is not None:
            query.sort_by("distance", asc=True)
            # query.sort_by("distance", asc=False)
        else:
            query.sort_by("document_id", asc=not self.desc)

        return query.return_fields("id", "distance")

    def query_params(self) -> Optional[Dict[str, Any]]:
        if self.embedding() is not None:
            return {"query_embedding": self.embedding().tobytes()}
        return None

    def get_score(self, distance: str) -> float:
        if self.embedding() is not None:
            # The embedding value is normalized to L2.
            # Therefore, the Inner Product(IP) value is between -1 and 1, just like Cosine Similarity.
            # But Redis already normalize distance to be between 0 and 1.
            return min(max(round(1.0 - float(distance), 4), 0), 1)
        return None

    def search(
        self, index_name: str, pipeline: Pipeline, redis_client: Optional[Redis] = None
    ) -> List[SearchResult]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        self._pipeline = pipeline

        if self.vector_search_document and self.embedding() is None:
            return []

        result = redis_client.ft(index_name).search(self.query(), self.query_params())

        search_results = []
        for document in result.docs:
            document_id = document.id[len("document:") :]

            op = original_post(document_id, redis_client)
            assert op is not None, document_id

            score = self.get_score(getattr(document, "distance", "1.0"))

            search_results.append(SearchResult(id=document_id, op=op, score=score))

        return search_results


class OriginalPost(TypedDict):
    id: str
    url: str


def original_post(
    document_id: str, redis_client: Optional[Redis] = None
) -> Union[OriginalPost, None]:
    if redis_client is None:
        redis_client = Redis(connection_pool=redis_pool.pool)

    if (
        document := redis_client.json().get(
            keyjoin("document", document_id), "category", "url", "metadata"
        )
    ) is None:
        return None

    # TODO: Add when webpage, arxiv?
    if document["category"] == "tweet":
        url = urljoin(Twitter._URL, document["metadata"]["thread_ids"][0])
        id = Document.url_to_id(url)
        assert id is not None
        return {"id": id, "url": url}

    return {"id": document_id, "url": document["url"]}


def search(
    index_name: str,
    query_model: QueryModel,
    pipeline: Pipeline,
    redis_client: Optional[Redis] = None,
) -> Tuple[List[SearchResult], Union[int, None]]:
    if redis_client is None:
        redis_client = Redis(connection_pool=redis_pool.pool)

    search_results, next_cursor = range_until_original_post(
        index_name, query_model, pipeline, redis_client
    )

    if (
        op := original_post(query_model.vector_search_document, redis_client)
    ) is not None:
        search_results = remove_vector_search_document_op(search_results, op)

    return search_results, next_cursor


def range_until_original_post(
    index_name: str,
    query_model: QueryModel,
    pipeline: Pipeline,
    redis_client: Redis,
) -> Tuple[List[str], Union[int, None]]:
    search_results = query_model.search(index_name, pipeline, redis_client)

    if len(search_results) == 0:
        return [], None

    search_results = [
        search_result for search_result in search_results if search_result.is_op
    ]

    remain_count = query_model.count - len(search_results)

    next_cursor = query_model.exclusive_end
    while True:
        next_search_results = query_model.model_copy(
            update={"offset": next_cursor, "count": 1}
        ).search(index_name, pipeline, redis_client)

        # Reached the end
        if len(next_search_results) == 0:
            next_cursor = None
            break

        if next_search_results[0].is_op:
            if remain_count == 0:
                break
            else:
                search_results.append(next_search_results[0])
                remain_count -= 1

        next_cursor += 1

    return search_results, next_cursor


def remove_vector_search_document_op(
    search_results: List[SearchResult], vector_search_document_op: OriginalPost
) -> List[SearchResult]:
    return [
        search_result
        for search_result in search_results
        if search_result.op["id"] != vector_search_document_op["id"]
    ]


def index_exists(
    index_name: str,
    redis_client: Optional[Redis] = None,
) -> bool:
    if redis_client is None:
        redis_client = Redis(connection_pool=redis_pool.pool)

    return index_name in redis_client.execute_command("FT._LIST")
