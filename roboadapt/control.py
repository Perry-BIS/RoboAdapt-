"""Open-loop and re-observe/re-plan manipulation controllers."""

from __future__ import annotations

from dataclasses import dataclass
import time
import numpy as np

from .env import RoboAdaptEnv
from .perception import noisy_pose_sensor, rgb_centroid_pose_sensor
from .task import is_lifted, in_goal


CONTROLLERS = ("open_loop", "reobserve_replan")
VISION_CONTROLLERS = ("oracle_state", "rgb_open_loop", "rgb_reobserve", "rgb_adaptive")


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


@dataclass
class VisionEpisodeResult:
    """Outcome and perception diagnostics for a vision benchmark episode."""

    success_grasp: bool
    success_place: bool
    failure_reason: str
    steps: int
    sim_seconds: float
    wall_seconds: float
    replan_count: int
    observation_count: int
    detection_failure_count: int
    endpoint_error_m: float
    initial_localization_error_m: float
    final_localization_error_m: float
    initial_confidence: float
    final_confidence: float
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


def run_vision_episode(
    env: RoboAdaptEnv,
    *,
    seed: int,
    controller: str,
    object_xy: np.ndarray,
    displacement_xy: np.ndarray,
    image_noise_std: float = 0.0,
    occlusion_fraction: float = 0.0,
    replan_threshold_m: float = 0.008,
    adaptive_confidence_min: float = 0.35,
    record: bool = False,
) -> VisionEpisodeResult:
    """Run an oracle or RGB-in-the-loop grasp-and-place episode.

    RGB controllers receive target coordinates only from rendered RGB images.
    Simulator pose is read after each image estimate solely to calculate logged
    localization error and final task metrics. ``oracle_state`` is the explicit
    upper-reference controller and is the only mode that uses cube truth as a
    control target.
    """
    if controller not in VISION_CONTROLLERS:
        raise ValueError(f"controller must be one of {VISION_CONTROLLERS}")
    if replan_threshold_m < 0:
        raise ValueError("replan_threshold_m must be non-negative")
    if not 0.0 <= adaptive_confidence_min <= 1.0:
        raise ValueError("adaptive_confidence_min must be in [0, 1]")

    start_wall = time.perf_counter()
    rng = np.random.default_rng(seed + 2_000_003)
    env.reset(object_xy)
    frames: list[np.ndarray] = []
    renderer = None
    if record:
        import mujoco

        renderer = mujoco.Renderer(env.model, height=480, width=640)
        renderer.update_scene(env.data, camera="overview")
        frames.append(renderer.render().copy())

    observation_count = 1
    detection_failure_count = 0
    replan_count = 0
    initial_confidence = 1.0
    final_confidence = 1.0

    truth_initial = env.cube_position[:2]
    if controller == "oracle_state":
        target = truth_initial.copy()
        initial_error = 0.0
    else:
        try:
            target, initial_confidence, _, _ = rgb_centroid_pose_sensor(
                env,
                rng=rng,
                image_noise_std=image_noise_std,
                occlusion_fraction=occlusion_fraction,
            )
        except RuntimeError:
            detection_failure_count = 1
            if renderer is not None:
                renderer.close()
            return VisionEpisodeResult(
                success_grasp=False,
                success_place=False,
                failure_reason="initial_vision_detection_failed",
                steps=env.steps,
                sim_seconds=env.steps * env.dt,
                wall_seconds=time.perf_counter() - start_wall,
                replan_count=0,
                observation_count=1,
                detection_failure_count=1,
                endpoint_error_m=float(np.linalg.norm(env.cube_position[:2] - env.goal_xy)),
                initial_localization_error_m=float("nan"),
                final_localization_error_m=float("nan"),
                initial_confidence=0.0,
                final_confidence=0.0,
                frames=frames,
            )
        initial_error = float(np.linalg.norm(target - truth_initial))

    final_error = initial_error
    final_confidence = initial_confidence
    if np.linalg.norm(displacement_xy) > 0:
        env.displace_cube(displacement_xy)

    # Re-observe after the scripted displacement while the gripper remains at its
    # camera-clear staging pose. Observing after moving directly above the stale
    # target would let the gripper occlude the cube in the top-down image.
    if controller == "oracle_state":
        observation_count += 1
        env.step_for(0.10, frames, renderer)
        second_target = env.cube_position[:2]
        final_error = 0.0
        if np.linalg.norm(second_target - target) > replan_threshold_m:
            target = second_target
            replan_count = 1
    elif controller in {"rgb_reobserve", "rgb_adaptive"}:
        observation_count += 1
        env.step_for(0.10, frames, renderer)
        try:
            second_target, second_confidence, _, _ = rgb_centroid_pose_sensor(
                env,
                rng=rng,
                image_noise_std=image_noise_std,
                occlusion_fraction=occlusion_fraction,
            )
            truth_for_metric = env.cube_position[:2]
            final_error = float(np.linalg.norm(second_target - truth_for_metric))
            final_confidence = second_confidence
            shift = float(np.linalg.norm(second_target - target))
            should_replan = controller == "rgb_reobserve" or (
                shift > replan_threshold_m and second_confidence >= adaptive_confidence_min
            )
            if should_replan:
                target = second_target
                replan_count = 1
        except RuntimeError:
            detection_failure_count += 1
            final_error = float("nan")
            final_confidence = 0.0

    # Execute the grasp from the final oracle or image-derived target.
    env.move_to(np.r_[target, 0.22], 0.55, frames=frames, renderer=renderer)

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
    return VisionEpisodeResult(
        success_grasp=grasp_success,
        success_place=place_success,
        failure_reason=reason,
        steps=env.steps,
        sim_seconds=env.steps * env.dt,
        wall_seconds=time.perf_counter() - start_wall,
        replan_count=replan_count,
        observation_count=observation_count,
        detection_failure_count=detection_failure_count,
        endpoint_error_m=endpoint_error,
        initial_localization_error_m=initial_error,
        final_localization_error_m=final_error,
        initial_confidence=float(initial_confidence),
        final_confidence=float(final_confidence),
        frames=frames,
    )

