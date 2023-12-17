import asyncio
import functools
from threading import Thread
from typing import Awaitable, Callable, TypeVar

from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


class EventLoopThread(Thread):
    """Thread subclass for running event loop in separate threads."""

    def __init__(
        self,
        target: Callable[P, Awaitable[R]],
        args=(),
        kwargs={},
        *,
        daemon: bool = True,
    ) -> None:
        super().__init__(None, target, None, args, kwargs, daemon=daemon)
        self._return: R = None

    def run(self) -> None:
        """Runs the target coroutine in the thread and captures its return value."""
        self._return = asyncio.run(self._target(*self._args, **self._kwargs))


def apply_sync(async_function: Callable[P, Awaitable[R]]):
    """Wraps a coroutine function to run it synchronously in a separate thread.

    Args:
        async_function: The coroutine function to be wrapped.

    Returns:
        A regular function that, when called, runs the original coroutine
        synchronously in a separate thread and returns its result.
    """

    @functools.wraps(async_function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        thread = EventLoopThread(async_function, args, kwargs)
        thread.start()
        thread.join()
        return thread._return

    return wrapper


def apply_async(sync_function: Callable[P, R]):
    """Wraps a function to run it asynchronously in the event loop.

    Args:
        sync_function: The function to be wrapped.

    Returns:
        A coroutine function that, when awaited, runs the original function
        asynchronously in the event loop.
    """

    @functools.wraps(sync_function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(
            None, functools.partial(sync_function, *args, **kwargs)
        )

    return wrapper
