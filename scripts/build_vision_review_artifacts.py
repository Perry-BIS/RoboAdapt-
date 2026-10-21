"""Build reviewer-facing pairing and stratified audit tables for v1.1.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from roboadapt.task import sample_task


PAIR_KEYS = ["seed", "vision_condition", "displacement_m"]
CONTROLLERS = ["oracle_state", "rgb_open_loop", "rgb_reobserve"]


def _finite_stats(values: pd.Series) -> tuple[float | None, float | None]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return None, None
    return float(clean.mean()), float(clean.median())


def build(csv_path: Path, output_dir: Path) -> None:
    df = pd.read_csv(csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    duplicates = int(df.duplicated(PAIR_KEYS + ["controller"]).sum())
    groups = df.groupby(PAIR_KEYS, sort=True)
    group_sizes = groups.size()
    controller_sets = groups.controller.agg(lambda values: sorted(set(values)))
    expected = sorted(CONTROLLERS)
    complete = int(sum(controllers == expected for controllers in controller_sets))

    rows: list[dict[str, object]] = []
    for key, group in groups:
        seed, vision, displacement = key
        task = sample_task(int(seed), float(displacement))
        row: dict[str, object] = {
            "seed": int(seed),
            "vision_condition": vision,
            "displacement_m": float(displacement),
            "object_x_m": float(task.object_xy[0]),
            "object_y_m": float(task.object_xy[1]),
            "displacement_x_m": float(task.displacement_xy[0]),
            "displacement_y_m": float(task.displacement_xy[1]),
            "final_object_x_m": float(task.object_xy[0] + task.displacement_xy[0]),
            "final_object_y_m": float(task.object_xy[1] + task.displacement_xy[1]),
        }
        first = group.iloc[0]
        row["image_noise_std"] = float(first.image_noise_std)
        row["occlusion_fraction"] = float(first.occlusion_fraction)
        for controller in CONTROLLERS:
            match = group[group.controller == controller]
            if len(match) != 1:
                continue
            item = match.iloc[0]
            prefix = controller + "__"
            for column in (
                "control_target_source",
                "success_grasp",
                "success_place",
                "initial_localization_error_m",
                "final_localization_error_m",
                "observation_count",
                "replan_count",
                "detection_failure_count",
                "steps",
                "failure_reason",
            ):
                row[prefix + column] = item[column]
        rows.append(row)
    pd.DataFrame(rows).to_csv(output_dir / "pairing_map.csv", index=False)

    strata: list[dict[str, object]] = []
    for key, group in df.groupby(
        ["controller", "vision_condition", "displacement_m"], sort=True
    ):
        controller, vision, displacement = key
        initial_mean, initial_median = _finite_stats(group.initial_localization_error_m)
        final_mean, final_median = _finite_stats(group.final_localization_error_m)
        strata.append(
            {
                "controller": controller,
                "vision_condition": vision,
                "displacement_m": float(displacement),
                "episodes": int(len(group)),
                "successes": int(group.success_place.astype(bool).sum()),
                "success_rate": float(group.success_place.astype(bool).mean()),
                "initial_localization_error_mean_m": initial_mean,
                "initial_localization_error_median_m": initial_median,
                "final_localization_error_mean_m": final_mean,
                "final_localization_error_median_m": final_median,
                "mean_observations": float(group.observation_count.mean()),
                "mean_replans": float(group.replan_count.mean()),
                "mean_steps": float(group.steps.mean()),
                "detection_failures": int(group.detection_failure_count.sum()),
            }
        )
    pd.DataFrame(strata).to_csv(output_dir / "stratified_metrics.csv", index=False)

    audit = {
        "source_csv": str(csv_path),
        "episodes": int(len(df)),
        "unique_scenarios": int(len(group_sizes)),
        "duplicate_controller_episode_keys": duplicates,
        "scenario_group_size_counts": {
            str(int(size)): int(count)
            for size, count in group_sizes.value_counts().sort_index().items()
        },
        "complete_three_controller_scenarios": complete,
        "expected_controllers": CONTROLLERS,
        "unique_seeds": sorted(int(value) for value in df.seed.unique()),
        "target_source_by_controller": {
            str(controller): sorted(str(value) for value in group.control_target_source.unique())
            for controller, group in df.groupby("controller", sort=True)
        },
        "results_source_commits": sorted(str(value) for value in df.git_commit.unique()),
        "pairing_definition": PAIR_KEYS,
        "task_sampling_note": (
            "sample_task(seed, displacement_m) is deterministic; the identical sampled "
            "object pose and displacement are reused for all three controllers in a scenario."
        ),
    }
    (output_dir / "pairing_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("results/vision_v1.1/episodes.csv"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build(args.csv, args.output_dir)


if __name__ == "__main__":
    main()
