---
name: x-republish
description: Republish an already-published X post into one or more destinations managed in PostFlow by extracting the source post text, capturing the quoted post cleanly, adapting the copy when needed, and creating or scheduling the publication. Use when a user shares an X post URL and wants to reuse that content on LinkedIn or any other PostFlow-managed account without rebuilding the post manually.
---

# X Republish

Use this skill when the source of truth is an X post that has already been published and now needs to be reused elsewhere.

The default flow is:
- take the published X post as input
- extract the author's own text
- detect the quoted post or cited content
- produce a clean image asset from that quoted post, preferably with a local render built from tweet metadata
- keep the post text exactly as published on X unless the user explicitly asks for a rewrite
- create or schedule the publication through PostFlow

This skill is not for writing net-new social posts from scratch.
It is for operational reuse of content that already exists on X.

## Core principle

Do not reinvent what is already validated.

The author has already chosen:
- the angle
- the framing
- the cited source

Reuse that work.
Only adapt what is necessary to make the post native to the target platform and valid for PostFlow.
The default assumption is stronger than that: if the X post already works, reuse the exact same text.

## Inputs

Expect these inputs whenever possible:
- URL of the published X post
- target accounts or platforms available in PostFlow
- mode: draft, schedule, or publish-now
- scheduled time when the publication is not immediate

If the user only gives the URL, default to preparing a draft and ask for targets only if they are required to continue.

## Workflow

### 1. Inspect the source X post

Preferred source order:
1. `bird read --json-full`
2. other read-only tweet metadata sources only if `bird` is unavailable or incomplete

Open the source post and capture:
- the author's post text
- whether it quotes another X post
- whether the quoted post includes media
- whether the quoted content is the main value or just supporting context

When using `bird --json-full`, prefer fields from the raw payload when they are available:
- quoted tweet text
- quoted tweet author name and handle
- quoted tweet avatar URL
- verification state
- counts such as likes, reposts, replies, and views

Preserve:
- line breaks when they help readability
- emphasis that should survive into PostFlow
- the original thesis and stance

Do not preserve:
- X-only artifacts that make no sense outside X
- obvious leftovers such as reply-only context, dangling mentions, or platform-specific noise

### 2. Extract the quoted post as an asset

If the post quotes another X post, create a clean visual asset for that quoted post.

Treat this as a **strict rendering task**, not as an open-ended design exercise.

Preferred order:
1. local render that recreates the quoted post from `bird --json-full` metadata
2. faithful screenshot of the quoted post
3. cropped screenshot focused on the quoted card if the full page includes too much noise
4. recreated card from fallback metadata if the preferred source is blocked

#### Objective

The final asset should:
- still read as a tweet
- feel native in a social feed outside X
- highlight the quoted content without turning into a generic promo card

#### Fixed hierarchy

Keep this element priority:
1. avatar
2. display name and handle
3. X mark
4. tweet text
5. attached media when present

By default, do not include:
- date
- likes
- reposts
- replies
- views

The resulting image should:
- center the quoted content
- avoid unrelated browser chrome
- keep attribution visible when possible
- stay readable at the target social aspect ratio
- keep attached media centered inside the lower media area when media is present; do not pin it to the top by default

Default canvas preference for social redistribution:
- use a square `1:1` canvas unless the user requests another format
- let the tweet card sit inside the canvas with generous padding instead of stretching it edge to edge
- optimize for feed presence on LinkedIn and similar platforms, even when the original tweet is narrower than the canvas
- omit the bottom metadata band by default when redistributing to other networks
- omit date, views, likes, reposts, and replies unless the user explicitly wants a more documentary render

If rendering locally from metadata:
- use the quoted tweet author avatar URL when present
- keep the quoted author name and handle visible
- include verification styling only when the source metadata supports it
- prefer a look close to X rather than an over-designed card
- use `assets/x-logo.svg` for the platform mark instead of a plain text `X`
- preserve the tweet text verbatim unless truncation is unavoidable for the chosen format
- keep the surrounding canvas visually quiet so the tweet remains the focal point
- avoid wrapping the text too early; use the available card width instead of imitating the narrow original tweet column mechanically
- make the layout adaptive: when the quoted post has little text and a strong image, give the media more vertical space and center the composition visually

#### Layout rules

Apply these rules in order:
- use the available card width for text before wrapping; do not preserve the narrow X column if it creates dead space
- avoid large empty zones on the right side of the text block
- avoid large empty zones below the media block
- when the quoted tweet has little text and strong media, enlarge the media and reduce unused whitespace
- when the quoted tweet has no media, let the text block take more vertical prominence
- when the quoted media is square or close to square, allow it to occupy more height inside the composition
- vertically center the full composition inside the card when content is short
- when there is attached media, center it inside the available lower area unless the user explicitly asks for another crop or alignment
- keep the background quiet; the tweet card must do the visual work

#### Fidelity rules

Prefer fidelity over decoration:
- use the real avatar whenever available
- use the real X logo asset
- keep name and handle intact
- keep text as close as possible to the source
- only simplify text when line breaks or glyph support force a small adjustment

Do not:
- add decorative flourishes unrelated to X
- invent metadata that is not present
- turn the card into a poster or flyer

#### Template usage

A template can be used as a baseline for spacing and structure, but it is not the source of truth.

The source of truth is:
1. the hierarchy above
2. the layout rules above
3. the final visual checklist below

If the template and the rules conflict, follow the rules.

#### Final visual checklist

Before showing the image to the user, check:
- does the text use enough width, or is it wrapping too early?
- is there too much empty space to the right of the text?
- is there too much empty space below the image?
- does the media have enough presence relative to the text?
- if there is media, is it centered cleanly in the lower area rather than stuck to the top edge?
- does the piece still read clearly as a tweet?
- does it look clean enough to repost on LinkedIn or similar networks?

If the quoted post contains media that is essential to the point, preserve it in the capture.

If there is no quoted post, the skill can still republish the copy without an image, but should not invent a fake quote card.

### 3. Adapt the copy for the destinations

Start from the original X text.

Default rule:
- keep the exact X text verbatim

Adapt only where needed, and only if the user asked for it or the unchanged text would fail for the requested destination:
- expand references that are too implicit outside X
- remove X-native phrasings that feel off elsewhere
- preserve the original opinion and energy

If the environment includes a house style or copy guardrails skill, use it before finalizing the text.

Read `references/platform-adaptation.md` when:
- multiple destinations are requested
- the same copy feels too X-native for the target
- you need quick guidance on whether to keep the text almost identical or reshape it more noticeably

### 4. Prepare PostFlow payloads

Use `postflow-cli` as the default publishing path.

Before creating anything:
- resolve the target account IDs from the requested destinations
- upload the quote image if one was generated
- keep the text and media together per destination
- when the user did not ask for copy changes, publish the exact source X text with no rewriting

Before publishing to any social network:
- show the generated image to the user first
- get explicit confirmation that the image is correct
- if the image needs visual fixes, adjust it before creating or promoting the publication

If the same base text goes to multiple destinations, allow small per-platform adjustments instead of forcing one identical payload everywhere.

Use:
- `draft` when the user wants to review first
- `schedule` when a time is provided
- `publish-now` only when explicitly requested

Always validate the payload before scheduling or publishing when that is practical in the current run.

When the publication step is already finalized and you have:
- the exact final text
- the image path, if any
- the target PostFlow account IDs

prefer using `scripts/postflow_publish.py` instead of rebuilding the CLI sequence manually.

Suggested flow:
1. resolve account IDs with `postflow --json accounts list` (or `go run ./cmd/postflow --json accounts list`)
2. save the exact X text to a file
3. run the helper script with the text file, image path, account IDs, and mode

Example:

```bash
python scripts/postflow_publish.py \
  --postflow-dir /path/to/postflow \
  --text-file /tmp/source-post.txt \
  --image /tmp/quoted-post-card.png \
  --account-id acc_linkedin \
  --account-id acc_instagram \
  --mode publish-now
```

### 5. Create the publication

Create the post in PostFlow with:
- the final text
- the uploaded quote image when present
- the requested account IDs
- a deterministic idempotency key when scheduling or retrying

If the publication spans multiple accounts, keep a clear mapping of:
- account
- resulting draft or scheduled post ID
- scheduled time

### 6. Report the outcome

The run should end with a concise operational summary:
- source X URL used
- targets created
- whether media was attached
- draft or scheduled status
- resulting PostFlow IDs when available

If something blocks the run, say exactly which part failed:
- source extraction
- quote capture
- local quote render
- media upload
- PostFlow validation
- PostFlow creation

## Guardrails

- Do not paraphrase aggressively when the source copy already works.
- Do not retouch the text by default. Exact X text is the baseline.
- Do not strip attribution from the quoted post.
- Do not force an image when there is no real quoted post to capture.
- Do not default to third-party screenshot generators when `bird --json-full` already provides the metadata needed for a local render.
- Do not bypass PostFlow unless the CLI is failing and debugging is required.
- Do not assume LinkedIn is the only target; use whichever PostFlow-managed destinations the user requests.
- Do not publish immediately unless the user asked for it.

## Good outcome

A good run leaves:
- a faithful reuse of the original X post thesis
- a clean image of the quoted post when applicable
- destination-aware copy that still sounds intentional
- a valid draft, scheduled post, or published post in PostFlow
