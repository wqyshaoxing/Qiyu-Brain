---
name: literature-search
description: Plan and run bounded scholarly searches, capture provenance for every result, and hand off a deduplicated matrix instead of a pile of links.
domain: academic-research
stage: [input]
loop_role: entry
consumes: [task_contract]
produces: [query_plan, result_matrix, search_log]
deps: [task-router, search-connectors]
---

# Literature Search

Decide what to look for, where to look, and how to prove later that the search was run as described. The deliverable is a matrix another person can re-run, not a link dump.

## When to use

- The task starts with "what has been done on X" and no prior matrix exists.
- A draft needs support for a claim that is not yet in the evidence map.
- A reviewer asks how candidates were selected.

Not for: judging novelty, or reading full texts — that is reasoning and later stages.

## Boundary

- Does not decide whether the literature is sufficient; it records what exists and what was excluded.
- Does not treat abstracts as full-text evidence. Each row carries its evidence level.
- Does not download paywalled or license-restricted PDFs; record the identifier and move on.
- Stops at a screened, deduplicated candidate set. Synthesis belongs to `evidence-synthesis`.

## Requires

`search-connectors` — the matrix comes from that primitive, or from any equivalent retrieval the agent chooses.

`task-router` — this skill assumes a signed task_contract (goal, non-goals, acceptance checks). Without it the search has no scope. Obtain it first if missing; how you do that is the agent's call.

## Workflow

1. Restate the question as 2–3 answerable sub-questions. If the request cannot be split, ask the user before searching.
2. Write inclusion and exclusion criteria, date range, and language limits **before** the first query. Queries chosen after seeing results are a bias, not a plan.
3. Run each query, record source, date, hits, and failures in `search_log`. Never silently retry into a different result set.
4. Deduplicate on DOI, then arXiv ID, then normalized title+year. Unresolvable collisions go to the log for human decision, not automatic merge.
5. Screen by title and abstract into include / maybe / exclude, with a one-line reason each.
6. Stop when two consecutive query variants return no new included records, or when the budget is spent. State which condition ended the search.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| query_plan | `docs/search/query-plan.md` | criteria written before queries; at least one reproducible query string |
| result_matrix | `docs/search/literature-matrix.csv` | identifier, source, year, evidence level, dedup key, screen decision |
| search_log | `docs/search/search-log.json` | every query with source, hits, errors, rate limits |

## Completion

- The matrix contains no row without a resolvable identifier.
- The plan's criteria predate the queries (check timestamps or ordering in the log).
- Excluded records remain visible with reasons — deletion is not screening.

## Failure and recovery

- Rate limits or 5xx: back off, retry bounded, then mark the query failed in the log and keep partial results.
- Source unreachable: record it as a coverage gap in the plan; do not substitute a different database silently.
