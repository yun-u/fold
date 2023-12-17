import logging
import signal
from multiprocessing import Process
from pathlib import Path
from typing import List, Union

import msgpack
import pika.spec
from pika import amqp_object
from pika.adapters.blocking_connection import BlockingChannel
from redis.client import Redis

from app import redis_pool
from app.document import Document
from app.embedding_pipeline.pipeline import Pipeline
from app.embedding_pipeline.utils import extract_model_id
from app.rabbitmq import Consumer, Publisher
from app.utils.logger_utils import setup_logger


def get_queue_name(model_path: Union[str, Path]) -> str:
    return ".".join(["embedding", "queue", str(model_path)])


class SentenceEmbeddingPipelinePublisher(Publisher):
    def publish(self, model_path: Union[str, Path], document_id: str) -> None:
        queue = get_queue_name(model_path)

        # self.channel.queue_declare(queue=queue, durable=True)

        super().publish(
            exchange="",
            routing_key=queue,
            message=msgpack.packb(document_id),
        )


class SentenceEmbeddingPipelineConsumer(Consumer):
    def __init__(self, model_path: Union[str, Path]) -> None:
        """Initialize the SentenceEmbeddingPipelineConsumer.

        Args:
            model_path (`Union[str, Path]`): The path to the pipeline.
        """
        super().__init__()

        self.model_path = model_path
        self.pipeline = Pipeline(model_path)
        self.redis_client = Redis(connection_pool=redis_pool.pool)

    def on_request(
        self,
        ch: BlockingChannel,
        method: Union[amqp_object.Method, pika.spec.Basic.Deliver],
        props: Union[amqp_object.Properties, pika.spec.BasicProperties],
        body: bytes,
    ) -> None:
        """Callback function to process incoming messages."""
        logging.debug(
            f"Received message from <{method.exchange}> '{method.routing_key}'"
        )

        document_id = msgpack.unpackb(body)

        if document := Document.from_id(document_id, self.redis_client):
            document.create_and_store_embedding(self.pipeline, self.redis_client)
            logging.info(f"Created embedding for document with ID: {document_id}.")
        else:
            logging.info(f"Document with ID {document_id} not found in Redis.")

        ch.basic_ack(delivery_tag=method.delivery_tag)


class EmbeddingWorkerManager:
    def __init__(self, model_path: Union[str, Path], num_workers: int) -> None:
        """Initialize the EmbeddingWorkerManager.

        Args:
            model_path (`Union[str, Path]`): The path to the pipeline.
            num_workers (`int`): The number of worker processes to start.
        """
        self.model_path = model_path
        self.num_workers = num_workers

        self.processes: List[Process] = []

    @property
    def prefix(self) -> str:
        return f"[{extract_model_id(self.model_path)}]"

    @staticmethod
    def worker_fn(model_path: Union[str, Path]) -> None:
        """Start a worker for the sentence embedding pipeline.

        Args:
            model_path (`Union[str, Path]`): The path to the pipeline.
        """
        setup_logger()

        # TODO: Use `Event` instead of SIGTERM
        def signal_handler(signum, frame):
            signame = signal.Signals(signum).name
            logging.error(f"Received {signame} in subprocess.")
            exit(0)  # raise SystemExit

        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)

        with SentenceEmbeddingPipelineConsumer(model_path) as consumer:
            consumer.consume_messages(get_queue_name(model_path))

        logging.info(f"[{extract_model_id(model_path)}] 👋 Closing consumer...")

    def run(self) -> None:
        """Start and manage the worker processes."""
        self.processes = [
            Process(target=self.worker_fn, args=(self.model_path,))
            for _ in range(self.num_workers)
        ]
        for p in self.processes:
            p.start()
        logging.info(f"{self.prefix} Started {self.num_workers} workers.")
        for p in self.processes:
            p.join()
        logging.info(f"{self.prefix} All workers have finished.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self) -> None:
        if len(self.processes) > 0:
            logging.info(f"{self.prefix} 👋 Closing {len(self.processes)} worker...")
            for p in self.processes:
                if p.is_alive():
                    p.terminate()
        self.processes.clear()
