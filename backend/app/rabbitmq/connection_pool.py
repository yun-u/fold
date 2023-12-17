import logging
import queue
import threading
from typing import Union

import pika
from pika.exceptions import AMQPConnectionError

from .connect import connect


class ConnectionPool:
    def __init__(
        self,
        max_connections: int,
        max_retries: int = 10,
        retry_delay_seconds: float = 5.0,
    ) -> None:
        self.max_connections = max_connections
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        self.created_connections = 0
        self.queue = queue.Queue()
        self._lock = threading.Lock()

    def get_connection(
        self, timeout: Union[float, None] = None
    ) -> pika.BlockingConnection:
        with self._lock:
            while True:
                if self.queue.empty():
                    if self.created_connections < self.max_connections:
                        return self.create_connection()

                    logging.info(
                        "Maximum allowed connections exceeded. Please wait until a connection is released."
                    )

                connection: pika.BlockingConnection = self.queue.get(timeout=timeout)
                self.queue.task_done()

                if connection.is_closed:
                    logging.info(
                        f"[{self.created_connections}-1] Connection was already closed."
                    )
                    self.created_connections -= 1
                    continue

                return connection

    def create_connection(self) -> pika.BlockingConnection:
        try:
            connection = connect(self.max_retries, self.retry_delay_seconds)
            logging.info(
                f"[{self.created_connections}+1] Connection successfully created."
            )
            self.created_connections += 1
        except AMQPConnectionError as e:
            logging.critical(e)
        return connection

    def release(self, connection: pika.BlockingConnection) -> None:
        self.queue.put_nowait(connection)


connection_pool = ConnectionPool(max_connections=32)
