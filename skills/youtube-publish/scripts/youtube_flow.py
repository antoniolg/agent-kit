#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

from english_variant import prepare_english_assets, translate_text
from dub_srt_utils import write_cleaned_and_dub_srt


def run(cmd, input_text=None):
    result = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def build_x_native_video(video_path: Path, thumbnail_path: str, workdir: Path) -> Path:
    thumb = Path(thumbnail_path.strip())
    if not thumb.is_absolute():
        thumb = (workdir / thumb).resolve()
    if not thumb.exists():
        raise FileNotFoundError(f"Thumbnail for X variant not found: {thumb}")

    output = workdir / "video-x.mp4"
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "build_x_native_video.py"),
        "--video",
        str(video_path),
        "--thumbnail",
        str(thumb),
        "--output",
        str(output),
        "--intro-ms",
        "500",
    ]
    run(cmd)
    return output


def parse_local_datetime(value: str, tz_name: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        if ZoneInfo is None:
            raise RuntimeError("ZoneInfo not available; use Python 3.9+ or provide timezone offset")
        dt = dt.replace(tzinfo=ZoneInfo(tz_name))
    return dt


def detect_system_timezone() -> str | None:
    env_tz = os.environ.get("TZ")
    if env_tz:
        return env_tz

    try:
        localtime = Path("/etc/localtime")
        if localtime.exists():
            target = os.path.realpath(localtime)
            match = re.search(r"/zoneinfo/(.+)$", target)
            if match:
                return match.group(1)
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["/usr/sbin/systemsetup", "-gettimezone"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            match = re.search(r"Time Zone:\\s*(\\S+)", result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass

    return None

def safe_slug(text):
    text = re.sub(r"[^a-zA-Z0-9\-\s]", "", text).strip().lower()
    text = re.sub(r"\s+", "-", text)
    return text or "video"


def read_existing_video_id(path: Path) -> str | None:
    if not path.exists():
        return None
    video_id = path.read_text(encoding="utf-8").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return video_id
    return None


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def move_inputs(videos, inputs_dir):
    moved = []
    for video in videos:
        src = Path(video)
        if not src.exists():
            raise FileNotFoundError(f"Missing video: {src}")
        dst = inputs_dir / src.name
        shutil.move(src, dst)
        moved.append(dst)
    return moved


def concat_videos(videos, out_path: Path):
    list_file = out_path.parent / "concat_list.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for v in videos:
            f.write(f"file '{v.as_posix()}'\n")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(out_path),
    ]
    run(cmd)
    return out_path


def transcribe_parakeet(video_path: Path, workdir: Path):
    cmd = [
        "parakeet-mlx",
        str(video_path),
        "--output-dir",
        str(workdir),
        "--output-format",
        "srt",
    ]
    run(cmd)
    # parakeet outputs {filename}.srt
    srt_path = workdir / f"{video_path.stem}.srt"
    if not srt_path.exists():
        raise FileNotFoundError("Parakeet SRT not found")
    return srt_path


def create_content_md(
    workdir: Path,
    title_hint: str,
    video_url: str | None,
    transcript_path: Path | None,
    english_transcript_path: Path | None = None,
    dubbed_audio_path: Path | None = None,
    dubbed_video_path: Path | None = None,
):
    transcript_ref = str(transcript_path) if transcript_path else ""
    english_transcript_ref = str(english_transcript_path) if english_transcript_path else ""
    dubbed_audio_ref = str(dubbed_audio_path) if dubbed_audio_path else ""
    dubbed_video_ref = str(dubbed_video_path) if dubbed_video_path else ""
    template = f"""# Pack YouTube — {title_hint or 'Sin título'}

## Enlace del vídeo
{video_url or ''}

## Transcript limpio
{transcript_ref}

## Transcript EN
{english_transcript_ref}

## Audio doblado EN
{dubbed_audio_ref}

## Video doblado EN
{dubbed_video_ref}

## Notas para el agente
- Lee el transcript limpio y genera títulos, ideas de thumbnail, descripción, capítulos y post de LinkedIn.
- Mantén las reglas editoriales y de programación definidas en la skill.
- Si existe transcript EN, genera también una propuesta de título y descripción en inglés para YouTube multi-language.

## Títulos

## Ideas de thumbnails

## Descripción

## Capítulos

## LinkedIn

## Título (final)

## Descripción (final)

## Capítulos (final)

## Post LinkedIn (final)

## Thumbnail (final)

## Programación (final)
(YYYY-MM-DD HH:MM o "private")

## Title (EN)

## Description (EN)
"""

    out_path = workdir / "content.md"
    out_path.write_text(template, encoding="utf-8")
    return out_path


def extract_section(md_text, heading):
    pattern = rf"^## {re.escape(heading)}\s*$"
    lines = md_text.splitlines()
    out = []
    capture = False
    for line in lines:
        if re.match(pattern, line.strip()):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def validate_final_content(md_text: str, workdir: Path, require_thumbnail: bool) -> None:
    required_sections = [
        ("Título (final)", "title"),
        ("Descripción (final)", "description"),
        ("Capítulos (final)", "chapters"),
        ("Post LinkedIn (final)", "linkedin"),
    ]

    errors = []
    warnings = []

    for heading, label in required_sections:
        content = extract_section(md_text, heading)
        if not content:
            errors.append(f"Missing {label} in '{heading}'.")

    thumbnail = extract_section(md_text, "Thumbnail (final)")
    if require_thumbnail and not thumbnail:
        errors.append("Missing thumbnail path in 'Thumbnail (final)'.")
    if thumbnail:
        thumb_path = Path(thumbnail.strip())
        if not thumb_path.is_absolute():
            thumb_path = (workdir / thumb_path).resolve()
        if not thumb_path.exists():
            errors.append(f"Thumbnail file not found: {thumb_path}")

    if errors:
        message = "Checklist failed:\n- " + "\n- ".join(errors)
        raise RuntimeError(message)

    if warnings:
        print("Checklist warnings:")
        for warning in warnings:
            print(f"- {warning}")


def load_existing_english_assets(workdir: Path) -> dict[str, str]:
    asset_map = {
        "transcript_en": workdir / "transcript.en.srt",
        "dubbed_audio_en": workdir / "dubbed_audio.en.wav",
        "dubbed_video_en": workdir / "dubbed_video.en.mp4",
        "title_en": workdir / "title.en.txt",
        "description_en": workdir / "description.en.txt",
    }
    return {key: str(path) for key, path in asset_map.items() if path.exists()}


def main():
    parser = argparse.ArgumentParser(description="End-to-end YouTube prep workflow")
    parser.add_argument("--videos", nargs="+", required=True, help="Input video file(s)")
    parser.add_argument("--title-hint", help="Optional title hint for folder naming")
    parser.add_argument("--workdir", help="Output folder")
    parser.add_argument("--skip-transcribe", action="store_true")
    parser.add_argument(
        "--skip-content-scaffold",
        action="store_true",
        help="Skip creating content.md scaffold for the calling model",
    )
    parser.add_argument("--skip-draft-upload", action="store_true")
    parser.add_argument("--upload", action="store_true", help="Upload via publish_youtube.py after validation")
    parser.add_argument("--client-secret", required=True, help="OAuth client secret JSON")
    parser.add_argument("--publish-at", help="Schedule time: YYYY-MM-DD HH:MM")
    parser.add_argument("--timezone")
    parser.add_argument("--thumbnail", help="Thumbnail path (optional, final)")
    parser.add_argument("--privacy-status", help="private|unlisted|public")
    parser.add_argument("--prepare-english", action="store_true", help="Prepare English transcript/title/description and dubbed audio")
    parser.add_argument("--english-voice", help="Reference English voice sample WAV for dubbing")
    parser.add_argument("--english-voice-text-file", help="Transcript of the English reference voice sample")
    parser.add_argument("--english-dub-model", default="voxtral-mini-tts-latest")
    parser.add_argument("--english-dubber-python", help="Python runtime for youtube-dubber (defaults to ~/.venvs/voxtral-local/bin/python)")
    parser.add_argument("--english-dubber-script", help="Path to youtube-dubber/scripts/dub_voxtral.py")
    parser.add_argument("--deepl-auth-key", help="DeepL auth key (falls back to DEEPL_API_KEY or DEEPL_AUTH_KEY)")
    args = parser.parse_args()

    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    slug = safe_slug(args.title_hint or Path(args.videos[0]).stem)
    workdir = Path(args.workdir) if args.workdir else Path(args.videos[0]).parent / f"{now}_{slug}"
    ensure_dir(workdir)

    inputs_dir = workdir / "inputs"
    ensure_dir(inputs_dir)
    moved = move_inputs(args.videos, inputs_dir)

    if len(moved) == 1:
        original = moved[0]
        video_out = workdir / f"{slug}.mp4"
        if original.resolve() != video_out.resolve():
            shutil.move(original, video_out)
    else:
        video_out = workdir / f"{slug}.mp4"
        concat_videos(moved, video_out)

    video_id = None
    video_url = None
    if not args.skip_draft_upload:
        video_id_path = workdir / "video_id.txt"
        existing_video_id = read_existing_video_id(video_id_path)
        if existing_video_id:
            video_id = existing_video_id
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            (workdir / "video_url.txt").write_text(video_url, encoding="utf-8")
            print(f"Reusing existing draft video id: {video_id}")
        else:
            draft_title = args.title_hint or video_out.stem.replace("-", " ").title()
            draft_desc = workdir / "description.draft.txt"
            draft_desc.write_text("Draft upload. Metadata will be updated.", encoding="utf-8")
            cmd = [
                sys.executable,
                str(Path(__file__).parent / "publish_youtube.py"),
                "--video",
                str(video_out),
                "--title",
                draft_title,
                "--description-file",
                str(draft_desc),
                "--privacy-status",
                "private",
                "--output-video-id",
                str(video_id_path),
                "--client-secret",
                args.client_secret,
            ]
            run(cmd)
            video_id = read_existing_video_id(video_id_path)
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                (workdir / "video_url.txt").write_text(video_url, encoding="utf-8")
            else:
                raise RuntimeError(f"Draft upload finished but no valid video id in {video_id_path}")

    srt_path = None
    cleaned_srt_path = None
    dub_srt_path = None
    english_assets = load_existing_english_assets(workdir)

    if not args.skip_transcribe:
        srt_path = transcribe_parakeet(video_out, workdir)
        cleaned_srt_path, dub_srt_path = write_cleaned_and_dub_srt(srt_path, workdir)
    else:
        existing_cleaned_srt = workdir / "transcript.es.cleaned.srt"
        cleaned_srt_path = existing_cleaned_srt if existing_cleaned_srt.exists() else None
        existing_dub_srt = workdir / "transcript.es.dub.srt"
        dub_srt_path = existing_dub_srt if existing_dub_srt.exists() else cleaned_srt_path

    if args.prepare_english:
        if not cleaned_srt_path:
            raise RuntimeError("transcript.es.cleaned.srt is required to prepare English assets")
        if not args.english_voice:
            raise RuntimeError("--english-voice is required with --prepare-english")
        required_english_assets = {"transcript_en", "dubbed_audio_en", "dubbed_video_en"}
        if not required_english_assets.issubset(english_assets):
            english_assets = prepare_english_assets(
                video=video_out,
                spanish_srt=dub_srt_path or cleaned_srt_path,
                out_dir=workdir,
                voice=Path(args.english_voice),
                voice_text_file=Path(args.english_voice_text_file) if args.english_voice_text_file else None,
                deepl_auth_key=args.deepl_auth_key,
                dubber_python=Path(args.english_dubber_python) if args.english_dubber_python else None,
                dubber_script=Path(args.english_dubber_script) if args.english_dubber_script else None,
                dub_model=args.english_dub_model,
            )
        else:
            print("Reusing existing English assets.")

    content_path = None
    skip_content_scaffold = args.skip_content_scaffold
    if not skip_content_scaffold:
        if not cleaned_srt_path:
            raise RuntimeError("No transcript available for content scaffold generation")
        content_path = workdir / "content.md"
        scaffold_created = False
        if not content_path.exists():
            content_path = create_content_md(
                workdir,
                args.title_hint or "",
                video_url,
                cleaned_srt_path,
                Path(english_assets["transcript_en"]) if english_assets.get("transcript_en") else None,
                Path(english_assets["dubbed_audio_en"]) if english_assets.get("dubbed_audio_en") else None,
                Path(english_assets["dubbed_video_en"]) if english_assets.get("dubbed_video_en") else None,
            )
            scaffold_created = True
        if scaffold_created:
            print(f"Content scaffold created: {content_path}")
            print("Fill the sections with the calling model, then rerun with --upload.")
    elif (workdir / "content.md").exists():
        content_path = workdir / "content.md"

    if args.upload and not content_path:
        raise RuntimeError("content.md required for upload")
    if args.upload and content_path and extract_section(
        content_path.read_text(encoding="utf-8"),
        "Título (final)",
    ) == "" and not skip_content_scaffold:
        raise RuntimeError(
            "content.md scaffold is still empty. Fill the FINAL sections with the calling model and rerun --upload."
        )

    if args.upload:
        md = content_path.read_text(encoding="utf-8")
        validate_final_content(md, workdir, require_thumbnail=not args.thumbnail)
        title = extract_section(md, "Título (final)")
        description = extract_section(md, "Descripción (final)")
        thumbnail = extract_section(md, "Thumbnail (final)") or args.thumbnail
        publish_at = extract_section(md, "Programación (final)") or args.publish_at
        schedule_input = (publish_at or "").strip()
        force_private = False
        explicit_private = schedule_input.lower() in {"private", "privado"}
        if explicit_private:
            schedule_input = ""
            force_private = True
        if not schedule_input and not explicit_private:
            raise RuntimeError(
                "Missing 'Programación (final)'. Set 'YYYY-MM-DD HH:MM' to schedule, "
                "or write 'private' to confirm no date."
            )

        if not title or not description:
            raise RuntimeError("Missing final title or description in content.md")

        desc_file = workdir / "description.final.txt"
        desc_file.write_text(description, encoding="utf-8")

        if args.prepare_english:
            title_en = extract_section(md, "Title (EN)")
            description_en = extract_section(md, "Description (EN)")
            if not title_en:
                title_en = translate_text(title.strip(), args.deepl_auth_key)
            if not description_en:
                description_en = translate_text(description.strip(), args.deepl_auth_key)
            title_en_path = workdir / "title.en.txt"
            description_en_path = workdir / "description.en.txt"
            title_en_path.write_text(title_en.strip() + "\n", encoding="utf-8")
            description_en_path.write_text(description_en.strip() + "\n", encoding="utf-8")
            english_assets["title_en"] = str(title_en_path)
            english_assets["description_en"] = str(description_en_path)

        cmd = [
            sys.executable,
            str(Path(__file__).parent / "publish_youtube.py"),
            "--title",
            title.strip(),
            "--description-file",
            str(desc_file),
            "--client-secret",
            args.client_secret,
        ]
        if video_id:
            cmd += ["--update-video-id", video_id]
        else:
            cmd += ["--video", str(video_out)]
        if thumbnail:
            cmd += ["--thumbnail", thumbnail.strip()]
            x_variant = build_x_native_video(video_out, thumbnail.strip(), workdir)
            print(f"X native variant: {x_variant}")
        scheduled_iso = None
        if schedule_input:
            timezone_name = args.timezone or detect_system_timezone()
            if not timezone_name:
                raise RuntimeError("Timezone is required for publish-at (pass --timezone)")
            publish_dt = parse_local_datetime(schedule_input.strip(), timezone_name)
            scheduled_dt = publish_dt + timedelta(minutes=15)
            scheduled_iso = scheduled_dt.isoformat()
            cmd += ["--timezone", timezone_name]
            cmd += ["--publish-at", schedule_input.strip()]
        if force_private:
            cmd += ["--privacy-status", "private"]
        if args.privacy_status:
            cmd += ["--privacy-status", args.privacy_status]

        run(cmd)

        if scheduled_iso:
            linkedin_text = extract_section(md, "Post LinkedIn (final)")
            if not linkedin_text:
                raise RuntimeError("Missing LinkedIn section for scheduling")

            linkedin_path = workdir / "linkedin.final.txt"
            linkedin_path.write_text(linkedin_text.strip(), encoding="utf-8")

            social_cmd = [
                sys.executable,
                str(Path(__file__).parent / "schedule_socials.py"),
                "--text-file",
                str(linkedin_path),
                "--scheduled-date",
                scheduled_iso,
            ]
            run(social_cmd)

    print(f"Workdir: {workdir}")
    print(f"Final video: {video_out}")
    if cleaned_srt_path:
        print(f"Transcript (clean): {cleaned_srt_path}")
    if english_assets.get("transcript_en"):
        print(f"Transcript (EN): {english_assets['transcript_en']}")
    if english_assets.get("dubbed_audio_en"):
        print(f"Dubbed audio (EN): {english_assets['dubbed_audio_en']}")
    if english_assets.get("dubbed_video_en"):
        print(f"Dubbed video (EN): {english_assets['dubbed_video_en']}")
    if english_assets.get("title_en"):
        print(f"Title (EN): {english_assets['title_en']}")
    if english_assets.get("description_en"):
        print(f"Description (EN): {english_assets['description_en']}")
    if content_path:
        print(f"Content: {content_path}")


if __name__ == "__main__":
    main()
