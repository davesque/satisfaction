import pytest

from satisfaction.layered import LayeredSet


@pytest.fixture
def ls() -> LayeredSet:
    return LayeredSet({1, 2, 3, 4})


class TestLayeredSet:
    def test_init(self, ls: LayeredSet) -> None:
        assert ls.els == {1, 2, 3, 4}
        assert ls._changed is None
        assert ls.depth == 0

    def test_push_pop_depth(self, ls: LayeredSet) -> None:
        assert ls.depth == 0
        ls.push_layer()
        assert ls.depth == 1
        ls.pop_layer()
        assert ls.depth == 0
        with pytest.raises(IndexError):
            ls.pop_layer()

    def test_changed_in_layer(self, ls: LayeredSet) -> None:
        # invariants across public API methods would normally prevent empty
        # layers from existing, but we're doing a bit of white box testing here

        first = ls._changed_in_layer
        assert ls._changed_in_layer is first
        assert ls._changed == [(0, set())]
        assert ls._changed == [(0, first)]

        ls.push_layer()
        second = ls._changed_in_layer
        assert ls._changed_in_layer is second
        assert ls._changed == [(0, set()), (1, set())]
        assert ls._changed == [(0, first), (1, second)]

    def test_api(self, ls: LayeredSet) -> None:
        ls.push_layer()
        assert ls.els == {1, 2, 3, 4}
        assert ls._changed is None
        assert ls.depth == 1

        ls.difference_update({2, 3, 5})
        assert ls.els == {1, 4}
        assert ls._changed == [(1, {2, 3})]

        ls.pop_layer()
        assert ls.els == {1, 2, 3, 4}
        assert ls._changed is None
        assert ls.depth == 0

        ls.difference_update(set())
        assert ls.els == {1, 2, 3, 4}
        assert ls._changed is None
        assert ls.depth == 0

        ls.difference_update({5, 6})
        assert ls.els == {1, 2, 3, 4}
        assert ls._changed is None
        assert ls.depth == 0

        ls.difference_update({1})
        assert ls.els == {2, 3, 4}
        assert ls._changed == [(0, {1})]
        assert ls.depth == 0

        ls.push_layer()
        ls.difference_update({2})
        assert ls.els == {3, 4}
        assert ls._changed == [(0, {1}), (1, {2})]
        assert ls.depth == 1

        ls.push_layer()
        ls.difference_update({3, 4})
        assert ls.els == set()
        assert ls._changed == [(0, {1}), (1, {2}), (2, {3, 4})]
        assert ls.depth == 2

        ls.pop_layer()
        assert ls.els == {3, 4}
        ls.pop_layer()
        assert ls.els == {2, 3, 4}
