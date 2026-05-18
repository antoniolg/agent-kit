#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Send a PDF to a Holded inbox using gog, optionally archiving a copy in Drive.

Usage:
  holded-send.sh --pdf /path/to/file.pdf --email <holdedbox> --nombre <filename-or-base> [options]

Options:
  --from <gmail-account>       Gmail/Drive account to use with gog.
  --drive-folder <folder-id>   Upload a copy to this Drive folder before email.
  --subject <subject>          Override email subject.
  --body <body>                Override email body.
  --dry-run                    Print gog commands without sending/uploading.

Defaults can be set in ~/.config/skills/config.json under holded_invoices:
  sender_email
  drive_inbox_folder_id

The PDF is emailed as an attachment to the Holded inbox. Drive upload is best
effort only after the email recipient and PDF are validated, and before send.
EOF
}

PDF=""
EMAIL=""
NOMBRE=""
FROM=""
DRIVE_FOLDER=""
SUBJECT=""
BODY=""
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pdf) PDF="$2"; shift 2;;
    --email) EMAIL="$2"; shift 2;;
    --nombre) NOMBRE="$2"; shift 2;;
    --from) FROM="$2"; shift 2;;
    --drive-folder) DRIVE_FOLDER="$2"; shift 2;;
    --subject) SUBJECT="$2"; shift 2;;
    --body) BODY="$2"; shift 2;;
    --dry-run) DRY_RUN="true"; shift 1;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

config_value() {
  local key="$1"
  python3 - "$key" <<'PY'
import json
import os
import sys

path = os.path.expanduser("~/.config/skills/config.json")
key = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    sys.exit(0)

val = data
for part in key.split("."):
    if isinstance(val, dict) and part in val:
        val = val[part]
    else:
        sys.exit(0)

if isinstance(val, (str, int, float)):
    print(val)
PY
}

if [[ -z "$PDF" || -z "$EMAIL" || -z "$NOMBRE" ]]; then
  usage
  exit 2
fi

if [[ ! -f "$PDF" ]]; then
  echo "PDF not found: $PDF" >&2
  exit 1
fi

if [[ -z "$FROM" ]]; then
  FROM="$(config_value holded_invoices.sender_email)"
fi
if [[ -z "$DRIVE_FOLDER" ]]; then
  DRIVE_FOLDER="$(config_value holded_invoices.drive_inbox_folder_id)"
fi

if [[ -z "$FROM" ]]; then
  echo "Missing sender account (pass --from or set holded_invoices.sender_email)" >&2
  exit 2
fi

if ! command -v gog >/dev/null 2>&1; then
  echo "Missing gog CLI in PATH" >&2
  exit 1
fi

BASE_NAME="$NOMBRE"
BASE_NAME="${BASE_NAME%.pdf}"
BASE_NAME="${BASE_NAME%.PDF}"
FILENAME="$BASE_NAME.pdf"

TMPDIR=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

SEND_PDF="$PDF"
if [[ "$(basename "$PDF")" != "$FILENAME" ]]; then
  SEND_PDF="$TMPDIR/$FILENAME"
  cp "$PDF" "$SEND_PDF"
fi

if [[ -z "$SUBJECT" ]]; then
  SUBJECT="$BASE_NAME"
fi
if [[ -z "$BODY" ]]; then
  BODY="Documento para Holded: $BASE_NAME"
fi

if [[ "$DRY_RUN" == "true" ]]; then
  if [[ -n "$DRIVE_FOLDER" ]]; then
    printf 'DRY-RUN: gog drive upload %q --account %q --parent %q --name %q --json --no-input\n' "$SEND_PDF" "$FROM" "$DRIVE_FOLDER" "$FILENAME"
  fi
  printf 'DRY-RUN: gog gmail send --account %q --from %q --to %q --subject %q --body %q --attach %q --json --no-input\n' "$FROM" "$FROM" "$EMAIL" "$SUBJECT" "$BODY" "$SEND_PDF"
  exit 0
fi

if [[ -n "$DRIVE_FOLDER" ]]; then
  DRIVE_JSON=$(gog drive upload "$SEND_PDF" \
    --account "$FROM" \
    --parent "$DRIVE_FOLDER" \
    --name "$FILENAME" \
    --json \
    --no-input)
  DRIVE_ID=$(printf "%s" "$DRIVE_JSON" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const j=JSON.parse(d);process.stdout.write(j.file?.id||j.id||'');});")
  echo "OK: uploaded $FILENAME to Drive${DRIVE_ID:+ ($DRIVE_ID)}"
fi

SEND_JSON=$(gog gmail send \
  --account "$FROM" \
  --from "$FROM" \
  --to "$EMAIL" \
  --subject "$SUBJECT" \
  --body "$BODY" \
  --attach "$SEND_PDF" \
  --json \
  --no-input)
MESSAGE_ID=$(printf "%s" "$SEND_JSON" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const j=JSON.parse(d);process.stdout.write(j.message?.id||j.id||'');});")
echo "OK: emailed $FILENAME to $EMAIL${MESSAGE_ID:+ ($MESSAGE_ID)}"
