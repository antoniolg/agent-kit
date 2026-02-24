#!/usr/bin/env python3
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_TARGET_LUFS = -14.0
DEFAULT_TARGET_LRA = 11.0
DEFAULT_TARGET_TRUE_PEAK = -1.0
DEFAULT_LUFS_TOLERANCE = 1.0
DEFAULT_TRUE_PEAK_TOLERANCE = 0.3
DEFAULT_MAX_LRA = 9.0


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result


def has_audio_stream(video_path: Path) -> bool:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return bool(result.stdout.strip())


def _parse_loudnorm_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower() == "-inf":
            return float("-inf")
        return float(cleaned)
    raise ValueError(f"Unexpected loudnorm value type: {type(value)}")


def _parse_loudnorm_json(stderr: str) -> Dict[str, float]:
    matches = re.findall(r"\{\s*\"input_i\"[\s\S]*?\}", stderr)
    if not matches:
        raise RuntimeError("Unable to parse loudnorm JSON from ffmpeg output.")

    payload = json.loads(matches[-1])
    return {
        "input_i": _parse_loudnorm_number(payload["input_i"]),
        "input_tp": _parse_loudnorm_number(payload["input_tp"]),
        "input_lra": _parse_loudnorm_number(payload["input_lra"]),
        "input_thresh": _parse_loudnorm_number(payload["input_thresh"]),
        "target_offset": _parse_loudnorm_number(payload["target_offset"]),
    }


def analyze_loudness(
    video_path: Path,
    target_lufs: float,
    target_lra: float,
    target_true_peak: float,
) -> Dict[str, float]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(video_path),
        "-vn",
        "-sn",
        "-dn",
        "-af",
        f"loudnorm=I={target_lufs}:LRA={target_lra}:TP={target_true_peak}:print_format=json",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Loudness analysis failed: {result.stderr}")
    return _parse_loudnorm_json(result.stderr)


def evaluate_normalization_need(
    metrics: Dict[str, float],
    target_lufs: float,
    target_true_peak: float,
    max_lra: float,
    lufs_tolerance: float,
    true_peak_tolerance: float,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    input_i = metrics["input_i"]
    input_tp = metrics["input_tp"]
    input_lra = metrics["input_lra"]

    if not math.isfinite(input_i):
        reasons.append("input_i is not finite")
    elif abs(input_i - target_lufs) > lufs_tolerance:
        reasons.append(
            f"integrated loudness {input_i:.2f} LUFS outside {target_lufs:.2f}±{lufs_tolerance:.2f}"
        )

    if not math.isfinite(input_tp):
        reasons.append("input_tp is not finite")
    elif input_tp > (target_true_peak + true_peak_tolerance):
        reasons.append(
            f"true peak {input_tp:.2f} dBTP exceeds limit {(target_true_peak + true_peak_tolerance):.2f}"
        )

    if not math.isfinite(input_lra):
        reasons.append("input_lra is not finite")
    elif input_lra > max_lra:
        reasons.append(f"loudness range {input_lra:.2f} LU exceeds max {max_lra:.2f}")

    return bool(reasons), reasons


def normalize_audio_two_pass(
    video_path: Path,
    output_path: Path,
    metrics: Dict[str, float],
    target_lufs: float,
    target_lra: float,
    target_true_peak: float,
) -> None:
    filter_chain = (
        f"loudnorm=I={target_lufs}:LRA={target_lra}:TP={target_true_peak}:"
        f"measured_I={metrics['input_i']}:"
        f"measured_LRA={metrics['input_lra']}:"
        f"measured_TP={metrics['input_tp']}:"
        f"measured_thresh={metrics['input_thresh']}:"
        f"offset={metrics['target_offset']}:linear=true:print_format=summary"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-map",
        "0",
        "-c:v",
        "copy",
        "-c:s",
        "copy",
        "-af",
        filter_chain,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    _run(cmd)


def maybe_normalize_audio(
    video_path: Path,
    mode: str = "auto",
    target_lufs: float = DEFAULT_TARGET_LUFS,
    target_lra: float = DEFAULT_TARGET_LRA,
    target_true_peak: float = DEFAULT_TARGET_TRUE_PEAK,
    lufs_tolerance: float = DEFAULT_LUFS_TOLERANCE,
    true_peak_tolerance: float = DEFAULT_TRUE_PEAK_TOLERANCE,
    max_lra: float = DEFAULT_MAX_LRA,
    report_path: Optional[Path] = None,
) -> dict:
    if mode not in {"auto", "always", "off"}:
        raise ValueError("mode must be one of: auto, always, off")

    report = {
        "mode": mode,
        "target_lufs": target_lufs,
        "target_lra": target_lra,
        "target_true_peak": target_true_peak,
        "lufs_tolerance": lufs_tolerance,
        "true_peak_tolerance": true_peak_tolerance,
        "max_lra": max_lra,
        "has_audio": False,
        "normalized": False,
        "decision": "skipped",
        "detected": None,
        "reasons": [],
    }

    if mode == "off":
        report["decision"] = "skipped_mode_off"
        if report_path:
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    if not has_audio_stream(video_path):
        report["decision"] = "skipped_no_audio"
        if report_path:
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    report["has_audio"] = True
    metrics = analyze_loudness(video_path, target_lufs, target_lra, target_true_peak)
    report["detected"] = metrics

    if mode == "always":
        needs_normalization = True
        reasons = ["forced_by_mode_always"]
    else:
        needs_normalization, reasons = evaluate_normalization_need(
            metrics=metrics,
            target_lufs=target_lufs,
            target_true_peak=target_true_peak,
            max_lra=max_lra,
            lufs_tolerance=lufs_tolerance,
            true_peak_tolerance=true_peak_tolerance,
        )

    report["reasons"] = reasons

    if not needs_normalization:
        report["decision"] = "already_within_target"
        if report_path:
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    output_path = video_path.with_name(f"{video_path.stem}.audio-normalized{video_path.suffix}")
    normalize_audio_two_pass(
        video_path=video_path,
        output_path=output_path,
        metrics=metrics,
        target_lufs=target_lufs,
        target_lra=target_lra,
        target_true_peak=target_true_peak,
    )
    output_path.replace(video_path)

    report["normalized"] = True
    report["decision"] = "normalized"

    if report_path:
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
