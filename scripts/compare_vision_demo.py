from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

from roboadapt.control import run_vision_episode
from roboadapt.env import RoboAdaptEnv
from roboadapt.task import sample_task


def label_frame(frame: np.ndarray, title: str, result) -> np.ndarray:
    image = Image.fromarray(frame)
    canvas = Image.new("RGB", (image.width, image.height + 58), "#15191f")
    canvas.paste(image, (0, 58))
    draw = ImageDraw.Draw(canvas)
    outcome = "SUCCESS" if result.success_place else result.failure_reason.upper()
    draw.text((10, 6), title, fill="white")
    draw.text(
        (10, 24),
        f"images={result.observation_count} replans={result.replan_count}",
        fill="#b8c4d8",
    )
    draw.text(
        (10, 41),
        f"FINAL: {outcome}",
        fill="#8fe388" if result.success_place else "#ff8a75",
    )
    return np.asarray(canvas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render matched oracle/RGB control trials.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--displacement", type=float, default=0.04)
    parser.add_argument("--gif", default="media/vision_closed_loop_comparison.gif")
    parser.add_argument("--mp4", default="media/vision_closed_loop_comparison.mp4")
    args = parser.parse_args()
    sample = sample_task(args.seed, args.displacement)
    controllers = ("oracle_state", "rgb_open_loop", "rgb_reobserve")
    results = {
        controller: run_vision_episode(
            RoboAdaptEnv(),
            seed=args.seed,
            controller=controller,
            object_xy=sample.object_xy,
            displacement_xy=sample.displacement_xy,
            record=True,
        )
        for controller in controllers
    }
    frame_count = max(len(result.frames) for result in results.values())
    combined = []
    for index in range(frame_count):
        panels = []
        for controller in controllers:
            result = results[controller]
            frame = result.frames[min(index, len(result.frames) - 1)]
            panels.append(label_frame(frame, controller.replace("_", " ").title(), result))
        combined.append(np.concatenate(panels, axis=1))
    gif_path = Path(args.gif)
    mp4_path = Path(args.mp4)
    gif_path.parent.mkdir(parents=True, exist_ok=True)
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(gif_path, combined, fps=30, loop=0)
    imageio.mimsave(mp4_path, combined, fps=30, codec="libx264", quality=8)
    for controller, result in results.items():
        print(
            f"{controller}: place={result.success_place} reason={result.failure_reason} "
            f"images={result.observation_count} replans={result.replan_count}"
        )
    print(f"wrote {gif_path} and {mp4_path} ({frame_count} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
