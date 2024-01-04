import logging
import pickle
import time

from app.pipeline.embed.tasks import EmbedSource, embed

model_id = "thenlper/gte-base"


def test_embed():
    start = time.time()

    embedding = embed(EmbedSource(text="Hello, World!", is_document_id=False), model_id)

    logging.info(f"[{time.time() - start:.4f}] {pickle.loads(embedding).shape}")
