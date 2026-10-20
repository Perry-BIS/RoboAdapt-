from pathlib import Path
import argparse
import imageio.v2 as imageio


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a RoboAdapt GIF to MP4 using imageio-ffmpeg.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()
    frames = imageio.mimread(args.input)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(args.output, frames, fps=args.fps, codec="libx264", quality=8)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

