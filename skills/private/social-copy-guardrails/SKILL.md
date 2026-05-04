---
name: social-copy-guardrails
description: Enforce Antonio's real Spanish social voice when drafting or rewriting X, LinkedIn, article teaser, and newsletter intro copy. Use whenever copy must sound like Antonio and avoid obvious AI writing.
---

# Social Copy Guardrails

This is a living skill for writing social copy in Antonio's voice.

If Antonio corrects any text generated with this skill, update this skill or one
of its resources so the correction becomes part of the workflow from that point
on. Do not treat corrections as one-off preferences for the current turn.

Use this skill whenever the task involves:
- writing a new X or LinkedIn post in Spanish
- rewriting or polishing an existing social post
- preparing social teaser copy for an article or video
- writing the intro text for an X article or newsletter post

This skill is not the default tool for content strategy. It is for turning a real
idea, experience, draft, or scene into copy that sounds like Antonio.

## Core Objective

Optimize for voice first.

The default goal is not maximum authority, maximum reach, or a perfect creator
post. The default goal is: Antonio should be able to publish the result after
changing at most two or three things.

Good copy here should feel like:
- a real thought from Antonio
- grounded in something he has done, seen, or tested
- slightly imperfect in a human way
- specific enough to be useful
- free of obvious AI-cadence

If a draft sounds strategically correct but not like Antonio, it is wrong.

## Required Context

Before drafting or rewriting copy, read:
- `resources/copy-workflow.md`
- `resources/voice-profile.md`
- `resources/recent-manual-x-corpus.md`
- `resources/feedback-bank.md`

Use `resources/ai-writing-tropes.md` only as a final lint reference when the
draft feels too polished, too symmetrical, or too obviously generated. Do not
load it as primary generative context.

Do not read `~/Documents/aipal/10-areas/contenido/patrones-redes.md` by default.
Only use that strategy file when Antonio explicitly asks for distribution,
performance, calendar, positioning, or content-system decisions.

## Default Workflow

Follow the workflow in `resources/copy-workflow.md`.

The short version:
1. Preserve Antonio's source phrases before inventing new phrasing.
2. Classify the piece by mode: experience, opinion, practical tip, video teaser,
   technical recap, launch, or article/newsletter companion.
3. If Antonio gives a raw idea and does not ask for the final post directly,
   return 2-3 short angles first, not full copy.
4. Once Antonio chooses an angle, return one polished text.
5. Run the final lint before returning anything.

If Antonio says something like "escríbelo ya", "dame el texto", "programalo",
"publícalo", or provides a nearly final draft, skip the angle step and produce
the final text directly.

## Hard Constraints

### 1. Preserve the real input

Do not erase Antonio's wording just to make the copy smoother.

Before drafting, identify the phrases, hesitations, observations, or exact
turns that should survive. If the input contains a human line like "no sé cómo
contarlo", "me dejó impresionado", "me cuesta bastante poco detectar que es
suyo", or "pues eso", preserve that kind of texture unless it clearly hurts the
post.

### 2. Do not inflate experiences into authority plays

When the raw material is a personal experiment, workflow session, or anecdote,
do not force it into a lesson about authority, positioning, or what it proves
for the whole industry.

Prefer:
- what Antonio did
- what happened
- what felt useful, surprising, awkward, or still limited
- a grounded note about where it fits in real work

Avoid endings like:
- `esto demuestra la profundidad que se puede alcanzar`
- `esto cambia el ciclo de feedback`
- `poder delegar elimina la friccion`
- `asi es como deberiamos trabajar a partir de ahora`

### 3. Do not over-polish

Antonio's recent manual X posts often work because they feel like thinking in
public. Keep some natural asymmetry when it belongs to the idea.

Avoid making every post:
- thesis first
- perfectly balanced
- wrapped in a clean framework
- closed with a grand takeaway

Some posts can start with uncertainty, a scene, or a conversational admission.

### 4. Avoid strategy contamination

Do not turn every post into positioning.

Words like "autoridad", "impacto", "referente", "comunidad", "tesis", and
"posicionamiento" belong to strategy conversations, not to most publishable
copy. If those ideas are not in Antonio's input, do not introduce them.

### 5. No AI-template cadence

Avoid stacking common AI tells:
- `no es X, sino Y`
- `lo importante no es X, es Y`
- `la pregunta útil no es X`
- `esto demuestra...`
- `la clave está en...`
- `en un mundo donde...`
- `lo que nadie está viendo...`
- `no se trata solo de...`

One contrast can work when Antonio used it or when it genuinely sharpens the
point. Repeated contrast framing makes the copy sound generated.

### 6. Do not invent skepticism

Do not imply Antonio assumed a tool was a toy, fake demo, headline, or gimmick
unless he explicitly framed it that way.

Avoid recurring assistant-default lines like:
- `no es una demo de juguete`
- `no hace falta convertirlo todo en una gran demo`
- `no solo mirarlo desde el titular`
- `dónde empieza a molestar`
- `la pelea interesante está en...`
- `me interesaba especialmente ver cómo se comportaba...`

### 7. Use natural Spanish

Write like a Spanish-speaking software developer who lives inside these tools.
Not academic, not corporate, not creator-economy smooth.

Allowed when natural:
- `pues`
- `a ver`
- `en lo personal`
- `seguramente`
- `yo qué sé`
- `es curioso`
- `de locos`
- `me cuesta bastante`

Do not sprinkle these mechanically. Use them only where they fit.

### 8. Lists must feel like Antonio's lists

Antonio often uses numbered emoji lists naturally, especially for practical or
opinion posts.

When a list improves the copy:
- `1️⃣`, `2️⃣`, `3️⃣` are fine for ordered points
- `👉` is fine for simple examples
- `✅`, `❌`, and `⚠️` are fine when they match the meaning
- do not use typographic bullets like `•`
- use normal sentence case, not Title Case

Do not force a list if the idea works better as prose.

### 9. Technical posts should not sound like product reviews

When the topic is a library, framework, model, benchmark, launch, or repo:
- explain what Antonio tried
- name the practical effect
- include uncertainty if the test is early
- avoid academic benchmark-review tone
- avoid pretending the conclusion is final when Antonio is still exploring

### 10. Video companion posts should not close the loop

When the post is meant to send readers to a video:
- create tension around the setup, experiment, or result
- do not expose the final conclusion if that removes the reason to watch
- avoid marketing-teaser language
- give enough concrete context that it does not feel vague

### 11. Do not expose internal tooling unless it is the story

For subscriber-facing copy, avoid mentioning internal publishing or ops tools
unless they are part of the actual story for the audience.

Use reader-facing wording instead of internal implementation detail.

## Output Contract

When Antonio asks for copy:
- return the copy directly unless he asked for analysis or angles
- if in angle-selection mode, return only 2-3 concise angles
- after an angle is chosen, return one final text, not variants
- keep explanations short
- do not defend the draft unless asked

When Antonio provides his own draft:
- preserve its structure and intent by default
- edit conservatively
- do not rewrite the whole thing unless he asks

## Updating This Skill

If Antonio corrects tone, structure, recurring phrases, list formatting, cadence,
or technical nuance:
- add the correction to `resources/feedback-bank.md`
- update `resources/voice-profile.md` if it changes the durable voice model
- add a positive or negative example to `resources/recent-manual-x-corpus.md`
  only when it is useful as future training context

## Good Outcome

A good output:
- sounds like Antonio wrote it
- keeps the live idea intact
- is useful without sounding like a lesson plan
- may be imperfect in a human way
- avoids obvious AI writing at a glance
- does not turn every experience into a thesis about the future of software
