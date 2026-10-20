from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from roboadapt.eval import wilson_interval


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate plots and summary strictly from episode CSV data.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    grouped = []
    for keys, group in df.groupby(["controller", "sigma_m", "displacement_m"], sort=True):
        n = len(group); k = int(group["success_place"].astype(bool).sum())
        lo, hi = wilson_interval(k, n)
        grouped.append({"controller": keys[0], "sigma_m": keys[1], "displacement_m": keys[2],
                        "n": n, "successes": k, "success_rate": k/n, "ci_low": lo, "ci_high": hi,
                        "mean_wall_seconds": group.wall_seconds.mean(),
                        "mean_endpoint_error_m": group.endpoint_error_m.mean()})
    summary = pd.DataFrame(grouped)
    summary.to_csv(out / "summary.csv", index=False)

    controllers = ["open_loop", "reobserve_replan"]
    colors = ["#4978b8", "#e06c4f"]
    sigmas = sorted(summary.sigma_m.unique())
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for ax, sigma in zip(axes.flat, sigmas):
        panel = summary[summary.sigma_m == sigma]
        displacements = sorted(panel.displacement_m.unique())
        x = np.arange(len(displacements)); width = 0.34
        for idx, controller in enumerate(controllers):
            rows = panel[panel.controller == controller].set_index("displacement_m").loc[displacements]
            y = rows.success_rate.to_numpy()
            yerr = np.vstack([y-rows.ci_low.to_numpy(), rows.ci_high.to_numpy()-y])
            ax.bar(x + (idx-0.5)*width, y, width, color=colors[idx], yerr=yerr,
                   capsize=3, label=controller.replace("_", " "))
        ax.set_title(f"Pose noise sigma = {sigma:.2f} m")
        ax.set_xticks(x, [f"{d:.2f} m" for d in displacements])
        ax.set_xlabel("Post-observation displacement")
        ax.grid(axis="y", alpha=0.25)
    axes[0, 0].set_ylabel("Place success rate"); axes[1, 0].set_ylabel("Place success rate")
    axes[0, 0].set_ylim(0, 1.08); axes[0, 1].legend(loc="lower left")
    fig.suptitle("RoboAdapt place success (Wilson 95% CI)")
    fig.tight_layout()
    fig.savefig(out / "success_rate.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.8))
    for controller, group in df.groupby("controller"):
        ax.hist(group.endpoint_error_m, bins=12, alpha=0.6, label=controller)
    ax.set(xlabel="Final object-to-goal error (m)", ylabel="Episodes", title="Endpoint error distribution")
    ax.legend(); ax.grid(alpha=0.2); fig.tight_layout()
    fig.savefig(out / "endpoint_error.png", dpi=180); plt.close(fig)

    failures = df.groupby(["controller", "failure_reason"]).size().unstack(fill_value=0)
    failures.plot(kind="bar", stacked=True, figsize=(7, 4.8), color=["#bc5a45", "#5a8fbd", "#5cb85c"])
    plt.ylabel("Episodes"); plt.title("Outcome / failure categories"); plt.xticks(rotation=0); plt.tight_layout()
    plt.savefig(out / "failure_categories.png", dpi=180); plt.close()

    overhead = df.groupby("controller").agg(
        mean_sim_seconds=("sim_seconds", "mean"), mean_steps=("steps", "mean"),
        mean_wall_seconds=("wall_seconds", "mean"),
    ).loc[controllers]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.3))
    overhead.mean_sim_seconds.plot.bar(ax=axes[0], color=colors)
    axes[0].set(ylabel="Simulated seconds / episode", xlabel="", title="Trajectory duration")
    overhead.mean_steps.plot.bar(ax=axes[1], color=colors)
    axes[1].set(ylabel="Physics steps / episode", xlabel="", title="Control / physics cost")
    for ax in axes:
        ax.tick_params(axis="x", rotation=0); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "timing_steps.png", dpi=180); plt.close(fig)
    overhead.to_csv(out / "controller_overhead.csv")
    print(json.dumps({"episodes": len(df), "plots": 4, "summary_rows": len(summary)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

