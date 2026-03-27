---
name: email
description: "Manage Gmail and iCloud inboxes via helper scripts: list messages, open, reply, and archive while preserving metadata for later actions. Use when triaging email, replying to messages, bulk-archiving threads, or checking inbox status across multiple accounts."
---

# Email (inbox)

List Gmail/iCloud inboxes showing a clean user view while preserving metadata (IDs) for later actions.

## Configuration

Accounts are configured in `~/.config/skills/config.json` under `email`:

```json
{
  "email": {
    "gmail_accounts": ["you@gmail.com", "other@gmail.com"],
    "icloud_user": "you@icloud.com"
  }
}
```

## Workflow

### 1. List inbox

```bash
scripts/email-inbox --json-out /tmp/inbox.json
```

- Show the user **only** the clean numbered list (see Output format below).
- Read `/tmp/inbox.json` internally for IDs — never show IDs to the user.
- Propose recommended actions (archive/open/reply/wait) using your judgment; ask for confirmation before acting.
- If the JSON is stale or missing, re-run with `--json-out`.

### 2. Open an email

```bash
scripts/email-open --index <n>
```

Prints from/subject/date/body and saves metadata to `/tmp/email-open.json`. Works for both Gmail and iCloud.

### 3. Reply to an email

**Always** show the draft to the user and get explicit approval before sending.

```bash
scripts/email-reply --index <n> --body-file /tmp/reply.txt
```

| Flag | Purpose |
|------|---------|
| `--reply-all` | Reply to all recipients (Gmail) |
| `--no-reply-all` | Reply only to sender (overrides default reply-all) |
| `--subject "Re: ..."` | Force a custom subject line |
| `--append-only` | Save to Sent without sending (already sent externally) |
| `--no-append-sent` | Send without saving to Sent |

iCloud replies via SMTP with the same app password and stores a copy in Sent. After sending, archive the thread to keep inbox clean:

```bash
scripts/email-archive --index <n>
```

### 4. Archive emails

```bash
scripts/email-archive --index 1 --index 2 --index 3
scripts/email-archive --index 1,2,3,4,9,10
```

Works for both Gmail and iCloud. For iCloud, if the archive mailbox cannot be detected automatically, specify it with `--mailbox "<Name>"`. List available mailboxes with `scripts/email-mailboxes --account <icloud>`.

## Metadata format

Each item in `/tmp/inbox.json` contains: `index`, `source` (`gmail`/`icloud`), `account`, `id` (Gmail: threadId, iCloud: UID), `from`, `subject`.

## Output format

- Separate by account with absolute numbering across all accounts.
- Account header: `📧 **<account>**` followed by `—` separator.
- Prefix each message with an action emoji: 🔍 open · 🗂️ archive · 👀 review · ⏳ wait.
- Do not bold the sender; bold is only for account headers.

## Triage rules

Custom rules in `rules.json` (this skill folder) refine action recommendations. Add rules when the user notices repeated misclassifications.

## Notes

- The script may prompt for the iCloud password if env vars are missing.
- Always pass `--json-out` when running inbox to ensure metadata is available for subsequent actions.
