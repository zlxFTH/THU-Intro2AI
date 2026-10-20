import pytest
from connect4.game import Board, from_moves, WINDOWS


def test_rules_and_immutability():
    board = Board()
    next_board = board.play(3)
    assert board.cells == (0,) * 42
    assert next_board.at(5, 3) == 1 and next_board.to_move == 2
    assert len(WINDOWS) == 69
    full_column = from_moves([0] * 6)
    assert 0 not in full_column.legal_actions()
    with pytest.raises(ValueError):
        full_column.play(0)
    for bad in (True, -1, 7, "3"):
        with pytest.raises(ValueError):
            board.play(bad)


@pytest.mark.parametrize("moves", [
    [0, 6, 1, 6, 2, 5, 3],
    [0, 1, 0, 1, 0, 2, 0],
    [0, 1, 1, 2, 4, 2, 2, 3, 4, 3, 5, 3, 3],
])
def test_wins(moves):
    board = from_moves(moves)
    assert board.winner() == 1
    assert board.terminal_score(1) == 1_000_000
    assert board.terminal_score(2) == -1_000_000
    assert not board.legal_actions()
    with pytest.raises(ValueError):
        board.play(6)


def test_draw_and_reverse_diagonal():
    cells = tuple([1, 1, 2, 2, 1, 1, 2] if r % 2 else [2, 2, 1, 1, 2, 2, 1] for r in range(6))
    board = Board(tuple(v for row in cells for v in row))
    assert board.winner() == 0 and board.terminal_score(1) == 0
    moves = [0, 1, 1, 2, 4, 2, 2, 3, 4, 3, 5, 3, 3]
    assert from_moves([6 - x for x in moves]).winner() == 1

