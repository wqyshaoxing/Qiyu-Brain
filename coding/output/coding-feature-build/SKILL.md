---
name: coding-feature-build
description: Implement the smallest change that satisfies the spec, with tests and a diff summary a reviewer can verify line by line.
domain: coding
stage: [output]
loop_role: render
consumes: [requirement_spec, decision_record]
produces: [patch, test_report, change_summary]
deps: [coding-architecture-choice]
---

# Feature Implement

Write the change the spec asks for and nothing else. Scope creep during implementation is the most common way a reviewed design becomes unreviewable code.

## When to use

- The spec and the design decision exist and the work is ready to be built.
- A failing test needs a minimal fix.

## Boundary

- Does not add unrequested features, refactors, renames, or dependency upgrades.
- Does not change public interfaces without an explicit spec line.
- Does not commit, push, or open pull requests unless asked.
- Does not report success from a green run alone; the tests must actually exercise the acceptance checks.

## Workflow

1. Write or identify one failing test per acceptance check, before the implementation. If a check cannot fail, it is not a test.
2. Implement the smallest change that makes them pass. Prefer deleting code to adding it.
3. Run the tests, then run the neighbouring suites that share the touched modules.
4. Self-review the diff: every hunk must map to a spec line or a test. Anything that does not, revert it.
5. Check the failure paths: empty input, error branches, cleanup on exception.
6. Write the change summary: what changed, what deliberately did not, and what the reviewer should look at first.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| patch | `changes/<slug>.diff` | hunks map to spec lines; no drive-by edits |
| test_report | `changes/<slug>-tests.json` | new tests fail before and pass after; neighbouring suites listed |
| change_summary | `changes/<slug>-summary.md` | what changed, what did not, review entry points, known gaps |

## Completion

- Every acceptance check from the spec maps to a passing test.
- The diff contains nothing that cannot be explained in one sentence tied to the spec.
- Tests actually run in this environment; a skipped test is reported as skipped, not counted.

## Failure and recovery

- The minimal change requires a design change: stop and return to `coding-architecture-choice`; do not smuggle it in.
- Tests cannot run locally: say which ones and why, and mark the report accordingly.
