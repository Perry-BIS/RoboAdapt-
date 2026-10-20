from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw
from roboadapt.env import RoboAdaptEnv
from roboadapt.perception import rgb_centroid_pose_sensor
from roboadapt.task import sample_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Level-1 RGB centroid pose observation.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="media/rgb_detection.png")
    args = parser.parse_args()
    env = RoboAdaptEnv(); sample = sample_task(args.seed)
    env.reset(sample.object_xy)
    xy, confidence, (u, v), rgb = rgb_centroid_pose_sensor(env)
    truth = env.cube_position[:2]
    error = float(((xy - truth) ** 2).sum() ** 0.5)
    image = Image.fromarray(rgb); draw = ImageDraw.Draw(image)
    draw.ellipse((u-7, v-7, u+7, v+7), outline="yellow", width=3)
    draw.text((8, 8), f"RGB centroid error: {error*1000:.1f} mm", fill="white", stroke_width=2, stroke_fill="black")
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); image.save(output)
    print(json.dumps({"seed": args.seed, "estimated_xy_m": xy.tolist(), "true_xy_m": truth.tolist(),
                      "error_m": error, "confidence": confidence, "output": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
