---
name: academic-zotero-archive
description: Archive validated PDFs into a Zotero cloud library with a timestamped collection, then verify what actually landed.
domain: academic-research
stage: [input]
loop_role: entry
consumes: []
produces: [import_result, import_report]
deps: [gateway-router]
---

# academic-zotero-archive

Ported from BoomSkills' `zotero-batch-pdf-import`; the contract now lives here.

## When to use

- Validated PDFs must be filed into a Zotero library with a traceable batch tag.
- You need to check cloud read access before writing anything.

## Boundary

- Does not decide which PDFs are worth keeping; screening happens upstream.
- Does not treat `check` as proof of write or file-edit permission.
- Does not claim metadata is correct because the upload succeeded.

## Requires

- `gateway-router` — obtain it first if missing; how is the agent's call.

Use the runtime `import` action for cloud archival. Begin with an offline `--dry-run`, then use `--yes` within the user's authorized source/library scope. The cloud adapter creates or reuses a timestamp collection and retains a batch tag, PDF validation, remote keys and all attempts. See [references/web-api.md](references/web-api.md) for arguments, metadata and recovery. `import-desktop` remains an explicitly selected local Connector alternative.

## Privacy

- Never store or echo personal names, usernames, email addresses, absolute local paths, private project identifiers, API keys, tokens, signed URLs, or credentials in the skill, its examples, manifests, logs, or deliverables.
- Use active-workspace-relative paths or paths relative to the skill folder. Reduce externally supplied absolute paths to neutral filenames or user-approved relative labels before recording them.
- Keep credentials in environment variables or an explicitly supplied secret file outside the skill and generated outputs.
- Scan outputs for private identifiers before delivery and redact them without altering evidence.

## Dependency detection and MCP fallback

- Default credentials come from uppercase system environment variables `ZOTERO_API_KEY` and `ZOTERO_LIBRARY_ID`; personal libraries use `user`, groups require their numeric ID and `group` configuration. The key itself must never enter config JSON or command arguments.
- On first use, the runtime opens the bundled browser guide for MinerU/Zotero registration, key creation and persistent environment setup. Missing prerequisites remain blocked. Restart the terminal/agent after changing system variables; `setup` reopens the guide. Read probes do not prove write/file permissions.
- Cloud archival requires pypdf and HTTPS access to Zotero and its authorized storage destination; no Desktop or MCP is required. The optional desktop action requires a reachable Connector and an existing selected collection.

## Workflow

Codex owns archival and recovery. Validate actual PDF structure, deduplicate by content SHA-256, and record cloud object keys before each write. Upload through authorization → file storage → registration, then read back MD5, content type, collection membership and tags. Keep API keys out of storage requests and signed upload URLs out of persisted artifacts. Reconcile saved keys/content tags after interruption; do not delete remote items or replace different file content to force success.

The cloud adapter does not recognize PDF metadata automatically. Supply explicitly reviewed bibliographic metadata to create a parent item; otherwise import a standalone PDF and mark metadata pending. Confirm parent fields against the input. Group libraries and Zotero Storage permissions/quota must be checked in the actual account; WebDAV uploads are not supported. Report invalid, failed, partial and unresolved entries without calling them imported.
## Artifacts

| role | kind |
| --- | --- |
| import_result | json |
| import_report | markdown |

