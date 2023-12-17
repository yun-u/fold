import abc
import concurrent.futures
import logging
import queue
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Thread, get_native_id
from typing import Callable, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    FileUrl,
    HttpUrl,
    TypeAdapter,
    field_serializer,
    field_validator,
)
from redis.client import Redis
from typing_extensions import Self

from app import redis_pool
from app.document import Document
from app.embedding_pipeline.utils import extract_model_id
from app.embedding_pipeline.worker import SentenceEmbeddingPipelinePublisher
from app.rabbitmq import RpcClient, RpcServer
from app.sources import Twitter
from app.utils.utils import OrderedSet


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


class DocumentProcessor:
    def __init__(
        self,
        fetchers: Dict[str, DocumentFetcher],
        redis_client: Optional[Redis] = None,
    ) -> None:
        self.redis_client = (
            redis_client if redis_client else Redis(connection_pool=redis_pool.pool)
        )
        self.fetchers: Dict[str, DocumentFetcher] = fetchers
        self.embedding_publisher = SentenceEmbeddingPipelinePublisher()

    def get_document_type(self, url: str) -> str:
        for doc_type, fetcher in self.fetchers.items():
            if fetcher.match(url):
                return doc_type
        raise ValueError("Invalid URL. Unable to determine the document type.")

    def fetch_documents(self, url: str) -> List[Document]:
        try:
            fetched = self.fetchers[self.get_document_type(url)].fetch_document(url)
            documents = [fetched] if isinstance(fetched, Document) else fetched
            return documents
        except Exception as e:
            logging.error(e, exc_info=True, stack_info=True)
            return []

    def fetch(self, document: Optional[Document], url: str) -> List[Document]:
        if document is None or document.is_new():
            documents = self.fetch_documents(url)

            with ThreadPoolExecutor(max_workers=max(1, len(documents))) as executor:
                for document_ in documents:
                    executor.submit(document_.store, self.redis_client)

            return documents
        else:
            return [document]

    def embed(
        self, documents: List[Document], model_path: Union[str, Path]
    ) -> List[Document]:
        fetched_documents = [
            document
            for document in documents
            if document.is_fetched(extract_model_id(model_path))
        ]

        with ThreadPoolExecutor(max_workers=max(1, len(fetched_documents))) as executor:
            for document in fetched_documents:
                executor.submit(
                    self.embedding_publisher.publish, model_path, document.id
                )

        return documents

    def process(self, url: str, model_path: Union[str, Path]) -> List[str]:
        # Check if it's already embedded
        if document := Document.from_url(url, self.redis_client):
            if document.is_embedded(extract_model_id(model_path)):
                return list(map(str, document.links))

        documents = self.embed(self.fetch(document, url), model_path)

        # In order to produce the same result as if it were already embedded (Idempotent),
        # returns the `links` of the `Document` that corresponds to the URL given as an argument.
        # Currently, the first item in the `Document` list is the `Document` that corresponds to the given URL.
        if len(documents) > 0:
            return list(map(str, documents[0].links))
        return []

    def close(self) -> None:
        self.embedding_publisher.close()


class Message(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    url: Union[HttpUrl, FileUrl]
    model_path: str

    @field_serializer("url")
    def serialize_url(self, url: Union[HttpUrl, FileUrl], _info) -> str:
        return str(url)

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, value: str) -> str:
        if Path(value).exists():
            return value
        raise FileNotFoundError(value)


def get_thread_id() -> str:
    return f"<{hex(get_native_id())}>"


class DocumentProcessorServer(RpcServer):
    def __init__(self, fetchers: Dict[str, DocumentFetcher]):
        super().__init__()
        self.document_processor = DocumentProcessor(fetchers)

    def process_request(self, url: str, model_path: str) -> List[str]:
        TypeAdapter(Message).validate_python({"url": url, "model_path": model_path})
        links = self.document_processor.process(url, model_path)
        return links

    def close(self):
        super().close()
        for fetcher in self.document_processor.fetchers.values():
            if isinstance(fetcher, Twitter):
                fetcher.quit()
        self.document_processor.close()


class DocumentProcessorWorkerManager:
    def __init__(
        self,
        initialize_fetchers: Callable[[], Dict[str, DocumentFetcher]],
        num_workers: int,
    ) -> None:
        self.initialize_fetchers = initialize_fetchers
        self.num_workers = num_workers
        self.threads: List[Thread] = []
        self.event = Event()

    @staticmethod
    def worker_fn(fetchers: Dict[str, DocumentFetcher], event: Event, worker_id: int):
        logging.info(f"[Worker-{worker_id}] {get_thread_id()} Start RPC server.")
        server = DocumentProcessorServer(fetchers)
        event.wait()
        server.close()
        logging.info(f"[Worker-{worker_id}] 👋 RPC server successfully closed.")

    def run(self) -> None:
        self.threads = [
            Thread(
                target=self.worker_fn,
                args=(self.initialize_fetchers(), self.event, i),
                daemon=True,
            )
            for i in range(self.num_workers)
        ]
        for t in self.threads:
            t.start()
        logging.info(f"Started {self.num_workers} workers.")
        self.event.wait()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self):
        self.event.set()
        for t in self.threads:
            t.join()
        logging.info("All workers have finished.")


class DocumentProcessorClientManager:
    def __init__(self) -> None:
        self.rpc_client = RpcClient()

    def send_rpc_request(self, url: str, model_path: str) -> List[str]:
        return self.rpc_client.send_request(url, model_path)

    @staticmethod
    def squeeze_queue(q: queue.Queue) -> List:
        items = []
        while not q.empty():
            items.append(q.get_nowait())
        return items

    def request(self, url: str, model_path: str) -> List[str]:
        total_links = OrderedSet([url])

        q = queue.Queue()
        q.put_nowait(url)

        while not q.empty():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self.send_rpc_request, link, model_path)
                    for link in self.squeeze_queue(q)
                ]
                for future in concurrent.futures.as_completed(futures):
                    links = future.result()
                    for link in links:
                        # Links may be circular references.
                        if link not in total_links:
                            q.put_nowait(link)
                            total_links.add([link])

        return list(total_links)
