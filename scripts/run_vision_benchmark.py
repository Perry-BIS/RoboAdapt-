from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roboadapt.eval import load_vision_config, run_vision_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run paired oracle and RGB-in-the-loop RoboAdapt episodes."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = load_vision_config(args.config)
    path = run_vision_benchmark(config, args.output)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
