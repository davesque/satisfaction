from __future__ import annotations
from collections import defaultdict
import logging

from satellite.expr import CNF, Clause, Lit

logger = logging.getLogger(__name__)


def set_repr(s: set) -> str:
    els_repr = ", ".join(sorted(map(repr, s)))
    return f"{{{els_repr}}}"


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
        if len(self.index.clauses_with_count(0)) > 0:
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
        for clause in self.index.clauses_with_count(1):
            lit = next(iter(clause.unassigned))
            # We only want to propagate one polarity of a literal at a time.
            # This avoids accidentally claiming things like (P & ~P) are
            # satisfiable.
            units[lit.atom()] = lit

        return set(units.values())

    def unit_propagate(self, *units: Lit) -> None:
        logger.debug("assigning unit literals: %s", units)

        for unit in units:
            clauses = self.index.clauses_with_lit(unit)
            self.index.assign_clause(*clauses, check_unassigned=False)

            not_unit = ~unit
            for clause in self.index.clauses_with_lit(not_unit):
                clause.assign(not_unit)


class Index:
    __slots__ = (
        "clauses",
        "clauses_by_lit",
        "clauses_by_count",
        "assigned_clauses",
        "unassigned_clauses",
    )

    clauses: tuple[IndexClause, ...]

    clauses_by_lit: dict[Lit, set[IndexClause]]
    clauses_by_count: dict[int, set[IndexClause]]

    unassigned_clauses: set[IndexClause]
    assigned_clauses: list[set[IndexClause]]

    def __init__(self, cnf: CNF) -> None:
        self.clauses = tuple(IndexClause(clause, self) for clause in cnf.args)

        self.clauses_by_lit = defaultdict(set)

        self.clauses_by_count = defaultdict(set)
        self.clauses_by_count[0] = set()

        self.unassigned_clauses = set(self.clauses)
        self.assigned_clauses = [set()]

        self._build_indices()

    def _build_indices(self) -> None:
        for clause in self.clauses:
            self.clauses_by_count[len(clause.unassigned)].add(clause)
            for lit in clause.unassigned:
                self.clauses_by_lit[lit].add(clause)

    def clauses_with_lit(self, lit: Lit) -> set[IndexClause]:
        return self.clauses_by_lit[lit] & self.unassigned_clauses

    def clauses_with_count(self, count: int) -> set[IndexClause]:
        return self.clauses_by_count[count] & self.unassigned_clauses

    def move(self, clause: IndexClause, prev_count: int, curr_count: int) -> None:
        if prev_count != curr_count:
            self.clauses_by_count[prev_count].remove(clause)
            self.clauses_by_count[curr_count].add(clause)

    def push(self) -> None:
        for clause in self.clauses:
            clause.push()

        self.assigned_clauses.append(set())

    def pop(self) -> None:
        for clause in self.clauses:
            clause.pop()

        assigned = self.assigned_clauses.pop()
        self.unassigned_clauses.update(assigned)

    def assign_clause(
        self, *clauses: IndexClause, check_unassigned: bool = True
    ) -> None:
        to_assign = set(clauses)

        if check_unassigned:
            self.assigned_clauses[-1].update(to_assign & self.unassigned_clauses)
        else:
            self.assigned_clauses[-1].update(to_assign)
        self.unassigned_clauses.difference_update(to_assign)


class IndexClause:
    __slots__ = ("index", "unassigned", "assigned")

    index: Index
    unassigned: set[Lit]
    assigned: list[set[Lit]]

    def __init__(self, clause: Clause, index: Index) -> None:
        self.index = index

        self.unassigned = set(clause.args)
        self.assigned = [set()]

    def push(self) -> None:
        self.assigned.append(set())

    def pop(self) -> None:
        assigned = self.assigned.pop()

        prev_len = len(self.unassigned)
        self.unassigned.update(assigned)
        curr_len = len(self.unassigned)

        self.index.move(self, prev_len, curr_len)

    def assign(self, *lits: Lit) -> None:
        to_assign = set(lits)

        self.assigned[-1].update(to_assign & self.unassigned)

        prev_len = len(self.unassigned)
        self.unassigned.difference_update(to_assign)
        curr_len = len(self.unassigned)

        self.index.move(self, prev_len, curr_len)

    def __repr__(self) -> str:
        assigned_repr = ", ".join(map(set_repr, self.assigned))
        return f"{set_repr(self.unassigned)} ({assigned_repr})"
