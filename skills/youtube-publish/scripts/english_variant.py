#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from dub_srt_utils import cues_to_srt, parse_srt_text


DEFAULT_DUBBER_SCRIPT = Path.home() / "Projects/antoniolg/youtube-dubber/scripts/dub_voxtral.py"
DEFAULT_DUBBER_PYTHON = Path.home() / ".venvs/voxtral-local/bin/python"
DEFAULT_DUB_MODEL = "voxtral-mini-tts-latest"
DEFAULT_SOURCE_LANG = "ES"
DEFAULT_TARGET_LANG = "EN-US"
DEFAULT_DEEPL_BASE_URL = "https://api-free.deepl.com/v2/translate"
DEFAULT_DEEPL_BASE_URL_PRO = "https://api.deepl.com/v2/translate"


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def resolve_deepl_auth_key(explicit: str | None) -> str:
    auth_key = (
        explicit
        or os.environ.get("DEEPL_API_KEY")
        or os.environ.get("DEEPL_AUTH_KEY")
        or ""
    ).strip()
    if not auth_key:
        raise RuntimeError(
            "Missing DeepL auth key. Pass --deepl-auth-key or set DEEPL_API_KEY/DEEPL_AUTH_KEY."
        )
    return auth_key


def deepl_base_url(auth_key: str) -> str:
    if auth_key.endswith(":fx"):
        return DEFAULT_DEEPL_BASE_URL
    return DEFAULT_DEEPL_BASE_URL_PRO


def translate_texts(
    texts: list[str],
    auth_key: str,
    source_lang: str = DEFAULT_SOURCE_LANG,
    target_lang: str = DEFAULT_TARGET_LANG,
) -> list[str]:
    if not texts:
        return []
    auth_key = resolve_deepl_auth_key(auth_key)

    data = urllib.parse.urlencode(
        {
            "auth_key": auth_key,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "preserve_formatting": "1",
            "split_sentences": "nonewlines",
            "text": texts,
        },
        doseq=True,
    ).encode("utf-8")
    request = urllib.request.Request(
        deepl_base_url(auth_key),
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
    translations = payload.get("translations", [])
    if len(translations) != len(texts):
        raise RuntimeError(
            f"DeepL returned {len(translations)} translations for {len(texts)} input texts."
        )
    return [item.get("text", "").strip() for item in translations]


def translate_text(
    text: str,
    auth_key: str,
    source_lang: str = DEFAULT_SOURCE_LANG,
    target_lang: str = DEFAULT_TARGET_LANG,
) -> str:
    return translate_texts([text], auth_key, source_lang=source_lang, target_lang=target_lang)[0]


def split_srt_blocks(text: str) -> list[str]:
    blocks = []
    current = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def translate_srt(
    spanish_srt: Path,
    english_srt: Path,
    auth_key: str,
    source_lang: str = DEFAULT_SOURCE_LANG,
    target_lang: str = DEFAULT_TARGET_LANG,
) -> Path:
    blocks = split_srt_blocks(spanish_srt.read_text(encoding="utf-8"))
    numbered_blocks: list[tuple[str, str, str]] = []
    text_blocks: list[str] = []

    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            raise RuntimeError(f"Invalid SRT block in {spanish_srt}: {block!r}")
        cue_id = lines[0]
        timing = lines[1]
        cue_text = "\n".join(lines[2:]).strip()
        numbered_blocks.append((cue_id, timing, cue_text))
        text_blocks.append(cue_text)

    translated = translate_texts(
        text_blocks,
        auth_key,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    out_blocks = []
    for (cue_id, timing, _), translated_text in zip(numbered_blocks, translated, strict=True):
        out_blocks.append(f"{cue_id}\n{timing}\n{translated_text}")

    english_srt.write_text("\n\n".join(out_blocks) + "\n", encoding="utf-8")
    return english_srt


def compact_english_srt_in_place(
    english_srt: Path,
    *,
    max_chars_per_second: float = 17.0,
) -> Path:
    cues = parse_srt_text(english_srt.read_text(encoding="utf-8"))
    compact_rules = [
        (r"^\s*Okay,\s+", ""),
        (r"^\s*Well,\s+", ""),
        (r"^\s*So,\s+", ""),
        (r"\bwe are going to\b", "we'll"),
        (r"\bwe're going to\b", "we'll"),
        (r"\bI am going to\b", "I'll"),
        (r"\bI'm going to\b", "I'll"),
        (r"\bit is\b", "it's"),
        (r"\bthat is\b", "that's"),
        (r"\bdo not\b", "don't"),
        (r"\bcannot\b", "can't"),
        (r"\bwe have\b", "we've"),
        (r"\bI have\b", "I've"),
        (r"\blet us\b", "let's"),
        (r"\bwhat I want to do is\b", "I want to"),
        (r"\bwhat we're going to do is\b", "we'll"),
    ]

    compacted = []
    for cue in cues:
        text = cue.text
        duration_s = max(0.1, cue.duration_ms / 1000)
        chars_per_second = len(text) / duration_s
        if chars_per_second > max_chars_per_second:
            for pattern, repl in compact_rules:
                updated = re.sub(pattern, repl, text, flags=re.IGNORECASE)
                updated = re.sub(r"\s+", " ", updated).strip(" ,")
                if updated != text:
                    text = updated
                    chars_per_second = len(text) / duration_s
                if chars_per_second <= max_chars_per_second:
                    break

        compacted.append(
            cue.__class__(
                cue_id=cue.cue_id,
                start=cue.start,
                end=cue.end,
                start_ms=cue.start_ms,
                end_ms=cue.end_ms,
                text=text,
            )
        )

    english_srt.write_text(cues_to_srt(compacted), encoding="utf-8")
    return english_srt


def dub_english_audio(
    *,
    video: Path,
    english_srt: Path,
    voice: Path,
    out_audio: Path,
    out_video: Path,
    voice_text_file: Path | None = None,
    dubber_python: Path = DEFAULT_DUBBER_PYTHON,
    dubber_script: Path = DEFAULT_DUBBER_SCRIPT,
    model: str = DEFAULT_DUB_MODEL,
) -> None:
    if not dubber_python.exists():
        raise RuntimeError(f"Missing dubbing Python runtime: {dubber_python}")
    if not dubber_script.exists():
        raise RuntimeError(f"Missing dubbing script: {dubber_script}")

    out_audio.parent.mkdir(parents=True, exist_ok=True)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(dubber_python),
        str(dubber_script),
        "--video",
        str(video),
        "--srt",
        str(english_srt),
        "--voice",
        str(voice),
        "--out-audio",
        str(out_audio),
        "--out-video",
        str(out_video),
    ]
    if model:
        cmd += ["--model", model]
    if voice_text_file is not None and voice_text_file.exists():
        cmd += ["--voice-text-file", str(voice_text_file)]

    run(cmd)


def prepare_english_assets(
    *,
    video: Path,
    spanish_srt: Path,
    out_dir: Path,
    voice: Path,
    voice_text_file: Path | None = None,
    spanish_title: str | None = None,
    spanish_description: str | None = None,
    deepl_auth_key: str | None = None,
    dubber_python: Path | None = None,
    dubber_script: Path | None = None,
    dub_model: str = DEFAULT_DUB_MODEL,
) -> dict[str, str]:
    auth_key = resolve_deepl_auth_key(deepl_auth_key)
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript_en_path = out_dir / "transcript.en.srt"
    translate_srt(spanish_srt, transcript_en_path, auth_key)
    compact_english_srt_in_place(transcript_en_path)

    title_en_path = out_dir / "title.en.txt"
    if spanish_title:
        title_en = translate_text(spanish_title, auth_key)
        title_en_path.write_text(title_en + "\n", encoding="utf-8")

    description_en_path = out_dir / "description.en.txt"
    if spanish_description:
        description_en = translate_text(spanish_description, auth_key)
        description_en_path.write_text(description_en.strip() + "\n", encoding="utf-8")

    dubbed_audio_path = out_dir / "dubbed_audio.en.wav"
    dubbed_video_path = out_dir / "dubbed_video.en.mp4"
    dub_english_audio(
        video=video,
        english_srt=transcript_en_path,
        voice=voice,
        out_audio=dubbed_audio_path,
        out_video=dubbed_video_path,
        voice_text_file=voice_text_file,
        dubber_python=dubber_python or DEFAULT_DUBBER_PYTHON,
        dubber_script=dubber_script or DEFAULT_DUBBER_SCRIPT,
        model=dub_model,
    )

    result = {
        "transcript_en": str(transcript_en_path),
        "dubbed_audio_en": str(dubbed_audio_path),
        "dubbed_video_en": str(dubbed_video_path),
    }
    if title_en_path.exists():
        result["title_en"] = str(title_en_path)
    if description_en_path.exists():
        result["description_en"] = str(description_en_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare English transcript/title/description and dubbed audio.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--spanish-srt", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--voice", type=Path, required=True)
    parser.add_argument("--voice-text-file", type=Path)
    parser.add_argument("--spanish-title-file", type=Path)
    parser.add_argument("--spanish-description-file", type=Path)
    parser.add_argument("--deepl-auth-key")
    parser.add_argument("--dubber-python", type=Path, default=DEFAULT_DUBBER_PYTHON)
    parser.add_argument("--dubber-script", type=Path, default=DEFAULT_DUBBER_SCRIPT)
    parser.add_argument("--dub-model", default=DEFAULT_DUB_MODEL)
    args = parser.parse_args()

    spanish_title = None
    if args.spanish_title_file and args.spanish_title_file.exists():
        spanish_title = args.spanish_title_file.read_text(encoding="utf-8").strip()
    spanish_description = None
    if args.spanish_description_file and args.spanish_description_file.exists():
        spanish_description = args.spanish_description_file.read_text(encoding="utf-8").strip()

    result = prepare_english_assets(
        video=args.video,
        spanish_srt=args.spanish_srt,
        out_dir=args.out_dir,
        voice=args.voice,
        voice_text_file=args.voice_text_file,
        spanish_title=spanish_title,
        spanish_description=spanish_description,
        deepl_auth_key=args.deepl_auth_key,
        dubber_python=args.dubber_python,
        dubber_script=args.dubber_script,
        dub_model=args.dub_model,
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
