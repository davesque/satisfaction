from satellite.solvers.parallel import DPLL
from satellite.expr import And, Or, var

from .base_suite import BaseSuite

w, x, y, z = var("w x y z")


class TestDPLL(BaseSuite):
    solver_cls = DPLL
    queens = (2, False)

    def test_find_units(self) -> None:
        expr = (w | x) & Or(y) & (y | z)
        assert DPLL.find_units(expr) == {y}

        expr = (w | x) & Or(~y) & (y | z)
        assert DPLL.find_units(expr) == {~y}

        expr = (w | x) & (y | z)
        assert DPLL.find_units(expr) == set()

    def test_unit_propagate(self) -> None:
        expr = (w | x) & Or(y) & (y | z) & (z | ~y)
        expected = (w | x) & Or(z)
        assert DPLL.unit_propagate({y}, expr) == expected

    def test_find_pure(self) -> None:
        assert DPLL.find_pure((w | x) & (y | z)) == {w, x, y, z}
        assert DPLL.find_pure((w | ~w) & (y | ~z)) == {y, ~z}

    def test_pure_literal_assign(self) -> None:
        assert DPLL.pure_literal_assign(y, (w | ~w) & (y | z)) == And(w | ~w)
        assert DPLL.pure_literal_assign(~x, (w | ~w) & (y | z) & (w | ~x)) == (
            w | ~w
        ) & (y | z)
