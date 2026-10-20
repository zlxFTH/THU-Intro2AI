"""Immutable game rules. Row zero is the TOP; player numbers are 1 and 2."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypedDict, cast


Coordinate = tuple[int, int]


class BoardSnapshot(TypedDict):
    kind: str
    cells: list[int]
    to_move: int
    actions: list[int]
    score1: int | None

ROWS, COLS, WIN = 6, 7, 1_000_000
WINDOWS = tuple(
    tuple((r + i * dr, c + i * dc) for i in range(4))
    for r in range(ROWS) for c in range(COLS)
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1))
    if 0 <= r + 3 * dr < ROWS and 0 <= c + 3 * dc < COLS
)


@dataclass(frozen=True)
class Board:
    cells: tuple[int, ...] = (0,) * 42
    to_move: int = 1

    def __post_init__(self) -> None:
        if (type(self.cells) is not tuple or len(self.cells) != 42
                or any(type(x) is not int or x not in (0, 1, 2) for x in self.cells)
                or type(self.to_move) is not int or self.to_move not in (1, 2)):
            raise ValueError("invalid board")

    def at(self, row: int, col: int) -> int:
        return self.cells[row * COLS + col]

    def winning_cells(self) -> tuple[Coordinate, ...]:
        for window in WINDOWS:
            values = [self.at(r, c) for r, c in window]
            if values[0] and values.count(values[0]) == 4:
                return window
        return ()

    def winner(self) -> int:
        line = self.winning_cells()
        return self.at(*line[0]) if line else 0

    def terminal_score(self, root_player: int) -> int | None:
        winner = self.winner()
        if winner:
            return WIN if winner == root_player else -WIN
        return 0 if all(self.cells) else None

    def legal_actions(self) -> tuple[int, ...]:
        if self.terminal_score(self.to_move) is not None:
            return ()
        return tuple(c for c in range(COLS) if not self.cells[c])

    def landing_row(self, col: int) -> int | None:
        if type(col) is not int or not 0 <= col < COLS:
            return None
        return next((r for r in range(ROWS - 1, -1, -1) if not self.at(r, col)), None)

    def play(self, col: int) -> Board:
        if type(col) is not int or col not in self.legal_actions():
            raise ValueError("illegal action")
        cells = list(self.cells)
        row = cast(int, self.landing_row(col))
        cells[row * COLS + col] = self.to_move
        return Board(tuple(cells), 3 - self.to_move)

    def snapshot(self) -> BoardSnapshot:
        return {"kind": "board", "cells": list(self.cells), "to_move": self.to_move,
                "actions": list(self.legal_actions()), "score1": self.terminal_score(1)}


def from_moves(moves: Iterable[int]) -> Board:
    board = Board()
    for move in moves:
        board = board.play(move)
    return board
