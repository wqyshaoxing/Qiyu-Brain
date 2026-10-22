---
name: scientific-figure
description: Produce an editable, reproducible scientific figure from data or mechanism evidence, choosing the route by what the figure must prove and reviewing it at final size.
domain: academic-research
stage: [output]
loop_role: render
consumes: [evidence_map]
produces: [figure_source, figure_preview, figure_qa]
deps: [evidence-synthesis]
---

# Scientific Figure

A figure is an argument, not decoration. Pick the route from what must be shown, keep the source editable, and check the export at the size a reader will see.

Adapted from BoomSkills' `scientific-figure-production`; the judgment layer lives here now.

## When to use

- A manuscript needs a data plot, a mechanism diagram, or a figure assembled from parts.
- An existing figure has to be rebuilt as editable source instead of a flat image.

Not for: photograph retouching beyond presentation, or inventing structure the evidence does not support.

## Boundary

- Does not invent data, axes, error bars, or mechanism arrows that the evidence map does not support.
- Does not ship only a raster export; an uneditable final figure is a failed deliverable.
- Does not mix measured geometry with schematic geometry without labelling which is which.
- Does not treat a passing SVG/render check as scientific correctness; it only proves structure.
- Does not reuse a reference figure's *design* as if it were evidence.

## Requires

`evidence-synthesis` — this skill assumes an evidence map exists, so the claim and the numbers each element carries are traceable. How the map is produced is the agent's call.

## Workflow

1. **State the claim the figure must make** in one sentence. If it needs two figures, split it.
2. **Choose the route** from that claim:
   - *Quantitative plot* — preserve values, units, the independent sampling unit, exclusions, and the uncertainty definition. Deliver data plus runnable code; never only the image.
   - *Mechanism diagram* — inventory objects, relationships, and direction first; mark uncertain links explicitly; lay out legibly before adding detail.
   - *Three-dimensional asset* — only when volume or occlusion is the point. Keep the scene script, camera, lighting, and seed. Missing 3D tooling does not block a sufficient 2D figure.
3. **Check the data path**: raw values → plotted values → axis labels → caption. Any break means the figure is wrong, however good it looks.
4. **Encode consistently**: one font, one unit style, one colour meaning across panels; label every panel; keep line weights readable when printed at final size.
5. **Preview at final size**, not zoomed. Look for overlap, clipping, unreadable ticks, and arrows that point nowhere.
6. **Record provenance**: which data file, which script, which parameters, which seed.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| figure_source | `figures/<name>/source/` | editable source: script or spec plus its data, rerunnable |
| figure_preview | `figures/<name>/preview.png` | rendered at intended print size |
| figure_qa | `figures/<name>/qa.md` | claim, checks performed, unresolved assumptions, encoding choices |

## Completion

- The figure can be regenerated from the source directory alone.
- Every number or relationship in the figure traces to the evidence map or a named data file.
- The preview was inspected at final size, and the QA record says what was actually checked.
- Schematic and measured elements are distinguishable.

## Failure and recovery

- Source data missing: state it and stop; do not approximate a plot from a caption.
- Mechanism uncertain: draw the uncertain link dashed and say so; do not quietly omit it.
- Export unreadable at final size: change the layout, not the font size alone.
