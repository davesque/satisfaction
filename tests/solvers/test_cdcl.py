from satisfaction.solvers.cdcl import CDCL

from .base_suite import BaseSuite


class TestCDCL(BaseSuite):
    solver_cls = CDCL
    queens = (8, True)
