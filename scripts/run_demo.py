from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import imageio.v2 as imageio
from roboadapt.control import CONTROLLERS, run_episode
from roboadapt.env import RoboAdaptEnv
from roboadapt.task import sample_task


def parse_args():
    parser = argparse.ArgumentParser(description="Run one contact-physics RoboAdapt pick-and-place episode.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--controller", choices=CONTROLLERS, default="reobserve_replan")
    parser.add_argument("--sigma", type=float, default=0.0, dest="sigma_m")
    parser.add_argument("--displacement", type=float, default=0.03, dest="displacement_m")
    parser.add_argument("--record", action="store_true", help="Write a real MuJoCo GIF to media/.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sample = sample_task(args.seed, args.displacement_m)
    env = RoboAdaptEnv()
    result = run_episode(env, seed=args.seed, controller=args.controller, sigma_m=args.sigma_m,
                         object_xy=sample.object_xy, displacement_xy=sample.displacement_xy,
                         record=args.record)
    payload = {key: value for key, value in vars(result).items() if key != "frames"}
    print(json.dumps(payload, indent=2))
    if args.record:
        output = Path("media") / f"demo_{args.controller}_seed{args.seed}.gif"
        output.parent.mkdir(exist_ok=True)
        imageio.mimsave(output, result.frames, fps=30, loop=0)
        print(f"wrote {output} ({len(result.frames)} frames)")
    return 0 if result.success_place else 2


if __name__ == "__main__":
    raise SystemExit(main())

