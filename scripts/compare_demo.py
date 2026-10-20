from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

from roboadapt.control import run_episode
from roboadapt.env import RoboAdaptEnv
from roboadapt.task import sample_task


def label_frame(frame: np.ndarray, title: str, outcome: str) -> np.ndarray:
    image = Image.fromarray(frame)
    canvas = Image.new("RGB", (image.width, image.height + 42), "#15191f")
    canvas.paste(image, (0, 42))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 7), title, fill="white")
    draw.text((12, 23), outcome, fill="#8fe388" if outcome.endswith("SUCCESS") else "#ff8a75")
    return np.asarray(canvas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render matched open-loop/adaptive displaced trials side by side.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--displacement", type=float, default=0.04)
    parser.add_argument("--gif", default="media/matched_displacement_comparison.gif")
    parser.add_argument("--mp4", default="media/matched_displacement_comparison.mp4")
    args = parser.parse_args()
    sample = sample_task(args.seed, args.displacement)
    results = {}
    for controller in ("open_loop", "reobserve_replan"):
        results[controller] = run_episode(
            RoboAdaptEnv(), seed=args.seed, controller=controller, sigma_m=0.0,
            object_xy=sample.object_xy, displacement_xy=sample.displacement_xy, record=True,
        )
    frame_count = max(len(result.frames) for result in results.values())
    combined = []
    for idx in range(frame_count):
        panels = []
        for controller in ("open_loop", "reobserve_replan"):
            result = results[controller]
            frame = result.frames[min(idx, len(result.frames) - 1)]
            outcome = "FINAL: SUCCESS" if result.success_place else f"FINAL: {result.failure_reason.upper()}"
            panels.append(label_frame(frame, controller.replace("_", " ").title(), outcome))
        combined.append(np.concatenate(panels, axis=1))
    gif_path = Path(args.gif); mp4_path = Path(args.mp4)
    gif_path.parent.mkdir(parents=True, exist_ok=True); mp4_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(gif_path, combined, fps=30, loop=0)
    imageio.mimsave(mp4_path, combined, fps=30, codec="libx264", quality=8)
    print(f"seed={args.seed} displacement={args.displacement:.3f}m")
    for controller, result in results.items():
        print(f"{controller}: grasp={result.success_grasp} place={result.success_place} "
              f"reason={result.failure_reason} frames={len(result.frames)}")
    print(f"wrote {gif_path} and {mp4_path} ({frame_count} combined frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
