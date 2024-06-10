from __future__ import annotations

from typing import Any, Tuple, Optional

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
            return Or(*(self.args + other.args))
        elif isinstance(self, Or):
            return Or(*(self.args + (other,)))
        elif isinstance(other, Or):
            return Or(*((self,) + other.args))
        else:
            return Or(*(self, other))

    def __ror__(self, _: Any) -> None:
        raise ValueError(f"cannot disjoin with non-expression")

    def __and__(self, other: Any) -> And:
        if not isinstance(other, Expr):
            raise ValueError(f"cannot conjoin with non-expression")

        if isinstance(self, And) and isinstance(other, And):
            return And(*(self.args + other.args))
        elif isinstance(self, And):
            return And(*(self.args + (other,)))
        elif isinstance(other, And):
            return And(*((self,) + other.args))
        else:
            return And(*(self, other))

    def __rand__(self, _: Any) -> None:
        raise ValueError(f"cannot conjoin with non-expression")

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

    expr: Expr

    @property
    def atom(self) -> Optional[Var]:
        # not `None` if `self.expr` is a `Var`
        return self.expr.atom

    def __repr__(self) -> str:
        if isinstance(self.expr, (Or, Var)):
            return f"~{repr(self.expr)}"
        else:
            return f"~({repr(self.expr)})"


class Var(Expr):
    __slots__ = ("name",)

    name: str

    @property
    def atom(self) -> Optional[Var]:
        return self

    def __repr__(self) -> str:
        return self.name


class Connective(Expr):
    __slots__ = ("args",)

    args: Tuple[Expr, ...]

    def __init__(self, *args: Expr):
        super().__init__(args)


class Or(Connective):
    def __repr__(self) -> str:
        args_repr = " | ".join(map(repr, self.args))
        return f"({args_repr})"


class And(Connective):
    def __repr__(self) -> str:
        return " & ".join(map(repr, self.args))


def var(*specs: str, sep: Optional[str] = None) -> Tuple[Var, ...]:
    res = []
    for spec in specs:
        for v in spec.split(sep=sep):
            res.append(Var(v.strip()))

    return tuple(res)
