---
name: evidence-synthesis
description: Map every candidate claim to supporting, contradicting, and missing evidence, and surface contradictions before any drafting begins.
domain: academic-research
stage: [reasoning]
loop_role: transform
consumes: [result_matrix, search_log, fulltext_notes]
produces: [evidence_map, contradiction_log]
deps: [literature-search]
---

# Evidence Synthesis

Turn a candidate set into a defensible claim structure. The output is a map from claim to evidence, including what is missing and what disagrees — not a summary paragraph.

## When to use

- A literature matrix exists and now needs to become an argument.
- Two sources appear to conflict and someone must decide whether they really do.
- Before writing any sentence that asserts a relationship.

Not for: producing prose. Prose comes after the map, in `paper-draft`.

## Boundary

- Does not read sources for you; it consumes notes and verifies their linkage.
- Does not resolve conflicts by voting. Contradiction is reported, not averaged away.
- Does not upgrade evidence level. An abstract-derived note stays abstract-level forever.
- Does not judge fraud; it flags patterns that need human or institutional review.

## Requires

`literature-search` — this skill assumes a screened, deduplicated matrix plus its search log. If neither exists, the claim map would be built on nothing. Obtain it first if missing; how you do that is the agent's call.

## Workflow

1. Enumerate candidate claims as single sentences with one verb each. A claim with "and" is two claims.
2. For each claim, attach citations that support it, contradict it, or are silent but relevant. Silent evidence is recorded, because absence usually means something.
3. Mark the evidence level per citation: full text, abstract only, second-hand citation, or memory. Anything below abstract is not evidence.
4. Compare contradictory pairs on design, population, measurement, and analysis before declaring a real conflict. Most conflicts are scope differences.
5. Check for the common failures: citation of a citation, effect size reported without interval, correlation stated as cause, sample described as representative without a sampling frame, and images or numbers that cannot be traced to a source file.
6. Write the map and the contradiction log, then mark unresolved items explicitly.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| evidence_map | `docs/analysis/evidence-map.json` | one entry per claim; support/contradict/silent arrays; evidence level per citation |
| contradiction_log | `docs/analysis/contradictions.md` | each conflict with compared attributes and a verdict: real / scope difference / unresolved |

## Completion

- No claim in the map has an empty evidence array and no explicit `unsupported` marker.
- Every "resolved" contradiction states the attribute that explains it.
- Unresolved items are listed with what would settle them.

## Failure and recovery

- A source cannot be obtained: mark the claim `unsupported` rather than deleting it, so the gap stays visible downstream.
- Notes contradict the matrix: trust the note only if it is traceable to a file; otherwise reopen the search log and re-derive.
