"""Stage 2 (6 points): fixed-depth action quality measured by regret."""
import alpha_beta_agent as agent

from connect4.local_metrics import action_quality_report


def test_evaluation_heuristic_action_regret():
    report = action_quality_report(agent.evaluate)
    print("\n=== Stage 2: evaluation heuristic (6 points) ===")
    print("Fixed student depth: 2; deeper reference depth: 4")
    for index, row in enumerate(report["rows"], start=1):
        print(
            f"position_{index}: action={row['chosen_action']} "
            f"chosen_value={row['chosen_value']:.1f} "
            f"best_value={row['best_value']:.1f} regret={row['regret']:.1f}"
        )
    print(f"central_column_total_regret={report['baseline_regret']:.1f}")
    print(f"student_total_regret={report['student_regret']:.1f}")
    print(f"regret_reduction={report['improvement']:.1f}")
    print(f"suggested_score={report['points']:.2f}/6.00")
    assert report["baseline_regret"] > 0
    assert report["student_regret"] >= 0
    assert 0 <= report["points"] <= 6
