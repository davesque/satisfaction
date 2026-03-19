import logging

import pytest

from satisfaction.expr import Implies, Lit, var
from satisfaction.solvers.indexed import Clauses, DPLL
from satisfaction.tseitin import Tseitin
from satisfaction.utils import numbered_var

from .base_suite import BaseSuite

p, q, r = var("p q r")

# (r -> p) -> (~(q & r) -> p)
expr = Implies(Implies(r, p), Implies(~(q & r), p))

tseitin = Tseitin(expr, rename_vars=False, name_gen=numbered_var("x", 1))
cnf = tseitin.transform(sort=True)

x1, x2, x3, x4, x5 = var("x1 x2 x3 x4 x5", generated=True)

logger = logging.getLogger(__name__)


@pytest.fixture
def clauses() -> Clauses:
    return Clauses(cnf)


class TestIndexed(BaseSuite):
    solver_cls = DPLL
    queens = (8, True)


class TestIndex:
    def test_init(self, clauses: Clauses) -> None:
        assert len(clauses.clauses) == len(cnf.args)
        assert sorted(clauses.by_lit.keys(), key=repr) == [
            p,
            q,
            r,
            x1,
            x2,
            x3,
            x4,
            x5,
            ~p,
            ~q,
            ~r,
            ~x1,
            ~x2,
            ~x3,
            ~x4,
            ~x5,
        ]
        assert sorted(clauses.by_count.keys()) == [0, 1, 2, 3]

    @pytest.mark.parametrize(
        "lit,clause_indices",
        (
            (p, (4, 7)),
            (q, (12,)),
            (r, (5, 13)),
            (x1, (0, 2, 3)),
            (x2, (2, 5, 6)),
            (x3, (1, 8, 9)),
            (x4, (8, 11)),
            (x5, (11, 14)),
            (~p, (6, 9)),
            (~q, (14,)),
            (~r, (4, 14)),
            (~x1, (1,)),
            (~x2, (1, 4)),
            (~x3, (3, 7)),
            (~x4, (7, 10)),
            (~x5, (10, 12, 13)),
        ),
    )
    def test_clauses_with_lit(
        self, clauses: Clauses, lit: Lit, clause_indices: tuple[int, ...]
    ) -> None:
        assert clauses.with_lit(lit) == {clauses.clauses[i] for i in clause_indices}

    @pytest.mark.parametrize(
        "count,clause_indices",
        (
            (1, (0,)),
            (2, (2, 3, 5, 6, 8, 9, 10, 11, 12, 13)),
            (3, (1, 4, 7, 14)),
        ),
    )
    def test_clauses_with_count(
        self, clauses: Clauses, count: int, clause_indices: tuple[int, ...]
    ) -> None:
        assert clauses.with_count(count) == {clauses.clauses[i] for i in clause_indices}

    def test_push_pop_literal_mutation(self, clauses: Clauses) -> None:
        clause = clauses.clauses[1]

        clauses.push_layer()
        assert clause.els == {~x1, ~x2, x3}
        assert clause.depth == 1

        len_1_clauses = (0,)
        assert clauses.with_count(1) == {clauses.clauses[i] for i in len_1_clauses}
        len_3_clauses = (1, 4, 7, 14)
        assert clauses.with_count(3) == {clauses.clauses[i] for i in len_3_clauses}

        clause.difference_update({x3, ~x2})
        assert clause.els == {~x1}

        len_1_clauses = (0, 1)
        assert clauses.with_count(1) == {clauses.clauses[i] for i in len_1_clauses}
        len_3_clauses = (4, 7, 14)
        assert clauses.with_count(3) == {clauses.clauses[i] for i in len_3_clauses}

        clauses.pop_layer()
        assert clause.els == {~x1, ~x2, x3}
        assert clause.depth == 0

        len_1_clauses = (0,)
        assert clauses.with_count(1) == {clauses.clauses[i] for i in len_1_clauses}
        len_3_clauses = (1, 4, 7, 14)
        assert clauses.with_count(3) == {clauses.clauses[i] for i in len_3_clauses}

    def test_push_pop_clause_removal(self, clauses: Clauses) -> None:
        """Removing a clause from Clauses.els should update by_count eagerly
        and restore correctly on pop."""
        c0, c1 = clauses.clauses[0], clauses.clauses[1]
        original_els = set(clauses.els)

        clauses.push_layer()

        # Remove two clauses: c0 (count 1) and c1 (count 3)
        clauses.difference_update({c0, c1})
        assert c0 not in clauses.els
        assert c1 not in clauses.els

        # by_count should no longer include removed clauses
        assert c0 not in clauses.with_count(1)
        assert c1 not in clauses.with_count(3)

        clauses.pop_layer()

        # Everything restored
        assert clauses.els == original_els
        assert c0 in clauses.with_count(1)
        assert c1 in clauses.with_count(3)

    def test_push_pop_literal_mutation_then_clause_removal(
        self, clauses: Clauses
    ) -> None:
        """A clause that has literals removed and is then removed from
        Clauses.els should restore both correctly on pop."""
        c1 = clauses.clauses[1]  # {~x1, ~x2, x3}, count 3
        original_els = set(clauses.els)

        clauses.push_layer()

        # First modify the clause's literals
        c1.difference_update({x3})
        assert c1.els == {~x1, ~x2}
        assert c1 in clauses.with_count(2)
        assert c1 not in clauses.with_count(3)

        # Then remove the clause entirely
        clauses.difference_update({c1})
        assert c1 not in clauses.els
        assert c1 not in clauses.with_count(2)

        clauses.pop_layer()

        # Both the clause membership and its literals should be restored
        assert clauses.els == original_els
        assert c1.els == {~x1, ~x2, x3}
        assert c1 in clauses.with_count(3)

    def test_multi_depth_inactive_clause(self, clauses: Clauses) -> None:
        """A clause removed at depth 1 should be skipped by depth 2's
        push/pop and correctly restored at depth 1's pop."""
        c1 = clauses.clauses[1]
        c4 = clauses.clauses[4]  # {~x2, ~r, p}, count 3
        original_els = set(clauses.els)

        # Depth 1: remove c1
        clauses.push_layer()
        clauses.difference_update({c1})
        assert c1 not in clauses.els

        # Depth 2: c1 is inactive, should be skipped
        clauses.push_layer()

        # Modify an active clause at depth 2
        c4.difference_update({p})
        assert c4.els == {~x2, ~r}
        assert c4 in clauses.with_count(2)

        # Pop depth 2: c4 restored, c1 still inactive
        clauses.pop_layer()
        assert c4.els == {~x2, ~r, p}
        assert c4 in clauses.with_count(3)
        assert c1 not in clauses.els

        # Pop depth 1: c1 restored
        clauses.pop_layer()
        assert clauses.els == original_els
        assert c1 in clauses.with_count(3)
