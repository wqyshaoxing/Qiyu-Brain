---
name: academic-citation-audit
description: Audit every citation in a draft against the actual source text and reporting standards, blocking release while any mismatch remains unresolved.
domain: academic-research
stage: [verify]
loop_role: verify
consumes: [draft, claim_index, evidence_map]
produces: [audit_report, evidence_bundle]
deps: [academic-paper-draft]
---

# Citation Evidence Audit

The last gate before anything leaves the workspace. Read the cited source and the sentence that cites it, side by side, and record the comparison.

## When to use

- Before submission, preprint posting, or sending a draft to a collaborator as final.
- When a claim is load-bearing and the citation has never been read in full.

Not for: copy-editing, reference style formatting, or validating the analysis code.

## Boundary

- Does not fix citations silently; it reports and blocks, the author decides.
- Does not accept a citation because it appears frequently elsewhere.
- Does not declare misconduct. It records traceable mismatches; judgement belongs to editors and institutions.
- Does not pass a draft it could not fully read. Partial coverage is reported as partial, never as pass.

## Requires

`academic-paper-draft` — this skill assumes a draft with a claim index. Auditing prose without claim keys cannot tell an unsupported sentence from an uncited one. Obtain it first if missing; how you do that is the agent's call.

## Workflow

1. Enumerate every in-text citation with its sentence context.
2. For each, open the actual source and extract the passage that supports the sentence. Quote it, with page or section.
3. Compare at four levels: does the source exist; does it say this; does it say it about the same population and conditions; does the draft's strength match the source's strength.
4. Check the surrounding hygiene: retraction and correction notices, version (preprint vs published), self-citation rate, and whether a cited number appears in the source at all.
5. Classify each citation: verified / weak / unsupported / wrong-source / unreadable.
6. Produce the audit report with counts and a release decision. Any unsupported, wrong-source, or unreadable citation blocks release.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| audit_report | `docs/audit/citation-audit.md` | per-citation verdict, quoted source passage, coverage counts, release decision |
| evidence_bundle | `docs/audit/evidence-bundle.json` | claim key, citation, source identifier, quote, location, verdict |

## Completion

- 100% of in-text citations have a recorded verdict and a quote, or are explicitly listed as unreadable.
- The release decision follows the rules, not the deadline.
- `artifact_sha256` in the review covers the audited draft version.

## Failure and recovery

- Source unavailable: mark unreadable, block release, and list what access is needed.
- Draft changed after the audit: the audit is void; re-run rather than patching the report.
