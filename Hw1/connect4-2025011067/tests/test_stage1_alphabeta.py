"""Stage 1 (18 points): Alpha-Beta correctness and budget handling."""
import alpha_beta_agent as agent
import pytest

from connect4.baselines import evaluate, order_actions
from connect4.game import from_moves
from connect4.sdk import LocalContext
from connect4.search import iterative_deepening, minimax


@pytest.fixture(autouse=True)
def fixed_stage1_heuristics(monkeypatch):
    """Keep Stage 1 independent of the later heuristic experiments."""
    monkeypatch.setattr(agent, "evaluate", evaluate)
    monkeypatch.setattr(agent, "order_actions", order_actions)


def test_student_matches_minimax():
    board = from_moves([3, 2, 3, 4])
    expected_ctx, ctx = LocalContext(board), LocalContext(board)
    expected, _ = minimax(
        expected_ctx.root,
        3,
        1,
        expected_ctx,
        evaluate,
        order_actions,
    )
    value, action = agent.alphabeta(
        ctx.root, 3, -float("inf"), float("inf"), 1, ctx
    )
    assert value == expected
    assert action in board.legal_actions()
    assert ctx.used <= expected_ctx.used


def test_student_terminal_before_cutoff():
    ctx = LocalContext(from_moves([0, 6, 1, 6, 2, 5, 3]))
    assert agent.alphabeta(
        ctx.root, 0, -float("inf"), float("inf"), 1, ctx
    ) == (1_000_000, None)
    assert ctx.used == 0


def test_student_handles_budget_interrupt():
    ctx = LocalContext(from_moves([]), budget=8)
    result = iterative_deepening(ctx.root, ctx, agent.alphabeta)
    assert result["action"] in ctx.root.legal_actions()
    assert ctx.used <= 8
