from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image, ImageDraw

from roboadapt.env import RoboAdaptEnv
from roboadapt.perception import rgb_centroid_pose_sensor
from roboadapt.task import sample_task


def panel(rgb: np.ndarray, centroid, estimate, truth, title: str) -> Image.Image:
    image = Image.fromarray(rgb)
    canvas = Image.new("RGB", (image.width, image.height + 58), "#15191f")
    canvas.paste(image, (0, 58))
    draw = ImageDraw.Draw(canvas)
    u, v = centroid
    draw.ellipse((u - 7, v + 51, u + 7, v + 65), outline="yellow", width=3)
    error_mm = float(np.linalg.norm(estimate - truth) * 1000)
    draw.text((10, 7), title, fill="white")
    draw.text((10, 27), f"RGB estimate error: {error_mm:.2f} mm", fill="#b8c4d8")
    draw.text((10, 43), f"estimate=({estimate[0]:+.3f}, {estimate[1]:+.3f}) m", fill="#b8c4d8")
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(description="Render initial and re-observed RGB estimates.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--displacement", type=float, default=0.04)
    parser.add_argument("--output", default="media/vision_reobservation_pair.png")
    args = parser.parse_args()
    env = RoboAdaptEnv()
    sample = sample_task(args.seed, args.displacement)
    env.reset(sample.object_xy)
    first, _, first_uv, first_rgb = rgb_centroid_pose_sensor(env)
    first_truth = env.cube_position[:2]
    env.displace_cube(sample.displacement_xy)
    second, _, second_uv, second_rgb = rgb_centroid_pose_sensor(env)
    second_truth = env.cube_position[:2]
    image = Image.new("RGB", (640, 378), "black")
    image.paste(panel(first_rgb, first_uv, first, first_truth, "Initial camera observation"), (0, 0))
    image.paste(
        panel(second_rgb, second_uv, second, second_truth, "Re-observation after 4 cm shift"),
        (320, 0),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
