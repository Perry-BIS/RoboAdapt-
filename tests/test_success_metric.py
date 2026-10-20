import numpy as np
from roboadapt.task import in_goal, is_lifted


def test_goal_requires_xy_and_low_z():
    goal = np.array([0.18, 0.14])
    assert in_goal(np.array([0.18, 0.14, 0.022]), goal)
    assert not in_goal(np.array([0.30, 0.14, 0.022]), goal)
    assert not in_goal(np.array([0.18, 0.14, 0.20]), goal)


def test_lift_threshold():
    assert is_lifted(0.08)
    assert not is_lifted(0.05)

