import functools
from pathlib import Path
from typing import Any, Dict, Union

import torch
import torch.nn.functional as F
import transformers
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers.modeling_outputs import BaseModelOutput, ModelOutput
from transformers.pipelines.base import GenericTensor

from app.embedding_pipeline.preprocess import preprocess_text
from app.embedding_pipeline.utils import extract_model_id


class SentenceEmbeddingPipeline(transformers.Pipeline):
    def _sanitize_parameters(self, **pipeline_parameters):
        return {}, {}, {}

    def preprocess(
        self, inputs: Any, **preprocess_parameters: Dict
    ) -> Dict[str, GenericTensor]:
        encoded_inputs = self.tokenizer(
            inputs, padding=True, truncation=True, return_tensors="pt"
        )
        return encoded_inputs

    def _forward(
        self, input_tensors: Dict[str, GenericTensor], **forward_parameters: Dict
    ) -> ModelOutput:
        outputs: BaseModelOutput = self.model(**input_tensors)
        return {"outputs": outputs, "attention_mask": input_tensors["attention_mask"]}

    def postprocess(
        self, model_outputs: ModelOutput, **postprocess_parameters: Dict
    ) -> Any:
        sentence_embeddings = self.mean_pooling(
            model_outputs["outputs"], model_outputs["attention_mask"]
        )
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings

    # Mean Pooling - Take attention mask into account for correct averaging
    @staticmethod
    def mean_pooling(model_output: ModelOutput, attention_mask: torch.Tensor):
        token_embeddings = model_output[
            0
        ]  # First element of model_output contains all token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )


def load_model_pipeline(model_path: Union[str, Path]) -> SentenceEmbeddingPipeline:
    path = Path(model_path)
    model_dir, file_name = path.parent, path.name

    model = ORTModelForFeatureExtraction.from_pretrained(model_dir, file_name=file_name)
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)

    pipeline = SentenceEmbeddingPipeline(
        model=model, tokenizer=tokenizer, framework="pt", device="cpu", batch_size=1
    )
    return pipeline


class Pipeline:
    def __init__(self, model_path: Union[str, Path]) -> None:
        self.model_path = Path(model_path)
        self.pipeline = load_model_pipeline(model_path)

    @functools.cached_property
    def model_id(self) -> str:
        return extract_model_id(self.model_path)

    def __call__(self, text: str) -> torch.Tensor:
        chunks = preprocess_text(text, self.pipeline.tokenizer)
        embeddings = torch.cat(self.pipeline(chunks), dim=0)
        return embeddings
