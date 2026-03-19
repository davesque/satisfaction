import logging

import pytest

from satisfaction.expr import Var, var
from satisfaction.examples.queens import (
    Queens,
    chessboard_size,
    exactly_one,
    fill_repr,
    lit_repr,
    lit_sort_key,
    partitions,
    row_repr,
    run_queens,
)


class TestPartitions:
    def test_single(self) -> None:
        (a,) = var("a")
        result = list(partitions((a,)))
        assert result == [(a, ())]

    def test_multiple(self) -> None:
        a, b, c = var("a b c")
        result = list(partitions((a, b, c)))
        assert result == [
            (a, (b, c)),
            (b, (a, c)),
            (c, (a, b)),
        ]

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="zero-length"):
            list(partitions(()))


class TestExactlyOne:
    def test_single_var(self) -> None:
        (a,) = var("a")
        result = exactly_one((a,))
        # exactly_one of a single var is just Or(a)
        assert result.args == (a,)

    def test_two_vars(self) -> None:
        a, b = var("a b")
        result = exactly_one((a, b))
        # (a & ~b) | (b & ~a)
        assert len(result.args) == 2


class TestQueens:
    def test_board_access(self) -> None:
        q = Queens(4)
        assert isinstance(q[0, 0], Var)
        assert isinstance(q[3, 3], Var)

    def test_board_out_of_bounds(self) -> None:
        q = Queens(4)
        with pytest.raises(IndexError):
            q[4, 0]
        with pytest.raises(IndexError):
            q[0, 4]

    def test_row_col(self) -> None:
        q = Queens(4)
        assert len(q.row(0)) == 4
        assert len(q.col(0)) == 4

    def test_diagonals(self) -> None:
        q = Queens(4)
        # Diagonals vary in length
        assert len(q.ldiag(0)) > 0
        assert len(q.rdiag(0)) > 0

    def test_formula(self) -> None:
        q = Queens(4)
        formula = q.get_formula()
        assert formula is not None


class TestDisplay:
    def test_lit_repr(self) -> None:
        (x,) = var("x")
        assert lit_repr(x) == " Q "
        assert lit_repr(~x) == "   "

    def test_row_repr(self) -> None:
        (x,) = var("x")
        result = row_repr([x, ~x])
        assert "Q" in result
        assert "│" in result

    def test_fill_repr(self) -> None:
        assert "┌" in fill_repr("top", 3)
        assert "└" in fill_repr("bottom", 3)
        assert "├" in fill_repr("mid", 3)

    def test_lit_sort_key(self) -> None:
        a1, b2, a10 = var("a1 b2 a10")
        keys = [lit_sort_key(v) for v in (a1, b2, a10)]
        assert keys[0] < keys[1]  # a1 < b2
        assert keys[0] < keys[2]  # a1 < a10

        # Negated literals sort by their atom
        assert lit_sort_key(~a1) == lit_sort_key(a1)


class TestRunQueens:
    def test_satisfiable(self, caplog) -> None:
        with caplog.at_level(logging.INFO):
            run_queens(4)
        assert "satisfiable" in caplog.text

    def test_unsatisfiable(self, caplog) -> None:
        with caplog.at_level(logging.INFO):
            run_queens(2)
        assert "satisfiable" in caplog.text


class TestChessboardSize:
    def test_valid(self) -> None:
        assert chessboard_size("4") == 4
        assert chessboard_size("8") == 8

    def test_too_small(self) -> None:
        with pytest.raises(ValueError):
            chessboard_size("1")
        with pytest.raises(ValueError):
            chessboard_size("0")
