---
name: social-copy-guardrails
description: Enforce Antonio's house style when drafting or rewriting Spanish copy for X, LinkedIn, article teasers, and newsletter intros. Use whenever generating social posts or article companion copy that must sound like him and respect his hard constraints.
---

# Social Copy Guardrails

This is a living skill.

If Antonio corrects any text generated with this skill, update this skill so the correction becomes part of the workflow from that point on.

Do not treat corrections as one-off preferences for the current turn.
Treat them as changes to the skill.

Use this skill whenever the task involves:
- writing a new X or LinkedIn post in Spanish
- rewriting or polishing an existing social post
- preparing social teaser copy for an article
- writing the intro text for an X article or newsletter post

This skill is not for planning content strategy.
It is for writing the actual copy without drifting into generic AI voice.

## Core principle

If the idea is good but the wording breaks the house rules, the output is still wrong.

Treat the constraints below as hard constraints, not soft preferences.
If a draft violates them, rewrite it before returning anything.

Before drafting or rewriting copy with this skill, read:
- `resources/voice-profile.md`
- `resources/ai-writing-tropes.md`
- `~/Documents/aipal/10-areas/contenido/patrones-redes.md`

Use it as an anti-slop filter.
Apply it with judgment:
- avoid stacking multiple AI-writing tells in the same piece
- prefer direct, specific phrasing over polished generic phrasing
- if a trope appears once naturally and the line is genuinely strong, do not weaken it just to satisfy the checklist mechanically

## Hard constraints

### 1. No default hedge words

Do not default to softeners such as:
- `creo`
- `cada vez más`
- `me parece`

Only use them when they add a real and deliberate nuance.
If the sentence works without them, remove them.

### 2. Lists must be easy to scan

When a list improves the copy:
- prefer `✅`, `❌`, `⚠️`, or `👉`
- do not use typographic bullets like `•`
- use `❌` for negative items, failure modes, or fragility examples
- use `✅` for positive items, working parts, or recommended elements

### 3. List items must use normal sentence case

In lists:
- capitalize only the first letter of the first word
- do not use Title Case
- do not make every line sound like a slide deck heading

Good:
- `✅ Validación por commit`

Bad:
- `✅ Validación Por Commit`

### 4. Avoid AI-template cadence

Do not let multiple posts sound like they come from the same mold.

Vary:
- rhythm
- sentence length
- paragraph shape
- closing style

Avoid the polished-neutral LinkedIn-robot tone.

### 5. Open with the thesis, not with warm-up

Start as close as possible to the real point.
Do not spend the opening lines arriving at the idea.
Lead with the claim, tension, or scene.

### 6. Do not over-explain obvious transitions

Avoid filler bridges like:
- `La idea es sencilla`
- `Básicamente`
- `En realidad`
- `Lo importante aquí es`

unless they genuinely sharpen the point.

### 7. Keep the Spanish natural

Write in natural Spanish from someone technical and opinionated.
Not academic.
Not ad-copy smooth.
Not generic creator-economy language.

### 8. Technical posts should not sound like reviews

When the topic is a library, framework, model, benchmark, or launch:
- do not drift into "analysis piece" tone
- explain the technical point in plain language
- prefer "this is what it does" / "this is the catch" over academic framing
- if there is hype, separate clearly between the base product and the benchmark-enhanced path
- if benchmarks need caveats, explain them so a reader who will never open the eval scripts still understands the practical implication

### 9. Video companion posts should not close the loop

When the post is meant to send readers to a video:
- create tension around the problem, setup, or experiment
- do not expose the final conclusion if that removes the reason to watch
- make the reader curious about the outcome, tradeoffs, or failure modes
- still provide enough concrete context to avoid vague teaser copy

### 10. Do not overuse contrast framing

Avoid repeating the same analytical contrast cadence:
- `no es X, sino Y`
- `lo relevante no es X, es Y`
- `lo que importa de esto no es X, sino Y`
- `la pregunta útil no es X, sino Y`
- `la gracia no está en X, está en Y`

One contrast can work when it genuinely sharpens the thesis. Repeating it across a newsletter, article intro, or post makes the copy sound generated and unlike Antonio.

Prefer:
- a concrete scene from Antonio's work
- a direct observation
- a specific consequence
- a plain-language catch or tradeoff

Good:
- `Esta semana he usado Codex para bastante más que programar: revisar sistemas, preparar contenido, operar herramientas y cerrar tareas que normalmente acabarían desperdigadas.`

Bad:
- `Lo importante de Codex no es que programe mejor, sino que se convierte en una capa de trabajo completa.`

### 11. Avoid invented skepticism

Do not imply Antonio or the reader assumed a tool was a toy, a fake demo, or only headline material unless Antonio explicitly framed it that way.

Avoid recurring phrases like:
- `no es una demo de juguete`
- `no hace falta convertirlo todo en una gran demo`
- `no solo mirarlo desde el titular`
- `dónde empieza a molestar`
- `la pelea interesante está en...`
- `me interesaba especialmente ver cómo se comportaba...`

These lines sound like assistant-default framing. They add a defensive stance Antonio did not necessarily take.

Prefer concrete, neutral wording:
- what Antonio tested
- what happened in the test
- where the tradeoff appeared
- what he wants to keep investigating

Good:
- `Lo probé con tareas largas porque ahí se ve mejor si mantiene contexto, si usa bien las herramientas y si el coste de ejecutarlo en local compensa.`

Bad:
- `Qwen 3.6 no es una demo de juguete, pero merece probarlo en condiciones reales y no solo mirarlo desde el titular.`

### 12. Do not expose internal tooling to readers

When writing subscriber-facing copy, avoid mentioning internal publishing or ops tools unless they are part of the actual story for the audience.

For example, do not mention:
- `Listmonk`
- campaign IDs
- draft mechanics
- internal automation plumbing

Use reader-facing wording instead:
- `preparar esta newsletter`
- `dejar un borrador revisable`
- `cerrar una tarea que normalmente quedaría desperdigada`

## Medium constraints

These are not absolute, but should usually hold:
- prefer one strong thesis over three medium ones
- if the post includes a list, make each item concrete
- if there is a CTA, it should feel like a natural consequence of the post
- article teaser copy should create curiosity without summarizing the whole piece
- if the post is about tooling, close with what changes in the work, not just what launched
- when critiquing hype, avoid sounding defensive or "debunk thread"; explain the useful part first, then the caveats

## Default workflow

### 1. Write the rough version fast

Start from the thesis, scene, or tension.
Do not optimize the first sentence for elegance.
Optimize it for clarity and force.

### 2. Run a constraint pass

Before returning, check:
- did I use `creo`, `cada vez más`, or `me parece` lazily?
- if there is a list, does it use `✅`/`❌`/`⚠️`/`👉`?
- do list items use normal sentence case?
- does the cadence sound templated?
- does the opening reach the point fast enough?
- if the piece mentions benchmarks or evals, would a smart reader understand the caveat without having to read the benchmark docs?

### 3. Rewrite if needed

If any answer is yes, rewrite.
Do not apologize.
Just fix it.

## What this skill should protect against

- copy that sounds generated from the same place
- soft openings that dilute the thesis
- clean but lifeless posts
- overuse of recurring verbal tics
- pretty formatting with weak signal

## Output expectations

When the user asks for copy:
- return the copy directly unless analysis was requested
- keep explanations short
- do not defend the draft unless asked

## Updating this skill

If Antonio corrects:
- tone
- structure
- recurring phrases
- list formatting
- cadence
- how technical nuance should be translated into plain-language copy

then update this skill so the correction becomes enforceable next time.

## Good outcome

A good output:
- sounds like Antonio
- reaches the point quickly
- is easy to scan
- does not use lazy hedge phrases
- does not feel like a generic AI post
