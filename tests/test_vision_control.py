from pathlib import Path

import numpy as np

from roboadapt.control import run_vision_episode
from roboadapt.env import RoboAdaptEnv
from roboadapt.eval import VISION_SCHEMA, load_vision_config
from roboadapt.perception import perturb_rgb_image
from roboadapt.task import sample_task


def test_rgb_image_perturbations_are_seed_reproducible_and_non_mutating():
    image = np.full((32, 32, 3), 128, dtype=np.uint8)
    original = image.copy()
    a = perturb_rgb_image(
        image, rng=np.random.default_rng(7), image_noise_std=12, occlusion_fraction=0.1
    )
    b = perturb_rgb_image(
        image, rng=np.random.default_rng(7), image_noise_std=12, occlusion_fraction=0.1
    )
    assert np.array_equal(a, b)
    assert np.array_equal(image, original)
    assert not np.array_equal(a, image)


def test_vision_benchmark_config_defines_360_paired_episodes():
    config = load_vision_config(Path("configs/vision_benchmark.yaml"))
    episodes = (
        len(config["seeds"])
        * len(config["controllers"])
        * len(config["displacement_m"])
        * len(config["vision_conditions"])
    )
    assert episodes == 360
    assert len(VISION_SCHEMA) == len(set(VISION_SCHEMA))


def test_rgb_reobserve_recovers_known_scripted_displacement():
    sample = sample_task(0, 0.04)
    result = run_vision_episode(
        RoboAdaptEnv(),
        seed=0,
        controller="rgb_reobserve",
        object_xy=sample.object_xy,
        displacement_xy=sample.displacement_xy,
    )
    assert result.success_place
    assert result.observation_count == 2
    assert result.replan_count == 1
    assert result.detection_failure_count == 0
    assert result.final_localization_error_m < 0.01


def test_rgb_open_loop_uses_one_image_and_misses_known_displacement():
    sample = sample_task(0, 0.04)
    result = run_vision_episode(
        RoboAdaptEnv(),
        seed=0,
        controller="rgb_open_loop",
        object_xy=sample.object_xy,
        displacement_xy=sample.displacement_xy,
    )
    assert not result.success_place
    assert result.observation_count == 1
    assert result.replan_count == 0
