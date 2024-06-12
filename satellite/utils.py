from textwrap import indent
from typing import Any, Iterator, List


class Places(list):
    __slots__ = ("base", "skip_zero")

    base: int
    skip_zero: bool

    def __init__(self, base: int, skip_zero: bool = True):
        super().__init__([0])

        self.base = base
        self.skip_zero = skip_zero

    def incr(self) -> List[int]:
        self[0] += 1
        self.carry()
        return self

    def carry(self) -> None:
        i = 0
        while True:
            if self[i] < self.base:
                break

            self[i] = 0
            if len(self) == i + 1:
                self.append(1 if self.skip_zero else 0)
            else:
                self[i + 1] += 1

            i += 1


class SlotClass:
    __slots__ = ()

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
    def __keys__(cls) -> Iterator[Any]:
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
        slot_lines = tuple(indent(repr(v), "  ") + "," for v in self.__values__())
        last_line = ")"

        lines = (first_line,) + slot_lines + (last_line,)
        return "\n".join(lines)

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        for x, y in zip(self.__values__(), other.__values__()):
            if x != y:
                return False

        return True
