from satisfaction.expr import And, Or, var
from satisfaction.solvers.cdcl import CDCL

from .base_suite import BaseSuite

x, y = var("x y")


class TestCDCL(BaseSuite):
    solver_cls = CDCL
    queens = (8, True)

    def test_unsat_at_level_zero(self) -> None:
        """A CNF with conflicting unit clauses is UNSAT at level 0."""
        cnf = And(Or(x), Or(~x))
        assert not CDCL(cnf).check()

    def test_unsat_unit_propagation_at_level_zero(self) -> None:
        """Unit propagation at level 0 reveals UNSAT."""
        cnf = And(Or(x), Or(x, y), Or(~x, ~y), Or(~x, y), Or(x, ~y))
        assert not CDCL(cnf).check()

    def test_unsat_requires_learning(self) -> None:
        """UNSAT formula with no unit clauses, requiring clause learning
        to eventually backjump to level 0 and discover UNSAT."""
        cnf = And(
            Or(x, y),
            Or(x, ~y),
            Or(~x, y),
            Or(~x, ~y),
        )
        assert not CDCL(cnf).check()
