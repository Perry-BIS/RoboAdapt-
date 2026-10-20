import numpy as np
from roboadapt.env import RoboAdaptEnv


def test_model_loads_and_reset_places_cube():
    env = RoboAdaptEnv()
    requested = np.array([-0.08, -0.04])
    env.reset(requested)
    assert np.allclose(env.cube_position[:2], requested, atol=1e-3)
    assert 0.018 <= env.cube_position[2] <= 0.026

