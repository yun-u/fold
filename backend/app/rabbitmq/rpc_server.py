import logging
import threading
from typing import Any, Union

import pika
import pika.spec
from pika import amqp_object
from pika.adapters.blocking_connection import BlockingChannel

from .basic_client import BasicPikaClient
from .rpc_message import RpcMessage

SERVER_QUEUE = "rpc.server.queue"


class RpcServer(BasicPikaClient):
    def __init__(self, queue: str = SERVER_QUEUE):
        """Initialize the RpcServer.

        This class represents an RPC (Remote Procedure Call) server for RabbitMQ.
        It sets up the connection and declares the server queue.

        Args:
            queue(`str`): The queue name; if empty string, the broker will create a unique queue name.
        """
        super().__init__()
        self.channel.queue_declare(queue=queue, durable=True)
        self.thread = threading.Thread(target=self.consume_messages, daemon=True)
        self.thread.start()

    def consume_messages(self) -> None:
        """Start consuming messages from the server queue.

        This function starts consuming messages from the server queue and calls the
        `on_request` callback function for processing each incoming request.
        """
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(SERVER_QUEUE, self.on_request)
        logging.debug("[*] Waiting for messages. To exit press CTRL+C")
        self.channel.start_consuming()
        logging.error("[x] Stop consuming")

    def run(self) -> None:
        """Run the RPC server.

        This function runs the RPC server by calling the 'consume_messages' method.
        """
        self.thread.start()

    def wait_until_terminate(self) -> None:
        self.thread.join()

    def on_request(
        self,
        ch: BlockingChannel,
        method: Union[amqp_object.Method, pika.spec.Basic.Deliver],
        props: Union[amqp_object.Properties, pika.spec.BasicProperties],
        body: bytes,
    ):
        """Callback function to handle incoming requests.

        This function is called when a request is received from an RPC client.
        It calls the `process_request` method to handle the incoming request,
        and then sends back the response to the client.

        Args:
            ch (`BlockingChannel`): The RabbitMQ channel.
            method (`Union[amqp_object.Method, pika.spec.Basic.Deliver]`): The method frame.
            props (`Union[amqp_object.Properties, pika.spec.BasicProperties]`): The message properties.
            body (`bytes`): The request body received from the client.
        """

        rpc_message = RpcMessage.decode(body)
        rpc_message.response = self.process_request(
            *rpc_message.args, **rpc_message.kwargs
        )

        ch.basic_publish(
            "",
            routing_key=props.reply_to,
            body=rpc_message.encode(),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def process_request(self, *args: Any, **kwargs: Any) -> Any:
        """Process an incoming request.

        This function is meant to be overridden in the subclass to handle incoming
        requests. It takes the request `message` as input and should return the response
        to be sent back to the RPC client.

        Args:

        Returns:
            `Any`: The response to be sent back to the RPC client.
        """
        raise NotImplementedError()
