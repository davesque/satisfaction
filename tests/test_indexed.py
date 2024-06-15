import pytest

from satellite.examples.queens import Queens
from satellite.expr import And, Or, var
from satellite.indexed import DPLL
from satellite.tseitin import Tseitin
from satellite.utils import numbered_var

w, x, y, z = var("w x y z")


class TestIndexed:
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
    def test_dpll_sat(self, and_expr: And) -> None:
        assert DPLL(and_expr).check()

    @pytest.mark.parametrize(
        "and_expr",
        (And(Or(x), Or(~x)),),
    )
    def test_dpll_unsat(self, and_expr: And) -> None:
        assert not DPLL(and_expr).check()


def test_queens() -> None:
    queens = Queens(8)
    queens_formula = queens.get_formula()

    tseitin = Tseitin(queens_formula, rename_vars=False, name_gen=numbered_var("x", 0))
    queens_cnf = tseitin.transform(sort=True)

    assert DPLL(queens_cnf).check()
