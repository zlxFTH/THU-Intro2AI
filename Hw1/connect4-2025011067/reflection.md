# Experiment Report

All numbers below come from the commands named in each section, run in this
repository. The screenshots of the test output are included in the PDF report
(`report_2025011067.pdf`, section Q3); screenshots cannot be added to this
repository because the submission checker only allows the three files
`agent.py`, `alpha_beta_agent.py` and `reflection.md`.

## Stage 1: Alpha-Beta (18 points)

Command: `python -m pytest -q tests/test_stage1_alphabeta.py` — result: `3 passed`.

Implementation notes:

- Scores are always in the fixed `root_player` perspective, so the maximizing
  side is decided by `state.to_move == root_player`; ties keep the first searched
  action because the comparisons are strict (`>` / `<`).
- Terminal states are tested **before** the depth cutoff, so a win at the horizon
  scores `+1_000_000` instead of the heuristic value; a terminal node returns
  `(score, None)` and consumes no successor budget.
- Every successor goes through `ctx.child`, move ordering through `ctx.ordered`
  and leaf values through `ctx.evaluate`, so the shared budget and the validation
  of `evaluate` / `order_actions` are respected.
- `alpha` is raised on maximizing nodes and `beta` lowered on minimizing nodes;
  the child loop breaks as soon as `alpha >= beta`. `BudgetExceeded` is not
  caught, so the iterative-deepening wrapper can fall back to the last fully
  completed depth.

Correctness and effect of pruning (same position `[3,2,3,4]`, same depth,
reference `minimax` versus this implementation):

| depth | minimax successors | alpha-beta successors | value |
|---|---|---|---|
| 2 | 56 | 32 | 6 |
| 3 | 399 | 147 | 9 |
| 4 | budget exhausted (2000) | 523 | 6 |

Both return exactly the same value; the budget saved by pruning is what lets
depth 4 complete at all.

## Stage 2: Evaluation Heuristic (6 points)

Command: `python -m pytest -q -s tests/test_stage2_evaluation.py`

| quantity | value |
|---|---|
| central-column baseline regret | 307.0 |
| this heuristic | 165.0 |
| reduction | 142.0 (46.3 %) |
| suggested score | 6.00 / 6.00 |

The heuristic walks the 69 windows returned by `state.windows()` and scores only
"three of mine plus one empty" (`+100`) and "three of the opponent plus one
empty" (`-200`); a window containing both colours is dead and is skipped.

What helped:

- Replacing "number of pieces in the centre column" with a window count was the
  entire improvement: the centre-column count says almost nothing about who is
  close to connecting four.
- Weighting the opponent's open three twice as much as my own (`-200` vs `+100`)
  removed the baseline's largest single loss. In the second benchmark position
  the baseline attacks the centre and picks a column worth −104 in the depth-4
  reference, i.e. it gives up 90 points of value; the opponent-aware version
  plays a column worth −35 instead, keeping the regret of that position at 21.

What did not help / is still missing:

- Two-in-a-row windows are not scored, so a move that creates two threats at
  once is undervalued. The remaining regret is concentrated in the fifth
  benchmark position (121 of the 165): the reference prefers column 2 while this
  heuristic cannot distinguish it from column 0, because neither makes a three
  immediately.
- Gravity is not modelled: a window whose only empty cell is not yet playable
  still receives full value.

## Stage 3: Move-Ordering Heuristic (6 points)

Command: `python -m pytest -q -s tests/test_stage3_ordering.py`

| quantity | value |
|---|---|
| left-to-right baseline accuracy | 19.565 % (9/46 pairs) |
| this ordering | 73.913 % (34/46 pairs) |
| improvement | +54.348 % |
| suggested score | 6.00 / 6.00 |

`order_actions` ranks the legal columns in tiers, cheapest test first:

1. placing here connects four for the root player (immediate win),
2. placing here connects four for the opponent (mandatory block),
3. placing here makes an open three for the root player,
4. placing here makes an open three for the opponent,
5. placing here makes a two for the root player,
6. everything else — all equally last.

The line check is a pure read of `state.at` starting from
`state.landing_row(col)` along the four axes (horizontal, vertical, both
diagonals), summing both directions from the landing cell. It never calls
`ctx.child`, so ordering costs no successor budget.

Why ordering matters: alpha-beta can only prune after it has found a refutation,
and the first move actually searched is what produces one. Same position, same
depth, same `alphabeta`; only `order_actions` is swapped:

| position | depth | left-to-right | this ordering |
|---|---|---|---|
| (3, 2, 4, 2, 5) | 4 | budget exhausted | 131 successors |
| (3, 2, 4, 2, 5) | 5 | budget exhausted | 314 successors |
| (3, 2, 3, 2, 4, 1) | 4 | 732 | 190 |
| (3, 2, 3, 2, 4, 1) | 5 | budget exhausted | 564 |
| (3, 1, 4, 2, 4, 2, 5, 3) | 4 | 807 | 96 |
| (3, 1, 4, 2, 4, 2, 5, 3) | 5 | budget exhausted | 383 |

The returned values are identical in every row, but the successor count drops by
a factor of three to eight, and depths that exhaust the 2000-successor budget
under the left-to-right order become reachable. Pairwise accuracy alone
understates this: a better first move is what makes the cut-off possible, and the
cut-off is what buys depth.

## AI Assistance and Verification

An AI coding agent (DeepSeek Harness) was used as a tutor and reviewer rather
than as the author of the submitted search code. It explained the `State` /
`Context` API, reviewed the Alpha-Beta implementation (terminal-versus-depth
order, which bound each side updates, budget accounting), and produced the
diagnostic tables above (per-column reference values, successor counts with
`order_actions` swapped). The implementations of `alphabeta`, `evaluate` and
`order_actions` were written by me; every change was then checked with the tests
before it was kept.

How the results were verified, so that no suggestion was accepted on trust:

- Stage 1: the value returned by `alphabeta` was compared against the reference
  `minimax` at depths 2, 3 and 4, and the successor count was checked to be no
  larger than the reference implementation's (`ctx.used <= expected_ctx.used`,
  asserted by the test itself). A separate run confirmed the expected saving
  (56 → 32, 399 → 147) instead of an equal count, which rules out a version that
  looks right but never prunes.
- Stage 2: every weight change was measured with `action_quality_report`, and
  each benchmark position was inspected column by column against the published
  depth-4 labels; a change was kept only when the total regret actually fell.
- Stage 3: the produced order was compared with the ideal order of all three
  benchmark positions, and the pruning effect was measured by swapping only
  `order_actions` while keeping the search and the heuristic fixed.

No external engine, network access, precomputed game database or information
carried across games was used. All successor generation goes through
`ctx.child`, and `order_actions` only reads the position.
