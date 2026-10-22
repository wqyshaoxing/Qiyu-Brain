---
name: livebetter-legal-basis
description: Find and quote the actual statute or regulation behind a life situation, with clause text, effective date, jurisdiction, and where to confirm it officially.
domain: livebetter
stage: [input]
loop_role: entry
consumes: [life_request]
produces: [legal_citations, applicability_note]
deps: [gateway-router]
---

# Legal Basis

Life questions are often regulated questions: deposits, refunds, overtime, rental deposits, medical leave, consumer complaints. The job is to find the clause that governs it and quote it — not to give a legal opinion.

## When to use

- A life situation has a rule behind it: housing, employment, consumer rights, refunds, insurance, inheritance, traffic.
- Someone asks "is this allowed" or "can they do that" and the answer depends on a regulation.

Not for: predicting how a case would be decided, drafting contracts, or anything already in litigation.

## Boundary

- Is not legal advice and does not predict outcomes. It locates text and states conditions.
- Does not invent article numbers, dates, or quotations. If the text cannot be found, say so.
- Does not quote a repealed or not-yet-effective clause as if it applied.
- Does not generalise across jurisdictions: a national rule, a provincial rule, and a local measure are different sources.
- Does not skip the retrieval date; regulations change and a quote without a date is unverifiable.

## Requires

`gateway-router` — this skill assumes the question and the jurisdiction are recorded. "Can my landlord keep the deposit" has no answer without a place. How the contract is obtained is the agent's call.

## Workflow

1. **Fix the jurisdiction and the time**: country, province/city, and whether the question is about something that happened before or after a rule changed.
2. **Name the legal domain**: contract, labour, consumer, housing, administrative, family. The domain decides which statute to look in.
3. **Find the authoritative source**: legislature or government portal, not a reposted blog. Prefer the official consolidated text.
4. **Quote exactly**: article number, the clause text verbatim, issuing body, effective date, and the URL. Mark any paraphrase as paraphrase.
5. **State the conditions**, not just the rule: who it applies to, thresholds, exceptions, and what evidence the person would need.
6. **Mark uncertainty honestly**: if the clause is ambiguous, if local implementing rules are missing, or if there are conflicting interpretations, say so and point to the authority that decides.
7. **Route the next step**: the government office, hotline, or a licensed lawyer. This skill ends at "here is the text and where to confirm", never at "you will win".

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| legal_citations | `life/legal-citations.json` | per citation: article, verbatim text, issuer, effective date, retrieval date, jurisdiction, URL |
| applicability_note | `life/legal-applicability.md` | disclaimer on line 1; conditions, exceptions, ambiguity, and where to confirm |

## Completion

- Every citation carries article number, verbatim text, issuer, effective date, retrieval date, and jurisdiction.
- No quotation is paraphrased silently; paraphrase is labelled.
- Ambiguity and missing local rules are stated, not smoothed over.
- The next step names an official channel, not a promise of outcome.

## Failure and recovery

- Text not found: report the gap and the sources searched; do not reconstruct the clause from memory.
- Rule recently amended: present both versions with dates and mark which applies when.
- User asks "will I win": decline the prediction, give the conditions and route to a lawyer or the deciding authority.
