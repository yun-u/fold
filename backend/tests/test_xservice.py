import logging
import time

from app.xservice.client import Client


def test_client():
    urls = ["https://twitter.com/karpathy/status/1657949234535211009"]

    client = Client("127.0.0.1:50051")

    for url in urls:
        start_time = time.time()
        tweets = client.request(url)
        logging.info(f"[{time.time() - start_time:.4f}] {tweets}")
