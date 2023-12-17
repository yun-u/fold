import os
from pathlib import Path
from typing import Union

ONNX_MODEL_HOME = os.environ["ONNX_MODEL_HOME"]


def extract_model_id(model_path: Union[str, Path]) -> str:
    return "/".join(Path(model_path).parent.parts[-2:])


def validate_model_path(model_id: str) -> str:
    model_path = Path(ONNX_MODEL_HOME, model_id, "model_optimized_quantized.onnx")
    if model_path.exists():
        return str(model_path)
    raise FileNotFoundError(model_path)
