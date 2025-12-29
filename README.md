# Worktree Helper

This repository serves two purposes:

1) Human documentation about Git worktrees
2) An AI skill (`worktree-helper/`) that guides agents through a consistent worktree workflow

## Repository layout

- `docs/` — human documentation
- `worktree-helper/` — the AI skill (SKILL.md + references + scripts)

## Skill overview

The skill helps an agent:

- Migrate a repo into a `main/` + `worktrees/` layout
- Create worktrees for tasks or issues
- Implement work and then merge or create PR/MR
- Clean up worktrees safely

## Documentation

Start here:

- `docs/what-is-a-worktree.md`
- `docs/worktree-workflow.md`
- `docs/troubleshooting.md`

## Tooling

Issue-based flows are easier with:

- GitHub CLI: `gh`
- GitLab CLI: `glab`

The skill will fall back to manual issue details if those tools (or MCP integrations) are not available.
