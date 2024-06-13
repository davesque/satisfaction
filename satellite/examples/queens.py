from typing import Iterator

from satellite.expr import And, Or, Var
from satellite.utils import letters


def partitions(vars: tuple[Var, ...]) -> Iterator[tuple[Var, tuple[Var, ...]]]:
    for i in range(len(vars)):
        var = vars[i]
        others = tuple(vars[:i]) + tuple(vars[i + 1 :])

        yield var, others


def exactly_one(vars: tuple[Var, ...]) -> Or:
    clauses = []
    for var, others in partitions(vars):
        no_others = ~Or(*others) if len(others) > 1 else ~others[0]
        clauses.append(var & no_others)

    return Or(*clauses)


class Queens:
    def __init__(self, n: int):
        self.n = n
        self.d = 2 * n - 1

        vars = []
        for r in range(1, n + 1):
            for c, _ in zip(letters(), range(n)):
                vars.append(Var(f"{c}{r}"))
        self.vars = vars

    def __getitem__(self, coords: tuple[int, int]) -> Var:
        c, r = coords
        if not (0 <= c < self.n) or not (0 <= r < self.n):
            raise IndexError(f"index is not on board: {c}, {r}")

        return self.vars[r * self.n + c]

    def row(self, i: int) -> tuple[Var, ...]:
        return tuple(self[j, i] for j in range(self.n))

    def col(self, i: int) -> tuple[Var, ...]:
        return tuple(self[i, j] for j in range(self.n))

    def ldiag(self, i: int) -> tuple[Var, ...]:
        diag = []
        for j in range(self.d):
            try:
                diag.append(self[j + i, j])
            except IndexError:
                pass
        return tuple(diag)

    def rdiag(self, i: int) -> tuple[Var, ...]:
        diag = []
        for j in range(self.d):
            try:
                diag.append(self[j + i, self.n - 1 - j])
            except IndexError:
                pass
        return tuple(diag)

    def get_formula(self) -> And:
        rows = []
        for i in range(self.n):
            rows.append(exactly_one(self.row(i)))
        one_per_row = And(*rows)

        cols = []
        for i in range(self.n):
            cols.append(exactly_one(self.col(i)))
        one_per_col = And(*cols)

        ldiag = []
        for i in range(1 - self.n, self.n):
            diag = self.ldiag(i)
            if len(diag) < 2:
                continue
            ldiag.append(exactly_one(diag) | ~Or(*diag))
        at_most_one_per_ldiag = And(*ldiag)

        rdiag = []
        for i in range(1 - self.n, self.n):
            diag = self.rdiag(i)
            if len(diag) < 2:
                continue
            rdiag.append(exactly_one(diag) | ~Or(*diag))
        at_most_one_per_rdiag = And(*rdiag)

        return one_per_row & one_per_col & at_most_one_per_ldiag & at_most_one_per_rdiag
