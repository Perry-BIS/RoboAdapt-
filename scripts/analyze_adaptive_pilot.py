"""Validate and summarize the exploratory fixed-versus-adaptive RGB pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PAIR_KEYS = ["seed", "vision_condition", "displacement_m"]
CONTROLLERS = ["rgb_reobserve", "rgb_adaptive"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(path: Path) -> dict[str, object]:
    df = pd.read_csv(path)
    duplicates = int(df.duplicated(PAIR_KEYS + ["controller"]).sum())
    if duplicates:
        raise ValueError(f"found {duplicates} duplicate controller/scenario rows")
    paired = df.pivot(index=PAIR_KEYS, columns="controller")
    missing = sorted(set(CONTROLLERS) - set(df.controller.unique()))
    if missing:
        raise ValueError(f"missing controllers: {missing}")
    success = df.pivot(index=PAIR_KEYS, columns="controller", values="success_place")
    steps = df.pivot(index=PAIR_KEYS, columns="controller", values="steps")
    if success[CONTROLLERS].isna().any().any():
        raise ValueError("incomplete controller pairs")
    success = success[CONTROLLERS].astype(bool)
    both_success = success.all(axis=1)
    fixed_only = success.rgb_reobserve & ~success.rgb_adaptive
    adaptive_only = ~success.rgb_reobserve & success.rgb_adaptive
    both_failure = ~success.any(axis=1)

    controller_summary: dict[str, object] = {}
    for controller in CONTROLLERS:
        group = df[df.controller == controller]
        controller_summary[controller] = {
            "successes": int(group.success_place.astype(bool).sum()),
            "episodes": int(len(group)),
            "success_rate": float(group.success_place.astype(bool).mean()),
            "mean_steps": float(group.steps.mean()),
            "mean_observations": float(group.observation_count.mean()),
            "mean_replans": float(group.replan_count.mean()),
            "detection_failures": int(group.detection_failure_count.sum()),
        }

    both_success_delta = (
        steps.loc[both_success, "rgb_adaptive"]
        - steps.loc[both_success, "rgb_reobserve"]
    )
    return {
        "status": "exploratory pilot; not part of the 360-episode main benchmark",
        "source_csv": str(path).replace("\\", "/"),
        "source_csv_sha256": sha256(path),
        "episodes": int(len(df)),
        "paired_scenarios": int(len(success)),
        "duplicate_controller_episode_keys": duplicates,
        "controllers": controller_summary,
        "paired_outcomes": {
            "both_success": int(both_success.sum()),
            "fixed_only": int(fixed_only.sum()),
            "adaptive_only": int(adaptive_only.sum()),
            "both_failure": int(both_failure.sum()),
        },
        "both_success_step_delta_adaptive_minus_fixed": {
            "pairs": int(both_success.sum()),
            "mean": float(both_success_delta.mean()),
            "minimum": int(both_success_delta.min()),
            "maximum": int(both_success_delta.max()),
        },
        "recorded_git_commits": sorted(str(value) for value in df.git_commit.unique()),
        "model_hashes": sorted(str(value) for value in df.model_hash.unique()),
        "provenance_caveat": (
            "Rows record base commit 2cada2c because the vision implementation was in an "
            "uncommitted working tree when this pilot ran. The exact dirty source snapshot "
            "cannot be reconstructed from Git; retain these data only as exploratory evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
