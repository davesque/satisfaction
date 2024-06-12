from collections import defaultdict
import logging
import random
from typing import Callable, Dict, Optional, Set, cast

from satellite.expr import And, CNF, Connective, Expr, Literal, Not, Or, Var

logger = logging.getLogger(__name__)


def count_lits(expr: Expr, counter: Dict[Var, int]) -> None:
    match expr:
        case Var(_):
            # if name.startswith("x"):
            counter[expr] += 1
        case Not(p):
            count_lits(p, counter)
        case Connective(args):
            for arg in args:
                count_lits(arg, counter)


def common_lit(expr: CNF) -> Literal:
    counter = defaultdict(lambda: 0)
    count_lits(expr, counter)

    counts = sorted(counter.items(), key=lambda i: i[1], reverse=True)
    return counts[0][0]


def first_lit(expr: CNF) -> Literal:
    or_expr = cast(Or, expr.args[0])
    return or_expr.args[0]


def last_lit(expr: CNF) -> Literal:
    or_expr = cast(Or, expr.args[-1])
    return or_expr.args[-1]


def random_lit(expr: CNF) -> Literal:
    or_expr = cast(Or, random.choice(expr.args))
    lit = random.choice(or_expr.args)
    return lit


def dpll(expr: CNF, choose_lit: Callable[[CNF], Literal] = common_lit) -> bool:
    """
    The Davis-Putnam-Logemann-Loveland (DPLL) SAT algorithm.

    Implementation based on the following description:
    https://en.wikipedia.org/wiki/DPLL_algorithm
    """
    while lit := find_unit(expr):
        expr = unit_propagate(lit, expr)

    while pure_lits := find_pure(expr):
        for lit in pure_lits:
            expr = pure_literal_assign(lit, expr)

    # If the root conjunction is empty, this implies that the formula is
    # satisfiable.  This follows from the fact that any clause that was
    # eliminated from the root conjunction was determined to have a truth value
    # of `true`. Therefore, the root conjunction also evaluates to true.
    if len(expr.args) == 0:
        return True

    # If any disjunctive clause is empty, this implies that the formula is not
    # satisfiable.  This follows from the fact that any literal that was
    # eliminated from a disjunction was determined to have a truth value of
    # `false`.  Therefore, the parent disjunction evaluates to `false` and the
    # root conjunction also evaluate to `false`.
    for or_expr in expr.args:
        if len(or_expr.args) == 0:
            return False

    lit = choose_lit(expr)

    logger.debug("+++++++++++++ branching +++++++++++++")
    if dpll(unit_propagate(lit, expr), choose_lit):
        return True
    logger.debug("------------ backtracking -----------")
    return dpll(unit_propagate(~lit, expr), choose_lit)


def find_unit(and_expr: CNF) -> Optional[Expr]:
    for or_expr in and_expr.args:
        if len(or_expr.args) == 1:
            return or_expr.args[0]


def unit_propagate(lit: Expr, and_expr: CNF) -> CNF:
    logger.debug("eliminating unit: %s", lit)

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


def find_pure(and_expr: CNF) -> Set[Expr]:
    lit_variants = defaultdict(set)
    for or_expr in and_expr.args:
        for or_lit in or_expr.args:
            atom = or_lit.atom
            lit_variants[atom].add(or_lit)

    pure_lits = {tuple(v)[0] for v in lit_variants.values() if len(v) == 1}
    return pure_lits


def pure_literal_assign(lit: Expr, and_expr: CNF) -> CNF:
    logger.debug("eliminating pure literal: %s", lit)

    and_args = []
    for or_expr in and_expr.args:
        if lit not in or_expr.args:
            and_args.append(or_expr)

    return And(*and_args)
