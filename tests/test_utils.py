from textwrap import dedent
from typing import Any, Callable

import pytest

from satellite import utils


class TestClass:
    pass


def test_func() -> None:
    pass


class OneSlot(utils.SlotClass):
    __slots__ = ("foo",)

    foo: Any


class TwoSlot(utils.SlotClass):
    __slots__ = ("foo", "bar")

    foo: Any
    bar: Any


class Inherited(TwoSlot):
    __slots__ = ("bing",)

    bing: Any


class Nested(utils.SlotClass):
    __slots__ = ("val", "nested")

    val: Any
    nested: TwoSlot


def test_slot_class() -> None:
    for one in (OneSlot(1), OneSlot(foo=1)):
        assert one.foo == 1
        with pytest.raises(AttributeError):
            one.__dict__

    for two in (TwoSlot(1, 2), TwoSlot(1, bar=2), TwoSlot(foo=1, bar=2)):
        assert two.foo == 1
        assert two.bar == 2
        with pytest.raises(AttributeError):
            two.__dict__


@pytest.mark.parametrize(
    "should_throw_error",
    (
        lambda: OneSlot(),
        lambda: TwoSlot(),
        lambda: TwoSlot(1),
        lambda: TwoSlot(foo=1),
        lambda: TwoSlot(bar=1),
    ),
)
def test_slot_class_raises(should_throw_error: Callable[..., Any]) -> None:
    with pytest.raises(TypeError, match="requires a setting for"):
        should_throw_error()


def test_slot_class_keys() -> None:
    assert tuple(Inherited.__keys__()) == ("foo", "bar", "bing")


def test_slot_class_values() -> None:
    inherited = Inherited(1, 2, 3)
    assert tuple(inherited.__values__()) == (1, 2, 3)


def test_slot_class_repr() -> None:
    nested = Nested("val", TwoSlot("foo", "bar"))

    assert (
        repr(nested)
        == dedent(
            """
        Nested(
          'val',
          TwoSlot(
            'foo',
            'bar',
          ),
        )
        """
        )[1:-1]
    )
