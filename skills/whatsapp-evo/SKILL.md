---
name: whatsapp-evo
description: "Manage WhatsApp via Evolution API (v2.x): list unread chats, reply to messages, and retrieve conversation history using helper scripts. Use when checking WhatsApp inbox, replying to contacts or groups, reviewing conversation threads, or triaging pending replies."
---

# WhatsApp (Evolution API)

Manage WhatsApp messaging through the Evolution API v2.x with helper scripts for inbox, reply, and history operations.

## Configuration

Set `EVOLUTION_API_TOKEN` as an environment variable (required). Configure the remaining settings in `~/.config/skills/config.json`:

```json
{
  "whatsapp_evo": {
    "api_url": "https://evo.example.com",
    "instance": "MyInstance"
  }
}
```

## Workflow

### 1. List unread chats

```bash
scripts/whatsapp-inbox --json-out /tmp/whatsapp-inbox.json
```

Show the user only the clean numbered list — never expose tokens or JIDs directly.

| Flag | Purpose |
|------|---------|
| `--since-days N` | Ignore messages older than N days (default: 7) |
| `--no-update-state` | List the same chats again without marking them seen |
| `--pending-reply` | Show conversations where the latest message is not yours |

State is saved in `~/.cache/whatsapp-evo/inbox-state.json` to avoid repeating chats. Override with `--state` or `WHATSAPP_EVO_STATE_PATH`.

**Note:** Unread status is computed from the last incoming message without `READ` status in the API — it may not match "mark as unread" in the WhatsApp app.

### 2. Reply to a chat

**Always ask the user for confirmation before sending.**

```bash
scripts/whatsapp-reply --index <n> --text "your reply here"
```

Uses `message/sendText` via the Evolution API. For direct chats, the index resolves to the phone number; for groups, use `remote_jid` if needed. Optional flags: `--delay <ms>`, `--link-preview`, `--instance`, `--url`.

### 3. View conversation history

```bash
scripts/whatsapp-history --index <n> --limit 50
```

| Flag | Purpose |
|------|---------|
| `--jid` or `--number` | Look up chat directly without an index |
| `--since YYYY-MM-DD` | Filter messages from a date (supports ISO 8601) |
| `--until YYYY-MM-DD` | Filter messages up to a date |
| `--incoming-only` | Show only inbound messages |

## Metadata format

Each entry in `/tmp/whatsapp-inbox.json` contains: `index`, `name`, `remote_jid`, `number`, `unread_count`, `last_message_id`, `last_message_from_me`, `last_message_text`, `last_message_timestamp`, `last_message_sender`.

## Error handling

- **Stale or missing JSON:** Re-run `scripts/whatsapp-inbox --json-out /tmp/whatsapp-inbox.json` to refresh.
- **Authentication errors (401/403):** Verify `EVOLUTION_API_TOKEN` is set and valid. Check that the instance name matches the configured instance in Evolution.
- **Connection failures:** Confirm `api_url` is reachable and the Evolution API service is running.
- **Invalid JID:** Ensure the phone number includes the country code without `+` (e.g., `5511999999999`) or use the `remote_jid` from inbox metadata for groups.
