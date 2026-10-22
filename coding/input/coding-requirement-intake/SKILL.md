---
name: coding-requirement-intake
description: Turn a vague request into explicit scope, acceptance criteria, non-goals, and open questions before any code is written.
domain: coding
stage: [input]
loop_role: entry
consumes: [task_contract]
produces: [requirement_spec, open_questions]
deps: [gateway-router]
---

# Requirement Intake

A spec that a developer, a reviewer, and a test can all agree on. Written before the first line of code, because ambiguity found later is a rewrite.

## When to use

- A feature request arrives as a sentence, a ticket, or a screenshot.
- Behaviour is described by example but not by rule.
- A bug report needs to become a reproducible statement.

## Boundary

- Does not write code or design modules; that is `coding-architecture-choice` and `coding-feature-build`.
- Does not estimate schedules unless asked, and never as a substitute for scope.
- Does not invent business rules. Unknown rules become questions with a stated default.
- Does not define UI aesthetics beyond what a test can check.

## Requires

`gateway-router` — this skill assumes a task contract. Without it, scope and acceptance criteria would be invented here instead of agreed upstream. Obtain it first if missing; how you do that is the agent's call.

## Workflow

1. Describe current behaviour and expected behaviour as separate, observable statements.
2. Enumerate boundary cases explicitly: empty, huge, duplicate, concurrent, offline, malformed, permission-denied.
3. Write acceptance criteria as executable checks, each mapped to at least one boundary case.
4. State non-goals: what a reader might reasonably expect that is deliberately out of scope.
5. Record data and interface contracts: inputs, outputs, errors, and who owns validation.
6. List unknowns with defaults. Mark anything that would change the architecture as blocking.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| requirement_spec | `docs/requirements/<slug>.md` | current vs expected behaviour, boundary cases, acceptance checks, non-goals, data contract |
| open_questions | `docs/requirements/<slug>-questions.md` | each with default, impact, blocking flag |

## Completion

- Every acceptance check can be turned into a test without further interpretation.
- Every boundary case names the expected outcome, including "undefined is acceptable" where true.
- Non-goals exist and cover the most likely scope creep.

## Failure and recovery

- Requirements contradict each other: stop and surface the conflict; do not pick one silently.
- The user cannot answer: implement the most conservative reading behind a flag, and record it as assumed.
