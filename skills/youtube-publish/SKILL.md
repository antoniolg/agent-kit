---
name: youtube-publish
description: "End-to-end YouTube publishing workflow using ordered scripts: prepare/concat video, upload draft, transcribe with Parakeet, generate copy+thumbnails with Gemini, update YouTube metadata, then schedule socials (Postiz) 15 minutes after publish."
---

# YouTube Publish (Scripted Flow)

Use scripts in order. Stop for validation after copy + thumbnail generation. Ask exact publish time if not provided.

## Behavior rules for the agent

- **Tone & Authority:** Strictly avoid clickbait terms ("Fácil", "Rápido", "Secreto"). Titles and copy must focus on engineering, architecture, and solving developer friction.
- **Title Derivation:** Do not ask for a title hint; derive it from the video stem and the technical density of the SRT.
- **Scheduling:** If the user provides a publish time, resolve to exact `YYYY-MM-DD HH:MM` using system time and pass `--publish-at` + `--timezone`. Always determine and pass `--timezone`.
- **Thumbnail Generation:** Generate 3 thumbnails by default using all three Antonio’s photo context (`assets/antonio-1.png`, `antonio-2.png`, `antonio-3.png`). Style: Dark mode, minimalist, cinematic lighting (cyan/purple), featuring a "Technical Artifact" (logo, code snippet, or nodes), or the person working in a dark office, server bunker, architect drafting table. Check what fits better to tell the story of the video. Bold massive white text. Use max 3-4 words. Don't mention names explicitly. Us "subject" instead.
- **Workflow:** Upload a private draft before generating copy so the video URL can be used in newsletter/social text.
- **Links:** In social posts, the comment must not be just the link; it must include a brief descriptive text inviting to watch (e.g., "Watch the full technical analysis here: https://...").
- **Timing:** Schedule social posts 15 minutes after the YouTube publish time.

---

## Content Styles

### LinkedIn Post Style

- **Length/Format**: 600–900 characters, 3–6 short paragraphs, 1–2 emojis.
- **Strategy**: 1 central idea focused on technical authority. No digressions.
- **Closing**: Final line “Link en el primer comentario.” followed by a short question or CTA.
- **Restrictions**: No hashtags.

---

## Scripted flow (order)

1. **Prepare video**
   - Command:
     ```bash
     python scripts/prepare_video.py --videos /path/v1.mp4 [/path/v2.mp4 ...]
     ```
   - Output JSON with `workdir`, `video`, `slug`.

2. **Upload draft (private)**
   - Command:
     ```bash
     python scripts/upload_draft.py --video <video> --output-video-id <workdir>/video_id.txt --client-secret <path>
     ```
   - Write `video_id.txt` and create `video_url.txt`.

3. **Transcribe + clean**
   - Command:
     ```bash
     python scripts/transcribe_parakeet.py --video <video> --out-dir <workdir>
     ```
   - Outputs `transcript.es.cleaned.srt`.

4. **Generate copy (Gemini headless)**
   - Use `gemini` CLI on the cleaned SRT. Generate:
     - 3 Technical Authority Titles.
     - 3 Thumbnail ideas (Artifact-based).
     - Description (remove any self-link to current video).
     - Chapters (MM:SS).
     - LinkedIn post (per rules).
     - Save into `<workdir>/content.md`.

5. **Generate 3 thumbnails (Gemini image)**
   - Always include all three Antonio’s photo context. Create 3 images into `<workdir>/thumb-1.png`, `thumb-2.png`, `thumb-3.png`.
   - Example with multiple inputs:
     ```bash
     uv run /path/to/nano-banana-pro/scripts/generate_image.py --prompt "Antonio working..." --filename "thumb-1.png" --input-image assets/antonio-1.png assets/antonio-2.png assets/antonio-3.png
     ```

6. **Stop to ask for validation of**:
    - Title (choose one of the 3 generated).
    - Thumbnail (choose one of the 3 generated).
    - Description (edit if needed).
    - Chapters (edit if needed).
    - LinkedIn post (edit if needed).

7. **Update YouTube**
   - Command:
     ```bash
     python scripts/update_youtube.py --video-id <id> --title "..." --description-file <desc.txt> --thumbnail <thumb.png> --publish-at "YYYY-MM-DD HH:MM" --timezone <IANA> --client-secret <path>
     ```

8. **Schedule socials (Postiz)**
   - Command:
     ```bash
     python scripts/schedule_socials.py --text-file <linkedin.txt> --scheduled-date <ISO8601+offset> --comment-url <video_url> --image <thumb.png>
     ```
   - Use `x-es` by default for X.
   - Note: `schedule_socials.py` percent-encodes underscores in the `--comment-url` (e.g. `_` -> `%5F`) to avoid LinkedIn/Postiz URL formatting issues.

9. **Final Reminder**
   - Explicitly remind the user to go to YouTube Studio to:
     - Enable monetization (not supported via API).
     - Add End Screens (not supported via API).
