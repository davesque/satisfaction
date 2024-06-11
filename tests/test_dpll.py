from itertools import combinations
from typing import Iterator, Tuple, Iterable, Any

import pytest

from satellite.dpll import (
    dpll,
    find_pure,
    find_unit,
    pure_literal_assign,
    unit_propagate,
)
from satellite.expr import And, Or, Var, var
from satellite.tseitin import Tseitin, numbered_var

w, x, y, z = var("w x y z")


def chunks(iter: Iterable[Any], n: int) -> Iterator[Tuple[Var, ...]]:
    chunk = []
    for el in iter:
        chunk.append(el)
        if len(chunk) == n:
            yield tuple(chunk)
            chunk = []

    if len(chunk) > 0:
        yield tuple(chunk)


def partitions(vars: Tuple[Var, ...]) -> Iterator[Tuple[Var, Tuple[Var, ...]]]:
    for i in range(len(vars)):
        var = vars[i]
        others = tuple(vars[:i]) + tuple(vars[i+1:])

        yield var, others


def make_vars(name1: str, n1: int, name2: str, n2: int) -> Iterator[Var]:
    for i in range(n1):
        for j in range(n2):
            yield Var(f"{name1}{i}_{name2}{j}")


def get_queen_clauses(n: int, name: str, m: int) -> Iterator[Or]:
    var_group = make_vars(name, m, "queen", n)
    for chunk in chunks(var_group, n):
        for x, y in combinations(chunk, 2):
            yield (~x | ~y)


def letters(n: int) -> Iterator[str]:
    a = ord("a")
    for i in range(n):
        yield chr(a + i)


class Board:
    def __init__(self, n: int):
        self.n = n
        self.d = 2 * n - 1
        self.vars = [Var(f"{c}{r}") for r in range(1, n + 1) for c in letters(n)]

    def __getitem__(self, coords: Tuple[int, int]) -> Var:
        c, r = coords
        if not (0 <= c < self.n) or not (0 <= r < self.n):
            raise IndexError(f"index is not on board: {c}, {r}")

        return self.vars[r * self.n + c]

    def row(self, i: int) -> Tuple[Var, ...]:
        return tuple(self[j, i] for j in range(self.n))

    def col(self, i: int) -> Tuple[Var, ...]:
        return tuple(self[i, j] for j in range(self.n))

    def ldiag(self, i: int) -> Tuple[Var, ...]:
        diag = []
        for j in range(self.d):
            try:
                diag.append(self[j + i, j])
            except IndexError:
                pass
        return tuple(diag)

    def rdiag(self, i: int) -> Tuple[Var, ...]:
        diag = []
        for j in range(self.d):
            try:
                diag.append(self[j + i, self.n - 1 - j])
            except IndexError:
                pass
        return tuple(diag)


def get_queen_formula(n: int) -> And:
    d = 2 * n - 1

    clauses = []
    for clause in get_queen_clauses(n, "row", n):
        clauses.append(clause)
    for clause in get_queen_clauses(n, "col", n):
        clauses.append(clause)
    for clause in get_queen_clauses(n, "ldiag", d):
        clauses.append(clause)
    for clause in get_queen_clauses(n, "rdiag", d):
        clauses.append(clause)

    return And(*clauses)


def test_find_unit() -> None:
    expr = (w | x) & Or(y) & (y | z)
    assert find_unit(expr) == y

    expr = (w | x) & Or(~y) & (y | z)
    assert find_unit(expr) == ~y

    expr = (w | x) & (y | z)
    assert find_unit(expr) is None


def test_unit_propagate() -> None:
    expr = (w | x) & Or(y) & (y | z) & (z | ~y)
    expected = (w | x) & Or(z)
    assert unit_propagate(y, expr) == expected


def test_find_pure() -> None:
    assert find_pure((w | x) & (y | z)) == {w, x, y, z}
    assert find_pure((w | ~w) & (y | ~z)) == {y, ~z}


def test_pure_literal_assign() -> None:
    assert pure_literal_assign(y, (w | ~w) & (y | z)) == And(w | ~w)
    assert pure_literal_assign(~x, (w | ~w) & (y | z) & (w | ~x)) == (w | ~w) & (y | z)


@pytest.mark.parametrize(
    "and_expr",
    (
        And(Or(x)),
        And(Or(~x)),
        And(x | y),
        And(x | x),
        And(x | ~x),
        And(~x | ~x),
    ),
)
def test_dpll_sat(and_expr: And) -> None:
    assert dpll(and_expr)


@pytest.mark.parametrize(
    "and_expr",
    (And(Or(x), Or(~x)),),
)
def test_dpll_unsat(and_expr: And) -> None:
    assert not dpll(and_expr)


def test_queens() -> None:
    board = Board(2)

    rows = []
    for i in range(board.n):
        clauses = []
        for var, others in partitions(board.row(i)):
            rhs = Or(*others) if len(others) > 1 else others[0]
            clauses.append(var & ~rhs)
        rows.append(Or(*clauses))

    cols = []
    for i in range(board.n):
        clauses = []
        for var, others in partitions(board.col(i)):
            rhs = Or(*others) if len(others) > 1 else others[0]
            clauses.append(var & ~rhs)
        cols.append(Or(*clauses))

    ldiag = []
    for i in range(1 - board.n, board.n):
        diag = board.ldiag(i)
        if len(diag) < 2:
            continue

        clauses = []
        for var, others in partitions(diag):
            rhs = Or(*others) if len(others) > 1 else others[0]
            clauses.append(var & ~rhs)

        clauses.append(~Or(*board.ldiag(i)))
        ldiag.append(Or(*clauses))

    rdiag = []
    for i in range(1 - board.n, board.n):
        diag = board.rdiag(i)
        if len(diag) < 2:
            continue

        clauses = []
        for var, others in partitions(diag):
            rhs = Or(*others) if len(others) > 1 else others[0]
            clauses.append(var & ~rhs)

        clauses.append(~Or(*board.rdiag(i)))
        rdiag.append(Or(*clauses))

    rows_and = And(*rows)
    cols_and = And(*cols)
    ldiag_and = And(*ldiag)
    rdiag_and = And(*rdiag)

    and_expr = rows_and & cols_and & ldiag_and & rdiag_and

    tseitin = Tseitin(and_expr)
    final = tseitin.transform()

    assert (final, dpll(final)) == []
