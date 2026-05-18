#!/usr/bin/env python3
"""Check whether a weekly Listmonk newsletter already exists for a send date."""

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date


MONTHS_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def load_base_url() -> str:
    if os.environ.get("LISTMONK_BASE_URL"):
        return os.environ["LISTMONK_BASE_URL"].rstrip("/")

    config_path = os.path.expanduser("~/.config/skills/config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg["listmonk"]["base_url"].rstrip("/")
    except Exception:
        return "https://listmonk.antonioleiva.com"


def request_json(base_url: str, username: str, api_key: str, path: str) -> dict:
    req = urllib.request.Request(base_url + path)
    auth = base64.b64encode(f"{username}:{api_key}".encode()).decode()
    req.add_header("Authorization", "Basic " + auth)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def campaign_matches(campaign: dict, target: date) -> bool:
    name = (campaign.get("name") or "").casefold()
    if "newsletter semanal" not in name:
        return False

    labels = [
        f"{target.day} {MONTHS_ES[target.month]} {target.year}",
        f"{target.day} de {MONTHS_ES[target.month]} de {target.year}",
        target.isoformat(),
    ]
    if any(label.casefold() in name for label in labels):
        return True

    # Scheduled/sent campaigns may expose different timestamp fields depending on Listmonk version.
    for key in ("send_at", "scheduled_at", "started_at"):
        value = campaign.get(key)
        if isinstance(value, str) and value.startswith(target.isoformat()):
            return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True, help="Send date to check, YYYY-MM-DD")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--fail-if-found", action="store_true", help="Exit 10 when a matching campaign exists")
    args = parser.parse_args()

    target = date.fromisoformat(args.target_date)
    username = os.environ.get("LISTMONK_USERNAME")
    api_key = os.environ.get("LISTMONK_API_KEY")
    if not username or not api_key:
        print("Missing LISTMONK_USERNAME or LISTMONK_API_KEY", file=sys.stderr)
        return 2

    base_url = load_base_url()
    matches = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        payload = request_json(base_url, username, api_key, f"/api/campaigns?{query}")
        data = payload.get("data", payload)
        results = data.get("results") or []
        matches.extend(c for c in results if campaign_matches(c, target))

        total = data.get("total") or 0
        if not results or page * 100 >= total:
            break
        page += 1

    simplified = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "subject": c.get("subject"),
            "status": c.get("status"),
            "started_at": c.get("started_at"),
            "updated_at": c.get("updated_at"),
        }
        for c in matches
    ]

    if args.json:
        print(json.dumps({"target_date": target.isoformat(), "exists": bool(matches), "campaigns": simplified}, ensure_ascii=False, indent=2))
    elif matches:
        print(f"Existing newsletter campaign(s) for {target.isoformat()}:")
        for c in simplified:
            print(f"- #{c['id']} {c['name']} | {c['subject']}")
    else:
        print(f"No existing newsletter campaign for {target.isoformat()}.")

    if matches and args.fail_if_found:
        return 10
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
