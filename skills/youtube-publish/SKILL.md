---
name: youtube-publish
description: “End-to-end YouTube publishing workflow — prepare video, upload draft, transcribe, generate copy and thumbnails, update metadata, and schedule socials via PostFlow. Use when publishing a YouTube video, generating thumbnails, scheduling social posts, or preparing multilingual content.”
---

# YouTube Publish (Scripted Flow)

Execute scripts in order. Stop for user validation after copy + thumbnail generation. Ask exact publish time if not provided.

## Agent rules

### Content tone

Titles and copy must focus on engineering, architecture, and solving developer friction. Avoid reaction-style hype.

- **Title blacklist (strict):** `RIP`, `Increíble`, `Brutal`, `Locura`, `Definitivo`, `¿El fin de...?`, crown/fire emojis.
- **Technical anchor (strict):** Every title must include at least one: `Orquestación`, `Despliegue`, `Infraestructura`, `Clean Architecture`, `Refactorización`, `Pipeline`, `Capa de Abstracción`.
- **Title derivation:** Derive from the video stem and SRT technical density — do not ask the user for a hint.

### Presenter selection

Default presenter is **antonio** (`assets/antonio-1.png`, `antonio-2.png`, `antonio-3.png`). Switch to **nino** (`assets/nino-1.png`, `nino-2.png`, `nino-3.png`) only when the user explicitly indicates a Nino video. Always pass all 3 presenter images as identity-anchor references for each thumbnail.

### Scheduling and publishing

- Resolve publish time to `YYYY-MM-DD HH:MM` with `--publish-at` + `--timezone` (always determine timezone).
- **Comment sequence:** set `unlisted` → insert promo comment (`Domina la IA...`) → set final status (`private` with `publishAt` if scheduled, otherwise `private`).
- **Schedule decision required:** Never publish without an explicit decision — either `YYYY-MM-DD HH:MM` or `private`.
- Schedule social posts **15 minutes after** YouTube publish time.
- Newsletter and X are excluded from this flow.

### Thumbnail rules

- Engine: `3rd-nano-banana-pro/scripts/generate_image.py` (keep default Flash model unless overridden).
- Two non-negotiables: (1) massive bold white text (max 3-4 words), (2) cinematic dark look with cyan/magenta accents.
- Target mix: 1 safe option + 2 exploratory. Avoid near-duplicates.

### English variant (multilingual)

When the user wants a multilingual version, generate an English pack (translated transcript, title, description, dubbed audio) for YouTube multi-language localization only. Do not create English social posts unless explicitly requested.

### Social posts

- In social posts, always include descriptive text inviting to watch — never just a bare link.
- `prepare_video.py` runs audio normalization in `auto` mode by default (targets `-14 LUFS`, `-1 dBTP`, max `LRA 9`; skips when already in range).

### LinkedIn post style

600–900 chars, 3–6 short paragraphs, 1–2 emojis. Start with an engineering principle or problem, not “new video.” Close with “Link en el primer comentario.” + question/CTA. No hashtags.

## Scripted flow (order)

1. **Prepare video**
   - Command:
     ```bash
     python scripts/prepare_video.py --videos /path/v1.mp4 [/path/v2.mp4 ...]
     ```
   - Audio behavior (default): `--audio-normalization auto` targets `-14 LUFS`, `-1 dBTP`, and max `LRA 9`; it skips normalization when already in range.
   - Optional:
     - `--audio-normalization always` to force normalization.
     - `--audio-normalization off` to skip analysis and normalization.
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

4. **Prepare English dubbing assets (when multilingual output is requested)**
   - Read `<workdir>/transcript.es.cleaned.srt` and create:
     - `<workdir>/transcript.en.srt` translated to natural English while preserving timestamps.
     - `<workdir>/title.en.txt` with 1 English YouTube title for the dubbed track.
     - `<workdir>/description.en.txt` with 1 English YouTube description for the dubbed track.
   - Generate dubbed English audio using the `youtube-dubber` project.
   - Default dubbing path:
     - `scripts/dub_voxtral.py`
     - model `voxtral-mini-tts-latest`
     - English reference clip from the presenter's own voice when available
   - Fallback path:
     - Chatterbox / Qwen only if Voxtral is unavailable or clearly worse for a specific run
   - Save at least:
     - `<workdir>/dubbed_audio.en.wav`
     - `<workdir>/dubbed_video.en.mp4` if the dubbing pipeline also muxes the video
   - Keep the English title/description technically faithful to the Spanish source, not marketing-localized beyond what is needed for natural English.
   - The goal is to run Voxtral through the same timed dubbing pipeline as the other models, not a manual narration-only shortcut.

5. **Generate copy with the calling model**
   - Read `<workdir>/transcript.es.cleaned.srt` directly and generate:
     - 3 Technical Authority Titles.
     - 3 Thumbnail ideas (Artifact-based).
     - Description (remove any self-link to current video).
     - Chapters (MM:SS).
     - LinkedIn post (per rules).
   - Save the result into `<workdir>/content.md`.
   - Also save thumbnail concepts into `<workdir>/ideas.json` with this shape:
     ```json
     {
       "titles": ["...", "...", "..."],
       "thumbnails": [
         {"text": "...", "artifact": "...", "concept": "..."},
         {"text": "...", "artifact": "...", "concept": "..."},
         {"text": "...", "artifact": "...", "concept": "..."}
       ]
     }
     ```
   - Make sure `content.md` contains at least these sections so downstream validation stays compatible:
     ```md
     # Pack YouTube — <slug>

     ## Enlace del vídeo
     <video_url>

     ## Títulos
     - ...
     - ...
     - ...

     ## Ideas de thumbnails
     1. Texto: ...
        Artifact: ...
        Concept: ...

     ## Descripción
     ...

     ## Capítulos
     00:00 ...

     ## LinkedIn
     ...

     ## Título (final)

     ## Descripción (final)

     ## Capítulos (final)

     ## Post LinkedIn (final)

     ## Thumbnail (final)

     ## Programación (final)
     (YYYY-MM-DD HH:MM o "private")

     ## Title (EN)

     ## Description (EN)
     ```
   - Title quality gate: reject title candidates that break blacklist or technical-anchor rules.

6. **Generate 3 thumbnails**
   - Use presenter photos according to context: by default `antonio`, and `nino` only when explicitly requested for a Nino video. Create 3 images into `<workdir>/thumb-1.png`, `thumb-2.png`, `thumb-3.png`.
   - The same model executing the skill must derive the 3 image prompts from the transcript and `ideas.json`, then save each prompt into `<workdir>/thumb-1.prompt.txt`, `thumb-2.prompt.txt`, `thumb-3.prompt.txt`.
   - Keep the two anchors fixed (massive white text + cinematic cyan/magenta look), but allow concept/composition/artifact/background to vary freely by story.
   - Target mix: 1 safe option + 2 exploratory options.
   - Example with multiple inputs:
     ```bash
     uv run /path/to/nano-banana-pro/scripts/generate_image.py --prompt "Antonio working..." --filename "thumb-1.png" --input-image assets/antonio-1.png assets/antonio-2.png assets/antonio-3.png
     ```
   - If using helper scripts:
     - Batch render from an existing `ideas.json`: `python scripts/generate_missing_thumbs.py --presenter antonio --out-dir <videos-root>`
     - Nino video: `python scripts/generate_missing_thumbs.py --presenter nino --out-dir <videos-root>`
     - Optional override: `--image-model <model>` only if explicitly needed; otherwise keep the default model.

7. **Stop to ask for validation of**:
    - Title (choose one of the 3 generated).
    - Thumbnail (choose one of the 3 generated).
    - Description (edit if needed).
    - Chapters (edit if needed).
    - LinkedIn post (edit if needed).
    - English title (edit if needed).
    - English description (edit if needed).

8. **Update YouTube**
   - Command:
     ```bash
     python scripts/update_youtube.py --video-id <id> --title "..." --description-file <desc.txt> --thumbnail <thumb.png> --publish-at "YYYY-MM-DD HH:MM" --timezone <IANA> --client-secret <path>
     ```

9. **Build native X video variant (after thumbnail choice)**
   - Command:
     ```bash
     python scripts/build_x_native_video.py --video <video.mp4> --thumbnail <thumb.png> --output <workdir>/video-x.mp4 --intro-ms 500
     ```
   - Result: a version ready for X where the first 500ms shows the selected thumbnail as a static cover frame.

10. **Schedule socials (PostFlow, excluding X)**
   - Command:
     ```bash
     python scripts/schedule_socials.py --text-file <linkedin.txt> --scheduled-date <ISO8601+offset> --comment-url <video_url> --image <thumb.png>
     ```
   - This script publishes to configured socials except X.
   - Note: `schedule_socials.py` percent-encodes underscores in the `--comment-url` (e.g. `_` -> `%5F`) to avoid LinkedIn URL formatting issues.

11. **Final Reminder**
   - Explicitly remind the user to go to YouTube Studio to:
     - Enable monetization (not supported via API).
     - Add End Screens (not supported via API).
     - If multilingual output was requested, upload the English dubbed audio track and apply the English title/description in the YouTube Studio multi-language UI.
