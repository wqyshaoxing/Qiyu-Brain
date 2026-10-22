---
name: livebetter-policy-lookup
description: Locate a policy document itself, with issuing body, document number, effective dates, eligible parties, and the local rules that implement it.
domain: livebetter
stage: [input]
loop_role: entry
consumes: [life_request]
produces: [policy_citations, eligibility_note]
deps: [gateway-router]
---

# Policy Lookup

A policy is not a news summary of a policy. The deliverable is the document, its identifiers, its dates, and who it actually covers.

## When to use

- A benefit, subsidy, permit, tax rule, or eligibility question depends on an official policy.
- A news item claims "the policy changed" and someone needs the actual text.

Not for: legal obligations between private parties — that is `livebetter-legal-basis`.

## Boundary

- Does not summarise a policy from a news article, a screenshot, or a repost. It quotes the source document.
- Does not mix national and local rules; every level gets its own citation.
- Does not present an expired or draft policy as current.
- Does not decide individual eligibility. It states conditions; the office decides.
- Does not omit the retrieval date — policies are amended without renaming.

## Requires

`gateway-router` — this skill assumes the question and the jurisdiction are recorded. How the contract is obtained is the agent's call.

## Workflow

1. **Fix jurisdiction, level, and period**: country, province, city, district; national vs local; which year's version.
2. **Search the issuer's own site first**: ministry, provincial government, human-resources or housing bureau. Use the document number when known.
3. **Capture identifiers**: issuing body, document number (文号), issue date, effective date, expiry or "to be revised" status, and URL.
4. **Quote the operative clauses** verbatim: eligibility, amounts, deadlines, required materials.
5. **Find the implementing rule**: national policy plus provincial implementation plus city细则; a national document rarely states local procedures.
6. **Mark what changed** if a newer version exists, with dates.
7. **State the next step**: which office or portal processes it, and what to bring.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| policy_citations | `life/policy-citations.json` | issuer, doc number, issue/effective/expiry dates, level, verbatim clauses, URL, retrieval date |
| eligibility_note | `life/eligibility.md` | who it covers, thresholds, required materials, local variations, where to apply |

## Completion

- Every policy has a document number and an official URL, or is marked as unfound.
- Effective and expiry dates are present; an expired policy is labelled expired.
- National and local rules are separated, never blended into one summary.
- Eligibility conditions are quoted, not paraphrased, or paraphrase is labelled.

## Failure and recovery

- Only news coverage found: say the source document was not located and list what was searched.
- Policy just changed: present old and new with dates and mark which applies to the user's timing.
- Local implementation missing: name the gap and the office that would hold it.
