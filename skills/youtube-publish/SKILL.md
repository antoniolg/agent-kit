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
- **Thumbnail Generation:** Generate 3 thumbnails by default using all three Antonio photo references (`assets/antonio-1.png`, `antonio-2.png`, `antonio-3.png`). Keep only two non-negotiables: (1) massive bold white text (max 3-4 words), (2) cinematic dark look with cyan/magenta accents. Everything else should adapt to the video's narrative with maximum creative freedom.
- **Thumbnail Creativity Rule:** Deliver 1 safer option + 2 exploratory options. Avoid producing near-duplicates. If an unconventional concept communicates better for that specific video, prioritize it.
- **Workflow:** Upload a private draft before generating copy so the video URL can be used in newsletter/social text.
- **X Strategy:** Do not schedule/publish to X via Postiz in this flow. X is handled as native video upload outside this step.
- **Links:** In social posts, the comment must not be just the link; it must include a brief descriptive text inviting to watch (e.g., "Watch the full technical analysis here: https://...").
- **Comment Sequence:** For final publish/update, always use this order: set video to `unlisted`, insert promo comment (`Domina la IA...`), then set final status (`private` with `publishAt` if scheduled, otherwise `private`).
- **Schedule Decision Required:** Never publish without an explicit decision in `Programación (final)`: either a date `YYYY-MM-DD HH:MM` or `private`.
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
   - After transcription, copy the SRT to the vault transcripts folder:
     ```bash
     cp <workdir>/transcript.es.cleaned.srt ~/Documents/aipal/transcripts/<YYYY-MM-DD>-<slug>.srt
     ```
   - Use today's date and the video slug from step 1 as the filename.

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
   - Keep the two anchors fixed (massive white text + cinematic cyan/magenta look), but allow concept/composition/artifact/background to vary freely by story.
   - Target mix: 1 safe option + 2 exploratory options.
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

8. **Build native X video variant (after thumbnail choice)**
   - Command:
     ```bash
     python scripts/build_x_native_video.py --video <video.mp4> --thumbnail <thumb.png> --output <workdir>/video-x.mp4 --intro-ms 500
     ```
   - Result: a version ready for X where the first 500ms shows the selected thumbnail as a static cover frame.

9. **Schedule socials (Postiz, excluding X)**
   - Command:
     ```bash
     python scripts/schedule_socials.py --text-file <linkedin.txt> --scheduled-date <ISO8601+offset> --comment-url <video_url> --image <thumb.png>
     ```
   - This script publishes to configured socials except X.
   - Note: `schedule_socials.py` percent-encodes underscores in the `--comment-url` (e.g. `_` -> `%5F`) to avoid LinkedIn/Postiz URL formatting issues.

10. **Final Reminder**
   - Explicitly remind the user to go to YouTube Studio to:
     - Enable monetization (not supported via API).
     - Add End Screens (not supported via API).
