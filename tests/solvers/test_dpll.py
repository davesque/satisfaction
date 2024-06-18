from satellite.expr import And, Or, var
from satellite.solvers.dpll import DPLL

from .base_suite import BaseSuite

w, x, y, z = var("w x y z")


class TestDPLL(BaseSuite):
    solver_cls = DPLL
    queens = (2, False)

    def test_find_unit(self) -> None:
        expr = (w | x) & Or(y) & (y | z)
        assert DPLL.find_unit(expr) == y

        expr = (w | x) & Or(~y) & (y | z)
        assert DPLL.find_unit(expr) == ~y

        expr = (w | x) & (y | z)
        assert DPLL.find_unit(expr) is None

    def test_unit_propagate(self) -> None:
        expr = (w | x) & Or(y) & (y | z) & (z | ~y)
        expected = (w | x) & Or(z)
        assert DPLL(expr).unit_propagate(y, expr) == expected

    def test_find_pure(self) -> None:
        assert DPLL.find_pure((w | x) & (y | z)) == {w, x, y, z}
        assert DPLL.find_pure((w | ~w) & (y | ~z)) == {y, ~z}

    def test_pure_literal_assign(self) -> None:
        expr = (w | ~w) & (y | z)
        assert DPLL(expr).pure_literal_assign(y, expr) == And(w | ~w)

        expr = (w | ~w) & (y | z) & (w | ~x)
        assert DPLL(expr).pure_literal_assign(~x, expr) == (w | ~w) & (y | z)
