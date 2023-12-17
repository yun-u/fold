import time
from typing import List

from redis.client import Redis


def keyjoin(*names: List[str], delimiter: str = ":") -> str:
    """Join multiple string arguments into a Redis key format.

    This function takes a variable number of string arguments and joins them together using the
    Redis delimiter ":". The resulting string is formatted as a Redis key, which can be used for
    indexing and organizing data in a Redis database.

    Args:
        *names (`List[str]`): Variable number of string arguments to be joined.

        delimiter (`str`, optional): The delimiter to be used for joining the strings.
            Default is ":".

    Returns:
        `str`: The Redis key formed by joining the input strings with the specified delimiter.

    Raises:
        AssertionError: If no arguments are provided for joining.
    """
    assert len(names) > 0, "At least one argument is required for joining."
    return delimiter.join(names)


def milliseconds() -> int:
    """Get the current time in milliseconds since the epoch.

    Returns:
        `int`: The current time in milliseconds.
    """
    return time.time_ns() // 1000_000


def zadd_with_timestamps(redis_client: Redis, name: str, *keys: str) -> int:
    """Add keys to a sorted set in Redis with scores based on current time in milliseconds.

    Args:
        redis_client (`Redis`): The Redis client instance.
        name (`str`): The name of the sorted set.
        keys (`str`): Keys to be added to the sorted set.

    Returns:
        `int`: The number of elements added to the sorted set.
    """
    score = milliseconds()
    return redis_client.zadd(name, {key: score + i for i, key in enumerate(keys)})
