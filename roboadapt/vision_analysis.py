"""Statistical summaries for the independent RGB-in-the-loop benchmark."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .analysis import (
    clustered_bootstrap_interval,
    exact_mcnemar_two_sided,
    exact_seed_sign_flip,
)
from .eval import wilson_interval


PAIR_KEYS = ["seed", "vision_condition", "displacement_m"]


def analyze_vision_csv(
    path: str | Path,
    *,
    bootstrap_resamples: int = 200_000,
    bootstrap_seed: int = 20_261_020,
) -> dict[str, Any]:
    df = pd.read_csv(path)
    required = set(
        PAIR_KEYS
        + [
            "controller",
            "success_place",
            "steps",
            "wall_seconds",
            "observation_count",
            "initial_localization_error_m",
            "final_localization_error_m",
            "detection_failure_count",
            "failure_reason",
        ]
    )
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    duplicates = int(df.duplicated(PAIR_KEYS + ["controller"]).sum())
    if duplicates:
        raise ValueError(f"found {duplicates} duplicate episode keys")
    needed = {"rgb_open_loop", "rgb_reobserve"}
    if not needed.issubset(set(df.controller.unique())):
        raise ValueError(f"expected at least {sorted(needed)}")

    paired = df[df.controller.isin(needed)].pivot(
        index=PAIR_KEYS, columns="controller", values="success_place"
    )
    if paired.isna().any().any():
        raise ValueError("incomplete RGB controller pairs")
    paired = paired.astype(bool)
    both_success = int((paired.rgb_open_loop & paired.rgb_reobserve).sum())
    both_failure = int((~paired.rgb_open_loop & ~paired.rgb_reobserve).sum())
    open_only = int((paired.rgb_open_loop & ~paired.rgb_reobserve).sum())
    reobserve_only = int((~paired.rgb_open_loop & paired.rgb_reobserve).sum())

    controllers: dict[str, Any] = {}
    for controller, group in df.groupby("controller", sort=True):
        successes = int(group.success_place.astype(bool).sum())
        total = int(len(group))
        lo, hi = wilson_interval(successes, total)
        controllers[str(controller)] = {
            "successes": successes,
            "episodes": total,
            "success_rate": successes / total,
            "wilson_95": [lo, hi],
            "mean_steps": float(group.steps.mean()),
            "mean_wall_seconds": float(group.wall_seconds.mean()),
            "mean_observations": float(group.observation_count.mean()),
            "detection_failures": int(group.detection_failure_count.sum()),
        }

    strata: dict[str, Any] = {}
    for keys, group in df.groupby(["vision_condition", "displacement_m"], sort=True):
        vision, displacement = keys
        name = f"vision={vision}_disp={float(displacement):.3f}"
        strata[name] = {
            str(controller): {
                "successes": int(rows.success_place.astype(bool).sum()),
                "episodes": int(len(rows)),
                "success_rate": float(rows.success_place.astype(bool).mean()),
                "mean_final_localization_error_m": (
                    None
                    if rows.final_localization_error_m.dropna().empty
                    else float(rows.final_localization_error_m.mean())
                ),
            }
            for controller, rows in group.groupby("controller", sort=True)
        }

    delta = paired.rgb_reobserve.astype(int) - paired.rgb_open_loop.astype(int)
    seed_scores = delta.groupby(level="seed").sum().sort_index().to_numpy(dtype=int)
    conditions_per_seed = delta.groupby(level="seed").size().sort_index().to_numpy(dtype=int)
    if not np.all(conditions_per_seed == conditions_per_seed[0]):
        raise ValueError("unequal scenario counts across seeds")
    seed_effects = seed_scores / conditions_per_seed
    boot_lo, boot_hi = clustered_bootstrap_interval(
        seed_effects, resamples=bootstrap_resamples, rng_seed=bootstrap_seed
    )

    rgb = df[df.controller.str.startswith("rgb_")]
    localization = {
        "initial_mean_m": float(rgb.initial_localization_error_m.mean()),
        "initial_median_m": float(rgb.initial_localization_error_m.median()),
        "final_mean_m": float(rgb.final_localization_error_m.mean()),
        "final_median_m": float(rgb.final_localization_error_m.median()),
    }
    open_steps = controllers["rgb_open_loop"]["mean_steps"]
    reobserve_steps = controllers["rgb_reobserve"]["mean_steps"]
    return {
        "source_csv": str(path),
        "episodes": int(len(df)),
        "paired_rgb_scenarios": int(len(paired)),
        "duplicate_episode_keys": duplicates,
        "controllers": controllers,
        "rgb_reobserve_minus_open_loop": (
            controllers["rgb_reobserve"]["success_rate"]
            - controllers["rgb_open_loop"]["success_rate"]
        ),
        "paired_outcomes": {
            "both_success": both_success,
            "both_failure": both_failure,
            "reobserve_only": reobserve_only,
            "open_loop_only": open_only,
        },
        "posthoc_exact_mcnemar_p": exact_mcnemar_two_sided(open_only, reobserve_only),
        "seed_cluster_exploratory": {
            "seed_count": int(len(seed_effects)),
            "conditions_per_seed": int(conditions_per_seed[0]),
            "bootstrap_resamples": int(bootstrap_resamples),
            "bootstrap_rng_seed": int(bootstrap_seed),
            "rate_difference_percentile_95": [boot_lo, boot_hi],
            "exact_sign_flip_p": exact_seed_sign_flip(seed_scores),
            "integer_seed_scores": seed_scores.tolist(),
        },
        "strata": strata,
        "localization": localization,
        "rgb_reobserve_step_overhead_fraction": (
            (reobserve_steps - open_steps) / open_steps if open_steps else None
        ),
        "failure_reason_counts": {
            str(key): int(value) for key, value in df.failure_reason.value_counts().items()
        },
        "interpretation_caveat": (
            "All comparisons are simulation-only and paired by seed, image condition, and "
            "scripted displacement. Bootstrap and sign-flip analyses are exploratory."
        ),
    }
