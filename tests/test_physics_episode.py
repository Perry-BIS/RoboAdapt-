from roboadapt.control import run_episode
from roboadapt.env import RoboAdaptEnv
from roboadapt.task import sample_task


def test_reobserve_controller_physically_picks_and_places_known_seed():
    """Integration test: the free cube must be lifted and released at the goal."""
    env = RoboAdaptEnv()
    sample = sample_task(0, 0.04)
    result = run_episode(
        env, seed=0, controller="reobserve_replan", sigma_m=0.0,
        object_xy=sample.object_xy, displacement_xy=sample.displacement_xy,
    )
    assert result.success_grasp
    assert result.success_place
    assert result.replan_count == 1
