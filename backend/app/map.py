from __future__ import annotations

import copy
from typing import Dict, Iterator, Mapping


def is_valid_variable_name(name: str) -> bool:
    """Check if the given string is a valid Python variable name.

    Args:
        name (`str`): The string to check.

    Returns:
        `bool`: True if the string is a valid Python identifier, False otherwise.
    """
    return name.isidentifier()


class Map(Mapping):
    """A recursive data structure representing a nested dictionary.

    The Map class allows accessing dictionary elements using attribute-like syntax.

    Attributes:
        _data (`dict`): The internal dictionary representation of the Map.

    Examples:
        ```python
        >>> data_dict = {'a': 1, 'b': {'c': 2}}
        >>> my_map = Map(data_dict)
        >>> print(my_map.a)  # Output: 1
        >>> print(my_map.b.c)  # Output: 2
        ```
    """

    def __init__(self, data_dict: Dict):
        assert isinstance(data_dict, dict)
        self.validate_variable_name(data_dict)
        self._parse_and_update(data_dict)
        self._initialized = True  # Set the flag to True after __init__ is called

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in self._data.items()])})"

    def __iter__(self) -> Iterator:
        return iter(self._data.keys())

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setattr__(self, name, value):
        if hasattr(self, "_initialized") and self._initialized:
            raise AttributeError("Cannot modify attributes after initialization.")
        super().__setattr__(name, value)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    @staticmethod
    def validate_variable_name(data_dict: Dict) -> None:
        """Check if all keys in the given dictionary are valid variable names.

        Args:
            data_dict (`dict`): The dictionary to check.

        Raises:
            ValueError: If any key in the dictionary is not a valid variable name,
                        with an appropriate error message indicating the problematic key.
        """
        for name in data_dict:
            if not is_valid_variable_name(name):
                raise ValueError(f"Invalid variable name: {name}")

    def _parse(self, data_dict: Dict) -> Dict:
        """Recursively parse a nested dictionary and convert it to a Map.

        Args:
            data_dict (`dict`): The dictionary to parse.

        Returns:
            `dict`: The resulting Map after parsing the nested dictionary.
        """
        return {
            k: self.__class__(v) if isinstance(v, dict) else v
            for k, v in data_dict.items()
        }

    def _parse_and_update(self, data_dict: Dict) -> None:
        """Parse the given dictionary and update the Map's data.

        Args:
            data_dict (`dict`): The dictionary to parse and update the Map's data.
        """
        if not hasattr(self, "_data"):
            self._data = {}
        parsed = self._parse(data_dict)
        self._data.update(parsed)
        self.__dict__.update(parsed)

    def _unparse(self, data_dict: Dict) -> Dict:
        """Recursively convert a Map back to a nested dictionary.

        Args:
            data_dict (`dict`): The Map to convert back to a dictionary.

        Returns:
            `dict`: The resulting dictionary after converting the Map.
        """
        return {
            k: self._unparse(v._data) if isinstance(v, Map) else v
            for k, v in data_dict.items()
        }

    def to_dict(self) -> Dict:
        """Convert the Map to a regular dictionary.

        Returns:
            `dict`: A copy of the Map as a nested dictionary.
        """
        return copy.deepcopy(self._unparse(self._data))


class MutableMap(Map):
    """A subclass of Map that allows modification of attributes after initialization."""

    def __setattr__(self, name, value):
        if hasattr(self, "_initialized") and self._initialized:
            self.validate_variable_name({name: value})
            self._parse_and_update({name: value})
        else:
            super().__setattr__(name, value)
