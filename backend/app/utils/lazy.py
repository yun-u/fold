import inspect
import threading
from typing import Callable, TypeVar

T = TypeVar("T")


class LazyEvaluationError(Exception):
    """
    Custom exception raised when a function with arguments is used with the lazy decorator.
    """

    pass


def lazy(fn: Callable[[], T]) -> Callable[[], T]:
    """
    A decorator that wraps a function to make it lazy-evaluated.

    Args:
        fn (`Callable[[], T]`): The function to be wrapped. Should take no arguments.

    Returns:
        `Callable[[], T]`: The lazy-evaluated version of the function.

    Raises:
        LazyEvaluationError: If the wrapped function takes any arguments.

    Examples:
        ```python
        @lazy
        def expensive_computation() -> int:
            print("Performing expensive computation...")
            return 42

        result = expensive_computation()  # This will execute the computation.
        result = expensive_computation()  # This will return the cached result.
        ```
    Raises:
        LazyEvaluationError: If the wrapped function takes any arguments, this error is raised.

    Notes:
        The decorator ensures that the wrapped function takes no arguments by checking the number
        of parameters in the function's signature. If the wrapped function takes any arguments,
        this error is raised to indicate that the function should be designed to take no arguments
        for proper lazy evaluation behavior.
    """
    if len(inspect.signature(fn).parameters) != 0:
        raise LazyEvaluationError(
            "The lazy-evaluated function should take no arguments."
        )

    instance_lock = threading.RLock()
    _instance: T = None

    def lazy_fn(*args, **kwargs) -> T:
        """
        A wrapper function for lazy evaluation.

        Returns:
            `T`: The result of the lazy-evaluated function.

        Notes:
            The result of the function is cached in the `_instance` variable to
            avoid repeated computation.
        """
        nonlocal _instance
        with instance_lock:
            if _instance is None:
                _instance = fn()
            return _instance

    return lazy_fn
