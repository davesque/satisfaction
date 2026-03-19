# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A toy SAT solver implementing the DPLL algorithm in Python. Includes a Tseitin transformation for converting arbitrary boolean formulas to CNF, and an N-Queens example that encodes the problem as a SAT instance.

## Commands

```bash
make setup    # Create venv and install deps (uses setup.py extras)
make test     # Run tests with coverage (note: coverage target is "satellite", likely a typo for "satisfaction")
make lint     # Check formatting and linting with ruff
```

Run a single test:
```bash
venv/bin/pytest tests/test_expr.py -vv
venv/bin/pytest tests/test_expr.py::test_name -vv
```

Run the N-Queens example:
```bash
python -m satisfaction.examples.queens N
```

## Architecture

**Expression tree** (`expr.py`): Boolean formula AST. `Var`, `Not`, `And`, `Or`, `Implies`, `Equivalent` form the tree. Operators `~`, `|`, `&` are overloaded on `Expr` for natural formula construction (e.g., `(~p | q) & (p | ~q)`). Type aliases `Lit`, `Clause`, `CNF` define the expected shapes for solver input.

**Tseitin transformation** (`tseitin.py`): Converts arbitrary `Expr` trees into equisatisfiable CNF via structural pattern matching on equivalences. Each sub-expression gets a fresh variable; equivalences are individually converted to CNF clauses.

**Solvers** (`solvers/`):
- `solver.py`: Abstract `Solver` base class with `__init__(cnf)` and `check() -> bool`.
- `dpll.py`: Naive DPLL — rebuilds the CNF expression tree on each recursive call. Supports pluggable literal choice heuristics (`ChooseLit` callback).
- `indexed.py`: Optimized DPLL — uses `Clauses`/`Clause` wrapper classes with `by_lit` and `by_count` indices for O(1) unit clause lookup and fast propagation. Both solvers use layered sets for backtracking.

**Layered sets** (`layered.py`): `SetLayers` provides push/pop semantics for set modifications, enabling efficient backtracking. `AddLayers` tracks additions; `RemoveLayers` tracks removals. Used by both solvers to manage assignments and clause state across branch/backtrack cycles.

**Literal choice strategies** (`choice.py`): `common_lit`, `first_lit`, `last_lit`, `random_lit` — heuristics for the naive DPLL solver's branching decision.

**Tests** (`tests/`): Solver tests share a `BaseSuite` mixin (`tests/solvers/base_suite.py`) that runs common SAT/UNSAT cases and an N-Queens integration test. Each solver subclasses it and sets `solver_cls` and `queens` (board size, expected satisfiability).

## Key Patterns

- Heavy use of `__slots__` throughout for memory efficiency.
- `SlotClass` (`utils.py`) is the base for `Expr` — provides `__init__`, `__repr__`, `__eq__` based on `__slots__`.
- Python 3.12+ features: PEP 695 type parameter syntax (`class Foo[T]`), `type` statement for aliases.
- Structural pattern matching (`match`/`case`) is used extensively in Tseitin and choice modules.
