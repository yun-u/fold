from pathlib import Path
from typing import Union

from optimum.onnxruntime import (
    AutoQuantizationConfig,
    OptimizationConfig,
    ORTModelForFeatureExtraction,
    ORTOptimizer,
    ORTQuantizer,
)


# optimize and quantize: https://discuss.huggingface.co/t/optimize-and-quantize-with-optimum/23675/7
def to_onnx(model_id: str, save_dir: Union[str, Path]) -> None:
    model = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)

    optimizer = ORTOptimizer.from_pretrained(model)
    optimization_config = OptimizationConfig(optimization_level=99)
    optimizer.optimize(save_dir=save_dir, optimization_config=optimization_config)

    # https://en.wikipedia.org/wiki/AVX-512
    quantizer = ORTQuantizer.from_pretrained(save_dir, "model_optimized.onnx")
    dqconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)
    quantizer.quantize(save_dir=save_dir, quantization_config=dqconfig)


if __name__ == "__main__":
    from transformers import AutoModel

    model_id = "sentence-transformers/msmarco-distilbert-base-v4"
    model_id = "thenlper/gte-base"

    model = AutoModel.from_pretrained(model_id)
    path = Path("onnx", model_id)
    path.mkdir(parents=True)
    to_onnx(model_id, path)
