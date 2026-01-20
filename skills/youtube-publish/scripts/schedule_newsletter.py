#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

SKILLS_CONFIG_PATH = os.path.expanduser("~/.config/skills/config.json")
DEV_PREFIX = "🧑‍💻 [DEV]"


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def extract_campaign_id(output: str) -> int:
    # Expected output from listmonk CLI: "Created campaign 123 (Name) ..."
    match = re.search(r"Created campaign\s+(\d+)", output)
    if match:
        return int(match.group(1))
    # Fallback: try to parse a JSON response containing id
    try:
        data = json.loads(output)
        if isinstance(data, dict):
            if "id" in data:
                return int(data["id"])
            if "data" in data and isinstance(data["data"], dict) and "id" in data["data"]:
                return int(data["data"]["id"])
    except json.JSONDecodeError:
        pass
    raise RuntimeError(f"Could not extract campaign id from output: {output}")


def ensure_dev_prefix(value: str) -> str:
    raw = value.strip()
    if raw.startswith(DEV_PREFIX):
        return raw
    return f"{DEV_PREFIX} {raw}"


def load_skills_config() -> dict:
    try:
        with open(SKILLS_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def main():
    parser = argparse.ArgumentParser(description="Schedule newsletter via Listmonk CLI")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body-file", required=True, help="Markdown body file")
    parser.add_argument("--send-at", required=True, help="ISO 8601 datetime with offset")
    parser.add_argument("--name", required=True, help="Campaign name")
    parser.add_argument("--list-id", type=int, help="Listmonk list ID")
    args = parser.parse_args()

    config = load_skills_config().get("youtube_publish", {})
    list_id = args.list_id or config.get("listmonk_list_id")
    if not list_id:
        raise SystemExit(
            "Missing list id (pass --list-id or set youtube_publish.listmonk_list_id in "
            "~/.config/skills/config.json)"
        )

    body_path = Path(args.body_file)
    body = body_path.read_text(encoding="utf-8").strip()
    tmp_path = body_path.parent / "newsletter.scheduled.md"
    tmp_path.write_text(body, encoding="utf-8")

    name = ensure_dev_prefix(args.name)
    subject = ensure_dev_prefix(args.subject)

    cmd = [
        "listmonk",
        "campaigns",
        "create",
        "--name",
        name,
        "--subject",
        subject,
        "--lists",
        str(list_id),
        "--body-file",
        str(tmp_path),
        "--content-type",
        "markdown",
        "--send-at",
        args.send_at,
    ]
    create_output = run(cmd)
    campaign_id = extract_campaign_id(create_output)

    schedule_cmd = [
        "listmonk",
        "campaigns",
        "schedule",
        str(campaign_id),
        "--status",
        "scheduled",
    ]
    run(schedule_cmd)
    print(f"Scheduled newsletter (campaign {campaign_id}).")


if __name__ == "__main__":
    main()
