from typing import Optional, TypeVar

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
