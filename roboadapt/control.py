"""Open-loop and re-observe/re-plan manipulation controllers."""

from __future__ import annotations

from dataclasses import dataclass
import time
import numpy as np

from .env import RoboAdaptEnv
from .perception import noisy_pose_sensor
from .task import is_lifted, in_goal


CONTROLLERS = ("open_loop", "reobserve_replan")


@dataclass
class EpisodeResult:
    success_grasp: bool
    success_place: bool
    failure_reason: str
    steps: int
    sim_seconds: float
    wall_seconds: float
    replan_count: int
    observation_count: int
    endpoint_error_m: float
    initial_observation_error_m: float
    final_observation_error_m: float
    frames: list[np.ndarray]


def run_episode(
    env: RoboAdaptEnv,
    *,
    seed: int,
    controller: str,
    sigma_m: float,
    object_xy: np.ndarray,
    displacement_xy: np.ndarray,
    replan_threshold_m: float = 0.008,
    record: bool = False,
) -> EpisodeResult:
    if controller not in CONTROLLERS:
        raise ValueError(f"controller must be one of {CONTROLLERS}")
    start_wall = time.perf_counter()
    rng = np.random.default_rng(seed + 1_000_003)
    env.reset(object_xy)
    frames: list[np.ndarray] = []
    renderer = None
    if record:
        import mujoco
        renderer = mujoco.Renderer(env.model, height=480, width=640)
        renderer.update_scene(env.data, camera="overview")
        frames.append(renderer.render().copy())

    truth_initial = env.cube_position[:2]
    initial_obs = noisy_pose_sensor(truth_initial, sigma_m, rng)
    target = initial_obs.copy()
    observation_count = 1
    final_obs_error = float(np.linalg.norm(initial_obs - truth_initial))
    replan_count = 0

    if np.linalg.norm(displacement_xy) > 0:
        env.displace_cube(displacement_xy)

    # Move above the initially planned target. Re-observation occurs before descent.
    env.move_to(np.r_[target, 0.22], 0.55, frames=frames, renderer=renderer)
    if controller == "reobserve_replan":
        truth_now = env.cube_position[:2]
        second_obs = noisy_pose_sensor(truth_now, sigma_m, rng)
        observation_count += 1
        final_obs_error = float(np.linalg.norm(second_obs - truth_now))
        if np.linalg.norm(second_obs - target) > replan_threshold_m:
            target = second_obs
            replan_count = 1
            env.move_to(np.r_[target, 0.22], 0.35, frames=frames, renderer=renderer)

    env.move_to(np.r_[target, 0.112], 0.5, frames=frames, renderer=renderer)
    env.set_grip(True, 0.5, frames=frames, renderer=renderer)
    env.move_to(np.r_[target, 0.23], 0.65, frames=frames, renderer=renderer)
    grasp_success = is_lifted(float(env.cube_position[2]))

    if grasp_success:
        env.move_to(np.r_[env.goal_xy, 0.23], 0.75, frames=frames, renderer=renderer)
        env.move_to(np.r_[env.goal_xy, 0.12], 0.5, frames=frames, renderer=renderer)
        env.set_grip(False, 0.45, frames=frames, renderer=renderer)
        env.move_to(np.r_[env.goal_xy, 0.22], 0.35, frames=frames, renderer=renderer)
        env.step_for(0.45, frames, renderer)
    else:
        env.set_grip(False, 0.2, frames=frames, renderer=renderer)

    place_success = bool(grasp_success and in_goal(env.cube_position, env.goal_xy))
    endpoint_error = float(np.linalg.norm(env.cube_position[:2] - env.goal_xy))
    if place_success:
        reason = "success"
    elif not grasp_success:
        reason = "grasp_missed"
    else:
        reason = "place_outside_goal"
    if renderer is not None:
        renderer.close()
    return EpisodeResult(
        success_grasp=grasp_success,
        success_place=place_success,
        failure_reason=reason,
        steps=env.steps,
        sim_seconds=env.steps * env.dt,
        wall_seconds=time.perf_counter() - start_wall,
        replan_count=replan_count,
        observation_count=observation_count,
        endpoint_error_m=endpoint_error,
        initial_observation_error_m=float(np.linalg.norm(initial_obs - truth_initial)),
        final_observation_error_m=final_obs_error,
        frames=frames,
    )

