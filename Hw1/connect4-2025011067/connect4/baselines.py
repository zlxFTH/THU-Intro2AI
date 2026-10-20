"""Public baselines, no hidden solution."""
import random
from collections.abc import Sequence
from typing import cast

from .game import Board
from .search import minimax
from .sdk import LocalContext, State

NAMES = ("Random", "Tactical", "Depth-2 Minimax", "My agent")


def evaluate(state: State, root_player: int) -> float:
    return 3 * sum(1 if state.at(r, 3) == root_player else -1 if state.at(r, 3) else 0
                   for r in range(6)) if state.kind == "board" else 0


def order_actions(
    state: State, actions: Sequence[int], root_player: int
) -> list[int]:
    return list(actions)


def choose(board: Board, name: str, seed: int = 0) -> int:
    actions = board.legal_actions()
    if not actions:
        raise ValueError("terminal board")
    if name == "Random":
        return random.Random(seed).choice(actions)
    if name == "Tactical":
        for a in actions:
            if board.play(a).winner() == board.to_move:
                return a
        # Same cells, opponent-to-move: a hypothetical threat probe for this public baseline.
        opponent = Board(board.cells, 3 - board.to_move)
        for a in actions:
            if opponent.play(a).winner() == opponent.to_move:
                return a
        return min(actions, key=lambda c: (abs(c - 3), c))
    if name != "Depth-2 Minimax":
        raise ValueError("unknown baseline")
    ctx = LocalContext(board)
    return cast(int, minimax(ctx.root, 2, board.to_move, ctx, evaluate, order_actions)[1])
