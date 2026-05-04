---
name: youtube-publish
description: "End-to-end YouTube publishing workflow using ordered scripts: prepare/concat video, upload draft, transcribe with Parakeet, generate copy with the calling model, optionally prepare English dubbing assets, render thumbnails, update YouTube metadata, then schedule socials (PostFlow) 15 minutes after publish."
---

# YouTube Publish (Scripted Flow)

Use scripts in order. Stop for validation after copy + thumbnail generation. If the user did not already specify them, ask up front for:
- the exact publish day/time
- whether they want English dubbing for YouTube
- whether they also want the English X variant

Rule: the English X variant depends on the English YouTube dubbing pack. It is valid to do English dubbing for YouTube without doing the English X variant, but not the other way around.

## Behavior rules for the agent

- **Tone & Authority:** Titles and copy must focus on engineering, architecture, and solving developer friction, but still need enough curiosity to earn the click. Avoid cheap reaction-style hype, but do not make titles read like internal architecture notes.
- **Title Blacklist (strict):** Forbidden in titles: `RIP`, `Increíble`, `Brutal`, `Locura`, `Definitivo`, `¿El fin de...?`, and crown/fire emojis.
- **Title Balance:** Titles should sit between technical authority and YouTube curiosity. It is valid to use product/vendor/model framing and an open question when that creates a stronger hook (e.g. "Nuevo modelo de Nvidia: ¿aguanta el hype?"). Do not over-explain the conclusion in the title.
- **Title Derivation:** Do not ask for a title hint; derive it from the video stem and the technical density of the SRT.
- **Scheduling:** If the user provides a publish time, resolve to exact `YYYY-MM-DD HH:MM` using system time and pass `--publish-at` + `--timezone`. Always determine and pass `--timezone`.
- **Missing decisions:** If publish date/time, English YouTube dubbing, or English X dubbing were not explicitly provided, ask for them before starting the workflow.
- **Content Generation Engine:** Titles, thumbnail ideas, description, chapters, and LinkedIn copy must be written by the same model executing this skill.
- **Social Curiosity Rule:** Social copy should create curiosity without revealing the verdict of the video. It may say what was tested and why it matters, but it should not spoil whether the model/tool/framework passed, failed, or won the comparison unless the user explicitly asks for that.
- **Series Context Rule:** If the video is part of a comparison, recurring series, or follow-up, anchor the social copy in that context (e.g. "after testing Qwen 3.6 and Gemma 4...") instead of repeating generic questions from previous posts.
- **English Variant:** When the user wants a multilingual YouTube version, always generate an English pack for the same video: translated transcript, dubbed English audio, and English title/description derived from the final approved Spanish title/description.
- **English Scope:** The English pack is for YouTube multi-language audio/localization only. Do not create English social posts unless the user explicitly asks for them.
- **English Deliverable:** For YouTube, treat the dubbed audio track as the primary deliverable. If the dubbing pipeline also creates a muxed preview video, keep it as optional verification output, not as the main handoff artifact.
- **English X Dependency:** If the user wants the English X variant, that implies the English YouTube dubbing pack must also be produced first.
- **Thumbnail Generation:** Generate 3 thumbnails using the presenter photo set. Default presenter is `antonio` (`assets/antonio-1.png`, `antonio-2.png`, `antonio-3.png`). If the user indicates the video is from Nino, switch presenter to `nino` (`assets/nino-1.png`, `nino-2.png`, `nino-3.png`). Keep only two non-negotiables: (1) massive bold white text (max 3-4 words), (2) cinematic dark look with cyan/magenta accents. Everything else should adapt to the video's narrative with maximum creative freedom.
- **Reference Photos (strict):** For each generated thumbnail, always use the 3 presenter images together as references. They are identity anchors (not fixed poses); the model is free to choose the best posture/composition.
- **Tool Logo Rule:** If the video is about a specific tool, product, framework, platform, model, or company, find its official/current logo or app icon early, copy it into `<workdir>/images/refs/`, and use it as a visual reference for thumbnail generation. If the logo cannot be found quickly, explicitly instruct the image model to include the tool's logo/app icon by name, while avoiding fake or distorted brand marks when accuracy matters.
- **Manual Image Attachment Gate:** Codex `imagegen` preserves presenter identity and brand marks much better when reference images are manually attached in the chat input. Before any thumbnail generation or edit that must preserve Antonio/Nino identity or a tool logo, open `<workdir>/images/refs/` for the user and explicitly ask them to attach the 3 presenter reference images and any relevant tool/logo reference in the message box. Do not call `imagegen` until the user confirms they have attached those images or explicitly asks to continue without them. Showing local Markdown images in chat is not enough for this gate.
- **Thumbnail Engine:** Use Codex built-in `imagegen` (`image_gen`) as the image generation/editing engine. Do not use Nano Banana for this flow unless the user explicitly asks for it.
- **Thumbnail Creativity Rule:** Deliver 1 safer option + 2 exploratory options. Avoid producing near-duplicates. If an unconventional concept communicates better for that specific video, prioritize it.
- **Thumbnail Edit Rule:** When the user asks to edit an existing thumbnail/image, treat the existing image as the edit target, not as inspiration for a new image. Load/show the exact current image first, ensure presenter references are manually attached when identity matters, then ask `imagegen` for a localized edit with hard invariants: same person, same layout, same headline unless changing text, same crop, same lighting, and no reinterpretation.
- **English Thumbnail Rule:** If the English YouTube dubbing pack is requested, once the user chooses the final thumbnail you must create an English-edited version of that same thumbnail by editing the selected image so its main headline text is in English instead of Spanish. Keep the composition, styling, and identity intact; only adapt the main headline text.
- **Workflow:** Upload a private draft before generating copy so the video URL can be used in social text.
- **Newsletter:** Disabled in this flow. Do not generate or schedule newsletter here.
- **X Strategy:** Do not schedule/publish to X via PostFlow in this flow. X is handled as native video upload outside this step.
- **X Spanish Asset (always):** Always build the Spanish native X video asset from the Spanish video plus the selected Spanish thumbnail, even when the user says "X no". In this workflow, "X no" means do not publish/schedule X and do not build an English X variant unless explicitly requested.
- **X Variants:** The default X asset is the Spanish native video with the selected Spanish thumbnail embedded as the first 500ms. If the user requested the English X variant too, also build an English native X video using the English-dubbed video plus the English-edited thumbnail.
- **Links:** In social posts, the comment must not be just the link; it must include a brief descriptive text inviting to watch (e.g., "Watch the full technical analysis here: https://...").
- **Comment Sequence:** For final publish/update, always use this order: set video to `unlisted`, insert promo comment (`Domina la IA...`), then set final status (`private` with `publishAt` if scheduled, otherwise `private`).
- **Schedule Decision Required:** Never publish without an explicit decision in `Programación (final)`: either a date `YYYY-MM-DD HH:MM` or `private`.
- **Timing:** Schedule social posts 15 minutes after the YouTube publish time.
- **Audio Consistency:** `prepare_video.py` runs audio normalization in `auto` mode by default. It analyzes LUFS/true peak/LRA and only re-encodes audio when out of target.
- **Thumbnail Upload Gate:** Before calling `update_youtube.py`, ensure the final thumbnail is accepted by YouTube: JPG/PNG, 16:9, preferably 1280x720, and under 2 MB. If a generated PNG is too large, create a compressed JPG sibling and upload that.
- **Verification Gate:** After final update/scheduling, verify the real YouTube `privacyStatus` and `publishAt`, then verify PostFlow using `postflow schedule list --view posts` for the target date. Do not rely on guessed CLI commands.
- **Final Asset Gate:** Before final handoff, confirm these expected artifacts exist when applicable: `content.md`, `.state/video_id.txt`, `.state/video_url.txt`, `images/final/thumb.es.png`, `video/video-x.es.mp4`, `transcripts/transcript.es.cleaned.srt`, and, for multilingual runs, `transcripts/transcript.en.srt`, `audio/dubbed.en.m4a`, `images/final/thumb.en.png`. If any required artifact is missing, create it or explicitly report why it is missing.
- **Verification Artifacts:** Save machine-readable verification output under `.state/` whenever practical, for example `.state/youtube_verification.json` and `.state/postflow_verification.json`, so later checks do not depend only on chat history.
- **Workdir Organization:** Keep the workdir tidy and predictable. `content.md` is the human/editorial source of truth for all copy in Spanish and English. Technical state for scripts may live outside it, but must be isolated under `.state/`. Media artifacts must be grouped by type:
  - `.state/` for script state such as `video_id.txt`, `video_url.txt`, YouTube verification JSON, and PostFlow verification JSON.
  - `transcripts/` for all SRT files.
  - `images/refs/` for presenter/logo/reference images.
  - `images/drafts/` for generated thumbnail drafts and their prompts.
  - `images/final/` for accepted Spanish and English thumbnails.
  - `audio/` for dubbed audio exports (`.wav`, `.m4a`).
  - `video/` for derived videos such as dubbed previews and native X variants.
- **Copy File Rule:** Do not create persistent standalone copy files such as `title.en.txt`, `description.en.txt`, `linkedin.final.txt`, or `description.final.es.txt` as canonical artifacts. Put those texts in `content.md`. If a downstream script requires a plain text file, create it as a temporary/generated helper under `.state/` or `tmp/`, and keep `content.md` as the canonical copy.

---

## Content Styles

### LinkedIn Post Style

- **Length/Format**: 600–900 characters, 3–6 short paragraphs, 1–2 emojis.
- **Strategy (Signal vs Noise):** Start with the concrete context that makes this video worth watching. For series/comparisons, mention the previous installments or contenders.
- **Identity:** Keep the tone of technical authority. Fewer creator-marketing phrases, more architecture conclusions and tradeoffs.
- **Curiosity:** Do not reveal the final verdict. Prefer the shape "I tested X against Y kinds of tasks; will it beat/hold up against Z?" over "X failed/passed because...".
- **Scope:** 1 central idea focused on technical authority. No digressions.
- **Closing**: Final line “Link en el primer comentario.” followed by a short question or CTA.
- **Restrictions**: No hashtags.

---

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
   - Immediately create the standard workdir subfolders:
     ```bash
     mkdir -p <workdir>/.state <workdir>/transcripts <workdir>/images/refs <workdir>/images/drafts <workdir>/images/final <workdir>/audio <workdir>/video <workdir>/tmp
     ```
   - Keep the prepared source video at the path returned by `prepare_video.py`. Derived videos should go under `<workdir>/video/`.

2. **Prepare reference images and manual attachment gate**
   - Copy the selected presenter references into `<workdir>/images/refs/`:
     ```bash
     cp assets/antonio-1.png assets/antonio-2.png assets/antonio-3.png <workdir>/images/refs/
     ```
     Use `nino-1.png`, `nino-2.png`, `nino-3.png` only when the user explicitly says the video is from Nino.
   - If the video is centered on a tool/product/framework/platform/model/company, locate the official/current logo or app icon and copy it into `<workdir>/images/refs/` with a clear name, for example `codex-logo.png`.
   - Open the references folder for the user:
     ```bash
     open <workdir>/images/refs
     ```
   - Ask the user to manually attach the 3 presenter photos in the Codex message box before thumbnail generation. If a logo/product image should be used visually, ask them to attach that too.
   - Do not proceed to thumbnail generation/editing until the user confirms the reference images are attached, unless they explicitly waive identity accuracy for that run.

3. **Upload draft (private)**
   - Command:
     ```bash
     python scripts/upload_draft.py --video <video> --output-video-id <workdir>/.state/video_id.txt --client-secret <path>
     ```
   - Write `.state/video_id.txt` and create `.state/video_url.txt`. Also record the video ID and URL in `content.md` under the YouTube section for human review.

4. **Transcribe + clean**
   - Command:
     ```bash
     python scripts/transcribe_parakeet.py --video <video> --out-dir <workdir>
     ```
   - Outputs:
     - `<workdir>/transcripts/transcript.es.cleaned.srt`
     - `<workdir>/transcripts/transcript.es.dub.srt` (same transcript resegmented into more natural dubbing units)
   - If the transcription script writes SRTs at the workdir root, move them into `<workdir>/transcripts/` before continuing and use the organized paths from then on.
   - After transcription, copy the SRT to the vault transcripts folder:
     ```bash
     cp <workdir>/transcripts/transcript.es.cleaned.srt ~/Documents/aipal/transcripts/<YYYY-MM-DD>-<slug>.srt
     ```
   - Use today's date and the video slug from step 1 as the filename.

5. **Prepare English transcript + dubbing assets (when multilingual output is requested)**
   - Read `<workdir>/transcripts/transcript.es.dub.srt` when present (fallback: `transcripts/transcript.es.cleaned.srt`) and create:
     - `<workdir>/transcripts/transcript.en.srt` translated to natural English while preserving timestamps.
   - Do **not** finalize English title/description yet. Those must be created after the user approves the final Spanish title and description, and they must be saved in `content.md` under `## Title (EN)` and `## Description (EN)`, not as canonical standalone files.
   - Generate dubbed English audio using the `youtube-dubber` project.
   - Default dubbing path:
     - `scripts/dub_voxtral.py`
     - model `voxtral-mini-tts-latest`
     - English reference clip from the presenter's own voice when available
   - Fallback path:
     - Chatterbox / Qwen only if Voxtral is unavailable or clearly worse for a specific run
   - Save at least:
     - `<workdir>/audio/dubbed.en.wav`
     - `<workdir>/audio/dubbed.en.m4a` as the upload-friendly audio-only export for YouTube Studio
     - `<workdir>/video/dubbed.en.mp4` if the dubbing pipeline also muxes the video
   - After dubbing, always export an audio-only upload artifact for YouTube Studio from the final dubbed track. Prefer `.m4a`/AAC unless the user asked for another format.
   - The goal is to run Voxtral through the same timed dubbing pipeline as the other models, not a manual narration-only shortcut.

6. **Generate copy with the calling model**
   - Read `<workdir>/transcripts/transcript.es.cleaned.srt` directly and generate:
     - 3 title candidates that balance technical authority and curiosity.
     - 3 Thumbnail ideas (Artifact-based).
     - Description (remove any self-link to current video).
     - Chapters (MM:SS).
     - LinkedIn post (per rules).
   - Title candidates must not reveal the full verdict unless that is the unavoidable premise of the video.
   - Social copy must not reveal the verdict. It should state the context, the kind of tasks tested, and a curiosity question that invites watching.
   - Save the result into `<workdir>/content.md`.
   - Also save thumbnail concepts into `content.md` under `## Ideas de thumbnails`. If a script needs JSON, create `<workdir>/.state/ideas.json` as technical state with this shape:
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

     ## YouTube
     Video ID:
     URL:
     Status:
     Publish at:

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

     ## Assets
     Thumbnail ES:
     Thumbnail EN:
     Transcript ES:
     Transcript EN:
     Audio EN:
     Video EN:
     ```
   - Title quality gate: reject title candidates that break the blacklist, sound like internal documentation, or reveal the conclusion too early.

7. **Generate 3 thumbnails**
   - Use presenter photos according to context: by default `antonio`, and `nino` only when explicitly requested for a Nino video. Copy the reference presenter photos into `<workdir>/images/refs/`. Create 3 images into `<workdir>/images/drafts/thumb-1.png`, `thumb-2.png`, `thumb-3.png`.
   - The same model executing the skill must derive the 3 image prompts from the transcript and thumbnail ideas, then save each prompt into `<workdir>/images/drafts/thumb-1.prompt.txt`, `thumb-2.prompt.txt`, `thumb-3.prompt.txt`.
   - Keep the two anchors fixed (massive white text + cinematic cyan/magenta look), but allow concept/composition/artifact/background to vary freely by story.
   - Target mix: 1 safe option + 2 exploratory options.
   - Use Codex built-in `imagegen` for each thumbnail. Before generation, confirm the user has manually attached the presenter reference images in the message box. You may also load/show the three presenter reference images in chat for visual confirmation, but that does not replace manual attachment.
   - `imagegen` saves under `~/.codex/generated_images/...` by default. After each generation, copy the selected output into `<workdir>/images/drafts/thumb-N.png`; leave the original generated file in place.
   - Do not use Nano Banana helper scripts in this flow unless the user explicitly asks to switch engines.
   - After generation, visually inspect each thumbnail and reject near-duplicates, unreadable text, wrong identity, or designs that reveal too much of the video's verdict.

7b. **Edit selected thumbnail when requested**
   - If the user asks to add a logo, change text, translate text, or otherwise edit a selected thumbnail, load/show the exact selected image first.
   - Prompt `imagegen` as an edit, with hard invariants: same person, same layout, same crop, same lighting, same main text unless that text is the requested edit, and no reinterpretation.
   - Save edited draft outputs under `<workdir>/images/drafts/` and visually inspect them against the original.
   - If the edit changes the presenter's identity or redraws the whole thumbnail, discard it and retry once with stricter invariants.

8. **Stop to ask for validation of**:
    - Title (choose one of the 3 generated).
    - Thumbnail (choose one of the 3 generated).
    - Description (edit if needed).
    - Chapters (edit if needed).
    - LinkedIn post (edit if needed).
   - After the user confirms the final Spanish title and description, and only then, create:
     - `## Title (EN)` in `<workdir>/content.md`
     - `## Description (EN)` in `<workdir>/content.md`
   - Keep the English title/description faithful to the final Spanish packaging and technically accurate, not mechanically translated from an outdated draft.
   - If the English YouTube dubbing pack is enabled, create the English-edited thumbnail after the user confirms the final thumbnail and before any final X-video build. Save the accepted Spanish thumbnail as `<workdir>/images/final/thumb.es.png` and the English thumbnail as `<workdir>/images/final/thumb.en.png`.

9. **Update YouTube**
   - Before updating, check final thumbnail size. If it is larger than 2 MB, create a compressed 1280x720 JPG sibling and upload that file instead of the source PNG:
     ```bash
     ffmpeg -y -i <thumb.png> -vf scale=1280:-2 -q:v 3 <thumb-upload.jpg>
     ```
   - Command:
     ```bash
     python scripts/update_youtube.py --video-id <id> --title "..." --description-file <workdir>/.state/description.final.es.txt --thumbnail <workdir>/images/final/thumb.es.png --publish-at "YYYY-MM-DD HH:MM" --timezone <IANA> --client-secret <path>
     ```
   - If the script needs `description.final.es.txt`, generate it from the final description and chapters in `content.md` under `.state/` immediately before the update. Do not treat it as canonical copy.
   - After updating, verify the real YouTube state with the API:
     - title matches final title
     - `privacyStatus` is `private`
     - `publishAt` matches the requested schedule in UTC
   - Save the verification response to `<workdir>/.state/youtube_verification.json`.
   - If comment insertion/listing fails because comments are disabled, report that explicitly instead of treating it as a silent success.

10. **Build native X video variant (after thumbnail choice)**
   - This step is always required for the Spanish asset. Do it even if the user opted out of X publishing/scheduling.
   - Command:
     ```bash
     python scripts/build_x_native_video.py --video <video.mp4> --thumbnail <workdir>/images/final/thumb.es.png --output <workdir>/video/video-x.es.mp4 --intro-ms 500
     ```
   - Result: a version ready for X where the first 500ms shows the selected thumbnail as a static cover frame.
   - Always build the Spanish X variant from the original Spanish video + final Spanish thumbnail.
   - If the user requested the English X variant too, also build:
     ```bash
     python scripts/build_x_native_video.py --video <workdir>/video/dubbed.en.mp4 --thumbnail <workdir>/images/final/thumb.en.png --output <workdir>/video/video-x.en.mp4 --intro-ms 500
     ```
   - The English X variant must use the English-edited thumbnail, not the Spanish one.

11. **Schedule socials (PostFlow, excluding X)**
   - Command:
     ```bash
     python scripts/schedule_socials.py --text-file <workdir>/.state/linkedin.final.txt --scheduled-date <ISO8601+offset> --comment-url <video_url> --image <workdir>/images/final/thumb.es.png
     ```
   - If the script needs `linkedin.final.txt`, generate it from `## Post LinkedIn (final)` in `content.md` under `.state/` immediately before scheduling. Do not treat it as canonical copy.
   - This script publishes to configured socials except X.
   - Note: `schedule_socials.py` percent-encodes underscores in the `--comment-url` (e.g. `_` -> `%5F`) to avoid LinkedIn URL formatting issues.
   - Verify with the real PostFlow schedule command:
     ```bash
     postflow --json schedule list --view posts --from <day-start-iso> --to <day-end-iso>
     ```
   - Confirm scheduled time, platforms, root post text, and first-comment link. Do not use non-existent `postflow posts list`.
   - Save the PostFlow schedule verification response to `<workdir>/.state/postflow_verification.json`.

12. **Final Reminder**
   - First run the Final Asset Gate and mention any missing optional/non-optional assets.
   - Explicitly remind the user to go to YouTube Studio to:
     - Enable monetization (not supported via API).
     - Add End Screens (not supported via API).
     - If multilingual output was requested, upload the prepared English audio-only track (preferably `<workdir>/audio/dubbed.en.m4a`) and apply the English title/description from `content.md` in the YouTube Studio multi-language UI.
     - If the English X variant was requested, remember that there should now be two native X assets ready: the Spanish `video/video-x.es.mp4` and the English `video/video-x.en.mp4`.
