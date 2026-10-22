---
name: livebetter-context-intake
description: Clarify a lifestyle goal, the current baseline, and the constraints that make a plan realistic, then triage whether this needs a clinician rather than a plan.
domain: livebetter
stage: [input]
loop_role: entry
consumes: [life_request]
produces: [life_context, triage_result]
deps: [gateway-router]
---

# Life Context Intake

The first job is not to give advice; it is to find out whether advice is the right output at all. A plan built on the wrong baseline fails quietly, and a missed red flag fails loudly.

## When to use

- Someone wants to change sleep, activity, diet, weight, stress, or a daily routine.
- A vague complaint ("I'm always tired") needs to become a measurable goal or a referral.

Not for: anything with acute symptoms — that routes to care immediately (see Workflow step 2).

## Boundary

- Is not medical advice. Every artifact opens with a one-line disclaimer, and no sentence asserts a diagnosis.
- Does not dose, combine, or stop medications. Drug interactions and dosages belong to a licensed clinician.
- Does not handle pregnancy, children, or known disease as routine optimisation; those route to a clinician.
- Does not collect more than the task needs, and never copies health details into `_memory`.

## Requires

`gateway-router` — this skill assumes a task contract exists (goal, acceptance, rigor level). Without it, "better sleep" has no definition of done. How the contract is obtained is the agent's call.

## Workflow

1. **Restate the goal as something observable**: not "be healthier" but "fall asleep before 00:30 on 5 of 7 nights for three weeks".
2. **Screen first, optimise second.** Ask the red-flag questions before anything else. If any answer is positive, stop: emit `triage_result` = `emergency`, give the local emergency number and what to say, and produce no plan. This gate is not optional and not deferrable.
3. **Record the baseline in countable terms**: current sleep window, steps or training per week, meals per day, screen time, pain level, energy 1–5. A baseline that cannot be counted cannot show change.
4. **Capture constraints that decide feasibility**: time budget, money, equipment, injuries, shift work, caregiving, dietary restrictions, medications (name only — not for adjustment), pregnancy, age band.
5. **Ask what was tried and why it stopped.** Past failure is the strongest predictor of the next failure.
6. **Triage**: `emergency` (stop), `clinician` (advice is to see a professional, with the reason and what to bring), or `self-manage` (a plan is appropriate).
7. Emit the context and the triage decision; do not draft the plan here.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| life_context | `life/context.json` | observable goal, countable baseline, constraints, prior attempts, triage verdict |
| triage_result | `life/triage.md` | disclaimer on line 1; verdict with reason; for emergency, the number and what to say |

## Completion

- The goal is observable and time-bounded; "improve" alone is not accepted.
- Red-flag screening actually happened and its answers are recorded, not assumed.
- Every constraint that could make a plan unrealistic is written down.
- The triage verdict is one of the three values; `emergency` produces no plan.

## Failure and recovery

- Red flag present: stop everything else and give the escalation script. Do not weigh probabilities.
- User refuses to answer screening questions: state that no plan can be given without them; offer general safety information only.
- Goal is actually a medical question ("why is my heart racing"): route to `clinician`, do not explain the symptom.
