import logging

import pytest

from satellite.expr import Implies, Lit, var
from satellite.solvers.indexed import DPLL, Clauses
from satellite.tseitin import Tseitin
from satellite.utils import numbered_var

from .base_suite import BaseSuite

p, q, r = var("p q r")

# (r -> p) -> (~(q & r) -> p)
expr = Implies(Implies(r, p), Implies(~(q & r), p))

tseitin = Tseitin(expr, rename_vars=False, name_gen=numbered_var("x", 1))
cnf = tseitin.transform(sort=True)

x1, x2, x3, x4, x5 = var("x1 x2 x3 x4 x5", generated=True)

logger = logging.getLogger(__name__)


@pytest.fixture
def index() -> Clauses:
    return Clauses(cnf)


class TestIndexed(BaseSuite):
    solver_cls = DPLL
    queens = (12, True)


class TestIndex:
    def test_init(self, index: Clauses) -> None:
        assert len(index.clauses) == len(cnf.args)
        assert sorted(index.by_lit.keys(), key=repr) == [
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
        assert sorted(index.by_count.keys()) == [0, 1, 2, 3]

    @pytest.mark.parametrize(
        "lit,clauses",
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
        self, index: Clauses, lit: Lit, clauses: tuple[int, ...]
    ) -> None:
        assert index.with_lit(lit) == {index.clauses[i] for i in clauses}

    @pytest.mark.parametrize(
        "count,clauses",
        (
            (1, (0,)),
            (2, (2, 3, 5, 6, 8, 9, 10, 11, 12, 13)),
            (3, (1, 4, 7, 14)),
        ),
    )
    def test_clauses_with_count(
        self, index: Clauses, count: int, clauses: tuple[int, ...]
    ) -> None:
        assert index.with_count(count) == {index.clauses[i] for i in clauses}

    def test_push_pop_mutation(self, index: Clauses) -> None:
        clause = index.clauses[1]

        index.push_layer()
        assert clause.els == {~x1, ~x2, x3}
        assert clause.depth == 1

        len_1_clauses = (0,)
        assert index.with_count(1) == {index.clauses[i] for i in len_1_clauses}
        len_3_clauses = (1, 4, 7, 14)
        assert index.with_count(3) == {index.clauses[i] for i in len_3_clauses}

        clause.difference_update({x3, ~x2})
        assert clause.els == {~x1}

        len_1_clauses = (0, 1)
        assert index.with_count(1) == {index.clauses[i] for i in len_1_clauses}
        len_3_clauses = (4, 7, 14)
        assert index.with_count(3) == {index.clauses[i] for i in len_3_clauses}

        index.pop_layer()
        assert clause.els == {~x1, ~x2, x3}
        assert clause.depth == 0

        len_1_clauses = (0,)
        assert index.with_count(1) == {index.clauses[i] for i in len_1_clauses}
        len_3_clauses = (1, 4, 7, 14)
        assert index.with_count(3) == {index.clauses[i] for i in len_3_clauses}
