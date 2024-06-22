import pytest

from satisfaction.expr import Equivalent, Expr, Implies, Var
from satisfaction.format import (
    Formatter,
    format_expr,
    pythonic,
    standard,
    default,
    set_formatter,
)

w = Var("w")
x = Var("x")
y = Var("y")
z = Var("z")


class TestFormatter:
    def test_init(self) -> None:
        symbols: dict[type[Expr], str] = {Implies: "foo"}
        formatter = Formatter(symbols)
        assert formatter.symbols == symbols

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
    def test_format(self, expr: Expr, repr_str: str) -> None:
        assert pythonic.format(expr) == repr_str

    def test_format_raises(self) -> None:
        with pytest.raises(ValueError):
            pythonic.format(1)  # type: ignore


@pytest.mark.parametrize(
    "formatter,expr,repr_str",
    (
        (pythonic, Equivalent(w, Implies(x, ~x & (y | z))), "w <-> x -> ~x & (y | z)"),
        (standard, Equivalent(w, Implies(x, ~x & (y | z))), "w ⇔ x ⇒ ¬x ∧ (y ∨ z)"),
    ),
)
def test_api(formatter: Formatter, expr: Expr, repr_str: str) -> None:
    save_default = default

    set_formatter(formatter)
    assert format_expr(expr) == repr_str
    set_formatter(save_default)
