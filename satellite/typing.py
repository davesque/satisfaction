from typing import Callable

from satellite.expr import CNF, Lit

type ChooseLit = Callable[[CNF], Lit]
