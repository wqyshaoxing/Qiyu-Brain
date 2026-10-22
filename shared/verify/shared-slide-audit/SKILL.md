---
name: shared-slide-audit
description: Check a rendered deck at presentation size for unreadable text, overflow, unsourced charts, and slides that carry no claim, then report what must change.
domain: shared
stage: [verify]
loop_role: verify
consumes: [slide_deck, deck_spec]
produces: [audit_report, residual_risks]
deps: [shared-slide-build]
---

# Slide Audit

Two different questions, asked separately: can it be read (technical), and is it worth reading (content). Mixing them produces "it looks nice" as a verdict.

Adapted (judgment only) from `mpuig/agent-slides` and `siril9/presentation-skill`.

## When to use

- Before a deck is presented, sent, or submitted.
- After any edit that changed layout, length, or fonts.

Not for: designing the deck (that is `shared-slide-build`), or copy-editing prose.

## Boundary

- Does not fix while auditing; findings go back to the builder as a list.
- Does not accept "readable on my screen" — the check is at projection size or the size the recipient will view.
- Does not score aesthetics. A passing deck is legible, sourced, and one-claim-per-slide, not "beautiful".
- Does not certify a deck it could only partially render; partial coverage is reported as partial.
- Does not pass a deck containing a chart whose numbers cannot be traced.

## Requires

`shared-slide-build` — this skill assumes a deck and its spec exist, so each slide can be compared against the intended claim and word budget. How the deck was produced is the agent's call.

## Workflow

1. **Technical pass**, per slide: body text at or above the floor, no overflow or clipping, no text over busy imagery, consistent alignment, images at sufficient resolution, fonts embedded or substituted.
2. **Content pass**, per slide: the title states a claim rather than a topic; the body supports that claim; nothing asserts a number without a source.
3. **Sequence pass**: read titles only, in order. They should form an argument. If they read as a table of contents, the deck has no spine.
4. **Evidence pass**: every chart has axis labels, units, and a data source; schematic diagrams are labelled as schematic.
5. **Notes pass**: narration exists where a slide is not self-explanatory, and the notes are not a verbatim copy of the bullets.
6. **Compile** a fix list ordered by severity, then hand it back. Re-audit only the changed slides.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| audit_report | `slides/audit.md` | per-slide findings with severity, what was inspected, pass/block |
| residual_risks | `slides/audit-risks.md` | slides not rendered, fonts unavailable, unverified data claims |

## Completion

- Every slide has a verdict, or is listed as unrendered with the reason.
- Blocking findings are blocking; a deadline does not downgrade them.
- The title-only read-through is recorded, not implied.
- The report distinguishes "readable" from "correct" — it does not vouch for facts.

## Failure and recovery

- Cannot render the deck (missing fonts, converter): audit the spec and images instead, and say which checks were skipped.
- Deck changed after the audit: the audit is void; re-run rather than patching the report.
- Disagreement about "too much text": fall back to the recorded word budget, not to taste.
