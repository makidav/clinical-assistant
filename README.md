# Clinical-Assistant — a Virtual Clinical Team as a single Agent Skill

**An 8-phase clinical reasoning and medical evidence workflow for Claude, built to be verifiable rather than merely fluent.** It runs differential diagnosis, evidence appraisal, a 13-perspective clinical board, and treatment planning — and it refuses to state more confidence than the evidence underneath it supports.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)
![Version](https://img.shields.io/badge/version-6.8-blue?style=flat-square)
![Self-contained](https://img.shields.io/badge/dependencies-none-success?style=flat-square)
![Language](https://img.shields.io/badge/language-EN%20%7C%20ES-informational?style=flat-square)
![QA gates](https://img.shields.io/badge/QA%20gates-60%20(28%20blocking)-orange?style=flat-square)

> ### ⚠️ Read this first
> This skill produces **research and decision-support drafts for qualified clinicians**. It is **not** a medical device, does not diagnose, does not prescribe, and does not replace a licensed professional. Every output carries a DRAFT header. The engineering targets in this repository are software quality metrics — **they are not clinical performance claims and must never be quoted as such.**

---

## Why this exists

Most medical AI output has the same failure mode: it is fluent, plausible, well-formatted, and impossible to check. The dangerous part is not that it is sometimes wrong — it is that **wrong and right look identical**.

This skill is built around one idea: *a clinician should be able to audit any statement in under thirty seconds.* Everything else follows from that.

| The usual failure | What this does instead |
|---|---|
| Confident prose, unverifiable claims | Every conclusion carries a confidence band, its basis, and **what would change it** |
| Citations that look real | Every PMID/DOI is resolved **and checked for retraction** — a retracted paper resolves perfectly |
| Anchors on the diagnosis it was given | Deep-research loop receives the **phenotype only**; prior labels withheld and later audited |
| "Order these tests" | Every test carries pre-test → post-test probability and is **dropped if it changes nothing** |
| Guidelines ranked by brand | Guidelines appraised with **AGREE II**; diagnostic studies with **QUADAS-2** |
| Findings that don't fit get discarded | The **residue list** — unexplained findings are tracked as signal, not noise |
| Inherits "already ruled out" as fact | Every exclusion is **audited** — a normal coagulation panel does not exclude factor XIII deficiency |
| Works forward from the diagnosis it was given | The differential is **rebuilt from presenting features first** — the anchor is strongest when the given diagnosis is correct |
| One guess when data is missing | A **decision tree** with the missing variable named as the hinge |
| Everything points toward more intervention | A **goals-of-care axis** runs parallel: disease-directed and comfort-directed arms written at equal depth |
| Newer sounds better | **N0–N3 novelty ladder**: preprints inform the differential, never the plan |

---

## How it operates

A router reads the request first and runs **either one focused task or the full workflow** — you never have to know which phase you want.

```
                 ┌─ FOCUSED MODES ──────────────────────────────┐
P0 · ROUTER ─────┤ ask · evidence · synthesis · frontier         │
 (always first)  │ deep-dx · board · plan · imaging              │
                 │ appraise · report · update                    │
                 └──────────────────────────────────────────────┘
       │
       └─ FULL CASE ──────────────────────────────────────────────
P1 INTAKE → [P2b IMAGING] → P2 EVIDENCE (A/B/C) → [P2c DEEP RESEARCH]
   → P3 GRADE + APPRAISAL → P4 BOARD → P5 PLAN → P6 REPORT → P7 QA → [P8 UPDATE]
                    ↑                     │
                    └─────────────────────┘
              diagnostic deadlock → re-enter deep research
```

The router reads **three independent axes** from one sentence, which is what stops keyword collisions:

| Axis | Determined by | Example |
|---|---|---|
| **Mode** | the *object* of the request | "analyze this case" → full workflow |
| **Deliverable** | the *format* word | "give me a **report** on GLP-1 studies" → literature mode, packaged as a document |
| **Language** | the user's language | full EN / ES parity |

### The 12 modes

`ask` · `case` (full workflow) · `evidence` (study list + sources) · `synthesis` (cross-study analysis) · `frontier` (what changed recently) · `deep-dx` (undiagnosed phenotype) · `board` · `plan` · `imaging` · `appraise` (one paper) · `report` · `update`

Ask in plain language — *"busca estudios donde el CKM se trata con agonistas GLP-1"* routes to synthesis; *"analiza este caso"* routes to the full workflow.

---

## What each phase contributes

| Phase | Embedded capabilities | What it adds to reliability |
|---|---|---|
| **P0 · Router** | intent classification | Focused answers stay focused; safety **upshifts** are mandatory — a literature question containing a patient in danger abandons the mode |
| **P1 · Intake** | structured anamnesis, red-flag screen, validated risk scores, specialty routing | Captures **occupational exposure with up-to-50-year latency**, **personal baselines and rate of change**, and a distinct intake shape for **episodic** presentations |
| **P2b · Imaging** | native vision analysis | Conditional but **mandatory when an image exists** — a decisive finding read informally is one nobody audited |
| **P2 · Evidence** | 3 parallel tracks — diagnostic criteria, treatment thresholds, **frontier scan** | Guideline hierarchy, ≥3 sources, **conflicts surfaced not resolved silently**; bidirectional drug-interaction matrix |
| **P2c · Deep research** | bounded phenotype-first loop | **Anti-anchoring**, rarest-feature-first, regression/trigger heuristics, dual-pathology check, hard 4-cycle budget with explicit stop rules |
| **P3 · GRADE + appraisal** | citation gate, retraction gate, Bayesian test engine, AGREE II / QUADAS-2 / RoB 2 / ROBINS-I / AMSTAR-2 | The heart of the reliability layer — see below |
| **P4 · Board** | 13 archetypes with declared blind spots | Structured disagreement; **deadlock is declared honestly**, not papered over |
| **P5 · Plan** | conditional decision trees, workup sequencing, two-axis planning | Ordered **treatable-first**, not probability-first; when trajectory warrants it, disease-directed and comfort-directed arms are written in parallel — never one as the other's fallback |
| **P6 · Report** | CARE/CONSORT-aware reporting | Traceable structure; novelty provenance stated |
| **P7 · QA** | 88 gates, 48 blocking · 9-attack red team | Nothing ships that fails a blocking gate |
| **P8 · Update** | targeted re-run with diff | New data collapses the right branch; **frontier re-check at 6 months** — a plan goes stale without the patient changing |

### The 13-perspective board

The Architect · Empiricist · Contrarian · Pragmatist · Minimalist · Sentinel · Historian · Futurist · Ethicist · Patient Advocate · Strategist · Geneticist · Outsider

Each carries a **declared blind spot**, and they are selected for genuine tension rather than agreement. The Minimalist exists to ask what to stop; the Contrarian exists to attack the leading hypothesis; the Outsider exists to ask what a different specialty would see.

---

## The reliability layer

This is the part that distinguishes the skill, and it is deliberately made of small, checkable rules.

<details>
<summary><b>1 · Citation integrity — resolution is not validity</b></summary>

Every identifier is resolved against PubMed and CrossRef, and the retrieved title and year are compared to what the document claims. Then a second check most tools skip:

**A retracted paper resolves perfectly.** It is still indexed, still carries its correct title. Existence checks pass it without hesitation. So every resolved reference is classified:

- 🔴 **Retracted** → remove the citation *and every claim resting on it*
- 🟡 **Expression of concern** → never load-bearing
- 🟠 **Corrected** → check whether the erratum touches *this* claim; it may leave it intact, or invert it
- 🟢 **Clear** → proceed

A third layer checks the **claim–source link** — citation drift, selective citation, causality inflation, and *context transfer mismatch* (a sensitivity measured in a referral cohort is not false in primary care; it is about different patients).

Unverifiable references are **removed, not flagged**. Identifiers are never invented to fill a field.
</details>

<details>
<summary><b>2 · Calibration — the goal is not maximum confidence</b></summary>

A system that says 95% and is right 70% of the time is **more dangerous** than one that says 70% and is right 70%, because unearned confidence stops the reviewer from checking.

Every conclusion carries three things: a **band**, its **basis**, and **what would change it**. A confidence with no stated falsifier is an opinion wearing a number. Confidence can never exceed the GRADE certainty beneath it, and certainty language ("clearly", "definitely", "diagnostic of") is banned outright.
</details>

<details>
<summary><b>3 · Diagnostic tests are evaluated, not just named</b></summary>

Naming a discriminating test is easy. This computes what it buys: pre-test probability → likelihood ratios → post-test probability on **both** result branches, against a stated decision threshold.

**If neither branch crosses a threshold, the test does not enter the workup.** It costs time and money and changes nothing.

Includes the PPV/NPV prevalence trap stated explicitly — a 90%/95% test at 10% prevalence yields ~67% post-positive probability, not 95%.
</details>

<details>
<summary><b>4 · Source quality is appraised with instruments, not impressions</b></summary>

GRADE asks "risk of bias?"; these answer it reproducibly. **AGREE II** for guidelines (replacing reputation-based ranking), **QUADAS-2** for the diagnostic accuracy studies feeding the Bayesian engine, **RoB 2** / **ROBINS-I** for therapy evidence, **AMSTAR-2** for systematic reviews.

Every domain judgment is reported **with the sentence of evidence that drove it**, so a reviewer can overturn it in seconds. Published evaluation shows LLM-applied bias assessment reaches only moderate agreement with experts — so these are presented as **reviewer aids, never automated verdicts**.
</details>

<details>
<summary><b>5 · Novelty is governed, not celebrated</b></summary>

| Tier | Can it reach a treatment recommendation? |
|---|---|
| **N0** established | ✅ normal GRADE path |
| **N1** emerging-validated | ⚠️ only labelled *beyond-guideline*, with specialist and stated uncertainty |
| **N2** investigational | ❌ trial pathway only, with NCT ID |
| **N3** frontier (preprints, case reports) | ❌ **blocked** — may inform the differential only |

Nothing is upgraded a tier within a session. *Newer ≠ better; rarer ≠ righter.*
</details>

<details>
<summary><b>6 · Missing data becomes a tree, not a guess</b></summary>

When a decision-critical variable is unavailable, the plan is written as a **conditional decision tree** with the missing variable named as the hinge and the resolving test attached — instead of a single confident path built on an assumption.

A standing **open requests** block carries what is needed *from the human*: specific documents, specific decisions, specific access. "The 2023 TSH, to establish the baseline" — not "more labs".
</details>

---

## Included tooling

Seven offline scripts, pure standard library, no API keys:

| Script | Purpose |
|---|---|
| `verify_citations.py` | Citation + **retraction** gate. `--selftest` verifies the logic offline |
| `validate_skill.py` | Structural linter — 53 safety invariants, install limits, cross-references, version consistency |
| `score_eval.py` | Aggregates evaluation cases into a report card with stop-the-line conditions |
| `score_bias.py` | Scores the bias-injection test — does the anti-anchoring rule actually hold? |
| `clinical_patterns.py` | Syndrome triads, occupational exposures with latency, red-flag differentials |
| `pharmacology_ref.py` | CYP/UGT roles, critical interaction pairs, narrow-therapeutic-index list |
| `roc_analysis.py` | AUC with bootstrap CI, Youden-optimal cutoff |

Plus `references/specialty-packs.md` — 13 specialty packs containing **routing information, not clinical facts**: authoritative bodies, must-not-miss lists, named criteria sets *to retrieve rather than recite*, and classic mimic pairs. Clinical values go stale; criteria names do not.

---

## Measuring it, not just asserting it

Everything above is reasoned design, and reasoning produces a *plausible* system — not a verified one. The literature on clinical LLMs documents a persistent **knowledge–practice gap**: models scoring near-perfect on exam benchmarks still fail on messy real cases.

`eval/` is the harness for finding out. It defines case sourcing, a scoring rubric, and three rules that keep the measurement honest:

1. **Establish the baseline before changing anything.** Otherwise "this version feels better" is all you will ever have.
2. **Any serious harm finding stops the release** — never averaged against good results. The harm lands on one patient; the correctness is distributed.
3. **Track overconfidence, not only accuracy.** A version that gets more accurate *and* more overconfident has probably got worse.

It also ships a **bias-injection protocol**: feed a case with a plausible but *wrong* prior diagnosis and check whether the anti-anchoring rule actually holds. That rule was built on reasoning and deserves to be tested rather than trusted.

The best evaluation cases are not published benchmarks — they are **the reviewing clinician's own de-identified closed cases**, because they match the real population and the real epidemiology.

---

## Installation

Copy the folder into your skills directory:

```bash
git clone https://github.com/makidav/clinical-assistant.git
cp -r clinical-assistant ~/.claude/skills/
```

Or in Claude Desktop / claude.ai: **Settings → Capabilities → Skills → Upload**, then select the `clinical-assistant` folder.

Verify the install:

```bash
cd clinical-assistant
python3 scripts/validate_skill.py SKILL.md      # expect: STATUS: CLEAN
python3 scripts/verify_citations.py --selftest  # expect: 10/10 passed
```

Nothing else to install — no packages, no API keys, no MCP servers. Optional connectors are used when present and have documented fallbacks when absent.

### Usage

Just describe what you need, in English or Spanish:

```
analyze this case and give me the report in Spanish
busca estudios recientes sobre el tratamiento del síndrome metabólico
find studies where CKM is treated with GLP-1 agonists
nadie sabe qué tengo — [phenotype]
what changed in MASLD treatment this year?
```

The router declares the mode it selected in one line, and you can correct it in one word.

---

## Limitations

Stated plainly, because a tool that hides these is harder to use safely:

- **Not a diagnostic device.** Output is a draft for a qualified clinician, always.
- **Decision thresholds are not pre-set.** The skill requires them to be declared per case — correct, but it means output quality depends on who declares them.
- **Bundled pattern tables are hypothesis prompts, not databases.** Anything they return needs literature confirmation.
- **Retraction data lags.** Very recent retractions may not be indexed yet.
- **The specialty must-not-miss lists are screening prompts, not differentials.** Absence from a list means nothing.
- **Appraisal instruments need human supervision.** They structure the judgment; they do not replace it.
- **No published accuracy figures.** The evaluation harness ships empty by design — run it on your own cases rather than trusting a number produced elsewhere.

---

## Provenance

Original work, CC BY 4.0. Reasoning frameworks adapted with attribution from:

- **ToolUniverse** (Mims Lab, Harvard Medical School) — Apache-2.0 — guideline hierarchy, test-purpose taxonomy, bidirectional interaction analysis, occupational screening, three bundled reference scripts
- **AIPOCH medical-research-skills** — MIT — retraction status taxonomy, citation-drift and context-transfer taxonomy, contradiction taxonomy, citation roles
- Personal-baseline and residue reasoning adapted from a published n=1 case study on episodic thyroid disease

Appraisal instruments (AGREE II, QUADAS-2, RoB 2, ROBINS-I, AMSTAR-2) and reporting standards belong to their respective consortia; this skill describes **when and how to apply them** and does not reproduce their forms. See [`NOTICE.md`](NOTICE.md) for full attribution and modifications, including a bug fix contributed back to an upstream script.

---

<sub>Clinical decision support · differential diagnosis · rare disease · evidence appraisal · GRADE · medical AI · Claude Agent Skill · bilingual EN/ES</sub>
