---
name: coding-regression-gate
description: Reproduce the reported behaviour first, then run the relevant test matrix and review the diff for unstated scope changes.
domain: coding
stage: [verify]
loop_role: verify
consumes: [patch, test_report, change_summary]
produces: [verification_report, residual_risks]
deps: [coding-feature-build]
---

# Regression Gate

The difference between "the test passed" and "the problem is gone". Reproduce before believing, and check what else moved.

## When to use

- Any change about to be merged, delivered, or declared fixed.
- A bug report claims a symptom that was never reproduced.

## Boundary

- Does not fix the code while reviewing it; findings go back to `coding-feature-build`.
- Does not accept "existing tests still pass" as coverage evidence.
- Does not certify performance or scale without a measurement.
- Does not pass a change whose reproduction step is missing.

## Workflow

1. Reproduce the original symptom on the pre-change revision. Record the exact command, version, and input.
2. Apply the patch and run the same reproduction. If the symptom persists, stop.
3. Run the test matrix: the new tests, the neighbours sharing changed modules, and the integration path.
4. Review the diff independently: unstated scope, silent behaviour changes, error paths, logging of sensitive data, and backwards compatibility.
5. Check that the reported symptom and the asserted fix describe the same mechanism, not just correlated outcomes.
6. Record pass or block, with residual risks and the conditions under which the fix does not hold.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| verification_report | `changes/<slug>-verification.md` | reproduction on both revisions, test matrix results, diff review findings, verdict |
| residual_risks | `changes/<slug>-risks.md` | known untested paths, environment gaps, rollback plan |

## Completion

- Reproduction exists for the before and after revisions, with commands.
- Every finding in the diff review is either fixed or listed as accepted risk.
- Blocking findings are blocking; a deadline does not downgrade them to notes.

## Failure and recovery

- Cannot reproduce: report it as unreproducible and do not claim the fix works.
- Environment differs from production: state the gap in residual risks rather than assuming parity.
