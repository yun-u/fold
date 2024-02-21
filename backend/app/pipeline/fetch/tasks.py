import abc
import functools
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Union

from celery import Task
from redis.client import Redis

from app.document import Document
from app.pipeline.celery import app
from app.pipeline.embed.tasks import EmbedSource, embed
from app.redis_pool import pool
from app.xservice.client import Client as XRPCClient

from .sources.arxiv import Arxiv
from .sources.webpage import WebPage

ARXIV_HOME = os.getenv("ARXIV_HOME", ".")
XSERVICE_HOST = os.getenv("XSERVICE_HOST", "127.0.0.1")


class DocumentFetcher(abc.ABC):
    __slots__ = ()

    @abc.abstractstaticmethod
    def match(url: str) -> re.Match:
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_document(self, url: str, **kwargs) -> Union[Document, List[Document]]:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, C):
        if cls is DocumentFetcher:
            if any(cls.__abstractmethods__ <= B.__dict__.keys() for B in C.__mro__):
                return True
        return NotImplemented


class Fetcher(Task):
    def __init__(self) -> None:
        # NOTE: the order is important because it checks to see if the URLs match in order.
        self.fetchers: Dict[str, DocumentFetcher] = {
            "arxiv": Arxiv(pdf_dir=ARXIV_HOME, redis_client=self.redis_client),
            "x": XRPCClient(f"{XSERVICE_HOST}:50051"),
            "webpage": WebPage(),
        }

    @functools.cached_property
    def redis_client(self) -> Redis:
        return Redis(connection_pool=pool)

    @staticmethod
    def urls(document: Document) -> List[str]:
        return [str(link) for link in document.links]

    def document_type(self, url: str) -> str:
        for doc_type, fetcher in self.fetchers.items():
            if fetcher.match(url):
                return doc_type
        raise ValueError("Invalid URL. Unable to determine the document type.")

    def fetch(self, url: str) -> List[Document]:
        if isinstance(documents := self.fetchers[self.document_type(url)].fetch_document(url), Document):  # fmt: skip
            documents = [documents]
        return documents

    def store(self, documents: List[Document]) -> None:
        if len(documents) == 0:
            return

        with ThreadPoolExecutor(max_workers=len(documents)) as executor:
            for document in documents:
                executor.submit(document.store, self.redis_client)

    def in_db(self, url: str, model_id: str) -> Optional[List[str]]:
        """Checks if a document is in the database."""
        if document := Document.from_url(url, self.redis_client):
            if document.is_embedded(model_id):
                return self.urls(document)
            if document.is_fetched(model_id):
                embed.delay(EmbedSource(text=document.id, is_document_id=True), model_id)  # fmt: skip
                return self.urls(document)

        return None

    def fetch_and_embed(self, url: str, model_id: str) -> List[str]:
        documents = self.fetch(url)
        self.store(documents)
        embed.delay(EmbedSource(text=documents[0].id, is_document_id=True), model_id)
        return self.urls(documents[0])


@app.task(base=Fetcher, bind=True)
def fetch(self: Fetcher, url: str) -> List[Document]:
    return self.fetch(url)


@app.task(base=Fetcher, bind=True)
def fetch_and_embed(self: Fetcher, url: str, model_id: str) -> List[str]:
    try:
        if (urls := self.in_db(url, model_id)) is not None:
            return urls
        return self.fetch_and_embed(url, model_id)
    except Exception as e:
        logging.error(f"[{url}] [{model_id}] {e}", exc_info=True, stack_info=True)
        return []
