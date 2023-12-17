from typing import Any, Type, TypeVar

import pydantic

T = TypeVar("T")


def create_and_validate_instance(__class: Type[T], __obj: Any) -> T:
    """Create and validate an instance of the given class using Pydantic's TypeAdapter.

    This function takes a class type and an object, and creates an instance of the class
    by validating the given object using Pydantic's TypeAdapter. If the object does
    not match the class's schema, it will raise a ValidationError.

    Args:
        __class (`Type[T]`): The class type to create an instance of.
        __obj (`Any`): The object to be validated and used to create the instance.

    Returns:
        `T`: An instance of the given class, validated and created from the input object.

    Raises:
        `pydantic.ValidationError`: If the input object does not match the class's schema.


    Examples:
        ```python
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> user_data = {"name": "Alice", "age": 30}
        >>> user = create_and_validate_instance(User, user_data)

        # The above call will create an instance of the User class using the user_data dictionary.
        # If the user_data does not contain the required keys or has invalid types, a
        # pydantic.ValidationError will be raised.
        ```
    """
    return pydantic.TypeAdapter(__class).validate_python(__obj)


instance_from_dict = create_and_validate_instance


def instance_to_dict(__obj: Any) -> Any:
    """Convert an instance to a dictionary representation.

    This function takes an instance of a Pydantic model and converts it to a dictionary
    representation using Pydantic's built-in functionality.

    Args:
        obj (`Any`): The instance to be converted to a dictionary.

    Returns:
        `Any`: A dictionary representation of the input instance.

    Examples:
        This function can be used to convert a Pydantic model instance to a dictionary:

        ```python
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> user_data = {"name": "Alice", "age": 30}
        >>> user = User(**user_data)
        >>> user_dict = instance_to_dict(user)

        # The above call will convert the user instance to a dictionary representation
        # with the same key-value pairs as in the original dictionary `user_data`.
        ```

    NOTE: `__obj` can be `dataclass` too.
    """
    return pydantic.RootModel[type(__obj)](__obj).model_dump()
