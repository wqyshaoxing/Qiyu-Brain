---
name: academic-paper-draft
description: Draft manuscript sections strictly from an evidence map, keeping each claim traceable and marking anything unsupported instead of smoothing it over.
domain: academic-research
stage: [output]
loop_role: render
consumes: [evidence_map, contradiction_log]
produces: [draft, claim_index]
deps: [academic-claim-map]
---

# Paper Draft

Produce readable prose whose every assertion can be traced back to an entry in the evidence map. Fluency that outruns evidence is the failure mode this skill exists to prevent.

## When to use

- An evidence map exists and a section (intro, methods, results, discussion) must be written.
- A draft needs revision for a specific reviewer concern.

Not for: inventing claims that the map does not contain, or polishing before the map is stable.

## Boundary

- Does not introduce new citations. Missing support goes back to `academic-claim-map` as a request, not into the text.
- Does not write results that the analysis did not produce.
- Does not hide negative or null findings; they are reported with the same care.
- Does not translate or typeset; those are separate skills.

## Workflow

1. Fix the section's job in one sentence: what the reader must believe after reading it.
2. Order claim keys from the map into that argument. If a needed claim is missing, stop and request it.
3. Draft with a claim index: every sentence that asserts something gets a claim key, including "obvious" background.
4. For each sentence without a key, either delete it or mark it `[needs-evidence]` in place. Do not soften it into vagueness to keep it.
5. Check hedging honestly: "may", "suggests", "consistent with" must match the evidence level, not the author's enthusiasm.
6. Read the claim index against the map in reverse — any map claim not used is either an omission or a sign the argument drifted.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| draft | `manuscript/sections/<section>.md` | prose only; no unresolved `[needs-evidence]` in a submission-ready version |
| claim_index | `manuscript/sections/<section>.claims.json` | sentence → claim key → map entry; no dangling keys |

## Completion

- Every assertive sentence maps to a claim key, and every key resolves in the map.
- Unsupported sentences are removed or explicitly queued, and the queue is in the review `limitations`.
- Numbers in the text match the source artifact exactly, including units and intervals.

## Failure and recovery

- A claim key turns out weak mid-draft: return to `academic-claim-map`, do not compensate with stronger wording.
- A reviewer rejects a paragraph: fix the map first, then the prose; editing prose alone re-creates the same error.
