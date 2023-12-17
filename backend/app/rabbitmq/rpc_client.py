import functools
import logging
import threading
import uuid
from typing import Any, Dict, TypeVar, Union

import pika
import pika.spec
from pika import amqp_object
from pika.adapters.blocking_connection import BlockingChannel
from pydantic import BaseModel, ConfigDict, PrivateAttr

from .basic_client import BasicPikaClient
from .rpc_message import RpcMessage

SERVER_QUEUE = "rpc.server.queue"


R = TypeVar("R")


class Request(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    response: Union[R, None] = None

    _event: threading.Event = PrivateAttr(default_factory=threading.Event)

    def set(self) -> None:
        self._event.set()

    def wait(self, timeout: Union[float, None] = None) -> bool:
        return self._event.wait(timeout)


class RpcClient(BasicPikaClient):
    def __init__(self, queue: str = SERVER_QUEUE):
        """Initialize the RpcClient.

        This class represents an RPC (Remote Procedure Call) client for RabbitMQ.
        It sets up the connection, declares the server queue, and configures the
        callback function for handling server responses.

        Args:
            queue(`str`): The queue name; if empty string, the broker will create a unique queue name.
        """
        super().__init__()
        self.channel.queue_declare(queue=queue, durable=True)
        self.requests: Dict[str, Request] = {}
        self.thread = threading.Thread(target=self.consume_messages, daemon=True)
        self.thread.start()

    def consume_messages(self) -> None:
        """Start consuming messages from the server queue.

        This function starts consuming messages from the server queue and calls the
        `on_response` callback function for processing each incoming request.
        """
        self.channel.basic_consume(
            "amq.rabbitmq.reply-to", self.on_response, auto_ack=True
        )
        self.channel.start_consuming()
        logging.error("[x] Stop consuming")

    def wait_until_terminate(self) -> None:
        self.thread.join()

    def on_response(
        self,
        ch: BlockingChannel,
        method: Union[amqp_object.Method, pika.spec.Basic.Deliver],
        props: Union[amqp_object.Properties, pika.spec.BasicProperties],
        body: bytes,
    ):
        """Callback function to handle the server response.

        This function is called when a response is received from the RabbitMQ server.
        It sets the 'response' attribute to the received 'body'.

        Args:
            ch (`BlockingChannel`): The RabbitMQ channel.
            method (`Union[amqp_object.Method, pika.spec.Basic.Deliver]`): The method frame.
            props (`Union[amqp_object.Properties, pika.spec.BasicProperties]`): The message properties.
            body (`bytes`): The response body received from the server.
        """

        rpc_message = RpcMessage.decode(body)
        request = self.requests[rpc_message.id]
        request.response = rpc_message.response
        request.set()

    def callback(self, body: bytes) -> None:
        self.channel.basic_publish(
            exchange="",
            routing_key=SERVER_QUEUE,
            body=body,
            properties=pika.BasicProperties(reply_to="amq.rabbitmq.reply-to"),
        )

    def send_request(self, *args: Any, **kwargs: Any) -> R:
        """Send a request to the RabbitMQ server and wait for the response.

        This function sends a request to the RabbitMQ server and waits
        for the response. The response is stored in the 'response' attribute.

        Args:
            procedure (`Callable[P, R]`): The request procedure to be sent.

        Returns:
            `R`: The response received from the RabbitMQ server.
        """
        request = Request(id=str(uuid.uuid4()))

        self.requests[request.id] = request

        self.connection.add_callback_threadsafe(
            functools.partial(
                self.callback,
                RpcMessage(id=request.id, args=args, kwargs=kwargs).encode(),
            )
        )

        request.wait()
        return request.response
