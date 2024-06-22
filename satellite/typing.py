from typing import Callable

from satisfaction.expr import CNF, Lit

type ChooseLit = Callable[[CNF], Lit]
