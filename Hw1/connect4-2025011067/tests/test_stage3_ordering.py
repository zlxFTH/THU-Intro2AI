"""Stage 3 (6 points): pairwise action-ordering accuracy on three positions."""
import alpha_beta_agent as agent

from connect4.local_metrics import ORDERING_POSITIONS, ordering_report


def test_move_ordering_pairwise_accuracy():
    report = ordering_report(agent.order_actions)
    print("\n=== Stage 3: move-ordering heuristic (6 points) ===")
    print(f"nonterminal_positions={len(ORDERING_POSITIONS)}")
    print("Action labels come from a deeper depth-4 reference search")
    print(f"left_to_right_accuracy={report['baseline_accuracy']:.3%}")
    print(
        f"student_accuracy={report['student_accuracy']:.3%} "
        f"({report['correct_pairs']}/{report['compared_pairs']} pairs)"
    )
    print(f"accuracy_improvement={report['improvement']:+.3%}")
    print(f"suggested_score={report['points']:.2f}/6.00")
    assert report["compared_pairs"] > 0
    assert 0 <= report["student_accuracy"] <= 1
    assert 0 <= report["points"] <= 6
