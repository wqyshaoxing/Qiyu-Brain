---
name: architecture-tradeoff
description: Compare candidate designs against measured constraints, and record the decision plus its reversal cost, instead of defending one option.
domain: coding
stage: [reasoning]
loop_role: transform
consumes: [requirement_spec, codebase_map]
produces: [option_matrix, decision_record]
deps: [requirement-intake]
---

# Architecture Trade-off

Design is choosing under constraint. Two options compared on real numbers beats one option argued with adjectives.

## When to use

- A change touches module boundaries, data ownership, external interfaces, or concurrency.
- A decision will be expensive to undo later.
- Someone has already picked a design and the reason is "it's cleaner".

## Boundary

- Does not defend a favourite. If the matrix produces an option the author dislikes, the matrix stands.
- Does not design for imagined future scale. Constraints come from the requirement spec, not from optimism.
- Does not produce production code. A spike is allowed and must be labelled as one.
- Does not skip the reversal cost. A reversible decision deserves less debate than an irreversible one.

## Requires

`requirement-intake` — this skill assumes a requirement spec with executable acceptance checks. Comparing designs against guesses is not a trade-off. Obtain it first if missing; how you do that is the agent's call.

## Workflow

1. Collect real constraints: latency, throughput, data volume, team size, existing dependencies, deployment limits, compliance.
2. Write two to four options, including the boring one: change nothing, or extend what exists.
3. Score each option per constraint with the unit of measurement. "Fast" is not a score; "p95 under 200 ms at 50 rps" is.
4. Estimate reversal cost for each: what must be rewritten, migrated, or re-learned if this turns out wrong.
5. Choose, and write the decision record with the rejected options and the condition under which each would win.
6. Mark the parts of the design that are intentionally provisional.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| option_matrix | `docs/design/<slug>-options.md` | options × constraints, measured units, estimates labelled as estimates |
| decision_record | `docs/design/<slug>-adr.md` | decision, context, rejected options, revival condition, reversal cost |

## Completion

- Every constraint used to decide is traceable to the requirement spec or a measurement.
- Each rejected option states what would make it the right choice.
- Reversal cost is written in work, not in feeling.

## Failure and recovery

- No measurement available: mark the comparison as unmeasured and prefer the option that is cheapest to reverse.
- New constraint appears mid-implementation: reopen the record; do not append a justification for the existing choice.
