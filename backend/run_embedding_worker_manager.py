import argparse
import os
from multiprocessing import Process  # noqa: F401
from pathlib import Path
from typing import Union

from app.embedding_pipeline.utils import validate_model_path
from app.embedding_pipeline.worker import EmbeddingWorkerManager
from app.utils.logger_utils import setup_logger

MODEL_ID = os.environ["MODEL_ID"]


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num-workers", default=4, type=int, help="the number of processes to use"
    )
    return parser


def run(model_path: Union[str, Path], num_workers: int = 1):
    setup_logger()

    with EmbeddingWorkerManager(model_path, num_workers) as manager:
        manager.run()


def main(args: argparse.Namespace) -> None:
    setup_logger()

    model_path = validate_model_path(MODEL_ID)

    p = Process(target=run, args=(model_path, args.num_workers))
    p.start()
    p.join()


if __name__ == "__main__":
    parser = get_args_parser()
    args = parser.parse_args()
    main(args)
