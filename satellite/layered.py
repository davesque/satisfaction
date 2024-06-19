class LayeredSet[T]:
    __slots__ = ("els", "_removed", "depth")

    els: set[T]
    _removed: list[tuple[int, set[T]]] | None
    depth: int

    def __init__(self, els: set[T]) -> None:
        self.els = els
        self._removed = None
        self.depth = 0

    def push_layer(self) -> None:
        self.depth += 1

    def pop_layer(self) -> None:
        if self.depth == 0:
            raise IndexError("cannot pop base layer")

        if self._removed is not None:
            removed_depth, removed = self._removed[-1]
            if removed_depth == self.depth:
                self.els.update(removed)
                self._removed.pop()

            if len(self._removed) == 0:
                # invariant:
                # if self._removed is not None, then len(self._removed) > 0
                self._removed = None

        self.depth -= 1

    @property
    def _removed_in_layer(self) -> set[T]:
        if self._removed is None:
            # invariant:
            # if self._removed is not None, then len(self._removed) > 0
            removed = set()
            self._removed = [(self.depth, removed)]
            return removed

        removed_depth, removed = self._removed[-1]
        if removed_depth != self.depth:
            removed = set()
            self._removed.append((self.depth, removed))

        return removed

    def difference_update(self, to_remove: set[T]) -> None:
        to_remove = to_remove & self.els
        if len(to_remove) == 0:
            # invariant:
            # if a layer exists in self._removed, then it must not be empty
            return

        self._removed_in_layer.update(to_remove)
        self.els.difference_update(to_remove)
