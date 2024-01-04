import functools
from pathlib import Path
from typing import List, Union

import numpy as np
from jaxtyping import Float32
from optimum.onnxruntime import ORTModel, ORTModelForFeatureExtraction
from transformers import AutoTokenizer, PreTrainedTokenizerBase

from ..preprocess import preprocess_text
from .utils import extract_model_id


class SentenceEmbeddingPipeline:
    def __init__(self, model: ORTModel, tokenizer: PreTrainedTokenizerBase) -> None:
        self.model = model
        self.tokenizer = tokenizer

    def __call__(
        self, text: Union[str, List[str]]
    ) -> Float32[np.ndarray, "batch_size sequence_length embedding_dimension"]:
        encoded_inputs = self.tokenizer(
            text, padding=True, truncation=True, return_tensors="np"
        )
        inputs = {name: encoded_inputs[name] for name in self.model.inputs_names.keys()}

        return self.model.model.run(None, inputs)[0]


def load_onnx_pipeline(model_path: Union[str, Path]) -> SentenceEmbeddingPipeline:
    path = Path(model_path)
    model_dir, file_name = path.parent, path.name

    model = ORTModelForFeatureExtraction.from_pretrained(model_dir, file_name=file_name)
    tokenizer = AutoTokenizer.from_pretrained(model_dir)

    return SentenceEmbeddingPipeline(model=model, tokenizer=tokenizer)


class Pipeline:
    def __init__(self, model_path: Union[str, Path]) -> None:
        self.model_path = Path(model_path)
        self.pipeline = load_onnx_pipeline(model_path)

    @functools.cached_property
    def model_id(self) -> str:
        return extract_model_id(self.model_path)

    def __call__(
        self, text: str
    ) -> Float32[np.ndarray, "batch_size embedding_dimension"]:
        chunks = preprocess_text(text, self.pipeline.tokenizer)
        embeddings = self.pipeline(chunks).mean(axis=1)
        embeddings = embeddings / np.clip(np.linalg.norm(embeddings, ord=2, axis=1, keepdims=True), a_min=1e-12, a_max=None)  # fmt: skip
        return embeddings
