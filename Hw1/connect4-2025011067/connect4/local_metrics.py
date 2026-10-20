"""Deterministic, student-visible metrics for heuristic experiments."""
from collections.abc import Callable, Iterable, Sequence
from typing import TypedDict

from .baselines import evaluate as central_column_evaluate
from .game import Board, from_moves
from .sdk import LocalContext, State
from .search import minimax


EvaluateFn = Callable[[State, int], float]
OrderActionsFn = Callable[[State, Sequence[int], int], Iterable[int]]

ACTION_QUALITY_POSITIONS = (
    (3, 3, 2, 4, 2, 4),
    (0, 1, 0, 1, 2, 3),
    (1, 2, 3, 2, 4, 3),
    (3, 2, 4, 3, 2, 4, 1, 5),
    (3, 2, 3, 4, 1, 5, 0, 6),
)

ORDERING_POSITIONS = (
    (3, 2, 4, 2, 5),
    (3, 2, 3, 2, 4, 1),
    (3, 1, 4, 2, 4, 2, 5, 3),
)


class RegretRow(TypedDict):
    moves: tuple[int, ...]
    chosen_action: int
    best_value: float
    chosen_value: float
    regret: float


class ActionQualityReport(TypedDict):
    baseline_regret: float
    student_regret: float
    improvement: float
    points: float
    rows: list[RegretRow]


class OrderingReport(TypedDict):
    baseline_accuracy: float
    student_accuracy: float
    improvement: float
    points: float
    correct_pairs: int
    compared_pairs: int


def left_to_right_order(
    state: State, actions: Sequence[int], root_player: int
) -> list[int]:
    """Uninformed ordering baseline used by the starter."""
    return list(actions)


_LOCAL_REFERENCE_VALUES = {
    (3, 3, 2, 4, 2, 4): (-27, -21, -96, -24, -122, -177, -177),
    (0, 1, 0, 1, 2, 3): (-14, -35, -34, -104, -142, -142, -142),
    (1, 2, 3, 2, 4, 3): (-1_000_000, -160, -233, -259, -177, -152, -152),
    (3, 2, 4, 3, 2, 4, 1, 5): (-279, -79, -153, -88, -235, -267, -280),
    (3, 2, 3, 4, 1, 5, 0, 6): (12, 24, 133, 35, 35, 12, 0),
    (3, 2, 4, 2, 5): (-1_000_000, -1_000_000, -1_000_000, -1_000_000,
                        -1_000_000, -1_000_000, -38),
    (3, 2, 3, 2, 4, 1): (-148, -146, 24, 151, -116, 9, 9),
    (3, 1, 4, 2, 4, 2, 5, 3): (-20, -6, 7, 137, 1_000_000, 3, 1_000_000),
}


def reference_action_values(board: Board, depth: int = 4) -> dict[int, float]:
    """Return published labels for the local practice positions only."""
    if depth != 4:
        raise ValueError("local labels are available only at depth 4")
    for moves, values in _LOCAL_REFERENCE_VALUES.items():
        if board == from_moves(moves):
            return {action: float(values[action]) for action in board.legal_actions()}
    raise ValueError("no public labels for this position")


def _shallow_action(board: Board, evaluate: EvaluateFn, depth: int = 2) -> int:
    ctx = LocalContext(board, budget=2_000)
    _, action = minimax(
        ctx.root, depth, board.to_move, ctx, evaluate, left_to_right_order
    )
    if action is None:
        raise ValueError("benchmark position must be nonterminal")
    return action


def _total_regret(evaluate: EvaluateFn) -> tuple[float, list[RegretRow]]:
    total = 0.0
    rows: list[RegretRow] = []
    for moves in ACTION_QUALITY_POSITIONS:
        board = from_moves(moves)
        values = reference_action_values(board)
        action = _shallow_action(board, evaluate)
        best = max(values.values())
        regret = best - values[action]
        total += regret
        rows.append({
            "moves": moves,
            "chosen_action": action,
            "best_value": best,
            "chosen_value": values[action],
            "regret": regret,
        })
    return total, rows


def action_quality_report(evaluate: EvaluateFn) -> ActionQualityReport:
    """Compare fixed-depth action regret with the central-column baseline."""
    baseline, _ = _total_regret(central_column_evaluate)
    student, rows = _total_regret(evaluate)
    improvement = baseline - student
    fraction = improvement / (0.4 * baseline) if baseline else 0.0
    return {
        "baseline_regret": baseline,
        "student_regret": student,
        "improvement": improvement,
        "points": 6.0 * min(1.0, max(0.0, fraction)),
        "rows": rows,
    }


def _ordering_accuracy(order_actions: OrderActionsFn) -> tuple[int, int]:
    correct = compared = 0
    for moves in ORDERING_POSITIONS:
        board = from_moves(moves)
        values = reference_action_values(board)
        ctx = LocalContext(board, budget=2_000)
        ordered = ctx.ordered(order_actions, ctx.root, board.to_move)
        for earlier_index, earlier in enumerate(ordered):
            for later in ordered[earlier_index + 1:]:
                if values[earlier] == values[later]:
                    continue
                compared += 1
                correct += values[earlier] > values[later]
    return correct, compared


def ordering_report(order_actions: OrderActionsFn) -> OrderingReport:
    """Measure pairwise agreement with deeper action values on three positions."""
    baseline_correct, baseline_pairs = _ordering_accuracy(left_to_right_order)
    student_correct, student_pairs = _ordering_accuracy(order_actions)
    baseline = baseline_correct / baseline_pairs
    student = student_correct / student_pairs
    improvement = student - baseline
    available = 0.70 - baseline
    fraction = improvement / available if available else 0.0
    points = 6.0 * min(1.0, max(0.0, fraction))
    return {
        "baseline_accuracy": baseline,
        "student_accuracy": student,
        "improvement": improvement,
        "points": points,
        "correct_pairs": student_correct,
        "compared_pairs": student_pairs,
    }
