---
name: shared-scholarly-search
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

## Invocation

`python scripts/search.py` — 与 `runtime.json` 的 `parameters` 一一对应：

| param | cli | type | default | meaning |
| --- | --- | --- | --- | --- |
| query | `--query` | string | **required** | 检索式；问题拆成 2–3 个变体 |
| out | `--out` | string | **required** | 产物目录 |
| providers | `--providers` | string | `arxiv,crossref,openalex` | 逗号分隔 |
| limit | `--limit` | integer | 20 | 每个来源条数，1–100 |
| plan | `--plan` | flag | false | 只打印计划，不联网 |
| force | `--force` | flag | false | 允许覆盖已有产物 |

布尔参数是 `store_true`：出现即真，不要写成 `--plan true`。

## Workflow

1. `--plan` first: it prints the providers that will run, which keys are present or missing, and the output paths, without touching the network.
2. Default sources are the three that need no key at all: `arxiv`, `crossref`, `openalex`.
3. `semantic_scholar` exists but is **not** in the default set: anonymous access measured 3/3 HTTP 429 (shared pool saturated). A key raises the limit; it is intentionally not configured here, so expect this source to fail with an explicit 429 message rather than silently returning nothing.
4. Write the query and its intent. If the query is a question, split it into 2–3 query variants rather than one long sentence.
5. Run with an explicit provider list and limit. Defaults are conservative: max 20 results per provider, 1 request per second per provider.
6. Read `search-log.json` before trusting the matrix. Failed or rate-limited providers are coverage gaps, not empty results.
7. Deduplicate by DOI, then arXiv ID, then normalized title + year. Collisions that cannot be resolved go to the log, never merged silently.
8. Hand the matrix to the caller; leave screening decisions to it.

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
