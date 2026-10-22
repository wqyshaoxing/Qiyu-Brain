---
name: search-connectors
description: Query multiple scholarly sources through one bounded interface, with per-provider retries, rate limits, provenance logging, and DOI-level deduplication.
domain: shared
stage: [input]
loop_role: entry
consumes: []
produces: [query_plan, result_matrix, search_log]
deps: []
---

# Search Connectors

One interface over arXiv, Crossref, OpenAlex, PubMed, Semantic Scholar, and Exa. It returns a deduplicated, provenance-carrying matrix — not a list of links.

## When to use

- Any task whose first step is "find what exists".
- A domain skill needs retrieval but must not reimplement HTTP, retries, or dedup.
- Coverage has to be defensible: which source, when, with which query, and what failed.

## Boundary

- Does not read full texts. Every row is metadata-level evidence and says so.
- Does not judge relevance or novelty. Screening belongs to the caller.
- Does not retry into a different result set; a failed query is logged as failed.
- Does not overwrite earlier results without `--force`.
- Does not require any API key for the free providers. Paid providers are opt-in and off unless their key is configured.

## Workflow

1. `--plan` first: it prints the providers that will run, which keys are present or missing, and the output paths, without touching the network.
2. Write the query and its intent. If the query is a question, split it into 2–3 query variants rather than one long sentence.
3. Run with an explicit provider list and limit. Defaults are conservative: max 20 results per provider, 1 request per second per provider.
4. Read `search-log.json` before trusting the matrix. Failed or rate-limited providers are coverage gaps, not empty results.
5. Deduplicate by DOI, then arXiv ID, then normalized title + year. Collisions that cannot be resolved go to the log, never merged silently.
6. Hand the matrix to the caller; leave screening decisions to it.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| query_plan | `<out>/query-plan.md` | query variants, providers, limits, criteria written before running |
| result_matrix | `<out>/results.csv` | one row per record with source, identifier, evidence level, retrieval time |
| search_log | `<out>/search-log.json` | per-provider status, HTTP code, hits, elapsed, retries, errors, dedup counts |

## Completion

- Every requested provider appears in the log with a status.
- No row lacks a source and a retrievable identifier or URL.
- Dedup counts in the log match the difference between raw and written rows.
- Failures are reported as failures; a provider that returned nothing is distinguished from one that errored.

## Failure and recovery

- 429 or 5xx: bounded exponential backoff (3 attempts), then mark failed and keep partial results.
- Missing key for a paid provider: skip it, list it under `skipped` with the exact env var name.
- DNS or TLS blocked: report the provider as unreachable and name the network condition; do not substitute another source silently.
