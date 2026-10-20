"""Untrusted-side adapter. Never imported by the official referee."""
import importlib.util
import json
import random
import sys
from .game import Board
from .sdk import Context, State, BudgetExceeded, LocalContext
from .search import iterative_deepening, minimax, run_move

MAX_FRAME = 16_384


class RemoteContext(Context):
    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer

    def send(self, data):
        raw = json.dumps(data, allow_nan=False, separators=(",", ":"))
        if len(raw.encode()) > MAX_FRAME:
            raise ValueError("frame too large")
        self.writer.write(raw + "\n")
        self.writer.flush()

    def receive(self):
        line = self.reader.readline(MAX_FRAME + 2)
        if not line or len(line.encode()) > MAX_FRAME or not line.endswith("\n"):
            raise ValueError("invalid frame")
        return json.loads(line)

    def child(self, state, action):
        self.send({"op": "child", "state": state.id, "action": action})
        reply = self.receive()
        if reply.get("error") == "budget":
            raise BudgetExceeded()
        if "state" not in reply:
            raise ValueError("referee rejected request")
        return State.decode(reply["state"], self)


def main():
    # Protocol retains its own stdout handle; normal student print() goes to stderr.
    ctx = RemoteContext(sys.stdin, sys.stdout)
    sys.stdout = sys.stderr
    ctx.send({"op": "ready"})
    agent = None
    while True:
        initial = ctx.receive()
        random.seed(initial.get("seed", 0))
        decision = initial["state"]["id"]
        search_ctx = ctx
        if initial.get("anti_cheat") == "normal" and initial["state"]["kind"] == "board":
            board = Board(tuple(initial["state"]["cells"]), initial["state"]["to_move"])
            search_ctx = LocalContext(board, initial["budget"])
            state = search_ctx.root
        else:
            state = State.decode(initial["state"], ctx)
        if agent is None or initial.get("reload_agent"):
            path = sys.argv[1]
            spec = importlib.util.spec_from_file_location("student_agent", path)
            agent = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent)
        if initial["mode"] == "move":
            result = run_move(state, search_ctx, agent.choose_action)
        elif initial["mode"] == "alphabeta_move":
            result = iterative_deepening(state, search_ctx, agent.alphabeta,
                                         initial.get("max_depth", 42))
        elif initial["mode"] == "search":
            if initial.get("fixed_functions"):
                from .baselines import evaluate, order_actions
                agent.evaluate, agent.order_actions = evaluate, order_actions
            value, action = agent.alphabeta(state, initial["depth"], -float("inf"),
                                          float("inf"), initial["root_player"], search_ctx)
            result = {"value": value, "action": action, "depth": initial["depth"]}
        elif initial["mode"] == "evaluation_search":
            value, action = minimax(state, initial["depth"], initial["root_player"],
                                    search_ctx, agent.evaluate,
                                    lambda state, actions, root: list(actions))
            result = {"value": value, "action": action, "depth": initial["depth"]}
        elif initial["mode"] == "order_actions":
            result = {"actions": search_ctx.ordered(
                agent.order_actions, state, initial["root_player"])}
        else:
            raise ValueError("unsupported mode")
        if search_ctx is not ctx:
            result["successors"] = search_ctx.used
        ctx.send({"op": "result", "decision": decision, **result})


if __name__ == "__main__":
    main()
