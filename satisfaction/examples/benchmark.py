"""
Benchmark comparing the three SAT solvers on N-Queens instances.

Usage:
    python -m satisfaction.examples.benchmark
"""

import argparse
import time

from satisfaction.examples.queens import Queens
from satisfaction.solvers.cdcl import CDCL
from satisfaction.solvers.dpll import DPLL as NaiveDPLL
from satisfaction.solvers.indexed import DPLL as IndexedDPLL
from satisfaction.solvers.solver import Solver
from satisfaction.tseitin import Tseitin
from satisfaction.utils import numbered_var


def make_queens_cnf(n: int):
    queens = Queens(n)
    formula = queens.get_formula()
    tseitin = Tseitin(formula, rename_vars=False, name_gen=numbered_var("x", 0))
    return tseitin.transform(sort=True)


def bench(solver_cls: type[Solver], cnf, runs: int = 1) -> float:
    total = 0.0
    for _ in range(runs):
        start = time.perf_counter()
        solver_cls(cnf).check()
        total += time.perf_counter() - start
    return total / runs


SOLVERS: list[tuple[str, type[Solver], list[int]]] = [
    ("naive", NaiveDPLL, [4, 5]),
    ("indexed", IndexedDPLL, [4, 5, 6, 8, 10, 12, 14]),
    ("cdcl", CDCL, [4, 5, 6, 8, 10, 12, 14]),
]


def run_benchmark(runs: int) -> None:
    # Collect all N values
    all_ns: list[int] = sorted({n for _, _, ns in SOLVERS for n in ns})

    # Pre-generate CNFs
    cnfs = {n: make_queens_cnf(n) for n in all_ns}

    # Run benchmarks
    results: dict[str, dict[int, float]] = {}
    for name, solver_cls, ns in SOLVERS:
        results[name] = {}
        for n in ns:
            avg = bench(solver_cls, cnfs[n], runs=runs)
            results[name][n] = avg

    # Print table
    solver_names = [name for name, _, _ in SOLVERS]
    col_width = 12

    header = f"{'N':>4}"
    for name in solver_names:
        header += f"{name:>{col_width}}"
    print(header)
    print("-" * len(header))

    for n in all_ns:
        row = f"{n:>4}"
        for name in solver_names:
            if n in results[name]:
                secs = results[name][n]
                row += f"{format_time(secs):>{col_width}}"
            else:
                row += f"{'--':>{col_width}}"
        print(row)


def format_time(secs: float) -> str:
    if secs < 0.001:
        return f"{secs * 1_000_000:.0f}us"
    if secs < 1.0:
        return f"{secs * 1_000:.1f}ms"
    return f"{secs:.2f}s"


parser = argparse.ArgumentParser(description="Benchmark SAT solvers on N-Queens")
parser.add_argument(
    "--runs",
    type=int,
    default=1,
    help="number of runs to average (default: 1)",
)

if __name__ == "__main__":
    args = parser.parse_args()
    run_benchmark(args.runs)
