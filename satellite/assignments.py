from .exceptions import ConflictError
from .expr import Lit, Not, Var


class Assignments:
    __slots__ = ("branches", "cache")

    branches: list[dict[Var, bool]]
    cache: dict[Var, bool]

    def __init__(self) -> None:
        self.branches = [{}]
        self.cache = {}

    def set(self, var: Var, x: bool) -> None:
        if var in self.cache:
            if self.cache[var] is x:
                return
            else:
                raise ConflictError(
                    f"'{x}' conflicts with existing assignment for '{var}'"
                )

        self.branches[-1][var] = x
        self.cache[var] = x

    def get(self, var: Var) -> bool:
        return self.cache[var]

    def assign(self, lit: Lit, x: bool) -> None:
        match lit:
            case Var(_):
                self.set(lit, x)
            case Not(Var(_) as var):
                self.set(var, not x)
            case _:
                raise ValueError(f"cannot assign to non-literal: {type(lit)}")

    def push(self) -> None:
        self.branches.append({})

    def pop(self) -> dict[Var, bool]:
        if len(self.branches) == 1:
            raise IndexError("cannot pop base branch")

        branch = self.branches.pop()
        for k in branch:
            self.cache.pop(k)

        return branch
