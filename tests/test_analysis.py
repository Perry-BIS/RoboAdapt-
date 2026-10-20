from pathlib import Path
import numpy as np

from roboadapt.analysis import analyze_episode_csv, exact_mcnemar_two_sided, exact_seed_sign_flip


FINAL_CSV = Path(__file__).parents[1] / "results" / "final" / "episodes.csv"


def test_exact_paired_statistics():
    assert np.isclose(exact_mcnemar_two_sided(14, 58), 1.6464300115968573e-7)
    assert exact_seed_sign_flip(np.array([1, 1, 1])) == 0.25


def test_checked_in_csv_analysis_is_recomputed_and_deterministic():
    a = analyze_episode_csv(FINAL_CSV, bootstrap_resamples=2_000, bootstrap_seed=123)
    b = analyze_episode_csv(FINAL_CSV, bootstrap_resamples=2_000, bootstrap_seed=123)
    assert a == b
    assert a["episodes"] == 320
    assert a["paired_scenarios"] == 160
    assert a["paired_outcomes"] == {
        "both_success": 69, "both_failure": 19, "adaptive_only": 58, "open_only": 14
    }
    assert np.isclose(a["aggregate_rate_difference"], 0.275)
    assert a["displacement_strata"]["0.00"]["open_loop"]["successes"] == 62
    assert a["displacement_strata"]["0.04"]["reobserve_replan"]["successes"] == 63
    assert a["outcome_diagnostics"]["grasp_place_mismatch_count"] == 0
    assert a["outcome_diagnostics"]["failure_reason_counts"] == {"success": 210, "grasp_missed": 110}
