from __future__ import annotations
from collections import defaultdict

from .expr import CNF, Clause, Lit


def set_repr(s: set) -> str:
    els_repr = ", ".join(sorted(map(repr, s)))
    return f"{{{els_repr}}}"


class Index:
    __slots__ = ("clauses", "by_lit", "by_count")

    clauses: tuple[IndexClause, ...]

    by_lit: dict[Lit, set[IndexClause]]
    by_count: dict[int, set[IndexClause]]

    def __init__(self, cnf: CNF) -> None:
        self.clauses = tuple(IndexClause(clause, self) for clause in cnf.args)

        self.by_lit = defaultdict(set)
        self.by_count = defaultdict(set)

        self._build_indices()

    def _build_indices(self) -> None:
        for clause in self.clauses:
            self.by_count[len(clause.unassigned)].add(clause)
            for lit in clause.unassigned:
                self.by_lit[lit].add(clause)

    def clauses_for_lit(self, lit: Lit) -> set[IndexClause]:
        return self.by_lit[lit]

    def clauses_for_count(self, count: int) -> set[IndexClause]:
        return self.by_count[count]

    def move(self, clause: IndexClause, prev_count: int, curr_count: int) -> None:
        if prev_count != curr_count:
            self.by_count[prev_count].remove(clause)
            self.by_count[curr_count].add(clause)

    def push(self) -> None:
        for clause in self.clauses:
            clause.push()

    def pop(self) -> None:
        for clause in self.clauses:
            clause.pop()


class IndexClause:
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
