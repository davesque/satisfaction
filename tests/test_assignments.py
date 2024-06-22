import pytest

from satisfaction.assignments import Assignments
from satisfaction.exceptions import ConflictError
from satisfaction.expr import Lit, Not, var


@pytest.fixture
def assignments() -> Assignments:
    return Assignments()


x, y = var("x y")


class TestAssignments:
    def test_init(self, assignments: Assignments) -> None:
        assert assignments.branches == [{}]
        assert assignments.cache == {}

    def test_set_not_in_cache(self, assignments: Assignments) -> None:
        assignments.set(x, True)
        assert assignments.branches == [{x: True}]
        assert assignments.cache == {x: True}

    def test_set_present_in_cache(self, assignments: Assignments) -> None:
        # this is kinda cheating but hey
        assignments.cache[x] = True
        assignments.set(x, True)
        assert assignments.branches == [{}]
        assert assignments.cache == {x: True}

    def test_set_raises(self, assignments: Assignments) -> None:
        assignments.set(x, True)
        with pytest.raises(
            ConflictError, match="'False' conflicts with existing assignment for 'x'"
        ):
            assignments.set(x, False)

    @pytest.mark.parametrize(
        "lit,val",
        (
            (x, True),
            (x, False),
            (~x, True),
            (~x, False),
            (x | y, True),
        ),
    )
    def test_assign(self, assignments: Assignments, lit: Lit, val: bool) -> None:
        assignments.assign(lit, val)
        if isinstance(lit, Not):
            assert assignments.get(~lit) is not val
        else:
            assert assignments.get(lit) is val

    def test_push(self, assignments: Assignments) -> None:
        assert len(assignments.branches) == 1
        assignments.push()
        assert len(assignments.branches) == 2

    def test_pop(self, assignments: Assignments) -> None:
        assignments.assign(x, True)
        assignments.push()
        assignments.assign(y, True)

        assert assignments.branches == [{x: True}, {y: True}]
        assert assignments.cache == {x: True, y: True}

        assert assignments.get(x)
        assert assignments.get(y)

        assert assignments.pop() == {y: True}

        assert assignments.get(x)
        with pytest.raises(KeyError):
            assignments.get(y)

    def test_pop_raises(self, assignments: Assignments) -> None:
        with pytest.raises(IndexError):
            assignments.pop()
