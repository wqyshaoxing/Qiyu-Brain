---
name: livebetter-playbook
description: Turn a life task into an ordered playbook with prerequisites, official channels, costs, time, decision points, and what to do when a step fails.
domain: livebetter
stage: [output]
loop_role: render
consumes: [life_request]
produces: [playbook, checklist]
deps: [gateway-router]
---

# Life Playbook

"攻略" fails in one of two ways: the steps are right but the prerequisites are missing, or the steps are wrong because nobody checked the official channel. This skill attacks both.

## When to use

- A concrete life task must be executed: open an account, contest a charge, apply for a permit, move house, handle a deposit dispute, plan a trip.
- Someone has already tried and got stuck at a specific step.

Not for: regulated questions where the answer is a clause — that is `livebetter-legal-basis`; not for health plans.

## Boundary

- Does not invent procedures. If the official channel cannot be found, the playbook says so and stops.
- Does not promise time or cost; it records what the official source states and marks it as an estimate otherwise.
- Does not bury failure branches in prose. Every step that can fail gets a branch.
- Does not assume a platform's policy is a rule; terms of service and regulation are different things.
- Does not skip prerequisites: identity, documents, eligibility, deadlines.

## Requires

`gateway-router` — this skill assumes the task and its deadline are recorded. How the contract is obtained is the agent's call. When the task is regulated, `livebetter-legal-basis` supplies the clause; when it is not, skip it.

## Workflow

1. **State the finish line** as a verifiable end state: "deposit returned to my account", not "resolve the deposit issue".
2. **List prerequisites first**: documents, eligibility, accounts, payment, waiting periods, deadlines. Missing a prerequisite is the most common cause of a wasted trip.
3. **Order the steps** with the official channel named for each: which office, which portal, which phone number, whether in person.
4. **Attach cost and time per step**, marked as official figure or estimate.
5. **Add decision points**: where the path forks on an answer, with the condition for each branch.
6. **Add failure branches**: what to do if rejected, timed out, or asked for something not listed.
7. **Add a verification step**: how the person confirms the outcome, and where to escalate if it does not happen.
8. **Compress to a checklist** that can be executed without reading the full playbook.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| playbook | `life/playbook.md` | finish line, prerequisites, ordered steps with channels, cost/time, branches |
| checklist | `life/checklist.md` | one line per action, checkable, ordered, includes escalation |

## Completion

- Every step names the channel where it happens; "submit online" without a URL is not a step.
- Every prerequisite is listed before the step that needs it.
- Failure branches exist for the steps most likely to fail.
- Costs and durations are marked official or estimated.
- The checklist can be executed by someone who has not read the playbook.

## Failure and recovery

- Official channel unknown: stop and say what to search for; do not reconstruct a procedure from memory.
- Steps differ by region: split the playbook by region instead of averaging.
- User reports a step failed: treat it as a branch, not an exception; update the branch rather than the whole playbook.
