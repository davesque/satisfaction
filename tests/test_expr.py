import pytest

from satellite.expr import And, Not, Or, Var, var, format_expr, Expr

w = Var("w")
x = Var("x")
y = Var("y")
z = Var("z")


@pytest.mark.parametrize(
    "expr,repr_str",
    (
        (x, "x"),
        (~x, "~x"),
        (~(x | y), "~(x | y)"),
        (~(x & y), "~(x & y)"),
        (x | y | z, "x | y | z"),
        (x & y & z, "x & y & z"),
        (x >> y >> z, "(x -> y) -> z"),
        (x ** y ** z, "x <-> (y <-> z)"),
        (x | y & z, "x | y & z"),
        (w | x & y | z, "w | x & y | z"),
        ((w | x) & (y | z), "(w | x) & (y | z)"),
        ((w & x) | (y & z), "w & x | y & z"),
        (w & x >> y, "w & (x -> y)"),
    ),
)
def test_format_expr(expr: Expr, repr_str: str) -> None:
    assert format_expr(expr) == repr_str


def test_format_expr_raises() -> None:
    with pytest.raises(ValueError):
        format_expr(1)  # type: ignore


class TestExpr:
    def test_invert(self) -> None:
        assert ~x == Not(x)
        assert ~(~x) == x

    def test_or_raises(self) -> None:
        with pytest.raises(TypeError, match="cannot combine"):
            _ = x | 1
        with pytest.raises(TypeError, match="unsupported operand"):
            _ = 1 | x

    def test_or(self) -> None:
        assert x | y == Or(x, y)
        assert (x | y) | z == Or(x, y, z)
        assert x | (y | z) == Or(x, y, z)
        assert (w | x) | (y | z) == Or(w, x, y, z)

    def test_and_raises(self) -> None:
        with pytest.raises(TypeError, match="cannot combine"):
            _ = x & 1
        with pytest.raises(TypeError, match="unsupported operand"):
            _ = 1 & x

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
        or_x = x | x
        and_x = x & x

        assert x.atom == x
        assert not_x.atom == x
        assert or_x.atom is None
        assert and_x.atom is None

    def test_is_cnf(self) -> None:
        assert not x.is_cnf
        assert not (w & x).is_cnf
        assert not (((w & x) | y) & z).is_cnf
        assert not ((~(w & x) | y) & z).is_cnf
        assert ((w | x) & (y | z)).is_cnf
        assert ((w | ~x) & (y | z)).is_cnf
        assert ((w | ~x) & (y | ~z)).is_cnf


def test_var() -> None:
    assert var("w x y z") == (w, x, y, z)
    assert var("w x", "y z") == (w, x, y, z)
    assert var("w, x, y, z", sep=",") == (w, x, y, z)
