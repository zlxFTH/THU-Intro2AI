"""State snapshots and budgeted search interface; not a Python security boundary."""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import TypedDict

from .game import Board, BoardSnapshot, WINDOWS


class BudgetExceeded(Exception):
    pass


class StateSnapshot(BoardSnapshot):
    id: str


class SearchDiagnostics(TypedDict):
    action: int
    depth: int
    value: float


@dataclass(frozen=True)
class State:
    id: str
    kind: str
    to_move: int
    actions: tuple[int, ...]
    score1: float | None
    cells: tuple[int, ...]
    ctx: Context = field(compare=False, repr=False)

    @classmethod
    def decode(cls, data: StateSnapshot, ctx: Context) -> State:
        return cls(data["id"], data["kind"], data["to_move"], tuple(data["actions"]),
                   data["score1"], tuple(data.get("cells", ())), ctx)

    def legal_actions(self) -> tuple[int, ...]:
        return self.actions

    def terminal_score(self, root_player: int) -> float | None:
        return self.score1 if root_player == 1 or self.score1 is None else -self.score1

    def at(self, row: int, col: int) -> int:
        return self.cells[row * 7 + col]

    def landing_row(self, col: int) -> int | None:
        return next((r for r in range(5, -1, -1) if not self.at(r, col)), None)

    def windows(self) -> tuple[tuple[int, ...], ...]:
        return tuple(tuple(self.at(r, c) for r, c in w) for w in WINDOWS)


class Context:
    last_search_result: SearchDiagnostics | None

    def child(self, state: State, action: int) -> State:
        """Generate a legal successor, charging the shared decision budget.

        Local and remote contexts implement this operation. Raise
        BudgetExceeded when no successor allowance remains; callers must not
        simulate transitions outside this interface.
        """
        raise NotImplementedError

    @staticmethod
    def evaluate(
        fn: Callable[[State, int], float], state: State, root: int
    ) -> float:
        value = fn(state, root)
        if type(value) not in (int, float) or abs(value) >= 100_000 or not math.isfinite(value):
            raise ValueError("heuristic must be finite and have magnitude < 100000")
        return value

    @staticmethod
    def ordered(
        fn: Callable[[State, Sequence[int], int], Iterable[int]],
        state: State,
        root: int,
    ) -> list[int]:
        actions = list(fn(state, state.legal_actions(), root))
        if (any(type(a) is not int for a in actions)
                or sorted(actions) != sorted(state.legal_actions())):
            raise ValueError("order_actions must return a permutation of legal actions")
        return actions


class LocalContext(Context):
    """Local learning only. Official accounting lives in the external referee."""
    def __init__(self, board: Board, budget: int = 2000) -> None:
        self.budget, self.used = budget, 0
        self.states: dict[str, Board] = {}
        self.root = self._add(board)
        self.last_search_result = None

    def _add(self, board: Board) -> State:
        key = str(len(self.states))
        self.states[key] = board
        snapshot = StateSnapshot(id=key, **board.snapshot())
        return State.decode(snapshot, self)

    def child(self, state: State, action: int) -> State:
        if self.used >= self.budget:
            raise BudgetExceeded()
        result = self.states[state.id].play(action)
        self.used += 1
        return self._add(result)
