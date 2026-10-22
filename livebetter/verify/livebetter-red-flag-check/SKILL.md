---
name: livebetter-red-flag-check
description: Re-screen a lifestyle plan for emergency signs, contraindications, and missing stop conditions before it reaches the user, and block delivery when any is present.
domain: livebetter
stage: [verify]
loop_role: verify
consumes: [life_context, plan_draft]
produces: [red_flag_screen, escalation_note]
deps: [livebetter-context-intake]
---

# Red Flag Check

The last gate before a plan is handed over. Its job is to be unpopular: it blocks.

## When to use

- Before any lifestyle plan, routine, or habit protocol is delivered.
- Before revising an existing plan for someone whose condition or medication has changed.

Not for: diagnosing. It screens and escalates; it does not interpret symptoms.

## Boundary

- Is not a diagnosis and does not rank probabilities. A possible emergency is handled as an emergency.
- Does not clear a plan for pregnancy, children, eating disorders, cardiac disease, diabetes, or psychiatric conditions; those need a clinician's sign-off.
- Does not accept "the user seems fine" as a negative screen. Absence of an answer is not a no.
- Does not soften a block into a warning to keep a deadline.

## Requires

`livebetter-context-intake` — this skill assumes a recorded context with a triage verdict. Without it, there is nothing to screen against. How the context was gathered is the agent's call.

## Workflow

1. **Re-ask the emergency set** at delivery time, not only at intake. Symptoms change; a screen from last week is not a screen.
2. **Check the plan against the person**: pregnancy or attempting conception, under-18, known cardiac/metabolic/renal condition, eating-disorder history, current medications, recent surgery, disability or injury. Any match means `block` or `clinician`, not "proceed carefully".
3. **Check the plan's own safety**: intensity ramp, volume jump, fasting or extreme restriction, supplement or drug suggestions, exercise with acute illness, heat or dehydration risk.
4. **Check the stop conditions**: every plan must state what to do when a symptom appears, and when to stop entirely. Missing stop conditions block delivery.
5. **Check the disclaimer and sourcing** actually present, on line one of the artifacts.
6. **Decide**: `pass`, `block`, or `clinician`. Only `pass` may ship; `clinician` ships the referral instead of the plan.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| red_flag_screen | `life/red-flag-screen.json` | each red-flag group asked, answer, verdict; contraindication matches |
| escalation_note | `life/escalation.md` | for block/clinician: what to say, whom to see, what to bring |

## Completion

- Every red-flag group has an explicit answer or is recorded as unanswered (which blocks).
- Contraindication list was checked against the recorded context, not assumed empty.
- The plan states stop conditions; if it does not, delivery is blocked.
- Verdict is one of `pass` / `block` / `clinician`, with a one-line reason.

## Failure and recovery

- Positive emergency screen: emit the escalation note only; no plan text, no reassurance.
- User pressure to skip the check: refuse; record that the check was requested and declined.
- Uncertainty about a contraindication: treat as `clinician`, not as `pass`.
