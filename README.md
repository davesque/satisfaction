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

## How the indexed DPLL solver works

The naive DPLL solver rebuilds the entire CNF expression tree on every
propagation step. The indexed solver (`solvers/indexed.py`) eliminates this by
operating on mutable clause objects backed by dynamic indices, making
propagation dramatically faster.

### Data structures

The solver wraps the input CNF into two layers of objects:

* **`Clause`** — a mutable set of literals (`els`) representing a single
  disjunctive clause. When a literal is removed (because its negation was
  assigned true), the clause shrinks in place.
* **`Clauses`** — a mutable set of all active `Clause` objects (`els`),
  with two indices:
  * **`by_lit`**: maps each literal to the set of clauses containing it.
    Built once at construction. Used to find which clauses are affected when a
    literal is assigned.
  * **`by_count`**: maps clause size to the set of clauses with that many
    remaining literals. Eagerly maintained as clauses shrink and grow. Used to
    find unit clauses (size 1) and empty clauses (size 0) in O(1).

### Unit propagation

When a literal `L` is assigned true:

1. **Remove satisfied clauses**: every clause containing `L` is satisfied, so
   it is removed from `Clauses.els`.  Found via `by_lit[L]`.
2. **Shrink remaining clauses**: every clause containing `~L` must have `~L`
   removed (it cannot contribute to satisfying that clause).  Found via
   `by_lit[~L]`.  As each clause shrinks, `by_count` is updated via `move()`.
3. **Cascade**: if shrinking a clause reduces it to size 1, it becomes a new
   unit clause. The solver collects all unit clauses via `by_count[1]` and
   propagates them in batch, repeating until no unit clauses remain.

### Backtracking with layered sets

DPLL explores the search space by branching: pick an unassigned literal, try
assigning it true, and recurse.  If that leads to a contradiction (an empty
clause), undo the assignment and try the opposite polarity.

The indexed solver uses **layered sets** (`layered.py`) to make undo
efficient.  `SetLayers` is an abstract base that wraps a mutable set and
records modifications per layer:

* **`push_layer()`** — starts a new layer.  Subsequent modifications are
  recorded.
* **`pop_layer()`** — undoes all modifications made in the current layer,
  restoring the set to its state at push time.

Two concrete subclasses exist:

* **`RemoveLayers`** — tracks elements removed from the set.  Pop restores
  them.  Used by `Clauses` (tracking which clauses were removed) and `Clause`
  (tracking which literals were removed).
* **`AddLayers`** — tracks elements added to the set.  Pop removes them.
  Used to track which literals have been assigned.

When the solver branches, it calls `push_layer()` on both `Clauses` and each
active `Clause`.  All propagation changes within that branch are recorded.  If
the branch fails, `pop_layer()` restores everything — clause membership,
literal membership, and index state — to exactly where it was before the
branch.

### Why this is fast

The naive solver does O(n) work per propagation step to rebuild the expression
tree.  The indexed solver does O(k) work where k is the number of clauses
directly affected by the assigned literal, found via index lookup rather than
scanning.  The `by_count` index provides O(1) access to unit and empty
clauses.  Backtracking is proportional to the number of changes made in the
branch rather than the total formula size.

## How the CDCL solver works

CDCL (Conflict-Driven Clause Learning) is the algorithm behind all modern SAT
solvers.  It extends DPLL with two key ideas: when the solver hits a dead end,
it **analyzes the conflict** to learn a new clause that prevents the same
mistake, and it **jumps back** to the earliest relevant decision rather than
undoing one level at a time.

Our implementation is in `solvers/cdcl.py`.

### The trail

CDCL replaces the recursive call stack and layered sets of DPLL with a single
flat data structure called the **trail** — an ordered list of all current
literal assignments.  Each entry records:

* **The literal** that was assigned true.
* **The decision level** — an integer that increments each time the solver
  makes a guess (as opposed to a forced propagation).
* **The reason clause** — the clause that forced this assignment via unit
  propagation, or `None` if the assignment was a decision (a guess).

The trail implicitly encodes the **implication graph**: for any propagated
literal, you can look up its reason clause, and the other literals in that
clause tell you *why* this literal was forced.  This graph is the foundation
of conflict analysis.

The companion array `trail_lim` records the trail index where each new
decision level begins, enabling efficient backjumping by simply truncating the
trail to the appropriate point.

### Boolean Constraint Propagation (BCP)

BCP is the inner loop of the solver.  A cursor (`prop_head`) tracks how far
along the trail has been processed.  For each unprocessed literal `L` on the
trail:

1. Look up all clauses containing `~L` (via the `by_lit` index) — these are
   the clauses that now have one fewer chance to be satisfied.
2. For each such clause, scan its literals and classify:
   * **Satisfied**: at least one literal is true.  Skip.
   * **Unit**: exactly one literal is unassigned, all others are false.
     Enqueue the unassigned literal on the trail with this clause as its
     reason.
   * **Conflict**: all literals are false.  Return the clause index.
   * **Otherwise**: multiple unassigned literals remain.  Skip.

BCP repeats until the cursor catches up to the end of the trail (no more
propagation to do) or a conflict is found.

### The main loop

```
enqueue initial unit clauses at level 0
if propagate() finds a conflict:
    return UNSAT

while unassigned variables remain:
    pick an unassigned variable and assign it (new decision level)

    while propagate() finds a conflict:
        if level == 0:
            return UNSAT                 # no decisions to undo
        analyze the conflict → learned clause + backjump level
        add the learned clause to the database
        backjump to the target level     # truncate the trail
        enqueue the learned clause's asserting literal

return SAT
```

There is no recursion. The outer loop makes decisions; the inner loop handles
conflicts.  Multiple conflicts can occur in sequence (a learned clause may
itself cause a new conflict after backjumping), which is why the inner loop
repeats.

### Conflict analysis (1-UIP)

When BCP finds a conflict, all literals in the conflicting clause are false.
The solver must figure out *why* and derive a compact clause that prevents
the same situation in the future.

The algorithm works by **resolution** — combining clauses to eliminate
variables.  Starting from the conflict clause, it walks backward along the
trail, resolving with reason clauses:

1. **Initialize**: take the conflict clause.  Count how many of its literals
   were assigned at the current decision level (the "current-level count").
2. **Resolve**: find the most recently assigned literal on the trail that
   appears in the working clause.  Look up its reason clause.  Combine the two
   clauses (union of literals, minus the resolved variable).  Decrement the
   current-level count.
3. **Repeat** until the current-level count reaches 1.

The last remaining current-level literal is called the **1-UIP** (First Unique
Implication Point).  It is the single point through which all implications at
the current level flowed toward the conflict.

The learned clause consists of the negation of the 1-UIP literal plus all
other literals encountered during resolution that belong to earlier decision
levels.

**Example**: suppose at decision level 5, the solver has assigned `a`, `b`,
and `c` through propagation, and hits a conflict clause `(~a ∨ ~b ∨ ~c)`.
Resolution with the reason for `c`, then the reason for `b`, might yield a
clause `(~a ∨ ~d)` where `d` was assigned at level 2.  The 1-UIP is `a`
(negated to `~a` in the learned clause), and the backjump level is 2.

### Backjumping

The **backjump level** is the highest decision level among the non-UIP
literals in the learned clause.  The solver truncates the trail to this level,
undoing all assignments above it.

After backjumping, the learned clause has exactly one unassigned literal (the
negation of the 1-UIP) — all other literals are false at or below the
backjump level.  This makes the learned clause unit, so BCP immediately
propagates the asserting literal.  The learned clause is recorded as its
reason, maintaining the implication graph for future conflict analysis.

This is a dramatic improvement over DPLL's chronological backtracking.  DPLL
always undoes exactly one level; CDCL can skip many levels when the conflict
is caused by a decision far up the search tree.

### What is learned

The learned clause is a logical consequence of the original formula — it is
always true whenever the original formula is satisfiable.  Adding it to the
clause database does not change the formula's satisfiability but *does* prune
the search space: the solver can never again make the same combination of
decisions that led to the conflict.

Over time, the solver accumulates clauses that encode information about which
parts of the search space are dead ends.  This is what makes CDCL dramatically
faster than DPLL on structured problems.

### What this implementation omits

This is a minimal CDCL implementation for educational purposes.  Production
solvers include additional techniques that provide major speedups:

* **Two Watched Literals (2WL)** — instead of scanning all literals in a
  clause during BCP, watch only two. This makes BCP nearly O(1) amortized per
  propagation and eliminates the need to undo clause state on backtrack.
* **VSIDS** — a decision heuristic that prioritizes variables involved in
  recent conflicts, focusing the search on the active part of the formula.
* **Restarts** — periodically restart the search from scratch (keeping learned
  clauses), preventing the solver from getting stuck.
* **Clause deletion** — remove low-quality learned clauses to keep the
  database manageable, using metrics like LBD (Literal Block Distance).
* **Phase saving** — remember the last polarity assigned to each variable and
  try it first on re-assignment.

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
