import pytest

from satisfaction.examples.queens import Queens
from satisfaction.expr import And, Or, var
from satisfaction.solvers.solver import Solver
from satisfaction.tseitin import Tseitin
from satisfaction.utils import numbered_var

x, y = var("x y")


class BaseSuite:
    solver_cls: type[Solver] = None  # type: ignore
    queens: tuple[int, bool] = None  # type: ignore

    @pytest.mark.parametrize(
        "cnf",
        (
            And(Or(x)),
            And(Or(~x)),
            And(x | y),
            And(x | x),
            And(x | ~x),
            And(~x | ~x),
        ),
    )
    def test_sat(self, cnf: And) -> None:
        assert self.solver_cls(cnf).check()

    @pytest.mark.parametrize(
        "cnf",
        (And(Or(x), Or(~x)),),
    )
    def test_unsat(self, cnf: And) -> None:
        assert not self.solver_cls(cnf).check()

    def test_queens(self) -> None:
        queens_n, queens_sat = self.queens

        queens = Queens(queens_n)
        queens_formula = queens.get_formula()

        tseitin = Tseitin(
            queens_formula, rename_vars=False, name_gen=numbered_var("x", 0)
        )
        queens_cnf = tseitin.transform(sort=True)

        assert self.solver_cls(queens_cnf).check() is queens_sat
