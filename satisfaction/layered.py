import abc


class SetLayers[T](abc.ABC):
    __slots__ = ("els", "_changed", "depth")

    els: set[T]
    _changed: list[tuple[int, set[T]]] | None
    depth: int

    def __init__(self, els: set[T]) -> None:
        self.els = els
        self._changed = None
        self.depth = 0

    def push_layer(self) -> None:
        self.depth += 1

    def pop_layer(self) -> None:
        if self.depth == 0:
            raise IndexError("cannot pop base layer")

        if self._changed is not None:
            changed_depth, changed = self._changed[-1]
            if changed_depth == self.depth:
                self._reset_els(changed)
                self._changed.pop()

            if len(self._changed) == 0:
                # invariant:
                # if self._changed is not None, then len(self._changed) > 0
                self._changed = None

        self.depth -= 1

    @property
    def _changed_in_layer(self) -> set[T]:
        if self._changed is None:
            # invariant:
            # if self._changed is not None, then len(self._changed) > 0
            changed = set()
            self._changed = [(self.depth, changed)]
            return changed

        changed_depth, changed = self._changed[-1]
        if changed_depth != self.depth:
            changed = set()
            self._changed.append((self.depth, changed))

        return changed

    def modify(self, changed: set[T]) -> None:
        changed = self._filter_changed(changed)
        if len(changed) == 0:
            # invariant:
            # if a layer exists in self._changed, then it must not be empty
            return

        self._changed_in_layer.update(changed)
        self._update_els(changed)

    @abc.abstractmethod
    def _reset_els(self, changed: set[T]) -> None: ...

    @abc.abstractmethod
    def _update_els(self, changed: set[T]) -> None: ...

    @abc.abstractmethod
    def _filter_changed(self, changed: set[T]) -> set[T]: ...


class RemoveLayers[T](SetLayers[T]):
    __slots__ = ()

    def _reset_els(self, changed: set[T]) -> None:
        self.els.update(changed)

    def _update_els(self, changed: set[T]) -> None:
        self.els.difference_update(changed)

    def _filter_changed(self, changed: set[T]) -> set[T]:
        return changed & self.els

    def difference_update(self, changed: set[T]) -> None:
        self.modify(changed)


class AddLayers[T](SetLayers[T]):
    __slots__ = ()

    def _reset_els(self, changed: set[T]) -> None:
        self.els.difference_update(changed)

    def _update_els(self, changed: set[T]) -> None:
        self.els.update(changed)

    def _filter_changed(self, changed: set[T]) -> set[T]:
        return changed - self.els

    def update(self, changed: set[T]) -> None:
        self.modify(changed)
