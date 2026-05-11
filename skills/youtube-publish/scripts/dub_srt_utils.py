#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


GLOSSARY_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bcloudbot\b", "ClawdBot"),
    (r"\bclawdbot\b", "ClawdBot"),
    (r"\bcloudboat\b", "ClawdBot"),
    (r"\bjust\s*do\s*it\b", "justdoit"),
    (r"\bcloud\s+opus\b", "Claude Opus"),
    (r"\bcloud\s+code\b", "Claude Code"),
    (r"\bclaude\s+code\b", "Claude Code"),
    (r"\bopen\s*cloud\b", "OpenClaw"),
    (r"\bopenclaw\b", "OpenClaw"),
    (r"\bwhatsapp\b", "WhatsApp"),
    (r"\btelegram\b", "Telegram"),
    (r"\bgemini\b", "Gemini"),
    (r"\bgoogle\s+places\b", "Google Places"),
    (r"\bgmail\b", "Gmail"),
    (r"\bgoogle\s+sheets\b", "Google Sheets"),
    (r"\bgoogle\s+drive\b", "Google Drive"),
]


@dataclass(frozen=True)
class Cue:
    cue_id: str
    start: str
    end: str
    start_ms: int
    end_ms: int
    text: str

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


def apply_replacements(text: str, replacements: list[tuple[str, str]] | None = None) -> str:
    updated = text
    for pattern, repl in replacements or GLOSSARY_REPLACEMENTS:
        updated = re.sub(pattern, repl, updated, flags=re.IGNORECASE)
    updated = re.sub(r"\b[xX]\b", "X", updated)
    return updated


def _time_to_ms(value: str) -> int:
    h, m, s = value.replace(",", ".").split(":")
    return int((int(h) * 3600 + int(m) * 60 + float(s)) * 1000)


def _ms_to_time(value: int) -> str:
    total_ms = max(0, int(value))
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    seconds = (total_ms % 60_000) // 1_000
    millis = total_ms % 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def split_srt_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
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


def parse_srt_text(text: str) -> list[Cue]:
    cues: list[Cue] = []
    for block in split_srt_blocks(text):
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        cue_id = lines[0].strip()
        timing = lines[1].strip()
        if "-->" not in timing:
            continue
        start, end = [part.strip() for part in timing.split("-->", 1)]
        cue_text = " ".join(part.strip() for part in lines[2:] if part.strip())
        cue_text = re.sub(r"\s+", " ", cue_text).strip()
        if not cue_text:
            continue
        cues.append(
            Cue(
                cue_id=cue_id,
                start=start,
                end=end,
                start_ms=_time_to_ms(start),
                end_ms=_time_to_ms(end),
                text=cue_text,
            )
        )
    return sorted(cues, key=lambda cue: (cue.start_ms, cue.end_ms, cue.cue_id))


def cues_to_srt(cues: list[Cue]) -> str:
    blocks = []
    for idx, cue in enumerate(cues, start=1):
        blocks.append(
            "\n".join(
                [
                    str(idx),
                    f"{_ms_to_time(cue.start_ms)} --> {_ms_to_time(cue.end_ms)}",
                    cue.text.strip(),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def clean_srt_text(raw_srt_text: str) -> str:
    return apply_replacements(raw_srt_text, GLOSSARY_REPLACEMENTS)


def _split_text_for_subtitles(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text or len(text) <= max_chars:
        return [text] if text else []

    parts = re.split(r"(?<=[.!?…:;])\s+", text)
    chunks: list[str] = []
    current = ""

    def flush_words(value: str) -> None:
        words = value.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and len(candidate) > max_chars:
                chunks.append(line)
                line = word
            else:
                line = candidate
        if line:
            chunks.append(line)

    for part in parts:
        candidate = f"{current} {part}".strip()
        if current and len(candidate) > max_chars:
            flush_words(current)
            current = part
        else:
            current = candidate

    if current:
        flush_words(current)
    return chunks


def resegment_cues_for_subtitles(
    cues: list[Cue],
    *,
    max_chars: int = 88,
    max_duration_ms: int = 5200,
    min_duration_ms: int = 900,
) -> list[Cue]:
    readable: list[Cue] = []

    for cue in cues:
        if len(cue.text) <= max_chars and cue.duration_ms <= max_duration_ms:
            readable.append(cue)
            continue

        by_text = _split_text_for_subtitles(cue.text, max_chars)
        if not by_text:
            continue

        estimated_parts = max(1, round(cue.duration_ms / max_duration_ms))
        part_count = max(len(by_text), estimated_parts)
        if part_count <= 1:
            readable.append(cue)
            continue

        if len(by_text) < part_count:
            by_text = _split_text_for_subtitles(cue.text, max(38, max_chars // 2))
            part_count = max(len(by_text), estimated_parts)

        start_ms = cue.start_ms
        cue_end_ms = cue.end_ms
        span_ms = cue_end_ms - start_ms

        for index, text_part in enumerate(by_text):
            part_start = start_ms + round(span_ms * index / len(by_text))
            part_end = start_ms + round(span_ms * (index + 1) / len(by_text))
            if (
                part_end - part_start < min_duration_ms
                and index < len(by_text) - 1
                and part_start + min_duration_ms < cue_end_ms
            ):
                part_end = part_start + min_duration_ms
            readable.append(
                Cue(
                    cue_id=cue.cue_id,
                    start=_ms_to_time(part_start),
                    end=_ms_to_time(part_end),
                    start_ms=part_start,
                    end_ms=part_end,
                    text=text_part,
                )
            )

    return readable


def _ends_with_strong_punctuation(text: str) -> bool:
    return bool(re.search(r"[.!?…:;][\"')\]]*$", text.strip()))


def _merge_text(left: str, right: str) -> str:
    left = left.strip()
    right = right.strip()
    if not left:
        return right
    if not right:
        return left
    separator = " "
    if left.endswith("-"):
        separator = ""
    return re.sub(r"\s+", " ", f"{left}{separator}{right}").strip()


def resegment_cues_for_dubbing(
    cues: list[Cue],
    *,
    min_segment_ms: int = 3200,
    target_segment_ms: int = 7600,
    max_segment_ms: int = 12000,
    max_pause_merge_ms: int = 350,
    min_text_chars: int = 48,
) -> list[Cue]:
    if not cues:
        return []

    grouped: list[Cue] = []
    current = cues[0]

    for cue in cues[1:]:
        pause_ms = max(0, cue.start_ms - current.end_ms)
        merged_duration_ms = cue.end_ms - current.start_ms
        has_overlap = cue.start_ms < current.end_ms
        current_short = current.duration_ms < min_segment_ms or len(current.text) < min_text_chars
        cue_short = cue.duration_ms < min_segment_ms // 2 or len(cue.text) < min_text_chars // 2
        strong_stop = _ends_with_strong_punctuation(current.text)
        should_merge = (
            has_overlap
            or (
                pause_ms <= max_pause_merge_ms
                and merged_duration_ms <= max_segment_ms
                and (
                    current_short
                    or cue_short
                    or not strong_stop
                    or current.duration_ms < target_segment_ms
                )
            )
        )

        if should_merge and merged_duration_ms <= max_segment_ms:
            current = Cue(
                cue_id=current.cue_id,
                start=current.start,
                end=_ms_to_time(max(current.end_ms, cue.end_ms)),
                start_ms=current.start_ms,
                end_ms=max(current.end_ms, cue.end_ms),
                text=_merge_text(current.text, cue.text),
            )
            continue

        if has_overlap:
            adjusted_start_ms = max(current.end_ms, cue.start_ms)
            current = Cue(
                cue_id=current.cue_id,
                start=current.start,
                end=current.end,
                start_ms=current.start_ms,
                end_ms=current.end_ms,
                text=current.text,
            )
            cue = Cue(
                cue_id=cue.cue_id,
                start=_ms_to_time(adjusted_start_ms),
                end=cue.end,
                start_ms=adjusted_start_ms,
                end_ms=max(adjusted_start_ms, cue.end_ms),
                text=cue.text,
            )

        should_merge = (
            pause_ms <= max_pause_merge_ms
            and merged_duration_ms <= max_segment_ms
            and (
                current_short
                or cue_short
                or not strong_stop
                or current.duration_ms < target_segment_ms
            )
        )

        if should_merge:
            current = Cue(
                cue_id=current.cue_id,
                start=current.start,
                end=_ms_to_time(cue.end_ms),
                start_ms=current.start_ms,
                end_ms=cue.end_ms,
                text=_merge_text(current.text, cue.text),
            )
            continue

        grouped.append(current)
        current = cue

    grouped.append(current)
    return grouped


def write_cleaned_and_dub_srt(raw_srt_path: Path, out_dir: Path) -> tuple[Path, Path]:
    raw_text = raw_srt_path.read_text(encoding="utf-8")
    cleaned_text = clean_srt_text(raw_text)
    cleaned_cues = parse_srt_text(cleaned_text)
    subtitle_cues = resegment_cues_for_subtitles(cleaned_cues)

    cleaned_path = out_dir / "transcript.es.cleaned.srt"
    cleaned_path.write_text(cues_to_srt(subtitle_cues), encoding="utf-8")

    dub_cues = resegment_cues_for_dubbing(cleaned_cues)
    dub_path = out_dir / "transcript.es.dub.srt"
    dub_path.write_text(cues_to_srt(dub_cues), encoding="utf-8")
    return cleaned_path, dub_path
