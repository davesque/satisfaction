import pytest

from satisfaction.expr import (
    And,
    Not,
    Or,
    Var,
    var,
)

w = Var("w")
x = Var("x")
y = Var("y")
z = Var("z")


class TestExpr:
    def test_invert(self) -> None:
        assert ~x == Not(x)
        assert ~(~x) == x

    def test_or_raises(self) -> None:
        with pytest.raises(TypeError, match="cannot combine"):
            _ = x | 1
        with pytest.raises(TypeError, match="unsupported operand"):
            _ = 1 | x  # type: ignore

    def test_or(self) -> None:
        assert x | y == Or(x, y)
        assert (x | y) | z == Or(x, y, z)
        assert x | (y | z) == Or(x, y, z)
        assert (w | x) | (y | z) == Or(w, x, y, z)

    def test_and_raises(self) -> None:
        with pytest.raises(TypeError, match="cannot combine"):
            _ = x & 1
        with pytest.raises(TypeError, match="unsupported operand"):
            _ = 1 & x  # type: ignore

    def test_and(self) -> None:
        assert x & y == And(x, y)
        assert (x & y) & z == And(x, y, z)
        assert x & (y & z) == And(x, y, z)
        assert (w & x) & (y & z) == And(w, x, y, z)

    def test_hash(self) -> None:
        assert hash(x) == hash(Var("x"))
        assert hash(x | y) == hash(x | y)
        assert hash(x | y) != hash(x & y)

    def test_atom(self) -> None:
        not_x = ~x
        not_and = ~(x & x)

        assert x.atom() == x
        assert not_x.atom() == x
        with pytest.raises(ValueError):
            not_and.atom()


def test_var() -> None:
    assert var("w x y z") == (w, x, y, z)
    assert var("w x", "y z") == (w, x, y, z)
    assert var("w, x, y, z", sep=",") == (w, x, y, z)
