# AGENTS.md

Personal Codex operating rules.

## Agent Protocol

- Workspace: `~/Projects`.
- Missing personal repos: clone them from your GitHub organization/account.
- 3rd-party/OSS repos: clone under `~/Projects/oss`.
- GitHub: use `gh` CLI
- Guardrails: use `trash` for deletes.
- Bugs: add regression test when it fits.
- Keep files <~500 LOC; split/refactor as needed.
- Architecture: prefer scalable, testable, maintainable layered designs, adapted
  to the project's complexity and the technology's best practices.
- Commits: Conventional Commits (`feat|fix|refactor|build|ci|chore|docs|style|perf|test`).
- CI: `gh run list/view` (rerun/fix til green).
- Prefer end-to-end verify; if blocked, say what’s missing.
- New deps: quick health check (recent releases/commits, adoption).
- Prefer pnpm for Node projects unless the repo specifies otherwise.
- Web: quote exact errors; prefer 2026 sources;
- Transcription: when asked to transcribe video/audio, use `mlx_whisper` (`mlx-whisper`) by default.

## Docs

- Read README/docs before coding.
- Follow links until domain makes sense; honor `Read when` hints.
- Keep notes short; update docs when behavior/API changes (no ship w/o docs).
- Add `read_when` hints on cross-cutting docs.
- When creating new skills, write the skill content in English (including `SKILL.md`).
- Skills are public: avoid any sensitive data (tokens, internal URLs, IDs, private paths). Use placeholders or env vars.

## PR Feedback

- Active PR: `gh pr view --json number,title,url --jq '"PR #\\(.number): \\(.title)\\n\\(.url)"'`.
- PR comments: `gh pr view …` + `gh api …/comments --paginate`.
- Replies: cite fix + file/line; resolve threads only after fix lands.
- When merging a PR: thank the contributor in `CHANGELOG.md`.

## Build / Test

- Before handoff: run full gate (lint/typecheck/tests/docs).
- CI red: `gh run list/view`, rerun, fix, push, repeat til green.
- Keep it observable (logs, panes, tails, MCP/browser tools).
- Release: read `docs/RELEASING.md` (or find best checklist if missing).

## Git

- Safe by default: `git status/diff/log`.
- `git checkout` ok for PR review / explicit request.
- Branch changes require user consent.
- Destructive ops forbidden unless explicit (`reset --hard`, `clean`, `restore`, `rm`, …).
- Remotes under `~/Projects`: prefer HTTPS; flip SSH->HTTPS before pull/push.
- Don’t delete/rename unexpected stuff; stop + ask.
- No repo-wide S/R scripts; keep edits small/reviewable.
- If user types a command (“pull and push”), that’s consent for that command.
- No amend unless asked.
- Multi-agent: check `git status/diff` before edits; ship small commits.
