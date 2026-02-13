#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path
import re
import subprocess

YOUTUBE_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def read_existing_video_id(path: Path) -> str | None:
    if not path.exists():
        return None
    video_id = path.read_text(encoding="utf-8").strip()
    if YOUTUBE_VIDEO_ID_RE.fullmatch(video_id):
        return video_id
    return None


def main():
    parser = argparse.ArgumentParser(description="Upload draft YouTube video")
    parser.add_argument("--video", required=True, help="Video path")
    parser.add_argument("--output-video-id", required=True, help="File to store video id")
    parser.add_argument("--client-secret", required=True, help="OAuth client secret JSON")
    args = parser.parse_args()

    output_video_id_path = Path(args.output_video_id)
    existing_video_id = read_existing_video_id(output_video_id_path)
    if existing_video_id:
        url_path = output_video_id_path.parent / "video_url.txt"
        url_path.write_text(f"https://www.youtube.com/watch?v={existing_video_id}", encoding="utf-8")
        print(f"Reusing existing draft video id: {existing_video_id}")
        return

    title = f"Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    desc_path = output_video_id_path.parent / "description.draft.txt"
    desc_path.write_text("Draft upload. Metadata will be updated.", encoding="utf-8")

    cmd = [
        "python",
        str(Path(__file__).parent / "publish_youtube.py"),
        "--video",
        args.video,
        "--title",
        title,
        "--description-file",
        str(desc_path),
        "--privacy-status",
        "private",
        "--output-video-id",
        args.output_video_id,
        "--client-secret",
        args.client_secret,
    ]
    run(cmd)

    # Read video id and write URL file
    vid = read_existing_video_id(output_video_id_path)
    if vid:
        url_path = output_video_id_path.parent / "video_url.txt"
        url_path.write_text(f"https://www.youtube.com/watch?v={vid}", encoding="utf-8")
    else:
        raise RuntimeError(f"Upload finished but no valid video id found in {output_video_id_path}")


if __name__ == "__main__":
    main()
