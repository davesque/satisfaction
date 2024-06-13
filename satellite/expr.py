from __future__ import annotations
import functools
from typing import Any, Callable

from satellite.utils import SlotClass


def require_expr[
    T: "Expr", U: "Expr"
](old_fn: Callable[[T, Expr], U]) -> Callable[[T, Any], U]:
    @functools.wraps(old_fn)
    def new_fn(self: T, other: Any) -> U:
        if not isinstance(other, Expr):
            raise TypeError(f"cannot combine expr and non-expr")

        return old_fn(self, other)

    return new_fn


class Expr(SlotClass):
    __slots__ = ()

    precedence = float("inf")

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
        return hash((type(self),) + tuple(self.__values__()))

    def __repr__(self) -> str:
        from satellite.format import format_expr

        return format_expr(self)

    @property
    def atom(self) -> Var | None:
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


class Not[T: Expr](Expr):
    __slots__ = ("expr",)
    __match_args__ = ("expr",)

    precedence = 4

    expr: T

    @property
    def atom(self) -> Var | None:
        # not `None` if `self.expr` is a `Var`
        return self.expr.atom


class Var(Expr):
    __slots__ = ("name", "generated")
    __match_args__ = ("name",)

    name: str
    generated: bool

    def __init__(self, name: str, generated: bool = False) -> None:
        self.name = name
        self.generated = generated

    @property
    def atom(self) -> Var:
        return self


class Connective[T: Expr](Expr):
    __slots__ = ("args",)
    __match_args__ = ("args",)

    precedence: int

    args: tuple[T, ...]

    def __init__(self, *args: T):
        super().__init__(args)


class And[T: Expr](Connective[T]):
    __slots__ = ()
    precedence = 3


class Or[T: Expr](Connective[T]):
    __slots__ = ()
    precedence = 2


class BinOp[T: Expr, U: Expr](Connective):
    __slots__ = ()

    args: tuple[T, U]

    # enforce two args
    def __init__(self, lhs: T, rhs: U):
        super().__init__(lhs, rhs)

    @property
    def lhs(self) -> T:
        return self.args[0]

    @property
    def rhs(self) -> U:
        return self.args[1]


class Implies[T: Expr, U: Expr](BinOp[T, U]):
    __slots__ = ()
    precedence = 1


class Equivalent[T: Expr, U: Expr](BinOp[T, U]):
    __slots__ = ()
    precedence = 0


type Lit = Var | Not[Var]
type CNF = And[Or[Lit]]


def var(
    *specs: str, sep: str | None = None, generated: bool = False
) -> tuple[Var, ...]:
    res = []
    for spec in specs:
        for v in spec.split(sep=sep):
            res.append(Var(v.strip(), generated=generated))

    return tuple(res)
