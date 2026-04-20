#!/usr/bin/env python3
"""Publish an already-finalized X repost through PostFlow.

This helper assumes the hard work is already done:
- the text is final and should be kept verbatim
- the quote image, if any, is already rendered and approved
- the destination account IDs are already resolved
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or publish a repost across one or more PostFlow accounts."
    )
    parser.add_argument(
        "--text",
        help="Exact post text. Kept verbatim.",
    )
    parser.add_argument(
        "--text-file",
        type=Path,
        help="Path to a file containing the exact post text.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Optional image to upload and attach.",
    )
    parser.add_argument(
        "--account-id",
        action="append",
        dest="account_ids",
        required=True,
        help="PostFlow account ID. Repeat for multiple destinations.",
    )
    parser.add_argument(
        "--mode",
        choices=("draft", "schedule", "publish-now"),
        default="draft",
        help="Publication mode.",
    )
    parser.add_argument(
        "--scheduled-at",
        help="RFC3339 datetime required when --mode schedule is used.",
    )
    parser.add_argument(
        "--idempotency-key-prefix",
        default="x-republish",
        help="Prefix used to build deterministic idempotency keys.",
    )
    parser.add_argument(
        "--postflow-cmd",
        help="Exact PostFlow command to run, for example 'postflow' or 'go run ./cmd/postflow'.",
    )
    parser.add_argument(
        "--postflow-dir",
        type=Path,
        help="Optional PostFlow repo directory. Useful with 'go run ./cmd/postflow'.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=0,
        help="Optional PostFlow max publish retries.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without creating, uploading, or publishing anything.",
    )
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if bool(args.text) == bool(args.text_file):
        raise SystemExit("provide exactly one of --text or --text-file")
    if args.text_file:
        return args.text_file.read_text(encoding="utf-8")
    return args.text


def resolve_postflow_cmd(args: argparse.Namespace) -> list[str]:
    if args.postflow_cmd:
        return shlex.split(args.postflow_cmd)
    if args.postflow_dir:
        return ["go", "run", "./cmd/postflow"]
    return ["postflow"]


def command_cwd(args: argparse.Namespace) -> str | None:
    if not args.postflow_dir:
        return None
    return str(args.postflow_dir)


def run_command(
    base_cmd: list[str],
    extra_args: list[str],
    cwd: str | None,
    expect_json: bool = False,
) -> dict | str:
    command = base_cmd + extra_args
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise RuntimeError(message)
    stdout = result.stdout.strip()
    if expect_json:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"expected JSON output, got: {stdout}") from exc
    return stdout


def build_idempotency_key(
    prefix: str,
    account_id: str,
    mode: str,
    scheduled_at: str | None,
    text: str,
    image_path: Path | None,
) -> str:
    digest = hashlib.sha256()
    digest.update(text.encode("utf-8"))
    digest.update(account_id.encode("utf-8"))
    digest.update(mode.encode("utf-8"))
    digest.update((scheduled_at or "").encode("utf-8"))
    digest.update(str(image_path or "").encode("utf-8"))
    return f"{prefix}:{mode}:{account_id}:{digest.hexdigest()[:12]}"


def upload_media(
    args: argparse.Namespace,
    base_cmd: list[str],
    cwd: str | None,
) -> str | None:
    if not args.image:
        return None
    if args.dry_run:
        return "dry_run_media"
    output = run_command(
        base_cmd,
        ["--json", "media", "upload", "--file", str(args.image), "--kind", "image"],
        cwd,
        expect_json=True,
    )
    media_id = str(output.get("id", "")).strip()
    if not media_id:
        raise RuntimeError(f"media upload returned no id: {output}")
    return media_id


def validate_post(
    base_cmd: list[str],
    cwd: str | None,
    account_id: str,
    text: str,
    media_id: str | None,
    scheduled_at: str | None,
    max_attempts: int,
) -> None:
    cmd = [
        "--json",
        "posts",
        "validate",
        "--account-id",
        account_id,
        "--text",
        text,
    ]
    if media_id:
        cmd.extend(["--media-id", media_id])
    if scheduled_at:
        cmd.extend(["--scheduled-at", scheduled_at])
    if max_attempts > 0:
        cmd.extend(["--max-attempts", str(max_attempts)])
    output = run_command(base_cmd, cmd, cwd, expect_json=True)
    if output.get("valid") is not True:
        raise RuntimeError(f"validation failed for {account_id}: {output}")


def create_post(
    base_cmd: list[str],
    cwd: str | None,
    account_id: str,
    text: str,
    media_id: str | None,
    scheduled_at: str | None,
    idempotency_key: str,
    max_attempts: int,
) -> dict:
    cmd = [
        "--json",
        "posts",
        "create",
        "--account-id",
        account_id,
        "--text",
        text,
        "--idempotency-key",
        idempotency_key,
    ]
    if media_id:
        cmd.extend(["--media-id", media_id])
    if scheduled_at:
        cmd.extend(["--scheduled-at", scheduled_at])
    if max_attempts > 0:
        cmd.extend(["--max-attempts", str(max_attempts)])
    return run_command(base_cmd, cmd, cwd, expect_json=True)


def publish_now(
    base_cmd: list[str],
    cwd: str | None,
    post_id: str,
    text: str,
) -> None:
    run_command(
        base_cmd,
        [
            "posts",
            "edit",
            "--id",
            post_id,
            "--text",
            text,
            "--intent",
            "publish_now",
        ],
        cwd,
        expect_json=False,
    )


def main() -> int:
    args = parse_args()
    text = load_text(args)
    if args.mode == "schedule" and not args.scheduled_at:
        raise SystemExit("--scheduled-at is required when --mode schedule is used")
    if args.mode != "schedule" and args.scheduled_at:
        raise SystemExit("--scheduled-at is only valid with --mode schedule")
    if args.image and not args.image.exists():
        raise SystemExit(f"image not found: {args.image}")

    base_cmd = resolve_postflow_cmd(args)
    cwd = command_cwd(args)

    if args.dry_run:
        summary = {
            "mode": args.mode,
            "scheduled_at": args.scheduled_at,
            "account_ids": args.account_ids,
            "image": str(args.image) if args.image else None,
            "text_length": len(text),
            "postflow_cmd": base_cmd,
            "cwd": cwd,
        }
        print(json.dumps(summary, indent=2))
        return 0

    media_id = upload_media(args, base_cmd, cwd)
    results: list[dict[str, str | None]] = []

    for account_id in args.account_ids:
        scheduled_at = args.scheduled_at if args.mode == "schedule" else None
        validate_post(
            base_cmd,
            cwd,
            account_id,
            text,
            media_id,
            scheduled_at,
            args.max_attempts,
        )
        idempotency_key = build_idempotency_key(
            args.idempotency_key_prefix,
            account_id,
            args.mode,
            scheduled_at,
            text,
            args.image,
        )
        created = create_post(
            base_cmd,
            cwd,
            account_id,
            text,
            media_id,
            scheduled_at,
            idempotency_key,
            args.max_attempts,
        )
        post_id = str(created.get("id", "")).strip()
        status = str(created.get("status", "")).strip()
        if not post_id:
            raise RuntimeError(f"create returned no post id for {account_id}: {created}")
        if args.mode == "publish-now":
            publish_now(base_cmd, cwd, post_id, text)
            status = "publish_now_requested"
        results.append(
            {
                "account_id": account_id,
                "post_id": post_id,
                "status": status,
                "media_id": media_id,
                "idempotency_key": idempotency_key,
            }
        )

    print(json.dumps({"results": results}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
