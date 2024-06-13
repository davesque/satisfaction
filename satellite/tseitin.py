from typing import Dict, Iterator, List, Optional, Set

from satellite.expr import (
    And,
    CNF,
    Connective,
    Equivalent,
    Expr,
    Implies,
    Lit,
    Not,
    Or,
    Var,
)
from satellite.utils import letters


class Tseitin:
    __slots__ = (
        "expr",
        "rename_vars",
        "name_gen",
        "equivalences",
        "renames",
        "root",
    )

    expr: Expr
    rename_vars: bool
    name_gen: Iterator[str]

    equivalences: Set[Equivalent[Var, Expr]]
    renames: Dict[Var, Var]
    root: Lit

    def __init__(
        self,
        expr: Expr,
        rename_vars: bool = True,
        name_gen: Optional[Iterator[str]] = None,
    ) -> None:
        if name_gen is None:
            name_gen = letters()

        self.expr = expr
        self.rename_vars = rename_vars
        self.name_gen = name_gen

        self.equivalences = set()
        self.renames = {}
        self.root = self.rewrite(expr)

    def new_var(self) -> Var:
        return Var(next(self.name_gen))

    def lookup(self, orig_var: Var) -> Var:
        try:
            return self.renames[orig_var]
        except KeyError:
            new_var = self.new_var()
            self.renames[orig_var] = new_var
            return new_var

    def rewrite(self, expr: Expr) -> Lit:
        match expr:
            case Var(_):
                return self.lookup(expr) if self.rename_vars else expr

            case Not(Var(_) as var):
                return Not(self.lookup(var)) if self.rename_vars else expr

            case Not(p):
                lhs = self.new_var()
                rhs = Not(self.rewrite(p))

            case Connective((p, q)):
                lhs = self.new_var()
                rhs = type(expr)(self.rewrite(p), self.rewrite(q))

            # special case for left-associative operators with more than 2 args
            case And((*ps, q)) | Or((*ps, q)):
                lhs = self.new_var()
                rhs = type(expr)(
                    self.rewrite(type(expr)(*ps)),
                    self.rewrite(q),
                )

            case _:
                assert False

        self.equivalences.add(Equivalent(lhs, rhs))
        return lhs

    @staticmethod
    def equiv_to_cnf(equiv: Equivalent[Var, Expr]) -> CNF:
        """
        Convert an equivalence to CNF.

        Each of these match cases should work regardless of the polarity of
        right-hand side literals.
        """
        match equiv:
            case Equivalent((p, Not(q))):
                # p <-> ~q
                # = (p -> ~q) & (~q -> p)
                # = (~p | ~q) & (q | p)
                return (~p | ~q) & (q | p)

            case Equivalent((p, Implies((q, r)))):
                # p <-> (q -> r)
                # = (~p | (q -> r)) & (~(q -> r) | p)
                # = (~p | (~q | r)) & (~(~q | r) | p)
                # = (~p | ~q | r) & (q & ~r | p)
                # = (~p | ~q | r) & (q | p) & (~r | p)
                return (~p | ~q | r) & (q | p) & (~r | p)

            case Equivalent((p, Or((q, r)))):
                # p <-> (q | r)
                # = (~p | (q | r)) & (~(q | r) | p)
                # = (~p | q | r) & (~q & ~r | p)
                # = (~p | q | r) & (~q | p) & (~r | p)
                return (~p | q | r) & (~q | p) & (~r | p)

            case Equivalent((p, And((q, r)))):
                # p <-> (q & r)
                # = (~p | (q & r)) & (~(q & r) | p)
                # = (~p | q) & (~p | r) & (~q | ~r | p)
                return (~p | q) & (~p | r) & (~q | ~r | p)

        assert False

    def transform(self, sort: bool = False) -> CNF:
        if sort:
            equivalences = list(self.equivalences)
            equivalences.sort(key=lambda equiv: equiv.lhs.name)
        else:
            equivalences = self.equivalences

        parts: List[Or[Lit]] = [Or(self.root)]
        for equiv in equivalences:
            and_expr = self.equiv_to_cnf(equiv)
            parts.extend(and_expr.args)

        return And(*parts)
