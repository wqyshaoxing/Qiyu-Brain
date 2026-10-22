---
name: preference-distillation
description: Distil durable preferences and identity facts from the conversation into the profile, separating one-off requests from standing rules.
domain: gateway
stage: [gateway]
loop_role: transform
consumes: [task_contract]
produces: [profile_update]
deps: [task-router]
---

# Preference Distillation

The profile only earns its keep if it stays trustworthy. One bad inference ("the user prefers brevity") costs more than ten missing entries.

## When to use

- The user repeats the same correction across tasks.
- The user says "always do it this way", "I hate when", or rejects a whole class of output.
- A standing constraint emerges that will outlive the current task.

Not for: recording anything said once in passing.

## Boundary

- Does not infer sensitive attributes. Never write health, religion, ethnicity, sexuality, or precise location unless the user stated it and asked for it to be remembered.
- Does not promote a one-off request to a standing preference. The test: would the user be annoyed if this were applied next month without asking.
- Does not overwrite user-authored lines. New entries are appended and marked; conflicts are recorded as superseded, not deleted.
- Does not rewrite global style after a single complaint. Three repetitions or an explicit "always" is the bar.
- Does not store project details in `_profile`. Project conventions live with the project.

## Workflow

1. Collect candidates and classify each: one-off request / project-level convention / durable preference / identity fact.
2. Attach source — which exchange, what was said — and a confidence level. Unconfirmed means low confidence.
3. Check conflicts against existing entries. A genuine reversal marks the old entry `superseded_by`, preserving history.
4. Write only durable preferences and stable identity facts to `_profile/`; everything else stays in the task workspace.
5. Ask the user to confirm new entries, at most three at a time. Batch confirmation beats interrupting every turn.
6. Record rejected inferences so the same guess is not repeated.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| profile_update | `_profile/.updates/<timestamp>.json` | per entry: text, target file, class, source, confidence, status (proposed/accepted/rejected/superseded) |

## Completion

- Every written entry has a source and a confidence level.
- No sensitive attribute appears without explicit user instruction.
- Rejected inferences are recorded, not silently dropped.
- The profile diff contains no project-specific detail.

## Failure and recovery

- User denies an entry: mark it `rejected`, keep the record, and stop re-inferring it.
- Two entries conflict and the user is unsure: keep both, surface the conflict at the next task rather than resolving it by guessing.
