from typing import Callable, Hashable, Iterable, Iterator, TypeVar, Union

T = TypeVar("T")


class OrderedSet:
    def __init__(
        self,
        value: Union[T, Iterable[T]],
        generate_key: Union[Callable[[T], Hashable], None] = None,
    ) -> None:
        self.generate_key = generate_key
        self.keys, self.values = set(), []

        self.add(value)

    def add(self, value: Union[T, Iterable[T]]) -> None:
        try:
            iterator = iter(value)
        except TypeError:
            iterator = [value]

        for i in iterator:
            self._add(i)

    def _add(self, value: T) -> None:
        key = self.generate_key(value) if self.generate_key else value
        if key not in self.keys:
            self.keys.add(key)
            self.values.append(value)

    def __len__(self) -> int:
        return len(self.values)

    def __contains__(self, value: T) -> bool:
        return value in self.keys

    def __iter__(self) -> Iterator[T]:
        return iter(self.values)

    def __repr__(self) -> str:
        return str(self.values)
