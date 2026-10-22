---
name: academic-pdf-extract
description: Convert selected PDFs through MinerU into full.md plus image assets, keeping the extraction source read-only.
domain: academic-research
stage: [input]
loop_role: transform
consumes: []
produces: [full_md, extraction_report]
deps: [gateway-router]
---

# academic-pdf-extract

Ported from BoomSkills' `mineru-pdf-to-markdown`; the contract now lives here.

## When to use

- A PDF must become text and images a later stage can read.
- Equations or figures matter, so plain text extraction is not enough.

## Boundary

- Does not treat full.md as a faithful copy of a paper; formulas and tables need checking.
- Does not overwrite a completed extraction to retry a partial one.
- Does not pick which papers to extract.

## Requires

- `gateway-router` — obtain it first if missing; how is the agent's call.

Convert only user-selected PDFs. Prefer a configured MinerU MCP service; otherwise use the runtime `convert` action with workspace-relative paths. On first use the runtime opens a browser guide containing MinerU/Zotero official registration and key links. Store the MinerU Token in uppercase persistent system environment variable `MINERU_API_KEY`, restart the terminal/agent and use `doctor` to verify its presence; `setup` reopens the guide. Missing credentials block uploads. Save results beside the source as `<pdf-stem>_mineru/full.md`; do not overwrite the PDF or an existing complete result. Apply the user's existing authorization to the selected upload scope.

## Privacy

- Never store or echo personal names, usernames, email addresses, absolute local paths, private project identifiers, API keys, tokens, signed URLs, or credentials in the skill, its examples, manifests, logs, or deliverables.
- Use active-workspace-relative paths or paths relative to the skill folder. Reduce externally supplied absolute paths to neutral filenames or user-approved relative labels before recording them.
- Keep credentials in environment variables or an explicitly supplied secret file outside the skill and generated outputs.
- Scan outputs for private identifiers before delivery and redact them without altering evidence.

## Dependency detection and MCP fallback

- Check for a callable MinerU MCP service before using the bundled script. Report the selected route and whether it uploads PDFs externally.
- If neither route is available, explain the missing dependency and offer portable setup steps. Apply any MCP configuration only after explicit approval, use an environment-variable token, and verify with a non-sensitive connectivity check before uploading a PDF.

## Workflow

Start with runtime `doctor` (or `setup` to reopen the guide) in a new workspace, including when an existing MCP route will be used. Give the user the official browser setup path before attempting an unavailable credential-dependent route.

Check the selected PDF and existing extraction first. Prefer a callable configured MCP; otherwise use `convert` with an environment-variable token. State that this route uploads PDFs and apply existing authorization to the selected scope. Preserve full.md and images, compare extraction to the PDF and log failures separately. Analysis retries must not replace the extraction source.
## Artifacts

| role | kind |
| --- | --- |
| full_md | markdown |
| extraction_report | json |

