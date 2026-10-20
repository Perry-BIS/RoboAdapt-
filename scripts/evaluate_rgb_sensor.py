from pathlib import Path
import argparse
import csv
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from roboadapt.env import RoboAdaptEnv
from roboadapt.perception import rgb_centroid_pose_sensor
from roboadapt.task import sample_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Level-1 RGB centroid localization over seeded poses.")
    parser.add_argument("--seeds", type=int, default=20, help="Evaluate seeds 0..N-1.")
    parser.add_argument("--output", default="results/rgb/observations.csv")
    args = parser.parse_args()
    env = RoboAdaptEnv(); rows = []
    for seed in range(args.seeds):
        sample = sample_task(seed); env.reset(sample.object_xy)
        estimate, confidence, _, _ = rgb_centroid_pose_sensor(env)
        truth = env.cube_position[:2]
        rows.append({"seed": seed, "true_x_m": truth[0], "true_y_m": truth[1],
                     "estimated_x_m": estimate[0], "estimated_y_m": estimate[1],
                     "error_m": np.linalg.norm(estimate-truth), "confidence": confidence,
                     "model_hash": env.model_hash})
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    errors = np.array([row["error_m"] for row in rows])
    summary = {"observations": len(rows), "mean_error_m": float(errors.mean()),
               "median_error_m": float(np.median(errors)), "max_error_m": float(errors.max()),
               "model_hash": env.model_hash, "output": str(output)}
    (output.parent / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
