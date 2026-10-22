---
name: livebetter-briefing
description: Assemble a dated briefing on current affairs or commercial news that separates official statements, reporting, interpretation, and unverified claims.
domain: livebetter
stage: [output]
loop_role: render
consumes: [life_request]
produces: [briefing, source_ledger]
deps: [gateway-router]
---

# Briefing

A briefing is not an opinion piece and not a feed dump. Its value is that a reader can tell what happened, who said it, and what is still unconfirmed — without trusting the writer.

## When to use

- Someone needs the state of a topic: a policy direction, a market event, a public controversy.
- A claim is circulating and the person needs to know what is actually confirmed.

Not for: regulated text (use `livebetter-legal-basis`), policy documents (use `livebetter-policy-lookup`), or investment advice.

## Boundary

- Does not take a political or commercial stance, and does not predict outcomes.
- Does not present commentary as fact, or a single outlet as consensus.
- Does not name private individuals in a way that invites harassment; public figures acting publicly are different from private people caught in an event.
- Does not publish unverified claims without labelling them, and does not repeat a rumour to "debunk" it in detail.
- Does not omit timestamps. A briefing without dates is fiction with citations.

## Requires

`gateway-router` — this skill assumes the topic, time window, and audience are recorded. How the contract is obtained is the agent's call.

## Workflow

1. **Fix the question and the window**: what the reader needs to decide, and the date range that matters.
2. **Collect across source tiers** and keep them labelled:
   - *primary*: official statement, filing, press release, statistics release
   - *reporting*: outlets with editorial standards and named reporters
   - *industry*: trade press, analyst notes — interest declared
   - *unverified*: social posts, screenshots, anonymous accounts
3. **Separate four things** per item: what happened, who said it, how it is being interpreted, what remains unconfirmed.
4. **Cross-check** the load-bearing claims across at least two independent tiers; note where only one source exists.
5. **State the uncertainty** explicitly: contested facts, missing numbers, conflicting official statements.
6. **Close with what to watch**, not with a prediction: which document, date, or decision would resolve the open questions.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| briefing | `life/briefing.md` | dated items; four-way separation; uncertainty stated; no stance or forecast |
| source_ledger | `life/sources.json` | per item: tier, outlet, author, date, URL, what it supports |

## Completion

- Every item carries a date and a source tier.
- Facts, statements, interpretations, and unconfirmed claims are visually separated, not blended.
- Load-bearing claims have at least two independent sources, or are marked single-source.
- No sentence predicts an outcome or assigns motive.
- Open questions name what would resolve them.

## Failure and recovery

- Only one tier available: say so and mark the briefing as single-tier.
- Sources conflict: present both with dates; do not average them into a false consensus.
- Topic is contested and the user wants a verdict: decline the verdict, give the state of evidence and what would settle it.
