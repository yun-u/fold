import logging
import time

import pika
from pika.exceptions import AMQPConnectionError


def connect(
    max_retries: int = 10, retry_delay_seconds: float = 5.0
) -> pika.BlockingConnection:
    """
    Establishes a connection to the RabbitMQ server.

    Args:
        max_retries (`int`): Maximum number of connection retries. Default is 10.
        retry_delay_seconds (`float`): Delay in seconds between retries. Default is 5.0.

    Returns:
        `pika.BlockingConnection`: The established RabbitMQ connection.

    Raises:
        AMQPConnectionError: If the connection cannot be established after the maximum number
            of retries.
    """
    tries = 0
    while True:
        try:
            connection = pika.BlockingConnection(
                # FIXME: heartbeat=0 would cause
                pika.ConnectionParameters(host="localhost", heartbeat=0)
            )
            if connection.is_open:
                return connection
        except (AMQPConnectionError, Exception) as e:
            logging.error(f"Failed to establish connection: {e}. Retrying...")
            time.sleep(retry_delay_seconds)
            tries += 1
            if tries == max_retries:
                logging.error("Connection retry limit reached.")
                raise AMQPConnectionError(e)
