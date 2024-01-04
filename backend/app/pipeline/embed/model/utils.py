import os
from pathlib import Path
from typing import Union

ONNX_MODEL_HOME = os.environ["ONNX_MODEL_HOME"]


def extract_model_id(model_path: Union[str, Path]) -> str:
    return "/".join(Path(model_path).parent.parts[-2:])


def get_model_path(model_id: str) -> Path:
    return Path(ONNX_MODEL_HOME, model_id, "model_optimized_quantized.onnx")


def validate_model_path(model_id: str) -> str:
    model_path = get_model_path(model_id)
    if model_path.exists():
        return str(model_path)
    raise FileNotFoundError(model_path)
