---
name: zh-en-translation
description: Translate an academic manuscript between Chinese and English without drifting in meaning, backed by a bilingual terminology map and an explicit fidelity contract.
domain: academic-research
stage: [output]
loop_role: render
consumes: [draft, claim_index]
produces: [translated_draft, terminology_map, qa_record]
deps: [paper-draft]
---

# Chinese ↔ English Academic Translation

Produce a publication-ready counterpart without changing scholarly meaning. Fluency that outruns the source is the failure mode, not a stylistic quibble.

Adapted from BoomSkills' `academic-zh-en-translation`; the judgment layer lives here now.

## When to use

- A manuscript needs a Chinese or English version, or a bilingual revision pass.
- A venue requires English but the evidence and notes are Chinese (or the reverse).

Not for: literary or marketing translation, or for rewriting the argument itself — that is `paper-draft`.

## Boundary

- Does not add, remove, or strengthen claims. A fluent sentence that is broader than the source is an error.
- Does not translate proper nouns, model names, symbols, variables, URLs, DOIs, file names, code, or citation keys without author or field convention.
- Does not treat a PDF as the editable source when substantive revision is expected; ask for LaTeX, DOCX, or Markdown.
- Does not invent terminology evidence. If the bilingual corpus does not support a mapping, say so.
- Does not silently resolve ambiguity in the source; flag it.

## Requires

`paper-draft` — this skill assumes a draft plus its claim index exist. Without claim keys a translator cannot tell which sentence carries which evidence. How the draft is obtained is the agent's call.

## Workflow

1. **Set the contract** before translating: source and target language, audience, venue style, authoritative file, and source format. Record all five; a wrong audience changes register across the whole document.
2. **Classify the field** (discipline, subfield, method, genre) and state confidence. If the classification could change terminology, ask instead of guessing.
3. **Build a bilingual evidence corpus**: at least ten works per language in the same field and direction, with DOI/URL, language, and the term evidence each one supports. Read abstracts, not paywalled full text; never bulk-copy copyrighted material.
4. **Build the terminology map** before translating prose: term, preferred rendering, evidence, context, confidence, and known alternatives or forbidden renderings. Do not force one-to-one where the target language needs a phrase.
5. **Translate**, then polish only for logic, cohesion, and register. Preserve hedging, modality, negation, causal strength, scope, tense where meaningful, numbers, units, equations, citations, and figure/table labels.
6. **Verify layout** in the source format: headings, captions, tables, equations, cross-references, and bibliography order must stay functional. Render and inspect every changed page plus all pages containing figures or equations.

## Artifacts

| role | file | checked for |
| --- | --- | --- |
| translated_draft | `translation/<name>.<ext>` | same format as source; structure mapping preserved |
| terminology_map | `translation/terminology-map.csv` | term, rendering, evidence, confidence; UTF-8 with BOM |
| qa_record | `translation/translation-qa.md` | pages inspected, ambiguities, conflicts with author glossary |

## Completion

- Every technical term in the output appears in the terminology map with evidence.
- Numbers, citations, and cross-references are byte-identical to the source unless the map records a deliberate change.
- Unresolved ambiguities are listed, not smoothed into fluent prose.
- The rendered output was actually inspected, not only generated.

## Failure and recovery

- No bilingual corpus available: translate with lower confidence, say so in the QA record, and mark terms as provisional.
- The author's glossary conflicts with corpus evidence: follow the author, record the conflict, and flag the factual risk.
- Layout breaks after translation: fix the structure, not the wording; a broken table is not a translation decision.
