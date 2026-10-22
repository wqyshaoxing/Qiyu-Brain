---
name: gateway-router
description: Read who the user is and what they actually need, then pick the domain skill and freeze goal, non-goals, and acceptance checks before work starts.
domain: gateway
stage: [gateway]
loop_role: route
consumes: [user_request, profile]
produces: [task_contract, routing_decision, open_questions]
deps: []
---

# Task Router

The only skill that runs before any domain skill. It answers three questions and refuses to answer a fourth: what does done look like, what is out of scope, and who should do it. The fourth — how to do it — belongs to the chosen domain.

## When to use

- Every request, including ones that look obvious. Short requests hide the most assumptions.
- When the user names a solution ("give me a dashboard") but not a goal.
- When a task changes scope mid-flight.

## Boundary

- Does not produce domain artifacts. No code, no analysis, no prose draft.
- Does not write user preferences. Profile updates go through `gateway-preferences`, with sources and confidence.
- Does not interrogate for completeness. Anything that can be reasonably assumed becomes a logged assumption with its cost.
- Does not guess sensitive attributes — health, religion, ethnicity, sexuality, precise location — unless the user volunteered them and the task needs them.
- Does not lower the contract when the user is in a hurry. Urgency lowers the rigor level, never the contract.

## Workflow

1. **Read the profile.** `_profile/user.md` and `_profile/preferences.md`: role, expertise, available tools, hard constraints, communication style. If a field would change the method and is missing, ask at most three questions; the rest becomes assumptions with confidence.
2. **Restate the request** as "after this, what is observable that is not observable now". If two or more readings differ in output, present them and let the user pick. Do not choose the convenient one.
3. **Pin the constraints** with three questions: who consumes the result, when is it needed, what does failure cost. Record each as confirmed or assumed, with source.
4. **Set the rigor level** from stakes × reversibility:
   - `quick-check` — cheap to undo, low cost; proceed, state assumptions.
   - `standard` — visible cost, undoable with effort; verify load-bearing assumptions only.
   - `high-assurance` — irreversible or safety-relevant; independent re-check and a named reviewer before release.
5. **Write the assumption register**: what the plan takes for granted, verification cost, consequence if wrong. Mark which must be checked before the first real step.
6. **Route**: choose the domain and the entry skill, and record the rejected candidates with reasons. If no domain fits, say so and propose a new partition instead of forcing the nearest bucket.
7. **Emit the contract**: goal, non-goals, acceptance checks (runnable by a third party), constraints, assumptions, rigor level, and the re-sign triggers.
8. **Read back three sentences** — what will be delivered, what will not be, how completion will be checked — and record who confirmed. Only then hand over.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| task_contract | `state/contract.md` | goal, non-goals, executable acceptance checks, constraints, assumption register, rigor level, re-sign triggers |
| routing_decision | `state/routing.json` | chosen domain and entry skill, rejected candidates with reasons |
| open_questions | `state/open-questions.md` | each with default, impact, blocking flag, cost of the default |

## Completion

- Every acceptance check can be executed by someone who was not in the conversation.
- The routing names a skill that actually exists in this repository.
- Re-sign triggers are specific enough for a third party to call them.
- The confirmation record names the contract version, or states that the contract was never confirmed.

## Failure and recovery

- User unavailable: issue a draft contract marked unconfirmed, prefer the most reversible reading, and surface that status at delivery.
- Goal changes mid-task: mark the old contract superseded and re-sign. Never edit a signed contract in place.
- No domain fits: propose a partition with a minimal contract rather than stretching an existing one.
