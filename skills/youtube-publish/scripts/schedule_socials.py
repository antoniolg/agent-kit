#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from urllib.parse import urlsplit, urlunsplit

SKILLS_CONFIG_PATH = os.path.expanduser("~/.config/skills/config.json")


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def upload_image(path):
    if not path:
        return None
    raw = run(["postiz", "upload", "--file-path", path])
    data = json.loads(raw)
    for key in ["url", "public_url", "publicUrl", "path"]:
        if key in data:
            return data[key]
    if "file" in data:
        file_obj = data["file"]
        for key in ["url", "public_url", "publicUrl", "path"]:
            if key in file_obj:
                return file_obj[key]
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


def parse_integrations(raw: str) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def resolve_integration_id(key: str, integrations: dict) -> str | None:
    if key in integrations:
        value = integrations.get(key)
        if isinstance(value, dict):
            return value.get("id") or None
        if isinstance(value, str):
            return value
    return key or None


def resolve_group_integrations(group_name: str, postiz: dict) -> list[str]:
    groups = postiz.get("groups", {})
    if not isinstance(groups, dict):
        return []
    group = groups.get(group_name, [])
    if not isinstance(group, list):
        return []
    integrations = postiz.get("integrations", {})
    resolved = []
    for item in group:
        if not isinstance(item, str):
            continue
        integration_id = resolve_integration_id(item, integrations)
        if integration_id:
            resolved.append(integration_id)
    return resolved


def filter_out_x_integrations(integration_ids: list[str], postiz_cfg: dict) -> list[str]:
    """
    Always exclude X integrations for youtube_publish.
    """
    integrations_cfg = postiz_cfg.get("integrations", {})
    if not isinstance(integrations_cfg, dict):
        return integration_ids

    known_x_ids = set()
    for key, value in integrations_cfg.items():
        if isinstance(value, dict):
            network = str(value.get("network", "")).strip().lower()
            integration_id = str(value.get("id", "")).strip()
            if network == "x" and integration_id:
                known_x_ids.add(integration_id)
        if isinstance(key, str) and key.lower().startswith("x"):
            if isinstance(value, dict):
                integration_id = str(value.get("id", "")).strip()
                if integration_id:
                    known_x_ids.add(integration_id)
            elif isinstance(value, str) and value.strip():
                known_x_ids.add(value.strip())

    return [integration_id for integration_id in integration_ids if integration_id not in known_x_ids]


def encode_underscores_in_url(url: str) -> str:
    """
    Some platforms (notably LinkedIn via Postiz) can mangle URLs that contain
    underscores (e.g. treat them as formatting markers). Percent-encoding
    underscores keeps the URL valid and avoids that formatting issue.
    """
    if not url:
        return url
    parts = urlsplit(url)
    rebuilt = urlunsplit(parts)
    return rebuilt.replace("_", "%5F")


def main():
    parser = argparse.ArgumentParser(description="Schedule socials via Postiz CLI")
    parser.add_argument("--text-file", required=True, help="Path to post text")
    parser.add_argument("--scheduled-date", required=True, help="ISO 8601 datetime with offset")
    parser.add_argument("--comment-url", required=True, help="URL for first comment")
    parser.add_argument("--image", help="Thumbnail image path")
    parser.add_argument("--integrations", help="Comma-separated Postiz integration IDs")
    parser.add_argument("--group", help="Postiz group name from config (default: youtube_publish)")
    parser.add_argument("--comment-text", default="🎥 Tienes el vídeo completo y la explicación técnica aquí:", help="Text prefix for the comment link")
    args = parser.parse_args()

    skills_cfg = load_skills_config()
    postiz_cfg = skills_cfg.get("postiz", {})
    yt_cfg = skills_cfg.get("youtube_publish", {})
    group_name = args.group or yt_cfg.get("postiz_group") or "youtube_publish"

    integrations = parse_integrations(args.integrations)
    if not integrations:
        integrations = resolve_group_integrations(group_name, postiz_cfg)
    if not integrations:
        integrations = yt_cfg.get("postiz_integrations", [])
    if not integrations:
        raise SystemExit(
            "Missing Postiz integrations (pass --integrations or set postiz.groups/postiz.integrations "
            "in ~/.config/skills/config.json)"
        )
    integrations = filter_out_x_integrations(integrations, postiz_cfg)
    if not integrations:
        raise SystemExit("No social integrations left after excluding X.")

    text = open(args.text_file, "r", encoding="utf-8").read().strip()
    if "#" in text:
        text = text.replace("#", "")

    image_url = upload_image(args.image) if args.image else None

    # Postiz CLI expects --content multiple times to build a thread.
    safe_comment_url = encode_underscores_in_url(args.comment_url)
    comment_content = f"{args.comment_text} {safe_comment_url}"
    content_args = ["--content", text, "--content", comment_content]

    for integration_id in integrations:
        cmd = [
            "postiz",
            "posts",
            "create",
            *content_args,
            "--integrations",
            integration_id,
            "--status",
            "scheduled",
            "--scheduled-date",
            args.scheduled_date,
        ]
        if image_url:
            cmd += ["--images", image_url]
        run(cmd)

    print("Scheduled socials.")


if __name__ == "__main__":
    main()
