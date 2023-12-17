import abc
import inspect


class Interface(abc.ABC):
    @classmethod
    def __subclasshook__(cls, C):
        sigs = {
            fn_name: inspect.signature(getattr(cls, fn_name))
            for fn_name in cls.__abstractmethods__
        }

        for B in C.__mro__:
            if all(
                [
                    fn_name in B.__dict__
                    and inspect.signature(B.__dict__[fn_name]) == sig
                    for fn_name, sig in sigs.items()
                ]
            ):
                return True
        return False
