---
name: justdoit
description: "Manage tasks via the justdoit CLI (Google Tasks + Calendar): view daily agenda, list and search tasks by list/section, complete or undo tasks by ID or title. Use when checking today's tasks, searching for specific tasks, marking tasks done, or reviewing the weekly backlog."
---

# justdoit CLI

CLI for Google Tasks + Calendar. Covers daily views, list/search, complete/undo, and common workflows.

## Common workflows

### Morning review: check tasks and complete what's done

```bash
justdoit next --ids                        # 1. See today's tasks with IDs
justdoit done <taskID> --list <List>       # 2. Mark completed tasks
justdoit next                              # 3. Verify updated view
```

### Find and complete a specific task

```bash
justdoit search "deploy fix" --list Work --ids   # 1. Find the task
justdoit done <taskID> --list Work               # 2. Complete it
```

## Commands

### Daily view (next)

```bash
justdoit next                  # Overdue → today → this week → next week → backlog
justdoit next --ids            # Include task IDs for later actions
justdoit next --backlog=false  # Hide backlog section
```

### List and search

```bash
justdoit list --list <List>                              # All tasks in a list
justdoit list --list <List> --section <Section>          # Filter by section
justdoit list --list <List> --section <Section> --all    # Include completed
justdoit search "<query>" --list <List> --ids            # Search with IDs
```

### Complete and undo

```bash
# Complete by ID or title
justdoit done <taskID> --list <List>
justdoit done --list <List> --title "<Exact title>" --section <Section>

# Undo completion by ID or title
justdoit undo <taskID> --list <List>
justdoit undo --list <List> --title "<Exact title>" --section <Section>
```

## Tips

- Use `--ids` whenever you plan to complete or undo tasks — the ID is required for those commands.
- Use `--all` to include completed items in list views.
