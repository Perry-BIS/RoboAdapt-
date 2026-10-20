from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roboadapt.control import run_episode
from roboadapt.env import RoboAdaptEnv
from roboadapt.eval import smoke_accepts
from roboadapt.task import sample_task


def main() -> int:
    total = 10
    minimum = 10
    env = RoboAdaptEnv()
    successes = 0
    for seed in range(total):
        sample = sample_task(seed, 0.04)
        result = run_episode(env, seed=seed, controller="reobserve_replan", sigma_m=0.0,
                             object_xy=sample.object_xy, displacement_xy=sample.displacement_xy)
        successes += int(result.success_place)
        print(f"seed={seed} grasp={result.success_grasp} place={result.success_place} reason={result.failure_reason}")
    passed = smoke_accepts(successes, total=total, minimum=minimum)
    print(f"smoke summary: {successes}/{total} place successes; required={minimum}/{total}; "
          f"status={'PASS' if passed else 'FAIL'}; model={env.model_hash}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

