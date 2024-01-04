from __future__ import annotations

import re
from typing import TYPE_CHECKING, List

import grpc
import msgpack

from app.pipeline.fetch.sources.x import Tweet, X
from app.utils.pydantic_utils import instance_from_dict

from . import xservice_pb2, xservice_pb2_grpc

if TYPE_CHECKING:
    from app.document import Document


class Client:
    def __init__(self, server_address: str) -> None:
        self.server_address = server_address
        self.x = X()

    def request(self, url: str) -> List[Tweet]:
        with grpc.insecure_channel(self.server_address) as channel:
            stub = xservice_pb2_grpc.XServiceStub(channel)
            response = stub.FetchTweet(xservice_pb2.TweetRequest(url=url))
            tweets = [
                instance_from_dict(Tweet, msgpack.unpackb(tweet))
                for tweet in response.tweets
            ]
            return tweets

    def match(self, url: str) -> re.Match:
        return self.x.match(url)

    def fetch_document(self, url: str) -> List[Document]:
        tweets = self.request(url)
        return [tweet.to_document() for tweet in tweets]
