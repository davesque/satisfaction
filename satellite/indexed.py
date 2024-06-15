import logging

from satellite.expr import CNF, Lit
from satellite.index import Index

logger = logging.getLogger(__name__)


class DPLL:
    __slots__ = ("expr", "index")

    expr: CNF

    def __init__(self, expr: CNF) -> None:
        self.expr = expr
        self.index = Index(expr)

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
        if len(self.index.unassigned_clauses) == 0:
            return True

        # If any disjunctive clause is empty, this implies that the formula is not
        # satisfiable.  This follows from the fact that any literal that was
        # eliminated from a disjunction was determined to have a truth value of
        # `false`.  Therefore, the parent disjunction evaluates to `false` and the
        # root conjunction also evaluate to `false`.
        if len(self.index.clauses_for_count(0)) > 0:
            return False

        first_clause = next(iter(self.index.unassigned_clauses))
        lit = next(iter(first_clause.unassigned))

        logger.debug("+++++++++++++ branching +++++++++++++")
        self.index.push()
        self.unit_propagate(lit)
        if self.check():
            return True
        self.index.pop()

        logger.debug("------------ backtracking -----------")
        self.index.push()
        self.unit_propagate(~lit)
        if self.check():
            return True
        self.index.pop()

        return False

    def find_units(self) -> set[Lit]:
        units = {}
        for clause in self.index.clauses_for_count(1):
            lit = next(iter(clause.unassigned))
            # We only want to propagate one polarity of a literal at a time.
            # This avoids accidentally claiming things like (P & ~P) are
            # satisfiable.
            units[lit.atom()] = lit

        return set(units.values())

    def unit_propagate(self, *units: Lit) -> None:
        logger.debug("assigning unit literals: %s", units)

        for unit in units:
            clauses = self.index.clauses_for_lit(unit)
            self.index.assign_clause(*clauses, check_unassigned=False)

            not_unit = ~unit
            for clause in self.index.clauses_for_lit(not_unit):
                clause.assign(not_unit)
