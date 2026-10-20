"""Student submission: implement Alpha-Beta, then improve evaluation and move ordering.

See connect4/search.py for the complete Minimax implementation.
Generate all successor states through ctx.child. Do not access the network or
external data, or use external engines or precomputed databases.
"""
from collections.abc import Sequence

from connect4.sdk import Context, State
from connect4.search import iterative_deepening


def choose_action(state: State, ctx: Context) -> int:
    """Optional: customize the move selected in the GUI and competition.

    Return one legal column index. The default uses Alpha-Beta with iterative
    deepening. If you replace it, use ctx.child for all successor generation
    and handle BudgetExceeded by returning your best legal action so far.
    Base grading tests alphabeta independently of this function.

    Args:
        state: Current nonterminal position, with at least one legal action.
        ctx: Shared successor budget and validated search operations for this move.

    Returns:
        A legal column index (0 through 6), not a value-action pair. The default
        returns the last completed depth's action, or the first legal action
        if the budget expires before any depth completes.
    """
    return iterative_deepening(state, ctx, alphabeta)["action"]


def evaluate(state: State, root_player: int) -> float:
    """Optional: improve this center-column heuristic.

    Args:
        state: Nonterminal position at the search cutoff.
        root_player: Player 1 or 2 whose perspective stays fixed during search.

    Returns:
        A finite score with absolute value below 100,000. Positive values favor
        root_player; negative values favor the opponent. Terminal scores come
        from state.terminal_score instead of this heuristic.
    """
    if state.kind != "board":
        return 0
    return 3 * sum(
        1 if state.at(row, 3) == root_player else -1 if state.at(row, 3) else 0
        for row in range(6)
    )


def order_actions(
    state: State, actions: Sequence[int], root_player: int
) -> list[int]:
    """Optional: reorder actions without removing or duplicating them.

    Use state.ctx.child to inspect successors; these calls consume the budget.

    Args:
        state: Position whose legal actions are being ordered.
        actions: Legal column indices provided by the search context.
        root_player: Fixed player perspective, independent of whose turn it is.

    Returns:
        A permutation of actions. Earlier actions are searched first, and the
        first searched action wins ties. The default preserves the given order.
    """
    return list(actions)


def alphabeta(
    state: State,
    depth: int,
    alpha: float,
    beta: float,
    root_player: int,
    ctx: Context,
) -> tuple[float, int | None]:
    """Required: return (value, best_action).

    Args:
        state: Position to search, possibly terminal.
        depth: Nonnegative number of remaining plies to search.
        alpha: Lower search bound in the fixed root_player perspective.
        beta: Upper search bound in the same perspective; may be infinite.
        root_player: Player 1 or 2; maximize on their turn and minimize otherwise.
        ctx: Shared context; all successor generation must use ctx.child.

    Returns:
        (value, best_action), keeping the first searched action on equal values.
        Check terminal states before the depth cutoff: wins and losses score
        +1,000,000 and -1,000,000 for root_player, and draws score zero.
        At a terminal state or depth zero, return (value, None). Otherwise,
        best_action is legal; a pruned search may return a bound on the value.

    Raises:
        BudgetExceeded: When successor generation exhausts the shared budget.
            Propagate this exception without returning an incomplete result.

    API: state.legal_actions(), state.to_move, state.terminal_score(root_player),
         ctx.child(state, action), ctx.evaluate(evaluate, state, root_player).
    Use ctx.ordered(order_actions, state, root_player) to validate move ordering.
    Let BudgetExceeded propagate to the provided iterative-deepening wrapper.
    """
    raise NotImplementedError("Implement Alpha-Beta; first read minimax in connect4/search.py")
