import os

from celery import Celery

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "127.0.0.1")


app = Celery(
    "pipeline",
    backend="rpc://",
    broker=f"amqp://guest@{RABBITMQ_HOST}:5672",
    include=[
        "app.pipeline.tasks",
        "app.pipeline.embed.tasks",
        "app.pipeline.fetch.tasks",
    ],
)

app.conf.update(
    accept_content=["msgpack"],
    result_serializer="msgpack",
    task_serializer="msgpack",
    # worker_concurrency=2,
    # worker_prefetch_multiplier=1,
    # worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(filename)s:%(lineno)s] %(message)s",
)

if __name__ == "__main__":
    app.start()
