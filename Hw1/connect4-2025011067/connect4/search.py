"""Teacher-provided minimax and anytime wrapper. No Alpha–Beta solution here."""
from collections.abc import Callable, Iterable, Sequence

from .sdk import BudgetExceeded, Context, SearchDiagnostics, State


EvaluateFn = Callable[[State, int], float]
OrderActionsFn = Callable[[State, Sequence[int], int], Iterable[int]]
SearchFn = Callable[
    [State, int, float, float, int, Context], tuple[float, int | None]
]
ChooseActionFn = Callable[[State, Context], int]


SearchResult = SearchDiagnostics


def minimax(
    state: State,
    depth: int,
    root_player: int,
    ctx: Context,
    evaluate: EvaluateFn,
    order_actions: OrderActionsFn,
) -> tuple[float, int | None]:
    terminal = state.terminal_score(root_player)
    if terminal is not None:
        return terminal, None
    if depth == 0:
        return ctx.evaluate(evaluate, state, root_player), None
    maximize = state.to_move == root_player
    best, best_action = (-float("inf") if maximize else float("inf")), None
    for action in ctx.ordered(order_actions, state, root_player):
        value, _ = minimax(ctx.child(state, action), depth - 1, root_player,
                           ctx, evaluate, order_actions)
        if best_action is None or (value > best if maximize else value < best):
            best, best_action = value, action
    return best, best_action


def iterative_deepening(
    state: State,
    ctx: Context,
    search: SearchFn,
    max_depth: int = 42,
) -> SearchResult:
    actions = state.legal_actions()
    if not actions:
        raise ValueError("cannot choose a move in a terminal state")
    result = {"action": actions[0], "depth": 0, "value": 0}
    for depth in range(1, max_depth + 1):
        try:
            value, action = search(state, depth, -float("inf"), float("inf"), state.to_move, ctx)
        except BudgetExceeded:
            break
        if type(action) is not int or action not in actions:
            raise ValueError("search returned an illegal action")
        result = {"action": action, "depth": depth, "value": value}
        if abs(value) >= 1_000_000:
            break
    ctx.last_search_result = dict(result)
    return result


def run_move(
    state: State, ctx: Context, choose_action: ChooseActionFn
) -> SearchResult:
    """Call the student move policy and retain optional, self-reported diagnostics."""
    ctx.last_search_result = None
    action = choose_action(state, ctx)
    if type(action) is not int or action not in state.legal_actions():
        raise ValueError("choose_action must return a legal column index")
    diagnostic = ctx.last_search_result
    if not isinstance(diagnostic, dict) or diagnostic.get("action") != action:
        diagnostic = {"depth": 0, "value": 0}
    return {"action": action, "depth": diagnostic["depth"], "value": diagnostic["value"]}
