from collections import defaultdict
from typing import Optional, Set, cast

from satellite.expr import And, Expr, Or


def dpll(expr: And) -> bool:
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
        assert isinstance(or_expr, Or)

        if len(or_expr.args) == 0:
            return False

    first_or = cast(Or, expr.args[0])
    lit = first_or.args[0]

    return dpll(unit_propagate(lit, expr)) or dpll(unit_propagate(~lit, expr))


def find_unit(and_expr: And) -> Optional[Expr]:
    assert isinstance(and_expr, And)

    for or_expr in and_expr.args:
        assert isinstance(or_expr, Or)

        if len(or_expr.args) == 1:
            lit = or_expr.args[0]

            assert lit.atom is not None
            return lit


def unit_propagate(lit: Expr, and_expr: And) -> And:
    assert isinstance(and_expr, And)

    not_lit = ~lit
    and_args = []
    for or_expr in and_expr.args:
        assert isinstance(or_expr, Or)

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


def find_pure(and_expr: And) -> Set[Expr]:
    assert isinstance(and_expr, And)

    lit_variants = defaultdict(set)
    for or_expr in and_expr.args:
        assert isinstance(or_expr, Or)

        for or_lit in or_expr.args:
            atom = or_lit.atom
            assert atom is not None

            lit_variants[atom].add(or_lit)

    pure_lits = {tuple(v)[0] for v in lit_variants.values() if len(v) == 1}
    return pure_lits


def pure_literal_assign(lit: Expr, and_expr: And) -> And:
    assert isinstance(and_expr, And)

    and_args = []
    for or_expr in and_expr.args:
        assert isinstance(or_expr, Or)

        if lit not in or_expr.args:
            and_args.append(or_expr)

    return And(*and_args)
