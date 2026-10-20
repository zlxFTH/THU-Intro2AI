# Connect Four: Adversarial Search Under a Fixed Budget

Implement Alpha-Beta search to choose moves under a limited search budget.

## Play a Few Games First

Install Python 3.12, then run these commands from your assignment directory:

```text
python -m pip install -r requirements.txt
python -m connect4.gui
```

Connect Four uses a board with 6 rows and 7 columns. Red moves first. Click a column to drop a piece into its lowest empty cell. Connect four pieces horizontally, vertically, or diagonally to win. A full board without a winning line is a draw.


## Question 1 (18 pts): Alpha-Beta Search

For Questions 1–3, edit `alpha_beta_agent.py`; you may add helper functions there. A complete Minimax implementation is provided in `connect4/search.py`. You should not modify the game rules or budget management code.

Both `alpha_beta_agent.py` and `agent.py` are tracked by Git and may be modified. The three local grading stages and the GUI load `alpha_beta_agent.py`. Cloud grading and competition load only `agent.py`; the local file is not executed or made available in the cloud sandbox. The two files may contain different implementations. Do not import the local file from `agent.py`.

```python
def alphabeta(state, depth, alpha, beta, root_player, ctx):
    # Return (value, best_action).
    ...
```

All scores use the fixed perspective of `root_player`. Maximize when that player is to move; otherwise, minimize. Check for a terminal state before checking whether the remaining depth is zero.

| Interface | Purpose |
| --- | --- |
| `state.to_move` | The player whose turn it is: 1 or 2 |
| `state.legal_actions()` | Legal column indices, from 0 to 6 |
| `state.terminal_score(root_player)` | `None` for a nonterminal state; +1,000,000 / -1,000,000 / 0 for a win / loss / draw |
| `ctx.child(state, col)` | Consume one unit of budget and return the successor state |
| `ctx.evaluate(evaluate, state, root_player)` | Call and validate the heuristic |
| `ctx.ordered(order_actions, state, root_player)` | Call and validate the permutation of legal moves |
| `state.at(row, col)` | Read a cell; 0 means empty, and row 0 is the top row |
| `state.landing_row(col)` | Find where the next piece would land in that column |
| `state.windows()` | Get all horizontal, vertical, and diagonal windows of length four |

At a terminal state or depth zero, return `(value, None)`. At an internal node, return an optimal action. Keep the first action encountered when scores tie. Tests accept any optimal action; it need not match the reference implementation's choice of column.

Generate successors through `ctx.child`. Do not implement your own board transitions to bypass the budget. When the budget runs out, `BudgetExceeded` is raised. Let it propagate: the iterative-deepening wrapper will use the result from the last fully completed depth, or a deterministic legal fallback if no depth was completed.

Each move allows 2,000 successor generations, shared across all iterative-deepening iterations. Successors generated while ordering moves count too, and repeated generations are charged again.

After completing Alpha-Beta, run the Stage 1 test and attach a screenshot of
the passing output to your report:

```text
python -m pytest -q tests/test_stage1_alphabeta.py
```

Stage 1 tests correctness and budget handling only.

## Question 2 (6 pts): Improve Evaluation

`evaluate()` initially provides a simple center-column heuristic. Improve it using ideas such as open two-piece or three-piece patterns and opponent threats. The heuristic must return a finite number with absolute value less than 100,000. Handle terminal scores separately from the heuristic.

Remember gravity when evaluating a gap in a three-piece pattern: a gap above an empty cell may not be playable immediately. The difference in the players' piece counts usually provides little useful information.

The local Stage 2 benchmark holds search depth and move ordering fixed. For
five nonterminal positions, it compares the action selected at depth 2 with
values from a deterministic depth-4 reference search. Lower regret is better:

```text
regret = best reference action value - chosen action's reference value
```

Run the benchmark with output capture disabled, then attach a screenshot and
brief analysis to your report:

```text
python -m pytest -q -s tests/test_stage2_evaluation.py
```

Stage 2 earns full credit (6 points) when total regret is reduced by at least
40% relative to the central-column baseline. Partial credit is proportional:

```text
score = 6 * clamp((baseline_regret - student_regret) / (0.40 * baseline_regret), 0, 1)
```

These published positions and labels are a local practice set. The instructor
uses separate private positions with the same metric and scoring formula for
the official `Grade`; do not specialize an implementation to the visible cases.
All student search performed by the three grading stages uses the same
2,000-successor budget as a competition move. The deeper reference-label search
is an instructor-side oracle and does not grant additional budget to student code.

## Question 3 (6 pts): Improve Move Ordering

`order_actions()` initially sorts by column index. Try prioritizing central columns, winning moves, or defensive moves. Return every legal action exactly once. To inspect a successor, call `state.ctx.child(state, action)`; the call consumes the same search budget.

The Stage 3 benchmark uses three fixed nonterminal positions. It labels legal
actions with a deeper depth-4 search, then measures the fraction of non-tied
action pairs that `order_actions()` puts in better-first order. The score is
the improvement over the starter's left-to-right ordering, normalized so
pairwise accuracy of at least 70% earns 6 points. Partial credit is proportional
to improvement from the left-to-right baseline:

```text
score = 6 * clamp((student_accuracy - baseline_accuracy) / (0.70 - baseline_accuracy), 0, 1)
```

With the current 46 local-practice pairs, at least 33 correctly ordered pairs
earns full credit. The official grade uses separate private positions with the
same pairwise metric and scoring formula.

```text
python -m pytest -q -s tests/test_stage3_ordering.py
```

Attach a screenshot and discuss both pairwise accuracy and its expected effect
on pruning in your report. Compare successor counts only at the same
position, depth, and evaluation heuristic. Better move ordering does not
guarantee strictly fewer visits on every individual position.

## Optional (5 bonus pts): Competition and Leaderboards

**How to Participate:** Competition participation is optional. Your completed Alpha-Beta agent can enter using the provided `choose_action()` unchanged; customizing this function is not required to participate or receive bonus points.

Provide your GitHub username to the instructor and accept the invitation to your private assignment repository. Clone that repository. Keep your local homework implementation in `alpha_beta_agent.py` and your cloud submission in `agent.py`. To use the same implementation for both, copy the local file to `agent.py` before committing (this overwrites the cloud version):

```text
python -c "import shutil; shutil.copyfile('alpha_beta_agent.py', 'agent.py')"
```

Before the announced deadline, run the tests in [Test and Submit](#test-and-submit), commit your solution, check the committed submission, and push it to the repository's default branch:

```text
git add alpha_beta_agent.py agent.py
git commit -m "Submit Connect Four agent"
python -m connect4.submission
git push
```

The instructor collects the version pushed to the default branch. Local edits, unpushed commits, and changes on other branches are not submitted. Include the required screenshots and short analysis in your homework report; do not add report files to the competition repository. The instructor will announce the report submission channel and competition deadline.

**Leaderboard:** View the published results at [Connect Four Leaderboard](https://AI-40470243-THU.github.io/connect4-leaderboard/). The public navigation contains the Baseline Leaderboard and Daily Tournament. `Qualified` reports whether all private Alpha-Beta eligibility checks passed. `Grade` is the 30-point base grade described below: 18 points for Alpha-Beta, 6 for evaluation, and 6 for move ordering. On the baseline page, click a rate under Vs. Random, Vs. Tactical, or Vs. Depth-2 Minimax to inspect all eight final boards and any failure reason.

The baseline leaderboard updates hourly. Every agent and every baseline use the same four reviewed openings, with colors swapped for eight games per baseline. A seven-round Swiss preview tournament runs daily, followed by a ten-round final tournament after submissions are frozen; the final result is retained for grading and review but has no separate public navigation entry. Each tournament pairing uses two starting positions with the agents swapping colors, for four games in total. The four-game total determines a pairing win, draw, or loss, worth 1, 0.5, or 0 tournament points respectively.

Ties are first broken by the sum of opponents' tournament points (Buchholz), then by lower average nodes expanded per move across the tournament. Players still tied share a rank. With an odd number of players, a low-scoring player who has not yet received a bye is preferred for the bye. A bye counts as a pairing win and contributes zero to the opponent-strength tiebreak. Starting positions are not guaranteed to be theoretically balanced; swapping colors gives both agents the same conditions.

Only submissions that pass the competition's existing Alpha-Beta eligibility checks and comply with the rules are eligible for bonus points. The top 10%, next 10%, and next 10% of eligible submissions receive 5, 3, and 1 bonus points respectively. Group boundaries are rounded up, and submissions tied at a boundary receive the same award. Displayed bonus points are provisional until source review.

The public leaderboard uses participant IDs only. A rejected new submission does not overwrite the historical score of an older version, but the final tournament does not automatically fall back to an older submission. Your instructor will announce the deadline and freeze procedure. Check your submission before the deadline rather than waiting for scheduled collection.

### Optional Strategy Improvement: Customize Move Selection

The GUI calls `choose_action(state, ctx)` in `alpha_beta_agent.py`; cloud competition calls it in `agent.py`. It must return one legal column index, not a `(value, action)` pair. The default implementation runs your Alpha-Beta search with the provided iterative-deepening wrapper:

```python
def choose_action(state, ctx):
    return iterative_deepening(state, ctx, alphabeta)["action"]
```

You may modify the body of this function to customize your agent's move-selection strategy. Keep its name and parameters unchanged. All successor generation must still use `ctx.child`, and the same per-move budget, time limit, and memory limit apply. If you replace the default wrapper, handle `BudgetExceeded` in your move-selection function and return your best legal action so far, or a legal fallback if no result is available. Let the exception propagate from the required `alphabeta()` function as before.

Changing `choose_action()` does not replace any of the three required stages
and earns no base points. You can leave it unchanged and receive all 30 base
points. Custom move selection matters only through the leaderboard bonus and
must still return a legal action within the shared budget.

### Fair Play Principles

- Treat `State` and `Context` as the authoritative environment interface. Generate every successor exclusively through `ctx.child(state, action)`; do not recreate, predict, or replace the environment transition logic.

- Do not maintain a separate board to perform uncharged search. Helper data for evaluating the current state is allowed, but locally simulating successor states to bypass the generation budget is not.

- Implement a general strategy. Do not hard-code actions for known test cases or opponents.

- Do not inspect protected files, other submissions, environment variables, or evaluation environment implementation details.

- Do not use external engines, networks, processes, precomputed game databases, or persistent information carried between games.

- Respect all time, memory, and successor-generation limits. Attempts to hide resource usage or interfere with measurement are prohibited.

- Competition results are subject to automated checks and source review. A strong score does not override an academic-integrity violation; **suspected cases may be disqualified from bonus points**.

## Test and Submit

```text
python -m pytest -q tests/test_stage1_alphabeta.py
python -m pytest -q -s tests/test_stage2_evaluation.py
python -m pytest -q -s tests/test_stage3_ordering.py
python -m pytest -q tests/test_game.py tests/test_search.py
python -m connect4.submission
```

Once it is complete, select `My agent` in the GUI to see how your agent performs.

Changes to `alpha_beta_agent.py`, `agent.py`, and the supplied `reflection.md` are allowed. Both Python files must remain regular files of at most 128 KiB each. Local test results describe `alpha_beta_agent.py` only; they do not validate a different `agent.py` implementation. Adding, deleting, renaming, or changing permissions on other files will cause your submission to be rejected from the official competition. The submission checker examines **the committed contents of HEAD**, so commit before running it. Uncommitted changes do not enter the competition.

Do not commit caches or virtual environments. Do not include external engines, opening books, precomputed databases, or dependency installation scripts. Do not access the network or private competition data, and do not bypass the search budget. Submissions receiving bonus points will undergo source review.

## Grading

The base grade is 30 points, according to your implementation in the `alpha_beta_agent.py` and analysis in the report:

| Stage | Evidence | Points |
| --- | --- | ---: |
| Alpha-Beta implementation | Correctness and budget-handling tests | 18 |
| Evaluation heuristic | Fixed-depth action regret versus the central-column baseline | 6 |
| Move-ordering heuristic | Pairwise better-first accuracy versus left-to-right ordering | 6 |

Each stage's screenshot and short analysis must be included in your report.
Custom `choose_action()` strategies, match win rates, and leaderboard placement
do not contribute to these 30 base points.

## Competition Process Lifetime

Each player has a separate sandbox for one game. Each move receives a fresh 2,000-successor budget and a 5-second
wall-clock decision limit. Exceeding the 5-second limit will be regarded as fail. State handles expire after the decision: never pass a
previous turn's State to ctx.child. Memory is limited to 256 MiB per sandbox;
logs are limited to 64 KiB per player per game. Base grading uses fresh processes
for independent calls.
