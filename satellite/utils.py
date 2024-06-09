from textwrap import indent
from typing import Any, Iterator, Tuple


class SlotClass:
    __slots__: Tuple[str, ...] = ()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # set parameters
        for name, param in zip(self.__keys__(), args):
            setattr(self, name, param)
        for name, param in kwargs.items():
            setattr(self, name, param)

        # make sure all parameters are set
        for name in self.__keys__():
            try:
                getattr(self, name)
            except AttributeError:
                raise TypeError(
                    f"{type(self).__name__} requires a setting "
                    f"for the '{name}' parameter"
                )

    @classmethod
    def __keys__(cls) -> Iterator[str]:
        for parent_cls in reversed(cls.__mro__):
            try:
                yield from parent_cls.__slots__
            except AttributeError:
                pass

    def __values__(self) -> Iterator[Any]:
        for k in self.__keys__():
            yield getattr(self, k)

    def __repr__(self) -> str:
        first_line = f"{type(self).__qualname__}("
        slot_lines = tuple(
            indent(repr(v), "  ") + ","
            for v in self.__values__()
        )
        last_line = ")"

        lines = (first_line,) + slot_lines + (last_line,)
        return "\n".join(lines)
