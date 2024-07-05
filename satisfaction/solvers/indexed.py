from __future__ import annotations
from collections import defaultdict
import logging

from satisfaction.expr import CNF, Clause as ClauseExpr, Lit
from satisfaction.layered import RemoveLayers

from .solver import Solver

logger = logging.getLogger(__name__)


def set_repr(s: set) -> str:
    els_repr = ", ".join(sorted(map(repr, s)))
    return f"{{{els_repr}}}"


class DPLL(Solver):
    __slots__ = ("expr", "clauses")

    expr: CNF

    def __init__(self, expr: CNF) -> None:
        self.expr = expr
        self.clauses = Clauses(expr)

    def check(self) -> bool:
        """
        The Davis-Putnam-Logemann-Loveland (DPLL) SAT algorithm.

        Implementation based on the following description:
        https://en.wikipedia.org/wiki/DPLL_algorithm
        """
        while units := self.find_units():
            self.unit_propagate(*units)

        # If the root conjunction is empty, this implies that the formula is
        # satisfiable.  This follows from the fact that any clause that was
        # eliminated from the root conjunction was determined to have a truth value
        # of `true`. Therefore, the root conjunction also evaluates to true.
        if len(self.clauses.els) == 0:
            return True

        # If any disjunctive clause is empty, this implies that the formula is not
        # satisfiable.  This follows from the fact that any literal that was
        # eliminated from a disjunction was determined to have a truth value of
        # `false`.  Therefore, the parent disjunction evaluates to `false` and the
        # root conjunction also evaluate to `false`.
        if len(self.clauses.with_count(0)) > 0:
            return False

        first_clause = next(iter(self.clauses.els))
        lit = next(iter(first_clause.els))

        logger.debug("+++++++++++++ branching +++++++++++++")
        self.clauses.push_layer()
        self.unit_propagate(lit)
        if self.check():
            return True
        self.clauses.pop_layer()

        logger.debug("------------ backtracking -----------")
        self.clauses.push_layer()
        self.unit_propagate(~lit)
        if self.check():
            return True
        self.clauses.pop_layer()

        return False

    def find_units(self) -> set[Lit]:
        units = {}
        for clause in self.clauses.with_count(1):
            lit = next(iter(clause.els))
            # We only want to propagate one polarity of a literal at a time.
            # This avoids accidentally claiming things like (P & ~P) are
            # satisfiable.
            units[lit.atom()] = lit

        return set(units.values())

    def unit_propagate(self, *units: Lit) -> None:
        logger.debug("assigning unit literals: %s", units)

        for unit in units:
            clauses = self.clauses.with_lit(unit)
            self.clauses.difference_update(clauses)

            not_unit = {~unit}
            for clause in self.clauses.with_lit(~unit):
                clause.difference_update(not_unit)


class Clauses(RemoveLayers["Clause"]):
    __slots__ = (
        "clauses",
        "by_lit",
        "by_count",
    )

    clauses: tuple[Clause, ...]

    by_lit: dict[Lit, set[Clause]]
    by_count: dict[int, set[Clause]]

    def __init__(self, cnf: CNF) -> None:
        self.clauses = tuple(Clause(clause, self) for clause in cnf.args)
        super().__init__(set(self.clauses))

        self.by_lit = defaultdict(set)
        self.by_count = defaultdict(set)
        self.by_count[0] = set()

        self._build_indices()

    def _build_indices(self) -> None:
        for clause in self.clauses:
            self.by_count[len(clause.els)].add(clause)
            for lit in clause.els:
                self.by_lit[lit].add(clause)

    def with_lit(self, lit: Lit) -> set[Clause]:
        return self.by_lit[lit] & self.els

    def with_count(self, count: int) -> set[Clause]:
        return self.by_count[count] & self.els

    def move(self, clause: Clause, prev_count: int, curr_count: int) -> None:
        if prev_count != curr_count:
            self.by_count[prev_count].remove(clause)
            self.by_count[curr_count].add(clause)

    def push_layer(self) -> None:
        super().push_layer()

        for clause in self.clauses:
            clause.push_layer()

    def pop_layer(self) -> None:
        super().pop_layer()

        for clause in self.clauses:
            clause.pop_layer()


class Clause(RemoveLayers[Lit]):
    __slots__ = ("clauses",)

    clauses: Clauses

    def __init__(self, clause: ClauseExpr, clauses: Clauses) -> None:
        super().__init__(set(clause.args))
        self.clauses = clauses

    def pop_layer(self) -> None:
        prev_len = len(self.els)
        super().pop_layer()
        curr_len = len(self.els)

        self.clauses.move(self, prev_len, curr_len)

    def difference_update(self, to_remove: set[Lit]) -> None:
        prev_len = len(self.els)
        super().difference_update(to_remove)
        curr_len = len(self.els)

        self.clauses.move(self, prev_len, curr_len)
