#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

from dub_srt_utils import write_cleaned_and_dub_srt


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Transcribe with Parakeet MLX and clean text")
    parser.add_argument("--video", required=True, help="Video path")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--max-words", type=int, default=14, help="Max words per subtitle sentence")
    parser.add_argument("--max-duration", type=float, default=5.2, help="Max subtitle sentence duration in seconds")
    parser.add_argument("--silence-gap", type=float, default=0.35, help="Split at silence gaps in seconds")
    args = parser.parse_args()

    video_path = Path(args.video)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "parakeet-mlx",
        str(video_path),
        "--output-dir",
        str(out_dir),
        "--output-format",
        "srt",
        "--max-words",
        str(args.max_words),
        "--max-duration",
        str(args.max_duration),
        "--silence-gap",
        str(args.silence_gap),
    ]
    run(cmd)

    srt_path = out_dir / f"{video_path.stem}.srt"
    if not srt_path.exists():
        raise FileNotFoundError("Parakeet SRT not found")

    cleaned_path, dub_path = write_cleaned_and_dub_srt(srt_path, out_dir)
    print(f"Dub-optimized SRT: {dub_path}")
    print(str(cleaned_path))


if __name__ == "__main__":
    main()
