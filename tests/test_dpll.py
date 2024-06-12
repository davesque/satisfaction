import pytest

from satellite.dpll import (
    dpll,
    find_pure,
    find_unit,
    pure_literal_assign,
    unit_propagate,
)
from satellite.examples.queens import Queens
from satellite.expr import And, Or, var
from satellite.tseitin import Tseitin
from satellite.utils import numbered_var

w, x, y, z = var("w x y z")


def test_find_unit() -> None:
    expr = (w | x) & Or(y) & (y | z)
    assert find_unit(expr) == y

    expr = (w | x) & Or(~y) & (y | z)
    assert find_unit(expr) == ~y

    expr = (w | x) & (y | z)
    assert find_unit(expr) is None


def test_unit_propagate() -> None:
    expr = (w | x) & Or(y) & (y | z) & (z | ~y)
    expected = (w | x) & Or(z)
    assert unit_propagate(y, expr) == expected


def test_find_pure() -> None:
    assert find_pure((w | x) & (y | z)) == {w, x, y, z}
    assert find_pure((w | ~w) & (y | ~z)) == {y, ~z}


def test_pure_literal_assign() -> None:
    assert pure_literal_assign(y, (w | ~w) & (y | z)) == And(w | ~w)
    assert pure_literal_assign(~x, (w | ~w) & (y | z) & (w | ~x)) == (w | ~w) & (y | z)


@pytest.mark.parametrize(
    "and_expr",
    (
        And(Or(x)),
        And(Or(~x)),
        And(x | y),
        And(x | x),
        And(x | ~x),
        And(~x | ~x),
    ),
)
def test_dpll_sat(and_expr: And) -> None:
    assert dpll(and_expr)


@pytest.mark.parametrize(
    "and_expr",
    (And(Or(x), Or(~x)),),
)
def test_dpll_unsat(and_expr: And) -> None:
    assert not dpll(and_expr)


def test_queens() -> None:
    queens = Queens(2)

    queens_formula = queens.get_formula()

    tseitin = Tseitin(queens_formula, rename_vars=False, name_gen=numbered_var("x", 0))
    queens_cnf = tseitin.transform(sort=True)

    assert not dpll(queens_cnf)
