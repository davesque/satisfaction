from __future__ import annotations

from typing import Any, Tuple

from satellite.utils import SlotClass


class Expr(SlotClass):
    __slots__ = ()

    def __invert__(self) -> Expr:
        if isinstance(self, Not):
            return self.expr
        else:
            return Not(self)

    def __or__(self, other: Any) -> Or:
        if not isinstance(other, Expr):
            raise ValueError(f"cannot disjoin with non-expression")

        if isinstance(self, Or) and isinstance(other, Or):
            return Or(self.args + other.args)
        elif isinstance(self, Or):
            return Or(self.args + (other,))
        elif isinstance(other, Or):
            return Or((self,) + other.args)
        else:
            return Or((self, other))

    def __ror__(self, other: Any) -> None:
        raise ValueError(f"cannot disjoin with non-expression")

    def __and__(self, other: Any) -> And:
        if not isinstance(other, Expr):
            raise ValueError(f"cannot conjoin with non-expression")

        if isinstance(self, And) and isinstance(other, And):
            return And(self.args + other.args)
        elif isinstance(self, And):
            return And(self.args + (other,))
        elif isinstance(other, And):
            return And((self,) + other.args)
        else:
            return And((self, other))

    def __rand__(self, other: Any) -> None:
        raise ValueError(f"cannot conjoin with non-expression")


class Not(Expr):
    __slots__ = ("expr",)

    expr: Expr


class Var(Expr):
    __slots__ = ("name",)

    name: str


class Or(Expr):
    __slots__ = ("args",)

    args: Tuple[Expr, ...]


class And(Expr):
    __slots__ = ("args",)

    args: Tuple[Expr, ...]
