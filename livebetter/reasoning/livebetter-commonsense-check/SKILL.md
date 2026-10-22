---
name: livebetter-commonsense-check
description: Decide whether a piece of everyday advice is a rule, a habit, an outdated belief, or a rumour, and say what evidence would settle it.
domain: livebetter
stage: [reasoning]
loop_role: transform
consumes: [life_request]
produces: [claim_check, sourcing_note]
deps: [gateway-router]
---

# Commonsense Check

"It's common knowledge" is the most expensive phrase in daily life. Most of what circulates is a habit from one region, a rule that changed, or a seller's talking point.

## When to use

- Someone repeats advice and acts on it: food storage, home safety, contracts, insurance, travel, appliances.
- Two sources disagree and the person needs to know which to trust.

Not for: regulated obligations (use `livebetter-legal-basis`) or policies (use `livebetter-policy-lookup`).

## Boundary

- Does not treat popularity as evidence. "Everyone says" and "my family always did" are not sources.
- Does not modernise a rule from memory; checks whether it still applies and where.
- Does not answer with "it depends" alone; names what it depends on and how to check.
- Does not give advice where being wrong is dangerous — that routes to `livebetter-red-flag-check` or a professional.

## Requires

`gateway-router` — this skill assumes the claim and the context (region, product, situation) are recorded. How the contract is obtained is the agent's call.

## Workflow

1. **Restate the claim as a testable sentence.** "Don't refreeze meat" vs "refreezing changes texture and safety in these conditions".
2. **Classify it**: official rule / manufacturer instruction / professional consensus / regional habit / commercial claim / rumour.
3. **Check the class-specific source**: regulation text, product manual, standards body, or a reputable reference. A seller's page is a commercial claim, not a standard.
4. **Check freshness and geography**: rules and best practice change; practices differ by climate, voltage, plumbing, and law.
5. **Look for the counter-case**: when would this advice be wrong, and who relies on the exception.
6. **Give a verdict**: `holds`, `holds-with-conditions`, `outdated`, `false`, or `cannot-determine` — with the condition or the missing evidence.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| claim_check | `life/claim-check.md` | claim restated, class, verdict, conditions, counter-case |
| sourcing_note | `life/sourcing.md` | each source with type, date, and why it counts as that class |

## Completion

- The verdict is one of the five values; "probably fine" is not one.
- Every verdict names the class of evidence behind it.
- Geography and date are stated where they change the answer.
- If the claim cannot be settled, the note says what evidence would settle it.

## Failure and recovery

- Only commercial sources available: say so and downgrade the verdict to `cannot-determine`.
- Claim is safety-critical and evidence is thin: route to a professional instead of guessing.
- Claim turns out to be a regulation: hand off to `livebetter-legal-basis` rather than paraphrase it here.
