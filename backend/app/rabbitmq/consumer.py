import logging
from typing import Union

import pika
import pika.spec
from pika import amqp_object
from pika.adapters.blocking_connection import BlockingChannel

from .basic_client import BasicPikaClient


class Consumer(BasicPikaClient):
    def on_request(
        self,
        ch: BlockingChannel,
        method: Union[amqp_object.Method, pika.spec.Basic.Deliver],
        props: Union[amqp_object.Properties, pika.spec.BasicProperties],
        body: bytes,
    ) -> None:
        raise NotImplementedError()

    def consume_messages(self, queue: str) -> None:
        self.channel.queue_declare(queue=queue, durable=True)

        # This happens because RabbitMQ just dispatches a message when the message enters the queue.
        # It doesn't look at the number of unacknowledged messages for a consumer. It just blindly dispatches every n-th message to the n-th consumer.
        # In order to defeat that we can use the `Channel#basic_qos` channel method with the `prefetch_count=1` setting.
        # This uses the `basic.qos` protocol method to tell RabbitMQ not to give more than one message to a worker at a time.
        # Or, in other words, don't dispatch a new message to a worker until it has processed and acknowledged the previous one.
        # Instead, it will dispatch it to the next worker that is not still busy.
        self.channel.basic_qos(prefetch_count=1)
        self.consumer_tag = self.channel.basic_consume(
            queue=queue, on_message_callback=self.on_request, auto_ack=False
        )
        self.channel.start_consuming()

    def cancel_consumer(self) -> None:
        if hasattr(self, "consumer_tag") and self.consumer_tag:
            self.channel.stop_consuming()
        else:
            logging.error("Failed to cancel consumer: 'consumer_tag' is not set.")
