from __future__ import annotations

import functools
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, TypedDict, Union

import numpy as np
from celery import Task
from redis.client import Redis

from app.document import Document
from app.pipeline.celery import app
from app.redis_pool import pool

from .model import Pipeline, to_onnx
from .model.utils import get_model_path

ONNX_MODEL_HOME = os.environ["ONNX_MODEL_HOME"]
MODEL_DOWNLOAD_TIMEOUT = 60 * 5


class Embed(Task):
    def __init__(self) -> None:
        self._pipeline: Dict[str, Pipeline] = {}

    @functools.cached_property
    def redis_client(self) -> Redis:
        return Redis(connection_pool=pool)

    def pipeline(self, model_id: str) -> Pipeline:
        if model_id not in self._pipeline:
            logging.info(f"Loading Pipeline: '{model_id}'")

            model_path = self.prepare_model(model_id)
            self._pipeline[model_id] = Pipeline(model_path)

        return self._pipeline[model_id]

    def prepare_model(self, model_id: str) -> Path:
        model_path = get_model_path(model_id)
        model_dir = model_path.parent

        with self.redis_client.lock(model_id, timeout=MODEL_DOWNLOAD_TIMEOUT):
            if not model_path.exists():
                to_onnx(model_id, model_dir)

        return model_path


class EmbedSource(TypedDict):
    text: str
    is_document_id: bool


@app.task(base=Embed, bind=True)
def embed(self: Embed, source: EmbedSource, model_id: str) -> Union[None, bytes]:
    if source["is_document_id"]:
        document_id = source["text"]

        if (document := Document.from_id(document_id)) is None:
            return

        if document.is_embedded(model_id):
            return

        # TODO: Redis lock?
        document.create_and_store_embedding(self.pipeline(model_id), self.redis_client)

        logging.info(f"Created embedding for document with ID: {document_id}.")
    else:
        embedding = self.pipeline(model_id)(source["text"])
        return pickle.dumps(embedding.astype(np.float32))
