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

from .control import VISION_CONTROLLERS, run_episode, run_vision_episode
from .env import RoboAdaptEnv
from .task import sample_task


SCHEMA = [
    "timestamp", "git_commit", "seed", "condition_id", "controller", "sigma_m",
    "displacement_m", "success_grasp", "success_place", "steps", "sim_seconds",
    "wall_seconds", "replan_count", "observation_count", "endpoint_error_m",
    "initial_observation_error_m", "final_observation_error_m", "failure_reason", "model_hash",
]

VISION_SCHEMA = [
    "timestamp", "git_commit", "seed", "condition_id", "controller", "control_target_source",
    "vision_condition", "image_noise_std", "occlusion_fraction", "displacement_m",
    "success_grasp", "success_place", "steps", "sim_seconds", "wall_seconds",
    "replan_count", "observation_count", "detection_failure_count", "endpoint_error_m",
    "initial_localization_error_m", "final_localization_error_m", "initial_confidence",
    "final_confidence", "failure_reason", "model_hash",
]


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    required = {"seeds", "controllers", "sigma_m", "displacement_m"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"missing config keys: {sorted(missing)}")
    return config


def load_vision_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a v1.1 vision benchmark configuration."""
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    required = {"seeds", "controllers", "displacement_m", "vision_conditions"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"missing config keys: {sorted(missing)}")
    unknown = set(config["controllers"]) - set(VISION_CONTROLLERS)
    if unknown:
        raise ValueError(f"unknown vision controllers: {sorted(unknown)}")
    if not config["vision_conditions"]:
        raise ValueError("vision_conditions must not be empty")
    ids: set[str] = set()
    for condition in config["vision_conditions"]:
        condition_id = str(condition["id"])
        if condition_id in ids:
            raise ValueError(f"duplicate vision condition id: {condition_id}")
        ids.add(condition_id)
        if float(condition.get("image_noise_std", 0.0)) < 0:
            raise ValueError("image_noise_std must be non-negative")
        occlusion = float(condition.get("occlusion_fraction", 0.0))
        if not 0.0 <= occlusion < 1.0:
            raise ValueError("occlusion_fraction must be in [0, 1)")
    return config


def git_commit() -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = subprocess.check_output(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=no",
                "--",
                ":(exclude)results/**",
                ":(exclude)media/**",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return f"{commit}-dirty" if dirty else commit
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


def run_vision_benchmark(config: dict[str, Any], output_dir: str | Path) -> Path:
    """Run paired oracle and RGB control episodes into an independent directory."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "episodes.csv"
    env = RoboAdaptEnv()
    rows: list[dict[str, Any]] = []
    for vision_condition in config["vision_conditions"]:
        vision_id = str(vision_condition["id"])
        image_noise_std = float(vision_condition.get("image_noise_std", 0.0))
        occlusion_fraction = float(vision_condition.get("occlusion_fraction", 0.0))
        for displacement in config["displacement_m"]:
            displacement = float(displacement)
            condition = f"vision={vision_id}_disp={displacement:.3f}"
            for seed in config["seeds"]:
                seed = int(seed)
                sample = sample_task(seed, displacement)
                for controller in config["controllers"]:
                    result = run_vision_episode(
                        env,
                        seed=seed,
                        controller=str(controller),
                        object_xy=sample.object_xy,
                        displacement_xy=sample.displacement_xy,
                        image_noise_std=image_noise_std,
                        occlusion_fraction=occlusion_fraction,
                        replan_threshold_m=float(config.get("replan_threshold_m", 0.008)),
                        adaptive_confidence_min=float(config.get("adaptive_confidence_min", 0.35)),
                    )
                    row = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "git_commit": git_commit(),
                        "seed": seed,
                        "condition_id": condition,
                        "controller": controller,
                        "control_target_source": (
                            "simulator_state" if controller == "oracle_state" else "rendered_rgb"
                        ),
                        "vision_condition": vision_id,
                        "image_noise_std": image_noise_std,
                        "occlusion_fraction": occlusion_fraction,
                        "displacement_m": displacement,
                        "success_grasp": result.success_grasp,
                        "success_place": result.success_place,
                        "steps": result.steps,
                        "sim_seconds": result.sim_seconds,
                        "wall_seconds": result.wall_seconds,
                        "replan_count": result.replan_count,
                        "observation_count": result.observation_count,
                        "detection_failure_count": result.detection_failure_count,
                        "endpoint_error_m": result.endpoint_error_m,
                        "initial_localization_error_m": result.initial_localization_error_m,
                        "final_localization_error_m": result.final_localization_error_m,
                        "initial_confidence": result.initial_confidence,
                        "final_confidence": result.final_confidence,
                        "failure_reason": result.failure_reason,
                        "model_hash": env.model_hash,
                    }
                    rows.append(row)
                    print(
                        f"{condition} seed={seed} {controller}: "
                        f"place={result.success_place} ({result.failure_reason})"
                    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISION_SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "episodes": len(rows),
        "git_commit": git_commit(),
        "python": sys.version,
        "platform": platform.platform(),
        "mujoco": mujoco.__version__,
        "numpy": np.__version__,
        "model_hash": env.model_hash,
        "control_input_policy": {
            "oracle_state": "simulator cube x/y; upper reference only",
            "rgb_controllers": "rendered RGB estimate only; truth used only for metrics",
        },
        "config": config,
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


def smoke_accepts(successes: int, *, total: int = 10, minimum: int = 10) -> bool:
    """Return whether a declared smoke run meets its explicit acceptance bar."""
    if not 0 <= minimum <= total:
        raise ValueError("minimum must be between zero and total")
    if not 0 <= successes <= total:
        raise ValueError("successes must be between zero and total")
    return successes >= minimum

