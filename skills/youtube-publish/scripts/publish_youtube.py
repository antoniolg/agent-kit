#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

import yaml
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/youtube-publish/config.yaml")
DEFAULT_TOKEN_PATH = os.path.expanduser("~/.config/youtube-publish/token.json")
DEFAULT_PROMO_LINE = "Domina la IA para el desarrollo de Software 👉 https://devexpert.io/cursos/expert/ai"
YOUTUBE_WATCH_URL = "https://www.youtube.com/watch?v="
YOUTUBE_SHORT_URL = "https://youtu.be/"


def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return data or {}


def resolve_promo_line(config: dict) -> str:
    env_line = os.environ.get("YOUTUBE_PROMO_LINE")
    cfg_line = config.get("promo_line") if isinstance(config, dict) else None
    return (env_line or cfg_line or DEFAULT_PROMO_LINE or "").strip()


def resolve_promo_comment(config: dict, promo_line: str) -> str:
    env_comment = os.environ.get("YOUTUBE_PROMO_COMMENT")
    cfg_comment = config.get("promo_comment") if isinstance(config, dict) else None
    return (env_comment or cfg_comment or promo_line or "").strip()


def ensure_promo_in_description(description: str, promo_line: str) -> str:
    if not promo_line:
        return description
    desc = description.strip()
    if desc.startswith(promo_line):
        return description
    return f"{promo_line}\n\n{description}"


def strip_self_video_url(description: str, video_id: str | None) -> str:
    if not video_id:
        return description
    urls = [
        f"{YOUTUBE_WATCH_URL}{video_id}",
        f"{YOUTUBE_SHORT_URL}{video_id}",
    ]
    cleaned = description
    for url in urls:
        cleaned = cleaned.replace(url, "")
    cleaned = re.sub(r"\[([^\]]*)\]\(\s*\)", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


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


def parse_publish_at(value: str, tz_name: str) -> str:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("publish-at must be ISO format: YYYY-MM-DD HH:MM")
    if dt.tzinfo is None:
        if ZoneInfo is None:
            raise ValueError("ZoneInfo not available; use Python 3.9+ or provide timezone offset")
        dt = dt.replace(tzinfo=ZoneInfo(tz_name))
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_authenticated_service(client_secret_path: str, token_path: str):
    creds = None
    token_file = Path(token_path)
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                prompt="consent",
            )
            print("Open this URL in your browser, approve access, then paste the final URL:")
            print(auth_url)
            redirect_response = input("Paste full redirect URL: ").strip()
            flow.fetch_token(authorization_response=redirect_response)
            creds = flow.credentials
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, video_path: str, body: dict, thumbnail_path: str = None, notify_subscribers: bool = False):
    media = MediaFileUpload(video_path, chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=notify_subscribers,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            percent = int(status.progress() * 100)
            print(f"Upload {percent}%")

    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("Upload failed: missing video id")

    if thumbnail_path:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path),
        ).execute()

    return video_id


def persist_output_video_id(output_video_id_path: str | None, video_id: str) -> None:
    if not output_video_id_path:
        return
    Path(output_video_id_path).write_text(video_id, encoding="utf-8")


def insert_promo_comment(youtube, video_id: str, comment_text: str):
    if not comment_text:
        return
    text = comment_text.strip()
    if not text:
        return
    # Avoid duplicate promo comments when re-running.
    try:
        existing = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=20,
            order="time",
        ).execute()
        for item in existing.get("items", []):
            top = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            existing_text = (top.get("textOriginal") or "").strip()
            if existing_text == text:
                print("Promo comment already exists; skipping.")
                return
    except Exception as exc:
        print(f"Warning: could not list comments before insert: {exc}", file=sys.stderr)

    try:
        youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {"snippet": {"textOriginal": text}},
                }
            },
        ).execute()
        print("Inserted promo comment.")
    except Exception as exc:
        print(
            f"Warning: could not insert promo comment (continuing): {exc}",
            file=sys.stderr,
        )


def main():
    parser = argparse.ArgumentParser(description="Upload and schedule a YouTube video")
    parser.add_argument("--video", help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", help="Video description")
    parser.add_argument("--description-file", help="Path to description text file")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--category-id", help="YouTube category id")
    parser.add_argument("--privacy-status", help="private|unlisted|public")
    parser.add_argument("--publish-at", help="Local time: YYYY-MM-DD HH:MM")
    parser.add_argument("--timezone", help="IANA timezone, default from config")
    parser.add_argument("--thumbnail", help="Path to thumbnail image")
    parser.add_argument("--update-video-id", help="Update an existing video id instead of uploading")
    parser.add_argument("--output-video-id", help="Write uploaded video id to this file")
    parser.add_argument("--notify-subscribers", action="store_true", help="Notify subscribers on publish")
    parser.add_argument("--no-notify-subscribers", action="store_true", help="Do not notify subscribers")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Config path")
    parser.add_argument("--client-secret", required=True, help="OAuth client secret JSON")
    parser.add_argument("--token", default=DEFAULT_TOKEN_PATH, help="Token cache path")
    args = parser.parse_args()

    config = load_config(args.config)
    promo_line = resolve_promo_line(config)
    promo_comment = resolve_promo_comment(config, promo_line)

    if not args.update_video_id:
        if not args.video:
            print("Video is required for upload", file=sys.stderr)
            sys.exit(1)
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"Video not found: {video_path}", file=sys.stderr)
            sys.exit(1)
    else:
        video_path = Path(args.video) if args.video else None

    description = args.description
    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8").strip()
    if not description:
        print("Description is required (use --description or --description-file)", file=sys.stderr)
        sys.exit(1)
    description = ensure_promo_in_description(description, promo_line)
    description = strip_self_video_url(description, args.update_video_id)

    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    elif isinstance(config.get("tags"), list):
        tags = config.get("tags")
    elif isinstance(config.get("tags"), str):
        tags = [t.strip() for t in config.get("tags").split(",") if t.strip()]

    publish_at = None
    if args.publish_at:
        timezone_name = args.timezone or config.get("timezone") or detect_system_timezone()
        if not timezone_name:
            raise ValueError("Timezone is required for publish-at (pass --timezone or set config)")
        publish_at = parse_publish_at(args.publish_at, timezone_name)

    # Process rule: always end in private (or scheduled private if publish_at is set).
    # We intentionally do not publish directly from this scripted flow.
    privacy_status = "private"

    category_id = args.category_id or config.get("category_id") or "27"
    made_for_kids = bool(config.get("made_for_kids", False))
    notify_subscribers = bool(config.get("notify_subscribers", False))
    if args.notify_subscribers:
        notify_subscribers = True
    if args.no_notify_subscribers:
        notify_subscribers = False
    default_language = config.get("default_language")
    default_audio_language = config.get("default_audio_language")

    snippet = {
        "title": args.title,
        "description": description,
    }
    if tags:
        snippet["tags"] = tags
    if category_id:
        snippet["categoryId"] = str(category_id)
    if default_language:
        snippet["defaultLanguage"] = default_language
    if default_audio_language:
        snippet["defaultAudioLanguage"] = default_audio_language

    status = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": made_for_kids,
    }
    if publish_at:
        status["publishAt"] = publish_at

    body = {
        "snippet": snippet,
        "status": status,
    }

    if not Path(args.client_secret).exists():
        print(f"Missing client secret: {args.client_secret}", file=sys.stderr)
        sys.exit(1)

    youtube = get_authenticated_service(args.client_secret, args.token)

    needs_comment = bool(promo_comment)
    if args.update_video_id:
        temp_status = {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": made_for_kids,
        }
        temp_body = {
            "id": args.update_video_id,
            "snippet": snippet,
            "status": temp_status,
        }
        youtube.videos().update(part="snippet,status", body=temp_body).execute()
        if args.thumbnail:
            youtube.thumbnails().set(
                videoId=args.update_video_id,
                media_body=MediaFileUpload(args.thumbnail),
            ).execute()
        if needs_comment:
            insert_promo_comment(youtube, args.update_video_id, promo_comment)
        final_body = {
            "id": args.update_video_id,
            "snippet": snippet,
            "status": status,
        }
        youtube.videos().update(part="snippet,status", body=final_body).execute()
        print(f"Updated video id: {args.update_video_id}")
        if publish_at:
            print(f"Scheduled for: {publish_at} (UTC)")
    else:
        temp_status = {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": made_for_kids,
        }
        temp_body = {
            "snippet": snippet,
            "status": temp_status,
        }
        video_id = upload_video(
            youtube=youtube,
            video_path=str(video_path),
            body=temp_body,
            thumbnail_path=args.thumbnail,
            notify_subscribers=notify_subscribers,
        )
        persist_output_video_id(args.output_video_id, video_id)
        if needs_comment:
            insert_promo_comment(youtube, video_id, promo_comment)
        final_body = {
            "id": video_id,
            "snippet": snippet,
            "status": status,
        }
        youtube.videos().update(part="snippet,status", body=final_body).execute()

        updated_description = strip_self_video_url(description, video_id)
        if updated_description != description:
            update_body = {
                "id": video_id,
                "snippet": {**snippet, "description": updated_description},
                "status": status,
            }
            youtube.videos().update(part="snippet,status", body=update_body).execute()

        print(f"Uploaded video id: {video_id}")
        persist_output_video_id(args.output_video_id, video_id)
        if publish_at:
            print(f"Scheduled for: {publish_at} (UTC)")
        print(f"Notify subscribers: {notify_subscribers}")


if __name__ == "__main__":
    main()
