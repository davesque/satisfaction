from __future__ import annotations

from satellite.expr import Expr, Var, Not, Connective, And, Or, Implies, Equivalent


class Formatter:
    symbols: dict[type[Expr], str]

    def __init__(self, symbols: dict[type[Expr], str]) -> None:
        self.symbols = symbols

    def format(self, expr: Expr, parent: Expr | None = None) -> str:
        match expr:
            case Var(name):
                return name

            case Not(sub_expr):
                symbol = self.symbols[Not]
                return f"{symbol}{self.format(sub_expr, expr)}"

            case Connective(args):
                symbol = self.symbols[type(expr)]
                args_repr = symbol.join(self.format(a, expr) for a in args)

                if parent is None or expr.precedence > parent.precedence:
                    return args_repr
                else:
                    return f"({args_repr})"

        raise ValueError(f"unsupported value: {expr}")


pythonic = Formatter(
    {
        Not: "~",
        And: " & ",
        Or: " | ",
        Implies: " -> ",
        Equivalent: " <-> ",
    }
)

standard = Formatter(
    {
        Not: "¬",
        And: " ∧ ",
        Or: " ∨ ",
        Implies: " ⇒ ",
        Equivalent: " ⇔ ",
    }
)

default = pythonic


def set_formatter(formatter: Formatter) -> None:
    global default
    default = formatter


def format_expr(expr: Expr) -> str:
    return default.format(expr)
