import numpy as np
import pytest
from roboadapt.perception import noisy_pose_sensor


def test_zero_noise_exact():
    pose = np.array([0.1, -0.2])
    assert np.array_equal(noisy_pose_sensor(pose, 0, np.random.default_rng(1)), pose)


def test_negative_noise_rejected():
    with pytest.raises(ValueError):
        noisy_pose_sensor(np.zeros(2), -0.1, np.random.default_rng(1))


def test_seed_reproducible_noise():
    a = noisy_pose_sensor(np.zeros(2), 0.02, np.random.default_rng(42))
    b = noisy_pose_sensor(np.zeros(2), 0.02, np.random.default_rng(42))
    assert np.array_equal(a, b)

