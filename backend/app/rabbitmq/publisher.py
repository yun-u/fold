import pika
import pika.spec

from .basic_client import BasicPikaClient


class Publisher(BasicPikaClient):
    def publish(self, exchange: str, routing_key: str, message: bytes) -> None:
        with self._lock:
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                ),
            )
