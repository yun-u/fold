from pathlib import Path
from typing import Union

from huggingface_hub import hf_hub_download
from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTOptimizer, ORTQuantizer
from optimum.onnxruntime.configuration import (
    AutoOptimizationConfig,
    AutoQuantizationConfig,
)


# optimize and quantize: https://discuss.huggingface.co/t/optimize-and-quantize-with-optimum/23675/7
def to_onnx(model_id: str, save_dir: Union[str, Path]) -> None:
    if model_id in ("jinaai/jina-embeddings-v2-base-en",):
        # https://huggingface.co/jinaai/jina-bert-implementation/discussions/7
        model_path = Path(hf_hub_download(repo_id=model_id, filename="model.onnx"))
        model_dir, file_name = model_path.parent, model_path.name
        model = ORTModelForFeatureExtraction.from_pretrained(model_dir, file_name=file_name)  # fmt: skip
    else:
        model = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)

    Path(save_dir).mkdir(parents=True, exist_ok=True)

    optimizer = ORTOptimizer.from_pretrained(model)
    optimization_config = AutoOptimizationConfig.O2()
    optimizer.optimize(save_dir=save_dir, optimization_config=optimization_config)

    # https://en.wikipedia.org/wiki/AVX-512
    quantizer = ORTQuantizer.from_pretrained(save_dir, "model_optimized.onnx")
    dqconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)
    quantizer.quantize(save_dir=save_dir, quantization_config=dqconfig)
