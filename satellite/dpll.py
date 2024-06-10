from collections import defaultdict
from typing import Optional, Set, TypeVar

from satellite.expr import And, Expr, Or


T = TypeVar("T", bound=Expr)


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
