import pytest

from satisfaction.layered import RemoveLayers


@pytest.fixture
def rl() -> RemoveLayers:
    return RemoveLayers({1, 2, 3, 4})


class TestRemoveLayers:
    def test_init(self, rl: RemoveLayers) -> None:
        assert rl.els == {1, 2, 3, 4}
        assert rl._changed is None
        assert rl.depth == 0

    def test_push_pop_depth(self, rl: RemoveLayers) -> None:
        assert rl.depth == 0
        rl.push_layer()
        assert rl.depth == 1
        rl.pop_layer()
        assert rl.depth == 0
        with pytest.raises(IndexError):
            rl.pop_layer()

    def test_changed_in_layer(self, rl: RemoveLayers) -> None:
        # invariants across public API methods would normally prevent empty
        # layers from existing, but we're doing a bit of white box testing here

        first = rl._changed_in_layer
        assert rl._changed_in_layer is first
        assert rl._changed == [(0, set())]
        assert rl._changed == [(0, first)]

        rl.push_layer()
        second = rl._changed_in_layer
        assert rl._changed_in_layer is second
        assert rl._changed == [(0, set()), (1, set())]
        assert rl._changed == [(0, first), (1, second)]

    def test_api(self, rl: RemoveLayers) -> None:
        rl.push_layer()
        assert rl.els == {1, 2, 3, 4}
        assert rl._changed is None
        assert rl.depth == 1

        rl.difference_update({2, 3, 5})
        assert rl.els == {1, 4}
        assert rl._changed == [(1, {2, 3})]

        rl.pop_layer()
        assert rl.els == {1, 2, 3, 4}
        assert rl._changed is None
        assert rl.depth == 0

        rl.difference_update(set())
        assert rl.els == {1, 2, 3, 4}
        assert rl._changed is None
        assert rl.depth == 0

        rl.difference_update({5, 6})
        assert rl.els == {1, 2, 3, 4}
        assert rl._changed is None
        assert rl.depth == 0

        rl.difference_update({1})
        assert rl.els == {2, 3, 4}
        assert rl._changed == [(0, {1})]
        assert rl.depth == 0

        rl.push_layer()
        rl.difference_update({2})
        assert rl.els == {3, 4}
        assert rl._changed == [(0, {1}), (1, {2})]
        assert rl.depth == 1

        rl.push_layer()
        rl.difference_update({3, 4})
        assert rl.els == set()
        assert rl._changed == [(0, {1}), (1, {2}), (2, {3, 4})]
        assert rl.depth == 2

        rl.pop_layer()
        assert rl.els == {3, 4}
        rl.pop_layer()
        assert rl.els == {2, 3, 4}
