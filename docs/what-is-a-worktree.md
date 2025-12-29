# What Is a Git Worktree?

A Git worktree is an additional working directory attached to the same repository. It lets you check out another branch (or commit) in a separate folder without cloning the repo again.

## Why use worktrees?

- Work on multiple branches at the same time
- Avoid stashing or context switching
- Share a single `.git` database across directories
- Keep builds or experiments isolated

## Mental model

- One repository can have **multiple worktrees**.
- Each worktree has its **own working directory** and checked-out branch.
- All worktrees share the same Git object database.

## Common use cases

- Implement a feature in one worktree while keeping `main` clean
- Review a PR in a separate folder
- Run tests or builds concurrently

## Core commands (quick look)

```
# Create a new worktree for a branch

git worktree add -b feature/my-work ../worktrees/feature-my-work main

# List worktrees

git worktree list

# Remove a worktree

git worktree remove ../worktrees/feature-my-work

# Clean stale worktrees

git worktree prune
```
