import logging
import os
from concurrent import futures

import grpc
import msgpack

from app.pipeline.fetch.sources.x import X
from app.utils.pydantic_utils import instance_to_dict

from . import xservice_pb2, xservice_pb2_grpc

PORT = 50051


class XService(xservice_pb2_grpc.XServiceServicer):
    def __init__(self, headless: bool, login: bool, verbose: bool) -> None:
        super().__init__()
        self.headless = headless
        self.login = login
        self.verbose = verbose

        self.x = X(headless=headless)

        if login:
            x_id, x_password = os.getenv("X_ID"), os.getenv("X_PASSWORD")

            if x_id and x_password:
                self.x.login(x_id, x_password)
            else:
                logging.error("Insufficient information to log in.")

    def FetchTweet(self, request, context):
        try:
            tweets = self.x.fetch(url=request.url, verbose=self.verbose)
            packed = [msgpack.packb(instance_to_dict(tweet)) for tweet in tweets]
            return xservice_pb2.TweetResponse(tweets=packed)
        except Exception as e:
            return xservice_pb2.TweetResponse(
                error=xservice_pb2.Error(code="", message=str(e))
            )


class Server:
    def __init__(
        self,
        service: XService,
        max_workers: int = 1,
        port: int = 50051,
    ) -> None:
        self.service = service
        self.max_workers = max_workers
        self.port = port

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
        xservice_pb2_grpc.add_XServiceServicer_to_server(service, self.server)
        self.server.add_insecure_port(f"[::]:{port}")

    def start(self) -> None:
        self.server.start()
        self.server.wait_for_termination()

    def close(self) -> None:
        self.service.x.quit()


if __name__ == "__main__":
    # python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. xservice.proto
    try:
        server = Server(XService(headless=True, login=False, verbose=True), port=PORT)
        server.start()
    finally:
        server.close()
