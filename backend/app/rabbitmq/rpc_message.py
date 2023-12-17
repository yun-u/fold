from __future__ import annotations

from typing import Any, Dict, Tuple

import msgpack
from pydantic import BaseModel, Field


class RpcMessage(BaseModel):
    id: str
    args: Tuple = ()
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    response: Any = None

    def encode(self) -> bytes:
        return msgpack.packb(self.model_dump())

    @staticmethod
    def decode(body: bytes) -> RpcMessage:
        return RpcMessage(**msgpack.unpackb(body))
