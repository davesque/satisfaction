from __future__ import annotations
import logging
from collections import defaultdict

from satisfaction.expr import CNF, Lit, Not, Var
from satisfaction.layered import AddLayers

from .solver import Solver

logger = logging.getLogger(__name__)


class CDCL(Solver):
    __slots__ = (
        "variables",
        "clauses",
        "by_lit",
        "trail",
        "trail_lim",
        "assigns",
        "levels",
        "reasons",
        "prop_head",
        "level",
        "assignments",
    )

    variables: list[Var]
    clauses: list[tuple[Lit, ...]]
    by_lit: dict[Lit, list[int]]

    trail: list[Lit]
    trail_lim: list[int]
    assigns: dict[Var, bool]
    levels: dict[Var, int]
    reasons: dict[Var, int | None]
    prop_head: int
    level: int

    assignments: AddLayers[Lit]

    def __init__(self, cnf: CNF) -> None:
        self.variables = []
        self.clauses = []
        self.by_lit = defaultdict(list)

        seen: set[Var] = set()
        for clause_expr in cnf.args:
            lits = tuple(clause_expr.args)
            clause_idx = len(self.clauses)
            self.clauses.append(lits)
            for lit in lits:
                self.by_lit[lit].append(clause_idx)
                var = lit.atom()
                if var not in seen:
                    seen.add(var)
                    self.variables.append(var)

        self.trail = []
        self.trail_lim = []
        self.assigns = {}
        self.levels = {}
        self.reasons = {}
        self.prop_head = 0
        self.level = 0
        self.assignments = AddLayers(set())

    def check(self) -> bool:
        """
        Conflict-Driven Clause Learning (CDCL) SAT algorithm.
        """
        # Enqueue initial unit clauses at decision level 0
        for idx, clause in enumerate(self.clauses):
            if len(clause) == 1:
                lit = clause[0]
                if lit.atom() not in self.assigns:
                    self._enqueue(lit, idx)

        if self._propagate() is not None:
            return False

        while len(self.assigns) < len(self.variables):
            self._decide()

            while (conflict := self._propagate()) is not None:
                if self.level == 0:
                    return False
                learned, btlevel = self._analyze(conflict)
                clause_idx = self._add_clause(learned)
                self._backjump(btlevel)
                self._enqueue(learned[0], clause_idx)

        self.assignments = AddLayers(set(self.trail))
        return True

    def _value(self, lit: Lit) -> bool | None:
        match lit:
            case Var():
                return self.assigns.get(lit)
            case Not(Var() as var):
                val = self.assigns.get(var)
                return None if val is None else not val

    def _enqueue(self, lit: Lit, reason: int | None) -> None:
        var = lit.atom()
        match lit:
            case Var():
                self.assigns[var] = True
            case Not(Var()):
                self.assigns[var] = False
        self.levels[var] = self.level
        self.reasons[var] = reason
        self.trail.append(lit)

    def _decide(self) -> None:
        for var in self.variables:
            if var not in self.assigns:
                self.level += 1
                self.trail_lim.append(len(self.trail))
                logger.debug("decide: %s at level %d", var, self.level)
                self._enqueue(var, None)
                return

    def _propagate(self) -> int | None:
        while self.prop_head < len(self.trail):
            lit = self.trail[self.prop_head]
            self.prop_head += 1

            for clause_idx in self.by_lit.get(~lit, []):
                clause = self.clauses[clause_idx]
                first_unassigned = None
                satisfied = False
                num_unassigned = 0

                for c_lit in clause:
                    val = self._value(c_lit)
                    if val is True:
                        satisfied = True
                        break
                    if val is None:
                        num_unassigned += 1
                        if num_unassigned > 1:
                            break
                        first_unassigned = c_lit

                if satisfied or num_unassigned > 1:
                    continue

                if num_unassigned == 0 or first_unassigned is None:
                    return clause_idx

                logger.debug(
                    "propagate: %s from clause %d", first_unassigned, clause_idx
                )
                self._enqueue(first_unassigned, clause_idx)

        return None

    def _analyze(self, conflict_idx: int) -> tuple[list[Lit], int]:
        """
        Analyze a conflict using the 1-UIP scheme.

        Returns (learned_clause, backjump_level) where learned_clause[0]
        is the asserting literal.
        """
        seen: set[Var] = set()
        learned: list[Lit] = []
        counter = 0

        def process_clause(clause_idx: int, skip_var: Var | None = None) -> None:
            nonlocal counter
            for lit in self.clauses[clause_idx]:
                var = lit.atom()
                if var == skip_var or var in seen:
                    continue
                seen.add(var)
                if self.levels[var] == self.level:
                    counter += 1
                else:
                    learned.append(lit)

        process_clause(conflict_idx)

        # Walk trail backward, resolving until 1-UIP
        idx = len(self.trail) - 1
        while counter > 1:
            while self.trail[idx].atom() not in seen:
                idx -= 1
            p = self.trail[idx]
            idx -= 1
            counter -= 1

            reason = self.reasons[p.atom()]
            assert reason is not None
            process_clause(reason, skip_var=p.atom())

        # Find the UIP on the trail
        while self.trail[idx].atom() not in seen:
            idx -= 1
        uip_lit = ~self.trail[idx]

        # Put asserting literal first
        learned.insert(0, uip_lit)

        # Backjump level = highest level among non-asserting literals
        btlevel = 0
        for lit in learned[1:]:
            lvl = self.levels[lit.atom()]
            if lvl > btlevel:
                btlevel = lvl

        logger.debug("learned: %s, backjump to level %d", learned, btlevel)
        return learned, btlevel

    def _add_clause(self, lits: list[Lit]) -> int:
        clause = tuple(lits)
        clause_idx = len(self.clauses)
        self.clauses.append(clause)
        for lit in clause:
            self.by_lit[lit].append(clause_idx)
        return clause_idx

    def _backjump(self, btlevel: int) -> None:
        target = (
            self.trail_lim[btlevel]
            if btlevel < len(self.trail_lim)
            else len(self.trail)
        )
        while len(self.trail) > target:
            lit = self.trail.pop()
            var = lit.atom()
            del self.assigns[var]
            del self.levels[var]
            del self.reasons[var]
        del self.trail_lim[btlevel:]
        self.level = btlevel
        self.prop_head = len(self.trail)
