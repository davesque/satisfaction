from collections import defaultdict
import logging
import random
from typing import Callable

from satellite.expr import CNF, Connective, Expr, Lit, Not, Var
from satellite.index import Index

logger = logging.getLogger(__name__)


type ChooseLit = Callable[[CNF], Lit]


def count_lits(expr: Expr, counter: dict[Var, int]) -> None:
    match expr:
        case Var(_):
            # if name.startswith("x"):
            counter[expr] += 1
        case Not(p):
            count_lits(p, counter)
        case Connective(args):
            for arg in args:
                count_lits(arg, counter)


def common_lit(expr: CNF) -> Lit:
    counter = defaultdict(lambda: 0)
    count_lits(expr, counter)

    counts = sorted(counter.items(), key=lambda i: i[1], reverse=True)
    return counts[0][0]


def first_lit(expr: CNF) -> Lit:
    or_expr = expr.args[0]
    return or_expr.args[0]


def last_lit(expr: CNF) -> Lit:
    or_expr = expr.args[-1]
    return or_expr.args[-1]


def random_lit(expr: CNF) -> Lit:
    or_expr = random.choice(expr.args)
    lit = random.choice(or_expr.args)
    return lit


class DPLL:
    __slots__ = ("expr", "choose_lit", "index")

    expr: CNF
    choose_lit: ChooseLit

    def __init__(self, expr: CNF, choose_lit: ChooseLit = common_lit) -> None:
        self.expr = expr
        self.choose_lit = choose_lit
        self.index = Index(expr)

    def check(self) -> bool:
        """
        The Davis-Putnam-Logemann-Loveland (DPLL) SAT algorithm.

        Implementation based on the following description:
        https://en.wikipedia.org/wiki/DPLL_algorithm
        """
        while units := self.find_units():
            self.unit_propagate(*units)

        # If the root conjunction is empty, this implies that the formula is
        # satisfiable.  This follows from the fact that any clause that was
        # eliminated from the root conjunction was determined to have a truth value
        # of `true`. Therefore, the root conjunction also evaluates to true.
        if len(self.index.unassigned_clauses) == 0:
            return True

        # If any disjunctive clause is empty, this implies that the formula is not
        # satisfiable.  This follows from the fact that any literal that was
        # eliminated from a disjunction was determined to have a truth value of
        # `false`.  Therefore, the parent disjunction evaluates to `false` and the
        # root conjunction also evaluate to `false`.
        if len(self.index.clauses_for_count(0)) > 0:
            return False

        first_clause = next(iter(self.index.unassigned_clauses))
        lit = next(iter(first_clause.unassigned))

        logger.debug("+++++++++++++ branching +++++++++++++")
        self.index.push()
        self.unit_propagate(lit)
        if self.check():
            return True
        self.index.pop()

        logger.debug("------------ backtracking -----------")
        self.index.push()
        self.unit_propagate(~lit)
        if self.check():
            return True
        self.index.pop()

        return False

    def find_units(self) -> set[Lit]:
        units = {}
        for clause in self.index.clauses_for_count(1):
            lit = tuple(clause.unassigned)[0]
            units[lit.atom()] = lit

        return set(units.values())

    def unit_propagate(self, *units: Lit) -> None:
        logger.debug("assigning unit literals: %s", units)

        for unit in units:
            for clause in self.index.clauses_for_lit(unit):
                self.index.assign_clause(clause)

            not_unit = ~unit
            for clause in self.index.clauses_for_lit(not_unit):
                clause.assign(not_unit)

    # @staticmethod
    # def find_pure(and_expr: CNF) -> set[Lit]:
    #     lit_variants = defaultdict(set)
    #     for or_expr in and_expr.args:
    #         for or_lit in or_expr.args:
    #             atom = or_lit.atom()
    #             lit_variants[atom].add(or_lit)

    #     pure_lits = {tuple(v)[0] for v in lit_variants.values() if len(v) == 1}
    #     return pure_lits

    # def pure_literal_assign(self, lit: Lit, and_expr: CNF) -> CNF:
    #     logger.debug("assigning pure literal: %s", lit)
    #     # self.index.assign(lit, True)

    #     and_args = []
    #     for or_expr in and_expr.args:
    #         if lit not in or_expr.args:
    #             and_args.append(or_expr)

    #     return And(*and_args)
