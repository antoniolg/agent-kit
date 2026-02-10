---
name: postiz
description: Use the Postiz CLI to publish posts (create, schedule, upload images) to any configured integrations.
---

# Postiz (generic)

This skill documents how to use the Postiz CLI to manage social media posts.

It should NOT contain user-specific channel IDs, default publication rules, or language policy.

## Postiz CLI

The `postiz` binary must be available in your PATH.

Auth (required):
- `POSTIZ_API_KEY`
- `POSTIZ_BASE_URL`

### Core Workflow

Creating a post follows a one or two-step process depending on whether images are included.

#### 1. List Integrations
Find the IDs for the channels you want to post to.
```bash
postiz channels --pretty
```

#### 2. Upload Images (Optional)
If your post needs images, upload them first to get a public URL. You can repeat this for multiple images.
```bash
postiz upload-file --file-path /path/to/image.jpg --pretty
```
**Capture the `file.path`** from the JSON response. This is the URL you'll use in the next step.

#### 3. Create a Post
Create a single post or a thread.

**Draft (safe default):**
If `--status` is omitted, the post is created as draft by default.
```bash
postiz posts create --content "Your post text" --integrations <id> --pretty
```

**Single post:**
```bash
postiz posts create --content "Your post text" --integrations <id> --status now --pretty
```

**Scheduled post with image:**
```bash
postiz posts create \
  --content "Your post text" \
  --integrations <id> \
  --status scheduled \
  --scheduled-date "YYYY-MM-DDTHH:mm:ss+01:00" \
  --images "https://public-url-from-upload.png" \
  --pretty
```

**Thread / Multiple posts:**
Add multiple `--content` flags. They will be posted in order as a thread.
```bash
postiz posts create \
  --content "First tweet" \
  --content "Second tweet" \
  --integrations <id> \
  --pretty
```

### Important Formatting Note
To avoid line break issues (like literal `\n`), pass multi-line content directly to the CLI or use a subshell to read from a file:
```bash
postiz posts create --content "$(cat post.txt)" --integrations <id> --pretty
```

## Useful Commands

- `postiz posts list --start-date YYYY-MM-DD --end-date YYYY-MM-DD --pretty`: List posts in a date range.
- `postiz posts delete --id <postId> --pretty`: Delete a scheduled or draft post.
