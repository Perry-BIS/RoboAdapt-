import json
from pathlib import Path

import pandas as pd


def test_checked_in_vision_results_are_complete_and_source_labeled():
    csv_path = Path("results/vision_v1.1/episodes.csv")
    analysis_path = Path("results/vision_v1.1/analysis.json")
    df = pd.read_csv(csv_path)
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert len(df) == 360
    assert analysis["episodes"] == 360
    assert analysis["paired_rgb_scenarios"] == 120
    assert df.git_commit.nunique() == 1
    source_commit = str(df.git_commit.iloc[0])
    assert source_commit not in {"uncommitted", ""}
    assert not source_commit.endswith("-dirty")
    assert set(df[df.controller == "oracle_state"].control_target_source) == {
        "simulator_state"
    }
    assert set(df[df.controller.str.startswith("rgb_")].control_target_source) == {
        "rendered_rgb"
    }


def test_checked_in_vision_result_rates_match_analysis():
    analysis = json.loads(
        Path("results/vision_v1.1/analysis.json").read_text(encoding="utf-8")
    )
    assert analysis["controllers"]["oracle_state"]["successes"] == 120
    assert analysis["controllers"]["rgb_open_loop"]["successes"] == 67
    assert analysis["controllers"]["rgb_reobserve"]["successes"] == 118
    assert abs(analysis["rgb_reobserve_minus_open_loop"] - 0.425) < 1e-12
