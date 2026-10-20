import numpy as np
from roboadapt.env import RoboAdaptEnv
from roboadapt.perception import rgb_centroid_pose_sensor


def test_rgb_centroid_backprojection_is_near_cube_truth():
    env = RoboAdaptEnv(); env.reset(np.array([-0.08, -0.04]))
    estimate, confidence, centroid, image = rgb_centroid_pose_sensor(env)
    assert image.shape == (320, 320, 3)
    assert 0 < confidence <= 1
    assert len(centroid) == 2
    assert np.linalg.norm(estimate - env.cube_position[:2]) < 0.01
