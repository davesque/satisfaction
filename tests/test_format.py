import pytest

from satellite.expr import Equivalent, Expr, Implies, Var
from satellite.format import format_expr

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
        (Implies(x, y), "x -> y"),
        (Equivalent(x, y), "x <-> y"),
        (x | y & z, "x | y & z"),
        (w | x & y | z, "w | x & y | z"),
        ((w | x) & (y | z), "(w | x) & (y | z)"),
        ((w & x) | (y & z), "w & x | y & z"),
        (Implies(w & x, y), "w & x -> y"),
    ),
)
def test_format_expr(expr: Expr, repr_str: str) -> None:
    assert format_expr(expr) == repr_str


def test_format_expr_raises() -> None:
    with pytest.raises(ValueError):
        format_expr(1)  # type: ignore
