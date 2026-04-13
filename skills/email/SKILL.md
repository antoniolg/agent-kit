---
name: email
description: Manage inbox email. Uses the inbox script and stores metadata (ids) to open or archive messages later.
---

# Email (inbox)

## Goal
List Gmail/iCloud inboxes showing a clean user view while preserving metadata (IDs) for later actions.

## Base command
- Helper in the skill: `scripts/email-inbox`
- Always pass `--json-out` to save metadata.
- Configure accounts in `~/.config/skills/config.json` under `email`:
  - `gmail_accounts`: list of Gmail accounts
  - `icloud_user`: iCloud user (optional)

Example:
```json
{
  "email": {
    "gmail_accounts": ["you@gmail.com", "other@gmail.com"],
    "icloud_user": "you@icloud.com"
  }
}
```

Example:
```
scripts/email-inbox
```

## Flow
1) Run the command with `--json-out /tmp/inbox.json`.
2) Show the user ONLY the clean output (numbered list), using the agreed format (see "Output format").
3) Read `/tmp/inbox.json` to get IDs and keep them for later actions.
4) Treat `/tmp/inbox.json` as a frozen snapshot until you explicitly refresh the inbox again.
5) If the user says "archive all except 141, 144" (or similar), interpret "all" as all items from the last shown snapshot, not every message currently in the live inbox. This avoids archiving new emails that arrived after the list was shown.
6) Only refresh/reload the inbox before acting when the user explicitly asks for it, or when you no longer trust the saved snapshot.
7) Propose recommended actions (archive/open/reply/wait) using your own judgment; ask for confirmation before acting.

Helpers (from the skill folder):
- `scripts/email-open --index <n>` (Gmail/iCloud) opens and writes `/tmp/email-open.json`.
- `scripts/email-archive --index <n>` (Gmail/iCloud) archives the message/thread. Accepts multiple indices.
- `scripts/email-reply --index <n> --body-file <path>` replies to the message (Gmail/iCloud).
- `scripts/email-mailboxes --account <icloud>` lists iCloud mailboxes.

## Metadata format
The JSON contains a list of items with:
- `index` (number shown to the user)
- `source` (`gmail` or `icloud`)
- `account`
- `id` (Gmail: threadId, iCloud: UID)
- `from`
- `subject`

## Open an email (Gmail)
Use the helper:
```
scripts/email-open --index <n>
```
This prints the email (from/subject/date/body) and saves metadata to `/tmp/email-open.json`.

## Reply to an email (Gmail/iCloud)
Before sending, **always** show the draft to the user and ask for explicit approval.

Use the helper:
```
scripts/email-reply --index <n> --body-file /tmp/reply.txt
```

- If you need to reply-all (Gmail), add `--reply-all`.
- To force a subject: `--subject "Re: ..."`
- iCloud replies via SMTP with the same app password and **stores a copy in Sent**.
- To save to Sent without sending (already sent): `--append-only`.
- To avoid saving to Sent: `--no-append-sent`.
- By default it replies-all and keeps CC. To reply only to the sender: `--no-reply-all`.
- After sending a reply, archive the thread with `scripts/email-archive --index <n>` to keep the inbox clean.

## Archive an email (Gmail)
Use the helper:
```
scripts/email-archive --index <n>
```
Examples:
```
scripts/email-archive --index 1 --index 2 --index 3
scripts/email-archive --index 1,2,3,4,9,10
```

## iCloud (current state)
- List: supported by `inbox`.
- Open: supported by `scripts/email-open --index <n>` (uses UID).
- Archive: supported by `scripts/email-archive --index <n>`.
  - If it cannot detect the archive mailbox, use `--mailbox "<Name>"`.
  - To list mailbox names: `scripts/email-mailboxes --account <icloud>`.

## Missing context
- If the JSON is stale or missing, run inbox again with `--json-out`.
- If you refresh, the new `/tmp/inbox.json` replaces the previous snapshot and becomes the new source of truth for follow-up actions.

## Notes
- The iCloud helpers (`inbox`, `email-open`, `email-reply`, `email-mailboxes`, `email-archive`) read the app password from the `ICLOUD_APP_PASSWORD` environment variable.
- If `ICLOUD_APP_PASSWORD` is not set, the script falls back to an interactive `getpass()` prompt, which fails in non-interactive/headless runs.
- If iCloud access fails, first verify whether `ICLOUD_APP_PASSWORD` is exported in the current session before assuming the credential is wrong.
- If a candidate password exists in local config for the same email address but IMAP returns `[AUTHENTICATIONFAILED]`, treat it as a different service credential rather than the iCloud app password.
- Useful diagnostics:
  - `python3 - <<'PY'
import os
print('ICLOUD_APP_PASSWORD' in os.environ)
PY`
  - `security find-internet-password -a '<icloud-user>' -s 'imap.mail.me.com' -g 2>&1 | head`
  - `security find-generic-password -a '<icloud-user>' -g 2>&1 | head`
- Avoid showing IDs to the user; only show the clean list.

## Output format
- Separate by account (Gmail/iCloud) while keeping the absolute numbering.
- Account header in bold: `📧 **<account>**`.
- Separator line after the header: `—`.
- Use emojis before each message with this legend:
  - 🔍 open
  - 🗂️ archive
  - 👀 review
  - ⏳ wait
- Do not bold the sender; bold is only for the account header.

## Optional triage rules
If the user notices failures, add specific rules in `rules.json` to refine future recommendations.

### Active rules
Rules live in `rules.json` inside this skill (single source of truth).
