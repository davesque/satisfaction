from textwrap import indent
from typing import Any, Iterator, Tuple, Type


def _get_mro_slots(mro: Tuple[Type[Any], ...]) -> Iterator[str]:
    for cls in reversed(mro):
        if cls is object:
            continue

        # We know that we must have slots here since the metaclass disables
        # multiple inheritance and sets an empty "__slots__" attr on all
        # subclasses by default.  So there's no way for a class to be
        # introduced into the mro (other than the base `object` built-in) that
        # doesn't have a "__slots__" attr.
        yield from cls.__slots__


class SlotMeta(type):
    def __new__(cls, name, bases, attrs):
        if len(bases) > 1:
            # I'm doing this because I don't feel like figuring out how to get
            # mro slots from multiple base classes.  Multiple inheritance also
            # kinda doesn't really work with slots anyway.  See here:
            # https://docs.python.org/3/reference/datamodel.html#object.__slots__
            raise TypeError("multiple inheritance not supported")

        slots = attrs.setdefault("__slots__", ())
        mro_slots = tuple(_get_mro_slots(bases[0].__mro__)) if len(bases) == 1 else ()
        all_slots = mro_slots + slots

        attrs.setdefault("__match_args__", all_slots)
        attrs.setdefault("__keys__", all_slots)

        return super().__new__(cls, name, bases, attrs)


class SlotClass(metaclass=SlotMeta):
    __slots__: Tuple[str, ...]

    __match_args__: Tuple[str, ...]
    __keys__: Tuple[str, ...]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # set parameters
        for name, param in zip(self.__keys__, args):
            setattr(self, name, param)
        for name, param in kwargs.items():
            setattr(self, name, param)

        # make sure all parameters are set
        for name in self.__keys__:
            try:
                getattr(self, name)
            except AttributeError:
                raise TypeError(
                    f"{type(self).__name__} requires a setting "
                    f"for the '{name}' parameter"
                )

    @property
    def __values__(self) -> Iterator[Any]:
        for k in self.__keys__:
            yield getattr(self, k)

    def __repr__(self) -> str:
        first_line = f"{type(self).__qualname__}("
        slot_lines = tuple(indent(repr(v), "  ") + "," for v in self.__values__)
        last_line = ")"

        lines = (first_line,) + slot_lines + (last_line,)
        return "\n".join(lines)

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        for x, y in zip(self.__values__, other.__values__):
            if x != y:
                return False

        return True
