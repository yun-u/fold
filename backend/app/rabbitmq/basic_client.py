from __future__ import annotations

import threading

from typing_extensions import Self

from .connect import connect


class BasicPikaClient:
    """A basic RabbitMQ client using the pika library.

    This class provides a simple interface for establishing and managing
    connections to a RabbitMQ server.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.connection = connect()
        self.channel = self.connection.channel()

    def close(self) -> None:
        """
        Closes the connection to the RabbitMQ server.
        """
        self.channel.close()
        self.connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        return self.close()
