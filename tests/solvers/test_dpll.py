from satisfaction.expr import And, Or, var
from satisfaction.solvers.dpll import DPLL

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

    def test_second_branch_succeeds(self) -> None:
        """Use a heuristic that picks the wrong literal to force the solver
        into the second branch (line 70)."""

        def wrong_lit(expr):
            from satisfaction.choice import first_lit

            return ~first_lit(expr)

        # (x | y) & (~x | y) & (x | ~y)
        # No units. No pures (x and y both appear + and -).
        # first_lit picks x. wrong_lit returns ~x.
        # Branch ~x: (x|y)->Or(y), (~x|y) sat, (x|~y)->Or(~y)
        #   unit prop y, then ~y -> conflict. First branch fails.
        # Branch x: (x|y) sat, (~x|y)->Or(y), (x|~y) sat
        #   unit prop y. SAT. Second branch succeeds (line 70).
        cnf = And(Or(x, y), Or(~x, y), Or(x, ~y))
        solver = DPLL(cnf, choose_lit=wrong_lit)
        assert solver.check()
