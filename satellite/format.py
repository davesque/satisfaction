from __future__ import annotations
from typing import Optional

from satellite.expr import Expr, Var, Not, Connective


def format_expr(expr: Expr, parent: Optional[Expr] = None) -> str:
    match expr:
        case Var(name):  # type: ignore
            return name

        case Not(sub_expr):  # type: ignore
            return f"~{format_expr(sub_expr, expr)}"

        case Connective(args):  # type: ignore
            try:
                parent_precedence = parent.precedence  # type: ignore
            except AttributeError:
                parent_precedence = float("inf")

            args_repr = expr.join_with.join(format_expr(a, expr) for a in args)
            if parent is None or expr.precedence > parent_precedence:
                return args_repr
            else:
                return f"({args_repr})"

    raise ValueError(f"unsupported value: {expr}")
