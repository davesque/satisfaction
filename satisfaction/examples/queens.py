import argparse
from datetime import datetime
import logging
import re
from typing import Iterator

from satisfaction.expr import And, Or, Var
from satisfaction.solvers.indexed import DPLL
from satisfaction.tseitin import Tseitin
from satisfaction.utils import chunks, letters, numbered_var

logger = logging.getLogger(__name__)


LIT_KEY_RE = re.compile(r"^([a-z]*)(\d*)$")


def partitions(vars: tuple[Var, ...]) -> Iterator[tuple[Var, tuple[Var, ...]]]:
    if len(vars) < 1:
        raise ValueError("cannot partition zero-length sequence")

    for i in range(len(vars)):
        var = vars[i]
        others = tuple(vars[:i] + vars[i + 1 :])

        yield var, others


def exactly_one(vars: tuple[Var, ...]) -> Or:
    clauses = []
    for var, others in partitions(vars):
        if len(others) == 0:
            clauses.append(var)
        else:
            no_others = ~others[0] if len(others) == 1 else ~Or(*others)
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


def row_repr(row):
    inner = "│".join(lit_repr(lit) for lit in row)
    return f"│{inner}│"


def fill_repr(pos, n):
    match pos:
        case "top":
            left, mid, right = "┌┬┐"
        case "bottom":
            left, mid, right = "└┴┘"
        case _:
            left, mid, right = "├┼┤"

    inner = mid.join(["───"] * n)
    return f"{left}{inner}{right}"


def lit_repr(lit):
    if isinstance(lit, Var):
        return " Q "
    else:
        return "   "


def lit_sort_key(lit):
    match = LIT_KEY_RE.match(lit.atom().name)
    assert match is not None
    return (match.group(1), int(match.group(2), 10))


def run_queens(queens_n: int) -> None:
    queens = Queens(queens_n)
    queens_formula = queens.get_formula()

    tseitin = Tseitin(queens_formula, rename_vars=False, name_gen=numbered_var("x", 0))
    queens_cnf = tseitin.transform(sort=True)

    dpll = DPLL(queens_cnf)
    if dpll.check():
        assignments = [lit for lit in dpll.assignments.els if not lit.atom().generated]
        assignments.sort(key=lit_sort_key)
        logger.info("satisfiable: %s", assignments)

        lines = [fill_repr("top", queens_n)]
        for row in chunks(assignments, queens_n):
            lines.extend([row_repr(row), fill_repr("mid", queens_n)])
        lines = lines[:-1]
        lines.append(fill_repr("bottom", queens_n))
        logger.info("placements:\n" + "\n".join(lines))
    else:
        logger.info("untsatisfiable")


def chessboard_size(s: str) -> int:
    n = int(s, 10)
    if n < 2:
        raise ValueError("not a valid chessboard size")

    return n


parser = argparse.ArgumentParser(
    description="Determine if N queens can be placed on an NxN chessboard"
)
parser.add_argument("N", help="the size of the chessboard", type=chessboard_size)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()

    start = datetime.now()
    run_queens(args.N)
    end = datetime.now()

    logger.info("took: %s", end - start)
