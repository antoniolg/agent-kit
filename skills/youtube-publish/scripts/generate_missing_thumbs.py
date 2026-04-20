#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PRESENTER_PHOTO_BASENAMES = {
    "antonio": ("antonio-1.png", "antonio-2.png", "antonio-3.png"),
    "nino": ("nino-1.png", "nino-2.png", "nino-3.png"),
}
DEFAULT_PRESENTER = "antonio"


def get_assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"


def get_api_key() -> str | None:
    # Prefer GOOGLE_API_KEY if present, otherwise fall back to the legacy GEMINI_API_KEY.
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def parse_presenter(value: str) -> str:
    presenter = (value or DEFAULT_PRESENTER).strip().lower()
    if presenter not in PRESENTER_PHOTO_BASENAMES:
        options = ", ".join(sorted(PRESENTER_PHOTO_BASENAMES))
        raise ValueError(f"Invalid presenter: {value!r}. Use one of: {options}")
    return presenter


def presenter_display_name(presenter: str) -> str:
    return presenter.capitalize()


def presenter_photo_keys(presenter: str) -> list[str]:
    return [f"assets/{basename}" for basename in PRESENTER_PHOTO_BASENAMES[presenter]]


def build_photo_map(assets_dir: Path, presenter: str) -> dict[str, Path]:
    return {key: assets_dir / Path(key).name for key in presenter_photo_keys(presenter)}


def word_count(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def normalize_thumb_text(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    banned = {"facil", "fácil", "rapido", "rápido", "secreto"}
    words = [w for w in cleaned.split(" ") if w.lower() not in banned]
    return " ".join(words[:4]).strip()


def build_image_prompt(thumb: dict, presenter_name: str) -> str:
    thumb_text = normalize_thumb_text(str(thumb.get("text", "") or ""))
    if word_count(thumb_text) > 4:
        thumb_text = " ".join(thumb_text.split(" ")[:4]).strip()

    artifact = str(thumb.get("artifact", "") or "")
    concept = str(thumb.get("concept", "") or "")

    return (
        "Create a YouTube thumbnail (16:9). "
        f"Use all provided reference photos as {presenter_name}'s identity anchors (face, hair, beard, proportions). "
        "You may choose the best posture, crop and expression for impact; do not copy a single source pose literally. "
        "Keep non-negotiable style anchors: cinematic dark mood with cyan/magenta accents, and massive bold white text. "
        "Allow creative freedom for composition, scene and storytelling if it improves the concept. "
        f"Technical artifact suggestion: {artifact}. "
        f"Concept direction: {concept}. "
        f'Add massive bold white text (<=4 words): \"{thumb_text}\". '
        "Prioritize strong mobile readability. High contrast, clean typography, no extra text, no watermark."
    )


def run_generate_image(
    image_script: Path,
    prompt: str,
    output_path: Path,
    input_images: list[Path],
    api_key: str,
    image_model: str | None,
    timeout_s: int,
) -> None:
    cmd = [
        "uv",
        "run",
        str(image_script),
        "--prompt",
        prompt,
        "--filename",
        str(output_path),
        "--input-image",
        *[str(path) for path in input_images],
        "--api-key",
        api_key,
    ]
    if image_model:
        cmd += ["--model", image_model]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Missing 'uv' command required to run nano-banana image generation.") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        raise RuntimeError(stderr or stdout or f"Command failed: {' '.join(cmd)}")

    if not output_path.exists():
        raise RuntimeError("Image generation succeeded but output file was not created")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate missing thumb-*.png files from existing ideas.json"
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.expanduser("~/Downloads/youtube-videos"),
        help="Directory containing per-video folders",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=90,
        help="Per-image generation timeout in seconds (default: 90)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Retries per image on failure (default: 1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate thumbs even if files already exist",
    )
    parser.add_argument(
        "--presenter",
        default=DEFAULT_PRESENTER,
        choices=sorted(PRESENTER_PHOTO_BASENAMES.keys()),
        help="Presenter photo set for thumbnails (default: antonio)",
    )
    parser.add_argument(
        "--image-model",
        help="Optional image model override passed to nano-banana image generator",
    )
    args = parser.parse_args()

    if args.timeout_s <= 0:
        print("--timeout-s must be > 0", file=sys.stderr)
        return 2
    if args.retries < 0:
        print("--retries must be >= 0", file=sys.stderr)
        return 2

    api_key = get_api_key()
    if not api_key:
        print(
            "Missing GOOGLE_API_KEY (or legacy GEMINI_API_KEY) in environment for thumbnail generation.",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(os.path.expanduser(args.out_dir))
    if not out_dir.exists():
        print(f"Missing out dir: {out_dir}", file=sys.stderr)
        return 1

    presenter = parse_presenter(args.presenter)
    presenter_name = presenter_display_name(presenter)
    assets_dir = get_assets_dir()
    photo_keys = presenter_photo_keys(presenter)
    photo_map = build_photo_map(assets_dir, presenter)
    missing_assets = [key for key, path in photo_map.items() if not path.exists()]
    if missing_assets:
        print(
            f"Missing presenter assets for '{presenter}': {', '.join(missing_assets)}",
            file=sys.stderr,
        )
        return 1
    presenter_reference_photos = [photo_map[key] for key in photo_keys]

    image_script = (
        Path(__file__).resolve().parents[2]
        / "nano-banana-pro"
        / "scripts"
        / "generate_image.py"
    )
    if not image_script.exists():
        print(f"Missing image generator script: {image_script}", file=sys.stderr)
        return 1

    ok = 0
    failed = 0
    skipped = 0

    for video_dir in sorted([p for p in out_dir.iterdir() if p.is_dir()]):
        ideas_path = video_dir / "ideas.json"
        if not ideas_path.exists():
            continue

        try:
            payload = json.loads(ideas_path.read_text(encoding="utf-8"))
        except Exception as exc:
            (video_dir / "error.thumbs.txt").write_text(
                f"Failed to read ideas.json: {exc}\n",
                encoding="utf-8",
            )
            failed += 1
            continue

        thumbnails = payload.get("thumbnails")
        if not isinstance(thumbnails, list) or not thumbnails:
            (video_dir / "error.thumbs.txt").write_text(
                "Invalid ideas.json: missing thumbnails\n",
                encoding="utf-8",
            )
            failed += 1
            continue

        for idx, thumb in enumerate(thumbnails, start=1):
            if not isinstance(thumb, dict):
                continue

            out_img = video_dir / f"thumb-{idx}.png"
            if out_img.exists() and not args.force:
                skipped += 1
                continue

            prompt = build_image_prompt(thumb, presenter_name=presenter_name)
            (video_dir / f"thumb-{idx}.prompt.txt").write_text(
                prompt,
                encoding="utf-8",
            )

            attempt = 0
            while True:
                try:
                    run_generate_image(
                        image_script=image_script,
                        prompt=prompt,
                        output_path=out_img,
                        input_images=presenter_reference_photos,
                        api_key=api_key,
                        image_model=args.image_model,
                        timeout_s=args.timeout_s,
                    )
                    ok += 1
                    break
                except Exception as exc:
                    attempt += 1
                    if attempt > args.retries:
                        (video_dir / "error.thumbs.txt").write_text(
                            f"Failed to generate thumb-{idx}: {exc}\n",
                            encoding="utf-8",
                        )
                        failed += 1
                        break

    print(f"Generated: {ok} | Skipped: {skipped} | Failed: {failed} | Out: {out_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
