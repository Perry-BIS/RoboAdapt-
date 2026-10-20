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
    parser = argparse.ArgumentParser(description="Plot RGB-in-the-loop benchmark results.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    controllers = [
        controller
        for controller in ("oracle_state", "rgb_open_loop", "rgb_reobserve", "rgb_adaptive")
        if controller in set(df.controller)
    ]
    colors = {
        "oracle_state": "#5f6c7b",
        "rgb_open_loop": "#4978b8",
        "rgb_reobserve": "#e06c4f",
        "rgb_adaptive": "#58a66c",
    }

    summary_rows = []
    for keys, group in df.groupby(
        ["controller", "vision_condition", "displacement_m"], sort=True
    ):
        successes = int(group.success_place.astype(bool).sum())
        total = int(len(group))
        lo, hi = wilson_interval(successes, total)
        summary_rows.append(
            {
                "controller": keys[0],
                "vision_condition": keys[1],
                "displacement_m": keys[2],
                "episodes": total,
                "successes": successes,
                "success_rate": successes / total,
                "ci_low": lo,
                "ci_high": hi,
                "mean_steps": float(group.steps.mean()),
                "mean_wall_seconds": float(group.wall_seconds.mean()),
                "mean_observations": float(group.observation_count.mean()),
                "mean_final_localization_error_m": float(
                    group.final_localization_error_m.mean()
                ),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output / "summary.csv", index=False)

    conditions = list(dict.fromkeys(df.vision_condition.tolist()))
    fig, axes = plt.subplots(1, len(conditions), figsize=(5 * len(conditions), 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, condition in zip(axes, conditions):
        panel = summary[summary.vision_condition == condition]
        displacements = sorted(panel.displacement_m.unique())
        x = np.arange(len(displacements))
        width = 0.8 / len(controllers)
        for index, controller in enumerate(controllers):
            rows = panel[panel.controller == controller].set_index("displacement_m").loc[displacements]
            y = rows.success_rate.to_numpy()
            yerr = np.vstack([y - rows.ci_low.to_numpy(), rows.ci_high.to_numpy() - y])
            ax.bar(
                x + (index - (len(controllers) - 1) / 2) * width,
                y,
                width,
                yerr=yerr,
                capsize=3,
                color=colors[controller],
                label=controller.replace("_", " "),
            )
        ax.set_title(condition.replace("_", " ").title())
        ax.set_xticks(x, [f"{value:.2f} m" for value in displacements])
        ax.set_xlabel("Scripted target displacement")
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Place success rate")
    axes[0].set_ylim(0, 1.08)
    axes[-1].legend(loc="lower left")
    fig.suptitle("Vision-in-the-loop manipulation (Wilson 95% CI)")
    fig.tight_layout()
    fig.savefig(output / "vision_success_rate.png", dpi=180)
    plt.close(fig)

    rgb = df[df.controller.str.startswith("rgb_")].copy()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    labels, values = [], []
    for (controller, condition), group in rgb.groupby(
        ["controller", "vision_condition"], sort=True
    ):
        labels.append(f"{controller.replace('rgb_', '')}\n{condition}")
        values.append(1000 * group.final_localization_error_m.dropna().to_numpy())
    ax.boxplot(values, tick_labels=labels, showfliers=False)
    ax.set_ylabel("Final RGB localization error (mm)")
    ax.set_title("Image-derived target localization")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "vision_localization_error.png", dpi=180)
    plt.close(fig)

    efficiency = df.groupby("controller").agg(
        mean_steps=("steps", "mean"),
        mean_wall_seconds=("wall_seconds", "mean"),
        mean_observations=("observation_count", "mean"),
    ).loc[controllers]
    efficiency.to_csv(output / "controller_efficiency.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.3))
    for ax, column, title in zip(
        axes,
        ["mean_steps", "mean_wall_seconds", "mean_observations"],
        ["Physics steps", "Wall time (s)", "Image observations"],
    ):
        efficiency[column].plot.bar(ax=ax, color=[colors[c] for c in controllers])
        ax.set_title(title)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "vision_efficiency.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"episodes": len(df), "plots": 3, "summary_rows": len(summary)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
