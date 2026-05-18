---
name: learnworlds-cli
description: Use the private LearnWorlds CLI to inspect DevExpert Academy users, find students by email, list their enrolled courses/products, look up products, and perform safe enrollment workflows. Trigger when Antonio asks what courses a student has in LearnWorlds or academia.devexpert.io, whether someone belongs to the current or next AI Expert edition, or to use the LearnWorlds/academy CLI.
---

# LearnWorlds CLI

Use this skill for DevExpert Academy / LearnWorlds checks. Prefer this CLI before browser automation when the user asks what courses a student has, whether an email belongs to an AI Expert edition, or whether an enrollment exists.

## CLI Path

Run from the CLI project or call the bin file directly:

```sh
cd /Users/antonio/Projects/antoniolg/learnworlds-cli
node bin/learnworlds.js --help
```

Direct invocation also works:

```sh
node /Users/antonio/Projects/antoniolg/learnworlds-cli/bin/learnworlds.js user courses --email alumno@example.com --json
```

The CLI reads the authenticated Helium browser session for `academia.devexpert.io`; do not look for a public LearnWorlds API token first.

## Read-Only Checks

Find a user:

```sh
node bin/learnworlds.js user find --email alumno@example.com --json
```

List the courses/products a user currently has in LearnWorlds:

```sh
node bin/learnworlds.js user courses --email alumno@example.com --json
```

Look up a product title ID:

```sh
node bin/learnworlds.js product find --product ai-expert-rec --json
```

Useful interpretation:

- `ai-expert-rec` is `AI Expert (Grabaciones)`.
- Listmonk edition lists are not the same as LearnWorlds access. If Antonio asks what access someone really has, trust `user courses` first.
- If Listmonk says `02. AI Expert - Siguiente edición` but LearnWorlds only shows `ai-expert-rec`, report both and say the academy access is recordings-only.

## Enrollment Safety

Mutating commands are dry-run by default. Only use `--execute` if Antonio explicitly asks to enroll/change access.

Dry-run enrollment:

```sh
node bin/learnworlds.js enroll --email alumno@example.com --product ai-expert-rec --json
```

Execute only with explicit confirmation:

```sh
node bin/learnworlds.js enroll --email alumno@example.com --product ai-expert-rec --execute --json
```

Do not send LearnWorlds enrollment emails unless Antonio explicitly requests it; that requires `--send-enrollment-email`.

## Troubleshooting

Check auth and author API access:

```sh
node bin/learnworlds.js doctor --json
```

If authentication fails, the expected defaults are:

```sh
LEARNWORLDS_BASE_URL=https://academia.devexpert.io
LEARNWORLDS_PROFILE_DIR="$HOME/Library/Application Support/net.imput.helium/Default"
LEARNWORLDS_KEYCHAIN_ACCOUNT=Helium
```

Do not print cookies, keychain secrets, or full raw user payloads in the final answer. Summarize only the email, username, product IDs/titles, and relevant edition conclusion.
