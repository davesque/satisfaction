from textwrap import dedent
from typing import Any, Callable

import pytest

from satisfaction import utils


def test_chunks() -> None:
    gen = utils.chunks(range(10), 3)
    assert list(gen) == [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (9,),
    ]


class TestPlaces:
    def test_slots(self) -> None:
        places = utils.Places(2)
        with pytest.raises(AttributeError):
            places.__dict__

    def test_init(self) -> None:
        places = utils.Places(2, skip_zero=False)
        assert places.base == 2
        assert places.skip_zero is False
        assert list(places) == [0]

        places = utils.Places(2)
        assert places.skip_zero is True

    def test_incr_and_carry(self) -> None:
        places = utils.Places(2, skip_zero=True)
        assert places.incr() == [1]
        assert places.incr() == [0, 1]
        assert places.incr() == [1, 1]
        assert places.incr() == [0, 0, 1]

        places = utils.Places(2, skip_zero=False)
        assert places.incr() == [1]
        assert places.incr() == [0, 0]
        assert places.incr() == [1, 0]
        assert places.incr() == [0, 1]
        assert places.incr() == [1, 1]
        assert places.incr() == [0, 0, 0]


def test_letters() -> None:
    gen = utils.letters()

    assert next(gen) == "a"
    for _ in range(24):
        next(gen)
    assert next(gen) == "z"
    assert next(gen) == "aa"
    assert next(gen) == "ab"
    for _ in range(23):
        next(gen)
    assert next(gen) == "az"
    assert next(gen) == "ba"
    for _ in range(25 * 26):
        next(gen)
    assert next(gen) == "aab"


def test_numbered_var() -> None:
    gen = utils.numbered_var("x", 0)
    assert next(gen) == "x0"
    assert next(gen) == "x1"

    gen = utils.numbered_var("x", 100)
    assert next(gen) == "x100"
    assert next(gen) == "x101"


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


class TestSlotClass:
    def test_init(self) -> None:
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
    def test_init_raises(self, should_throw_error: Callable[..., Any]) -> None:
        with pytest.raises(TypeError, match="requires a setting for"):
            should_throw_error()

    def test_keys(self) -> None:
        assert tuple(Inherited.__keys__()) == ("foo", "bar", "bing")

    def test_values(self) -> None:
        inherited = Inherited(1, 2, 3)
        assert tuple(inherited.__values__()) == (1, 2, 3)

    def test_repr(self) -> None:
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

    def test_eq(self) -> None:
        nested1 = Nested("val", TwoSlot("foo", "bar"))
        nested2 = Nested("val", TwoSlot("foo", "bing"))
        nested3 = Nested("val", TwoSlot("foo", "bar"))

        assert nested1 != nested2
        assert nested1 == nested3
        assert nested1 != 1
