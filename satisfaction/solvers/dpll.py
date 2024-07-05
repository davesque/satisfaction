from collections import defaultdict
import logging

from satisfaction.choice import common_lit
from satisfaction.expr import And, CNF, Lit, Or
from satisfaction.layered import AddLayers
from satisfaction.typing import ChooseLit

from .solver import Solver

logger = logging.getLogger(__name__)


class DPLL(Solver):
    __slots__ = ("expr", "choose_lit", "assignments")

    expr: CNF
    choose_lit: ChooseLit
    assignments: AddLayers

    def __init__(self, expr: CNF, choose_lit: ChooseLit = common_lit) -> None:
        self.expr = expr
        self.choose_lit = choose_lit
        self.assignments = AddLayers(set())

    def check(self, expr: CNF | None = None) -> bool:
        """
        The Davis-Putnam-Logemann-Loveland (DPLL) SAT algorithm.

        Implementation based on the following description:
        https://en.wikipedia.org/wiki/DPLL_algorithm
        """
        if expr is None:
            expr = self.expr

        while lit := self.find_unit(expr):
            expr = self.unit_propagate(lit, expr)

        while pure_lits := self.find_pure(expr):
            for lit in pure_lits:
                expr = self.pure_literal_assign(lit, expr)

        # If the root conjunction is empty, then the overall formula is
        # satisfiable because any clause that was eliminated from the root
        # conjunction had a truth value of `true`. Therefore, the root
        # conjunction also evaluates to true.
        if len(expr.args) == 0:
            return True

        # If any disjunctive clause is empty, then the overall formula is not
        # satisfiable because any literal that was eliminated from a
        # disjunction had a truth value of `false`. Therefore, the parent
        # disjunction evaluates to `false` and the root conjunction also
        # evaluate to `false`.
        for or_expr in expr.args:
            if len(or_expr.args) == 0:
                return False

        lit = self.choose_lit(expr)

        logger.debug("+++++++++++++ branching +++++++++++++")
        self.assignments.push_layer()
        if self.check(self.unit_propagate(lit, expr)):
            return True
        self.assignments.pop_layer()

        logger.debug("------------ backtracking -----------")
        self.assignments.push_layer()
        if self.check(self.unit_propagate(~lit, expr)):
            return True
        self.assignments.pop_layer()

        return False

    @staticmethod
    def find_unit(and_expr: CNF) -> Lit | None:
        for or_expr in and_expr.args:
            if len(or_expr.args) == 1:
                return or_expr.args[0]

    def unit_propagate(self, lit: Lit, and_expr: CNF) -> CNF:
        logger.debug("assigning unit literal: %s", lit)
        self.assignments.update({lit})

        not_lit = ~lit
        and_args = []
        for or_expr in and_expr.args:
            delete = False
            or_args = []
            for or_lit in or_expr.args:
                # delete any disjunction that contains the literal
                if or_lit == lit:
                    delete = True
                    break

                # delete any arg equal to the literal's negation
                if or_lit == not_lit:
                    continue

                or_args.append(or_lit)

            if not delete:
                and_args.append(Or(*or_args))

        return And(*and_args)

    @staticmethod
    def find_pure(and_expr: CNF) -> set[Lit]:
        lit_variants = defaultdict(set)
        for or_expr in and_expr.args:
            for or_lit in or_expr.args:
                atom = or_lit.atom()
                lit_variants[atom].add(or_lit)

        pure_lits = {tuple(v)[0] for v in lit_variants.values() if len(v) == 1}
        return pure_lits

    def pure_literal_assign(self, lit: Lit, and_expr: CNF) -> CNF:
        logger.debug("assigning pure literal: %s", lit)
        self.assignments.update({lit})

        and_args = []
        for or_expr in and_expr.args:
            if lit not in or_expr.args:
                and_args.append(or_expr)

        return And(*and_args)
