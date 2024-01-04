import logging
import pickle
import time

from app.pipeline.embed.tasks import EmbedSource, embed
from app.pipeline.tasks import process

model_id = "thenlper/gte-base"


def test_process():
    # https://docs.celeryq.dev/en/4.0/whatsnew-4.0.html#the-task-base-class-no-longer-automatically-register-tasks

    urls = [
        "https://twitter.com/karpathy/status/1657949234535211009",
    ]

    for url in urls:
        start = time.time()
        res = process(url, model_id)
        logging.info(f"[{time.time() - start:.4f}] {res}")


def test_embed():
    start = time.time()

    res = embed.delay(EmbedSource(text="Hello, World!", is_document_id=False), model_id)
    embedding = res.get()

    logging.info(f"[{time.time() - start:.4f}] {pickle.loads(embedding).shape}")
