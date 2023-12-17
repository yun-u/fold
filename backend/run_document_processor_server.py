import argparse
from multiprocessing import Process
from typing import Dict

from app.document_processor import DocumentFetcher, DocumentProcessorWorkerManager
from app.sources import Arxiv, Twitter, WebPage
from app.utils.logger_utils import setup_logger


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num-workers", default=4, type=int, help="the number of processes to use"
    )
    return parser


def run(num_workers: int):
    from app.secrets import secrets

    setup_logger()

    with Twitter(headless=True) as twitter:
        twitter.login(secrets.twitter.id, secrets.twitter.password)

        def initialize_fetchers() -> Dict[str, DocumentFetcher]:
            return {
                "arxiv": Arxiv(),
                "twitter": twitter,
                "webpage": WebPage(),
            }

        with DocumentProcessorWorkerManager(
            initialize_fetchers, num_workers
        ) as manager:
            manager.run()


def main(args: argparse.Namespace) -> None:
    setup_logger()

    p = Process(target=run, args=(args.num_workers,))
    p.start()
    p.join()


if __name__ == "__main__":
    parser = get_args_parser()
    args = parser.parse_args()
    main(args)
