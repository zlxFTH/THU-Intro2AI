import pytest
from connect4.game import Board, from_moves
from connect4.sdk import BudgetExceeded, LocalContext
from connect4.search import minimax, iterative_deepening
from connect4.baselines import evaluate, order_actions, choose


def test_minimax_finds_win():
    board = from_moves([0, 6, 1, 6, 2, 5])
    ctx = LocalContext(board)
    assert minimax(ctx.root, 1, 1, ctx, evaluate, order_actions) == (1_000_000, 3)
    assert choose(board, "Tactical") == 3


def test_budget_shared_and_fallback():
    ctx = LocalContext(Board(), budget=10)
    def search(state, depth, alpha, beta, root, ctx):
        return minimax(state, depth, root, ctx, evaluate, order_actions)
    result = iterative_deepening(ctx.root, ctx, search)
    assert result["depth"] == 1 and ctx.used == 10
    ctx = LocalContext(Board(), budget=0)
    assert iterative_deepening(ctx.root, ctx, search)["action"] == 0
    with pytest.raises(BudgetExceeded):
        ctx.child(ctx.root, 3)


def test_helper_contracts():
    ctx = LocalContext(Board())
    with pytest.raises(ValueError):
        ctx.evaluate(lambda s, r: float("nan"), ctx.root, 1)
    with pytest.raises(ValueError):
        ctx.ordered(lambda s, a, r: [0, 0], ctx.root, 1)
    with pytest.raises(ValueError):
        ctx.evaluate(lambda s, r: 100_000, ctx.root, 1)

