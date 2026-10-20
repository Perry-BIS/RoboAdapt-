from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roboadapt.analysis import analyze_episode_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute RoboAdapt statistics from an exact episode CSV.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-resamples", type=int, default=200_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_261_019)
    args = parser.parse_args()
    result = analyze_episode_csv(
        args.input, bootstrap_resamples=args.bootstrap_resamples, bootstrap_seed=args.bootstrap_seed
    )
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
