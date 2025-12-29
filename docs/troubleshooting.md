# Troubleshooting Worktrees

## "not a git repository"

You are not inside `main/`. Change to the repo root and retry:
```
cd main
```

## "A branch named 'X' already exists"

The branch already exists. Create the worktree without `-b`:
```
git worktree add ../worktrees/X X
```

## "worktree already exists" / path exists

Choose a new directory name or remove the old one:
```
git worktree remove <path>
```

## "locked" worktree

Prune stale metadata:
```
git worktree prune
```

## Uncommitted changes block checkout

Commit or stash changes before creating a new worktree:
```
git status
git add -A
git commit -m "WIP" # or: git stash
```
