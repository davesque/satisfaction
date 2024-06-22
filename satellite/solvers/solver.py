import abc

from satisfaction.expr import CNF


class Solver(abc.ABC):
    @abc.abstractmethod
    def __init__(self, cnf: CNF) -> None: ...

    @abc.abstractmethod
    def check(self) -> bool: ...
