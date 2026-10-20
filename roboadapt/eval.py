"""Benchmark orchestration and auditable episode records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import platform
import subprocess
import sys
from typing import Any

import mujoco
import numpy as np
import yaml

from .control import run_episode
from .env import RoboAdaptEnv
from .task import sample_task


SCHEMA = [
    "timestamp", "git_commit", "seed", "condition_id", "controller", "sigma_m",
    "displacement_m", "success_grasp", "success_place", "steps", "sim_seconds",
    "wall_seconds", "replan_count", "observation_count", "endpoint_error_m",
    "initial_observation_error_m", "final_observation_error_m", "failure_reason", "model_hash",
]


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    required = {"seeds", "controllers", "sigma_m", "displacement_m"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"missing config keys: {sorted(missing)}")
    return config


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted"


def run_benchmark(config: dict[str, Any], output_dir: str | Path) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "episodes.csv"
    env = RoboAdaptEnv()
    rows: list[dict[str, Any]] = []
    for sigma in config["sigma_m"]:
        for displacement in config["displacement_m"]:
            condition = f"sigma={float(sigma):.3f}_disp={float(displacement):.3f}"
            for seed in config["seeds"]:
                sample = sample_task(int(seed), float(displacement))
                for controller in config["controllers"]:
                    result = run_episode(
                        env, seed=int(seed), controller=controller, sigma_m=float(sigma),
                        object_xy=sample.object_xy, displacement_xy=sample.displacement_xy,
                        replan_threshold_m=float(config.get("replan_threshold_m", 0.008)),
                    )
                    row = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "git_commit": git_commit(), "seed": int(seed), "condition_id": condition,
                        "controller": controller, "sigma_m": float(sigma),
                        "displacement_m": float(displacement), "success_grasp": result.success_grasp,
                        "success_place": result.success_place, "steps": result.steps,
                        "sim_seconds": result.sim_seconds, "wall_seconds": result.wall_seconds,
                        "replan_count": result.replan_count, "observation_count": result.observation_count,
                        "endpoint_error_m": result.endpoint_error_m,
                        "initial_observation_error_m": result.initial_observation_error_m,
                        "final_observation_error_m": result.final_observation_error_m,
                        "failure_reason": result.failure_reason, "model_hash": env.model_hash,
                    }
                    rows.append(row)
                    print(f"{condition} seed={seed} {controller}: place={result.success_place} ({result.failure_reason})")
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "episodes": len(rows),
        "python": sys.version, "platform": platform.platform(), "mujoco": mujoco.__version__,
        "numpy": np.__version__, "model_hash": env.model_hash, "config": config,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return csv_path


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (float("nan"), float("nan"))
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    spread = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return float(center - spread), float(center + spread)

