from pathlib import Path

from app.pipeline.embed.model import to_onnx


def test_to_onnx():
    model_ids = [
        "sentence-transformers/msmarco-distilbert-base-v4",
        "thenlper/gte-base",
        "jinaai/jina-embeddings-v2-base-en",
    ]

    onnx_dir = "__onnx"
    for model_id in model_ids:
        path = Path(onnx_dir, model_id)
        to_onnx(model_id, path)
