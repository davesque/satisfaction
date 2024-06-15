from __future__ import annotations
from collections import defaultdict

from .expr import CNF, Clause, Lit


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
        self.unassigned.add(*assigned)
        curr_len = len(self.unassigned)

        self.index.move(self, prev_len, curr_len)

    def assign(self, *lit: Lit) -> None:
        self.assigned[-1].add(set(*lit) & self.unassigned)

        prev_len = len(self.unassigned)
        self.unassigned.remove(*lit)
        curr_len = len(self.unassigned)

        self.index.move(self, prev_len, curr_len)

    def __repr__(self) -> str:
        assigned_repr = ", ".join(map(repr, self.assigned))
        return f"{repr(self.unassigned)} ({assigned_repr})"
