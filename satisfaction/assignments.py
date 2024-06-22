from .exceptions import ConflictError
from .expr import Clause, Lit, Not, Var

type Subject = Clause | Var
type Facts = dict[Clause | Var, bool]


class Assignments:
    __slots__ = ("branches", "cache")

    branches: list[Facts]
    cache: Facts

    def __init__(self) -> None:
        self.branches = [{}]
        self.cache = {}

    def set(self, expr: Subject, x: bool) -> None:
        if expr in self.cache:
            if self.cache[expr] is x:
                return
            else:
                raise ConflictError(
                    f"'{x}' conflicts with existing assignment for '{expr}'"
                )

        self.branches[-1][expr] = x
        self.cache[expr] = x

    def get(self, expr: Subject) -> bool:
        return self.cache[expr]

    def assign(self, expr: Clause | Lit, x: bool) -> None:
        match expr:
            case Not(Var(_) as var):
                self.set(var, not x)
            case _:
                self.set(expr, x)

    def push(self) -> None:
        self.branches.append({})

    def pop(self) -> Facts:
        if len(self.branches) == 1:
            raise IndexError("cannot pop base branch")

        branch = self.branches.pop()
        for k in branch:
            self.cache.pop(k)

        return branch
