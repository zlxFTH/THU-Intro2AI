"""Run with python -m connect4.gui. Local practice is NOT a security sandbox."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from .game import Board, COLS, ROWS
from .baselines import NAMES, choose


def local_ai():
    """Fresh subprocess, JSON-only transport (no multiprocessing pickle)."""
    data = json.loads(sys.stdin.readline())
    board = Board(tuple(data["cells"]), data["to_move"])
    if data["name"] != "My agent":
        result = {"action": choose(board, data["name"], data["seed"])}
    else:
        import importlib.util
        from .sdk import LocalContext
        from .search import run_move
        protocol = sys.stdout
        sys.stdout = sys.stderr
        spec = importlib.util.spec_from_file_location("student", "alpha_beta_agent.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ctx = LocalContext(board)
        result = run_move(ctx.root, ctx, module.choose_action)
        result["nodes"] = ctx.used
        sys.stdout = protocol
    print(json.dumps(result, allow_nan=False))


class GameSession:
    def __init__(self):
        self.process = None
        self.output = None
        self.name = NAMES[2]
        self.human = 1
        self.generation = 0
        self.reset()

    def cancel(self):
        if self.process:
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait(timeout=3)
            self.process = None
        if self.output:
            self.output.close()
            self.output = None

    def reset(self):
        self.cancel()
        self.generation += 1
        self.board, self.last, self.info, self.failed = Board(), None, "", False

    def play(self, col):
        row = self.board.landing_row(col)
        self.board = self.board.play(col)
        self.last = (row, col)

    def start_ai(self):
        import tempfile
        self.output = tempfile.TemporaryFile()
        self.process = subprocess.Popen(
            [sys.executable, "-m", "connect4.gui", "--ai-worker"],
            stdin=subprocess.PIPE, stdout=self.output, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.process.stdin.write(json.dumps({"cells": self.board.cells,
            "to_move": self.board.to_move, "name": self.name,
            "seed": self.generation * 100 + sum(x != 0 for x in self.board.cells)}).encode())
        self.process.stdin.write(b"\n")
        self.process.stdin.close()
        self.started = time.monotonic()

    def tick(self):
        if self.process:
            if time.monotonic() - self.started > 5:
                self.cancel()
                self.info, self.failed = "AI timed out. Press R to restart.", True
            elif self.process.poll() is not None:
                try:
                    if self.process.returncode:
                        raise ValueError("AI failed")
                    self.output.seek(0)
                    result = json.loads(self.output.read(16_384))
                    self.play(result["action"])
                    self.info = f"Local: depth {result.get('depth', '-')} / successors {result.get('nodes', '-')}"
                except (ValueError, KeyError, TypeError):
                    self.info, self.failed = "AI error. Implement alphabeta or select a baseline.", True
                finally:
                    self.cancel()
        elif (not self.failed and self.board.to_move != self.human
              and self.board.terminal_score(1) is None):
            self.start_ai()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ai-worker", action="store_true")
    parser.add_argument("--smoke-frames", type=int, default=0)
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    if args.ai_worker:
        local_ai()
        return
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((1000, 720))
    pygame.display.set_caption("Connect Four | Adversarial Search Lab")
    # Pygame's bundled font avoids dependence on fonts installed on a student's OS.
    font = pygame.font.Font(None, 26)
    title_font = pygame.font.Font(None, 42)
    small = pygame.font.Font(None, 23)
    clock = pygame.time.Clock()
    session = GameSession()
    left, top, cell = 35, 145, 82
    buttons = [(pygame.Rect(650, 175 + i * 48, 310, 38), n) for i, n in enumerate(NAMES)]
    switch = pygame.Rect(650, 395, 310, 42)
    restart = pygame.Rect(650, 450, 310, 42)

    def text(value, position, color=(225, 232, 243), face=font):
        screen.blit(face.render(value, True, color), position)

    running, frames = True, 0
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        session.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    x, y = event.pos
                    for rect, name in buttons:
                        if rect.collidepoint(x, y):
                            session.name = name
                            session.reset()
                    if switch.collidepoint(x, y):
                        session.human = 3 - session.human
                        session.reset()
                    elif restart.collidepoint(x, y):
                        session.reset()
                    elif (left <= x < left + COLS * cell and top <= y < top + ROWS * cell
                          and session.board.to_move == session.human and not session.failed
                          and not session.process):
                        col = (x - left) // cell
                        if col in session.board.legal_actions():
                            session.play(col)
            session.tick()
            screen.fill((15, 23, 42))
            text("CONNECT FOUR", (35, 28), face=title_font)
            text("Drop a piece. Connect four. Think ahead.", (35, 77), face=small)
            pygame.draw.rect(screen, (35, 65, 126), (left, top, COLS * cell, ROWS * cell), border_radius=15)
            colors = ((15, 23, 42), (250, 107, 107), (251, 199, 79))
            for r in range(ROWS):
                for c in range(COLS):
                    pos = (left + c * cell + cell // 2, top + r * cell + cell // 2)
                    pygame.draw.circle(screen, colors[session.board.at(r, c)], pos, 31)
                    if session.last == (r, c):
                        pygame.draw.circle(screen, (245, 247, 250), pos, 33, 2)
            mx, my = pygame.mouse.get_pos()
            col = (mx - left) // cell
            if (session.board.to_move == session.human and not session.failed and
                    left <= mx < left + COLS * cell and top <= my < top + ROWS * cell
                    and col in session.board.legal_actions()):
                row = session.board.landing_row(col)
                pygame.draw.circle(screen, colors[session.human],
                    (left + col * cell + cell // 2, top + row * cell + cell // 2), 27, 3)
            for r, c in session.board.winning_cells():
                pygame.draw.circle(screen, (120, 255, 180),
                    (left + c * cell + cell // 2, top + r * cell + cell // 2), 35, 4)
            winner = session.board.winner()
            status = ("You win!" if winner == session.human else "AI wins!") if winner else (
                "Draw!" if session.board.terminal_score(1) is not None else
                "AI thinking..." if session.board.to_move != session.human else "Your turn: click a column")
            text(status, (35, 655))
            text("PRACTICE OPPONENT", (650, 140))
            for rect, name in buttons:
                pygame.draw.rect(screen, (46, 110, 126) if name == session.name else (35, 47, 67), rect, border_radius=7)
                text(name, (rect.x + 12, rect.y + 8))
            for rect, label in ((switch, "You play " + ("FIRST" if session.human == 1 else "SECOND") + "  [switch]"),
                                (restart, "New game  [R]")):
                pygame.draw.rect(screen, (35, 47, 67), rect, border_radius=7)
                text(label, (rect.x + 12, rect.y + 11))
            for i, line in enumerate(("RULES", "Click a column to drop a piece.", "Pieces fall to the lowest empty cell.",
                                     "Four in any direction wins.", "A full board without four is a draw.", "Red plays first. ESC exits.")):
                text(line, (650, 520 + i * 26), face=small)
            text(session.info, (35, 692), face=small)
            pygame.display.flip()
            frames += 1
            if args.smoke_frames and frames >= args.smoke_frames:
                if args.screenshot:
                    pygame.image.save(screen, args.screenshot)
                running = False
            clock.tick(60)
    finally:
        session.cancel()
        pygame.quit()


if __name__ == "__main__":
    main()
