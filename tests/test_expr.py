import pytest

from satellite.expr import And, Not, Or, Var


class TestExpr:
    def test_invert(self) -> None:
        x = Var("x")

        assert ~x == Not(x)
        assert ~(~x) == x

    def test_or_raises(self) -> None:
        x = Var("x")
        with pytest.raises(ValueError, match="cannot disjoin"):
            _ = x | 1
        with pytest.raises(ValueError, match="cannot disjoin"):
            _ = 1 | x

    def test_or(self) -> None:
        w = Var("w")
        x = Var("x")
        y = Var("y")
        z = Var("z")

        assert x | y == Or((x, y))
        assert (x | y) | z == Or((x, y, z))
        assert x | (y | z) == Or((x, y, z))
        assert (w | x) | (y | z) == Or((w, x, y, z))

    def test_and_raises(self) -> None:
        x = Var("x")
        with pytest.raises(ValueError, match="cannot conjoin"):
            _ = x & 1
        with pytest.raises(ValueError, match="cannot conjoin"):
            _ = 1 & x

    def test_and(self) -> None:
        w = Var("w")
        x = Var("x")
        y = Var("y")
        z = Var("z")

        assert x & y == And((x, y))
        assert (x & y) & z == And((x, y, z))
        assert x & (y & z) == And((x, y, z))
        assert (w & x) & (y & z) == And((w, x, y, z))
