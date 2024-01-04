# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import xservice_pb2 as xservice__pb2


class XServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.FetchTweet = channel.unary_unary(
            "/XService/FetchTweet",
            request_serializer=xservice__pb2.TweetRequest.SerializeToString,
            response_deserializer=xservice__pb2.TweetResponse.FromString,
        )


class XServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def FetchTweet(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_XServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "FetchTweet": grpc.unary_unary_rpc_method_handler(
            servicer.FetchTweet,
            request_deserializer=xservice__pb2.TweetRequest.FromString,
            response_serializer=xservice__pb2.TweetResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "XService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class XService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def FetchTweet(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/XService/FetchTweet",
            xservice__pb2.TweetRequest.SerializeToString,
            xservice__pb2.TweetResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )