from __future__ import annotations
import functools
from typing import Any, Callable, Optional, Tuple, TypeVar

from satellite.utils import SlotClass

T = TypeVar("T", bound="Expr")
U = TypeVar("U", bound="Expr")


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


def require_expr(old_fn: Callable[[T, Expr], U]) -> Callable[[T, Any], U]:
    @functools.wraps(old_fn)
    def new_fn(self: T, other: Any) -> U:
        if not isinstance(other, Expr):
            raise TypeError(f"cannot combine expr and non-expr")

        return old_fn(self, other)

    return new_fn


class Expr(SlotClass):
    def __invert__(self) -> Expr:
        if isinstance(self, Not):
            return self.expr
        else:
            return Not(self)

    @require_expr
    def __or__(self, other: Expr) -> Or:
        if isinstance(self, Or) and isinstance(other, Or):
            return Or(*(self.args + other.args))
        elif isinstance(self, Or):
            return Or(*(self.args + (other,)))
        elif isinstance(other, Or):
            return Or(*((self,) + other.args))
        else:
            return Or(*(self, other))

    @require_expr
    def __and__(self, other: Expr) -> And:
        if isinstance(self, And) and isinstance(other, And):
            return And(*(self.args + other.args))
        elif isinstance(self, And):
            return And(*(self.args + (other,)))
        elif isinstance(other, And):
            return And(*((self,) + other.args))
        else:
            return And(*(self, other))

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__values__))

    def __repr__(self) -> str:
        return format_expr(self)

    @property
    def atom(self) -> Optional[Var]:
        return None

    @property
    def is_cnf(self) -> bool:
        if not isinstance(self, And):
            return False

        for and_arg in self.args:
            if not isinstance(and_arg, Or):
                return False

            for or_arg in and_arg.args:
                if or_arg.atom is None:
                    return False

        return True


class Not(Expr):
    __slots__ = ("expr",)

    precedence = 4

    expr: Expr

    @property
    def atom(self) -> Optional[Var]:
        # not `None` if `self.expr` is a `Var`
        return self.expr.atom


class Var(Expr):
    __slots__ = ("name",)

    name: str

    @property
    def atom(self) -> Optional[Var]:
        return self


class Connective(Expr):
    __slots__ = ("args",)

    join_with: str
    precedence: int

    args: Tuple[Expr, ...]

    def __init__(self, *args: Expr):
        super().__init__(args)


class And(Connective):
    join_with = " & "
    precedence = 3


class Or(Connective):
    join_with = " | "
    precedence = 2


class BinOp(Connective):
    # enforce two args
    def __init__(self, lhs: Expr, rhs: Expr):
        super().__init__(lhs, rhs)


class Implies(BinOp):
    join_with = " -> "
    precedence = 1


class Equivalent(BinOp):
    join_with = " <-> "
    precedence = 0


def var(*specs: str, sep: Optional[str] = None) -> Tuple[Var, ...]:
    res = []
    for spec in specs:
        for v in spec.split(sep=sep):
            res.append(Var(v.strip()))

    return tuple(res)
