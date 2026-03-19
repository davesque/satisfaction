# satisfaction

Toy implementations of SAT solving algorithms written in Python.

This repo may hopefully be interesting to anyone trying to understand SAT
solving algorithms by playing around with some simple implementations.

Three solvers are included:

* **Naive DPLL** — a straightforward implementation based on the description
  found in the following Wikipedia article:
  https://en.wikipedia.org/wiki/DPLL_algorithm
* **Indexed DPLL** — an optimized DPLL that uses dynamic indices and parallel
  unit propagation to speed up the naive implementation by about 500x.
* **CDCL** — a conflict-driven clause learning solver with 1-UIP conflict
  analysis and non-chronological backjumping.

An implementation of the Tseitin transformation is included that is based on
the following references:

* https://en.wikipedia.org/wiki/Tseytin_transformation
* https://www.youtube.com/watch?v=fd9gjzZE1-4
* https://www.youtube.com/watch?v=v2uW258qIsM

No docs provided currently :).  If you're curious how things work, have a look
at the test suite.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```
git clone git@github.com:davesque/satisfaction.git
cd satisfaction
make setup
```

## Running the tests

From the project root directory:
```
make test
```

## Linting and type checking

```
make lint
make typecheck
```

## Benchmarking

Compare all three solvers on N-Queens instances:
```
uv run python -m satisfaction.examples.benchmark
```
