#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def has_audio_stream(video_path: Path) -> bool:
    output = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "json",
            str(video_path),
        ]
    )
    data = json.loads(output or "{}")
    streams = data.get("streams", [])
    return isinstance(streams, list) and len(streams) > 0


def build_video_with_cover(video_path: Path, thumbnail_path: Path, output_path: Path, intro_ms: int) -> None:
    intro_seconds = intro_ms / 1000.0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if has_audio_stream(video_path):
        filter_complex = (
            f"[0:v][1:v]scale2ref=w=iw:h=ih[cover_src][main_src];"
            f"[cover_src]trim=duration={intro_seconds},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[cover];"
            "[main_src]setpts=PTS-STARTPTS,setsar=1,format=yuv420p[main];"
            "[cover][main]concat=n=2:v=1:a=0[v];"
            f"[1:a]adelay={intro_ms}:all=1[a]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(thumbnail_path),
            "-i",
            str(video_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    else:
        filter_complex = (
            f"[0:v][1:v]scale2ref=w=iw:h=ih[cover_src][main_src];"
            f"[cover_src]trim=duration={intro_seconds},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[cover];"
            "[main_src]setpts=PTS-STARTPTS,setsar=1,format=yuv420p[main];"
            "[cover][main]concat=n=2:v=1:a=0[v]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(thumbnail_path),
            "-i",
            str(video_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

    run(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build native X video with thumbnail as first 500ms")
    parser.add_argument("--video", required=True, help="Input video")
    parser.add_argument("--thumbnail", required=True, help="Final thumbnail image")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--intro-ms", type=int, default=500, help="Cover duration in milliseconds (default: 500)")
    args = parser.parse_args()

    video_path = Path(args.video)
    thumbnail_path = Path(args.thumbnail)
    output_path = Path(args.output)

    if not video_path.exists():
        raise FileNotFoundError(f"Missing video: {video_path}")
    if not thumbnail_path.exists():
        raise FileNotFoundError(f"Missing thumbnail: {thumbnail_path}")
    if args.intro_ms <= 0:
        raise ValueError("--intro-ms must be > 0")

    build_video_with_cover(video_path, thumbnail_path, output_path, args.intro_ms)
    print(str(output_path))


if __name__ == "__main__":
    main()
