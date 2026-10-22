---
name: livebetter-plan-draft
description: Turn a triaged lifestyle goal into a dated plan with a measurable baseline, a gentle ramp, explicit stop conditions, and a review date.
domain: livebetter
stage: [output]
loop_role: render
consumes: [life_context]
produces: [plan_draft, plan_metrics]
deps: [livebetter-context-intake]
---

# Life Plan Draft

A plan is a hypothesis with a schedule. It must say what will be done, how it will be measured, when it will be reviewed, and when to stop.

## When to use

- Triage returned `self-manage` and a goal, baseline, and constraints are recorded.
- An existing plan needs a revision after a review date.

Not for: `clinician` or `emergency` triage — those produce a referral, not a plan.

## Boundary

- Does not recommend drugs, supplements, or doses of any kind.
- Does not prescribe extreme restriction (very low calorie, multi-day fasting, single-food diets) or rapid weight change targets.
- Does not build a plan on an uncountable baseline; measure first or say the plan cannot be sized.
- Does not promise outcomes. It states expected direction and the condition under which the plan is reconsidered.
- Does not skip stop conditions. A plan without them is not deliverable.

## Requires

`livebetter-context-intake` — this skill assumes a triage verdict of `self-manage` and a countable baseline. Without them, the plan would be sized by guesswork. How the context was gathered is the agent's call.

## Workflow

1. **Copy the goal verbatim** from the context; do not reword it into something easier.
2. **Start below capacity.** First two weeks at roughly half the intended volume; the purpose is adherence, not progress.
3. **Make each action verifiable**: what, how often, how long, under what condition it is skipped.
4. **Add a ramp** with explicit weeks and a rule for when to advance (e.g. two consecutive weeks at 90% adherence).
5. **Write stop conditions** as symptoms or situations: pain that persists past a day, dizziness, sleep collapsing, resting heart rate rising for a week, mood worsening. Each names the action to take and when to seek care.
6. **Define the measurement**: one primary metric, one or two supporting metrics, how often recorded, and where.
7. **Set a review date** (2–4 weeks). Plans are reviewed, not renewed by default.
8. **Open with the disclaimer line.** Then emit the plan and the metrics.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| plan_draft | `life/plan.md` | disclaimer on line 1; dated actions; ramp; stop conditions; review date |
| plan_metrics | `life/metrics.csv` | primary + supporting metrics, recording frequency, empty rows ready to fill |

## Completion

- Every action is verifiable by a third party from the written plan alone.
- The ramp has a stated advance rule; no action jumps from zero to full.
- Stop conditions exist and name both the action and the escalation threshold.
- The review date is explicit and in the future.
- No drug, supplement, or dose appears anywhere in the plan.

## Failure and recovery

- Baseline missing: stop and request it; an unsized plan is a guess.
- User asks for a drug or dose: decline, explain that this is outside the skill, and route to `livebetter-red-flag-check` / a clinician.
- User wants faster results than a safe ramp allows: shorten the review interval, not the safety margin.
