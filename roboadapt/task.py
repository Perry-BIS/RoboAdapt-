"""Task sampling and success metrics."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class TaskSample:
    object_xy: np.ndarray
    displacement_xy: np.ndarray


def sample_task(seed: int, displacement_m: float = 0.0) -> TaskSample:
    rng = np.random.default_rng(seed)
    object_xy = np.array([rng.uniform(-0.14, 0.04), rng.uniform(-0.14, 0.04)])
    angle = rng.uniform(0.0, 2.0 * np.pi)
    displacement = displacement_m * np.array([np.cos(angle), np.sin(angle)])
    return TaskSample(object_xy, displacement)


def in_goal(object_xyz: np.ndarray, goal_xy: np.ndarray, radius_m: float = 0.05) -> bool:
    object_xyz = np.asarray(object_xyz, dtype=float)
    return bool(np.linalg.norm(object_xyz[:2] - goal_xy) <= radius_m and object_xyz[2] <= 0.055)


def is_lifted(object_z: float, threshold_m: float = 0.075) -> bool:
    return bool(object_z >= threshold_m)

