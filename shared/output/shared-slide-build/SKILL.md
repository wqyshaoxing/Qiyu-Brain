---
name: shared-slide-build
description: Turn a brief into a slide deck with an explicit storyline, layout archetypes, and size rules that keep text readable on a projector.
domain: shared
stage: [output]
loop_role: render
consumes: []
produces: [deck_spec, slide_deck, build_log]
deps: []
---

# Slide Build

A deck is an argument delivered aloud, not a document projected on a wall. Decide the storyline first, choose layouts second, and let size rules decide how much text survives.

Adapted (judgment only) from `mpuig/agent-slides`; see [references/upstreams.md](references/upstreams.md).

## When to use

- A talk, defense, review, or report needs slides built from a brief or an existing outline.
- An existing deck must be rebuilt because its text cannot be read on a projector.

Not for: writing the underlying argument — that is `academic-paper-draft` or `coding-*`; not for editing an existing deck in place.

## Boundary

- Does not invent findings, numbers, or citations that the brief does not contain.
- Does not decide the rendering tool. python-pptx, LibreOffice, HTML→PDF, or Keynote are all acceptable; the choice is the agent's.
- Does not treat "it looks fine at 100% zoom" as readable; the check is at presentation size.
- Does not put the speaker's full script on the slide and in the notes at once.

## Workflow

1. **Fix the one-sentence spine**: what the audience must remember after the last slide. If two sentences, the deck is two decks.
2. **Outline the arc** as titles only: opening (why care), evidence (what we did/found), implication (so what), close. A title-only outline exposes a weak argument before any design work.
3. **Budget words per slide** from the venue: ~30–40 words for a projected talk, ~60–80 for a read-later report. State the budget; it is the only defence against walls of text.
4. **Assign layout archetypes**: title, section break, one-claim-plus-evidence, comparison, timeline, data chart, quote, summary. Reuse a small set; novelty in layout costs attention that belongs to content.
5. **Build to a spec file** (titles, bullets, chart data, image paths, notes) before rendering. Rebuilding from a spec is cheap; fixing a rendered deck is not.
6. **Set size rules explicitly**: body text floor (e.g. 18–20 pt projected), title floor, max 2 font families, one accent colour, charts with labelled axes and units.
7. **Render, then hand off** to `shared-slide-audit`; do not self-certify.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| deck_spec | `slides/deck-spec.json` | per-slide title, layout, bullets, chart data, notes; word budget respected |
| slide_deck | `slides/<name>.pptx` or `.pdf` | renders, correct slide count, notes attached |
| build_log | `slides/build-log.json` | renderer used, fonts substituted, images missing, slides skipped |

## Completion

- The title-only outline reads as an argument, not a table of contents.
- Every slide has one claim; the claim is visible in its title.
- Word budget and size floors are recorded in the spec, not just followed by habit.
- Notes exist for slides that need narration, and they are not a copy of the bullets.

## Failure and recovery

- No renderer available: deliver the spec plus a placeholder deck, say which renderer is needed; do not hand over a fake `.pptx`.
- Content exceeds the budget: cut, do not shrink the font below the floor.
- Charts lack source data: label them as schematic or remove them; an invented chart is worse than no chart.
