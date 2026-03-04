#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from urllib.parse import urlsplit, urlunsplit

SKILLS_CONFIG_PATH = os.path.expanduser("~/.config/skills/config.json")


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def detect_media_kind(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".mp4", ".mov", ".mkv", ".webm"}:
        return "video"
    return "image"


def upload_media(path: str) -> str | None:
    if not path:
        return None
    raw = run(
        [
            "postflow",
            "--json",
            "media",
            "upload",
            "--file",
            path,
            "--kind",
            detect_media_kind(path),
        ]
    )
    data = json.loads(raw)
    if isinstance(data, dict):
        media_id = data.get("id")
        if isinstance(media_id, str) and media_id:
            return media_id
    return None


def load_skills_config() -> dict:
    try:
        with open(SKILLS_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def parse_csv(raw: str) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def load_connected_accounts() -> list[dict]:
    raw = run(["postflow", "--json", "accounts", "list"])
    data = json.loads(raw)
    if not isinstance(data, dict):
        return []
    items = data.get("items", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def build_platform_map(accounts: list[dict]) -> dict[str, list[str]]:
    platform_map: dict[str, list[str]] = {}
    for item in accounts:
        account_id = str(item.get("id", "")).strip()
        platform = str(item.get("platform", "")).strip().lower()
        status = str(item.get("status", "connected")).strip().lower()
        if not account_id or not platform or status != "connected":
            continue
        if platform not in platform_map:
            platform_map[platform] = []
        platform_map[platform].append(account_id)
    return platform_map


def resolve_account_id(key: str, accounts_cfg: dict, platform_map: dict[str, list[str]]) -> str | None:
    if key in accounts_cfg:
        value = accounts_cfg.get(key)
        if isinstance(value, dict):
            return value.get("id") or None
        if isinstance(value, str):
            return value
    if key.startswith("acc_"):
        return key
    alias = key.split("-")[0].strip().lower()
    candidates = platform_map.get(alias, [])
    if candidates:
        return candidates[0]
    return None


def unique(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def resolve_account_list(raw_items: list[str], accounts_cfg: dict, platform_map: dict[str, list[str]]) -> list[str]:
    resolved = []
    for item in raw_items:
        key = item.strip()
        if not key:
            continue
        account_id = resolve_account_id(key, accounts_cfg, platform_map)
        if account_id:
            resolved.append(account_id)
    return unique(resolved)


def resolve_group_accounts(group_name: str, postflow_cfg: dict, platform_map: dict[str, list[str]]) -> list[str]:
    groups = postflow_cfg.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}

    group = groups.get(group_name, [])
    if not isinstance(group, list):
        group = []

    accounts_cfg = postflow_cfg.get("accounts", {})
    if not isinstance(accounts_cfg, dict):
        accounts_cfg = {}
    return resolve_account_list(group, accounts_cfg, platform_map)


def filter_out_x_accounts(account_ids: list[str], postflow_cfg: dict, platform_map: dict[str, list[str]]) -> list[str]:
    x_ids = set(platform_map.get("x", []))

    accounts_cfg = postflow_cfg.get("accounts", {})
    if isinstance(accounts_cfg, dict):
        for key, value in accounts_cfg.items():
            if isinstance(value, dict):
                platform = str(value.get("platform", "")).strip().lower()
                account_id = str(value.get("id", "")).strip()
                if platform == "x" and account_id:
                    x_ids.add(account_id)
            if isinstance(key, str) and key.lower().startswith("x"):
                if isinstance(value, str) and value.strip():
                    x_ids.add(value.strip())
                if isinstance(value, dict):
                    account_id = str(value.get("id", "")).strip()
                    if account_id:
                        x_ids.add(account_id)

    return [account_id for account_id in unique(account_ids) if account_id not in x_ids]


def encode_underscores_in_url(url: str) -> str:
    """
    Some platforms (notably LinkedIn) can mangle URLs that contain
    underscores (e.g. treat them as formatting markers). Percent-encoding
    underscores keeps the URL valid and avoids that formatting issue.
    """
    if not url:
        return url
    parts = urlsplit(url)
    rebuilt = urlunsplit(parts)
    return rebuilt.replace("_", "%5F")


def main():
    parser = argparse.ArgumentParser(description="Schedule socials via PostFlow CLI")
    parser.add_argument("--text-file", required=True, help="Path to post text")
    parser.add_argument("--scheduled-date", required=True, help="ISO 8601 datetime with offset")
    parser.add_argument("--comment-url", required=True, help="URL for first comment")
    parser.add_argument("--image", help="Thumbnail image path")
    parser.add_argument("--accounts", help="Comma-separated PostFlow account IDs or aliases")
    parser.add_argument("--group", help="PostFlow group name from config (default: youtube_publish)")
    parser.add_argument("--comment-text", default="🎥 Tienes el vídeo completo y la explicación técnica aquí:", help="Text prefix for the comment link")
    args = parser.parse_args()

    skills_cfg = load_skills_config()
    postflow_cfg = skills_cfg.get("postflow", {})
    if not isinstance(postflow_cfg, dict):
        postflow_cfg = {}
    yt_cfg = skills_cfg.get("youtube_publish", {})
    if not isinstance(yt_cfg, dict):
        yt_cfg = {}
    group_name = args.group or yt_cfg.get("postflow_group") or "youtube_publish"

    connected_accounts = load_connected_accounts()
    platform_map = build_platform_map(connected_accounts)
    accounts_cfg = postflow_cfg.get("accounts", {})
    if not isinstance(accounts_cfg, dict):
        accounts_cfg = {}

    accounts = resolve_account_list(parse_csv(args.accounts), accounts_cfg, platform_map)
    if not accounts:
        accounts = resolve_group_accounts(group_name, postflow_cfg, platform_map)
    if not accounts:
        raw_accounts = yt_cfg.get("postflow_accounts", [])
        if isinstance(raw_accounts, list):
            parsed = [str(item) for item in raw_accounts if isinstance(item, (str, int))]
            accounts = resolve_account_list(parsed, accounts_cfg, platform_map)
    if not accounts and platform_map:
        all_connected = []
        for ids in platform_map.values():
            all_connected.extend(ids)
        accounts = unique(all_connected)

    if not accounts:
        raise SystemExit(
            "Missing PostFlow accounts (pass --accounts or set postflow.groups/postflow.accounts "
            "in ~/.config/skills/config.json)"
        )

    accounts = filter_out_x_accounts(accounts, postflow_cfg, platform_map)
    if not accounts:
        raise SystemExit("No social accounts left after excluding X.")

    text = open(args.text_file, "r", encoding="utf-8").read().strip()
    if "#" in text:
        text = text.replace("#", "")

    media_id = upload_media(args.image) if args.image else None

    safe_comment_url = encode_underscores_in_url(args.comment_url)
    comment_content = f"{args.comment_text} {safe_comment_url}"
    segments_json = json.dumps([{"text": text}, {"text": comment_content}], ensure_ascii=False)

    for account_id in accounts:
        cmd = [
            "postflow",
            "posts",
            "create",
            "--account-id",
            account_id,
            "--segments-json",
            segments_json,
            "--scheduled-at",
            args.scheduled_date,
        ]
        if media_id:
            cmd += ["--media-id", media_id]
        run(cmd)

    print("Scheduled socials.")


if __name__ == "__main__":
    main()
