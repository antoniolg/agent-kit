---
name: holded-invoices
description: "Process invoice PDFs/emails: extract vendor + date, generate normalized filename, optionally archive to Drive, and email the PDF to the right Holded inbox."
---

# Holded invoices (PDF/Gmail → Drive archive → Holded inbox email)

Goal: send invoice/receipt PDFs to Holded's inbox email after normalizing their filenames. Prefer direct Gmail delivery via `gog`; the old n8n webhook is legacy fallback only.

## Destinations

Configure defaults in `~/.config/skills/config.json` under `holded_invoices`:
- `company_email`
- `freelancer_email`
- `sender_email`
- `drive_inbox_folder_id` (optional, archives a copy before sending)
- `webhook` (legacy fallback)

Example:
```json
{
  "holded_invoices": {
    "company_email": "empresa@holdedbox.com",
    "freelancer_email": "autonomo@holdedbox.com",
    "sender_email": "sender@example.com",
    "drive_inbox_folder_id": "drive-folder-id"
  }
}
```

Filename convention:
- `<company>-<YYYY>-<MM>.pdf`
- Vendor slug: lowercased, spaces → dashes, simplified (e.g. "Google INC" → `google`).

## Scripts

### 1) Extract vendor + date from a PDF

- `scripts/invoice-extract.js --pdf /path/to/invoice.pdf`
  - Outputs JSON: `{ vendor, vendorSlug, year, month }`

### 2) Send a PDF to Holded via Gmail

- `scripts/holded-send.sh --pdf /path/to/invoice.pdf --email <holdedbox> --nombre google-2026-01.pdf`
  - Uses `gog gmail send` with the configured `sender_email` or `--from`.
  - If `drive_inbox_folder_id` or `--drive-folder` is set, first uploads the normalized PDF to that Drive folder.
  - Use `--dry-run` before changing the workflow or debugging auth.

### Legacy fallback: upload via n8n

- `scripts/holded-upload.sh --pdf /path/to/invoice.pdf --email <holdedbox> --nombre google-2026-01.pdf`
  - Uses the `webhook` config or `--webhook`.
  - Use only when direct Gmail delivery is not available.

### 3) End-to-end: from a Gmail message ID

Downloads the first PDF attachment, suggests a filename, and (optionally) uploads.

- `scripts/holded-from-gmail.sh --account <gmail-account> --message-id <id> --type empresa|autonomo`
  - If not configured, pass `--email-empresa`, `--email-autonomo`, `--from`, and/or `--drive-folder`.
  - Passing `--webhook` forces the legacy n8n path.

Flags:
- `--yes` skip confirmation and upload

## Agent workflow

When reviewing an email thread with a PDF invoice:
1) Ask: is it `empresa` or `autonomo`.
2) Download the PDF attachment.
3) Run `invoice-extract.js` to infer vendor + year/month.
4) Propose filename and ask for confirmation.
5) Send via `holded-send.sh` so Drive/Gmail return observable output.

If extraction fails, ask for vendor + date and continue.
