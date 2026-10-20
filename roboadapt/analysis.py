"""Deterministic statistical analysis derived only from an episode CSV."""

from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .eval import wilson_interval


PAIR_KEYS = ["seed", "sigma_m", "displacement_m"]


def exact_mcnemar_two_sided(open_only: int, adaptive_only: int) -> float:
    n = open_only + adaptive_only
    if n == 0:
        return 1.0
    k = min(open_only, adaptive_only)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2**n))


def exact_seed_sign_flip(scores: np.ndarray) -> float:
    """Exact two-sided randomization p-value for integer per-seed score blocks."""
    scores = np.asarray(scores, dtype=int)
    distribution: dict[int, int] = {0: 1}
    for score in scores:
        updated: defaultdict[int, int] = defaultdict(int)
        for total, count in distribution.items():
            updated[total + int(score)] += count
            updated[total - int(score)] += count
        distribution = dict(updated)
    observed = abs(int(scores.sum()))
    extreme = sum(count for total, count in distribution.items() if abs(total) >= observed)
    return extreme / (2 ** len(scores))


def clustered_bootstrap_interval(
    seed_effects: np.ndarray,
    *,
    resamples: int = 200_000,
    rng_seed: int = 20_261_019,
) -> tuple[float, float]:
    """Percentile interval by resampling whole seed blocks with replacement."""
    effects = np.asarray(seed_effects, dtype=float)
    if len(effects) == 0 or resamples <= 0:
        raise ValueError("seed_effects and resamples must be non-empty/positive")
    rng = np.random.default_rng(rng_seed)
    indices = rng.integers(0, len(effects), size=(resamples, len(effects)))
    draws = effects[indices].mean(axis=1)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(lo), float(hi)


def analyze_episode_csv(
    path: str | Path,
    *,
    bootstrap_resamples: int = 200_000,
    bootstrap_seed: int = 20_261_019,
) -> dict[str, Any]:
    df = pd.read_csv(path)
    required = set(PAIR_KEYS + ["controller", "success_grasp", "success_place", "failure_reason", "wall_seconds"])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    duplicate_count = int(df.duplicated(PAIR_KEYS + ["controller"]).sum())
    if duplicate_count:
        raise ValueError(f"found {duplicate_count} duplicate episode keys")
    controllers = {"open_loop", "reobserve_replan"}
    if set(df.controller.unique()) != controllers:
        raise ValueError(f"expected exactly {sorted(controllers)}")

    paired = df.pivot(index=PAIR_KEYS, columns="controller", values="success_place")
    if paired.isna().any().any():
        raise ValueError("incomplete controller pairs")
    paired = paired.astype(bool)
    both_success = int((paired.open_loop & paired.reobserve_replan).sum())
    both_failure = int((~paired.open_loop & ~paired.reobserve_replan).sum())
    open_only = int((paired.open_loop & ~paired.reobserve_replan).sum())
    adaptive_only = int((~paired.open_loop & paired.reobserve_replan).sum())

    controllers_out: dict[str, Any] = {}
    for controller, group in df.groupby("controller"):
        successes = int(group.success_place.astype(bool).sum())
        total = int(len(group))
        lo, hi = wilson_interval(successes, total)
        controllers_out[controller] = {
            "successes": successes,
            "episodes": total,
            "success_rate": successes / total,
            "wilson_95": [lo, hi],
            "mean_wall_seconds": float(group.wall_seconds.mean()),
            "mean_steps": float(group.steps.mean()),
            "mean_sim_seconds": float(group.sim_seconds.mean()),
        }

    displacement: dict[str, Any] = {}
    for shift, group in df.groupby("displacement_m"):
        displacement[f"{float(shift):.2f}"] = {
            controller: {
                "successes": int(rows.success_place.astype(bool).sum()),
                "episodes": int(len(rows)),
                "success_rate": float(rows.success_place.astype(bool).mean()),
            }
            for controller, rows in group.groupby("controller")
        }

    delta = paired.reobserve_replan.astype(int) - paired.open_loop.astype(int)
    integer_seed_scores = delta.groupby(level="seed").sum().sort_index().to_numpy(dtype=int)
    conditions_per_seed = delta.groupby(level="seed").size().sort_index().to_numpy(dtype=int)
    if not np.all(conditions_per_seed == conditions_per_seed[0]):
        raise ValueError("unequal scenario counts across seeds")
    seed_effects = integer_seed_scores / conditions_per_seed
    boot_lo, boot_hi = clustered_bootstrap_interval(
        seed_effects, resamples=bootstrap_resamples, rng_seed=bootstrap_seed
    )

    grasp = df.success_grasp.astype(bool)
    place = df.success_place.astype(bool)
    failure_counts = {str(k): int(v) for k, v in df.failure_reason.value_counts().items()}
    return {
        "source_csv": str(path),
        "episodes": int(len(df)),
        "paired_scenarios": int(len(paired)),
        "duplicate_episode_keys": duplicate_count,
        "controllers": controllers_out,
        "aggregate_rate_difference": controllers_out["reobserve_replan"]["success_rate"]
        - controllers_out["open_loop"]["success_rate"],
        "paired_outcomes": {
            "both_success": both_success,
            "both_failure": both_failure,
            "adaptive_only": adaptive_only,
            "open_only": open_only,
        },
        "naive_posthoc_mcnemar_p": exact_mcnemar_two_sided(open_only, adaptive_only),
        "displacement_strata": displacement,
        "seed_cluster_exploratory": {
            "seed_count": int(len(seed_effects)),
            "conditions_per_seed": int(conditions_per_seed[0]),
            "bootstrap_resamples": int(bootstrap_resamples),
            "bootstrap_rng_seed": int(bootstrap_seed),
            "rate_difference_percentile_95": [boot_lo, boot_hi],
            "exact_sign_flip_p": exact_seed_sign_flip(integer_seed_scores),
            "integer_seed_scores": integer_seed_scores.tolist(),
        },
        "outcome_diagnostics": {
            "grasp_place_mismatch_count": int((grasp != place).sum()),
            "failure_reason_counts": failure_counts,
        },
        "interpretation_caveat": (
            "Seeds are reused across eight scenario conditions. The row-level McNemar calculation "
            "is post-hoc and treats scenario pairs as independent; seed-block analyses are exploratory."
        ),
    }
