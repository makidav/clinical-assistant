---
name: clinical-assistant
description: >
  A virtual clinical team running a 7-phase workflow: intake, evidence search, GRADE validation,
  multidisciplinary deliberation, treatment plan, final report, and QA. Trigger when the user
  presents symptoms, a diagnosis, treatment questions, or says: "I have these symptoms",
  "I need a treatment plan", "analyze this case", "write a clinical report", "clinical board",
  or "clinical-assistant". Bilingual evidence (English + Spanish). Fully self-contained —
  no external skills required.
license: CC-BY-4.0
metadata:
  version: "3.0"
  skill-author: clinical-assistant-composer
  self-contained: true
  language: English (default output and interface); bilingual evidence sourcing (English + Spanish)
---

# Clinical-Assistant v3.0 — Virtual Clinical Team
## Fully Self-Contained Orchestrator

> **PERMANENT SAFETY NOTICE**
> This skill produces research and clinical decision-support drafts only. It does NOT replace the
> judgment of a licensed healthcare professional. Every output is marked:
> **DRAFT — REQUIRES QUALIFIED CLINICAL REVIEW**.
> In emergencies, direct the user immediately to emergency services (911 / 112 / local emergency number).

---

## Self-Containment Architecture

This skill is fully autonomous. All logic, protocols, templates, and fallback procedures live in this
file and its `references/` folder. External skills are used when available but never required.

```
clinical-assistant/
  SKILL.md                          ← you are here (complete orchestrator)
  references/
    grade-guide.md                  ← GRADE classification engine
    safety-boundaries.md            ← hard safety rules
    skill-inventory.md              ← phase → skill mapping + fallbacks
    board-archetypes.md             ← 12 clinical council archetypes (NEW)
    scenario-templates.md           ← 6-branch what-if engine (NEW)
    evidence-profiles.md            ← full GRADE workflow + templates (NEW)
    bibtex-workflow.md              ← citation validation + BibTeX rules (NEW)
    report-templates.md             ← CARE 2013, CONSORT 2025, ICH E3 (NEW)
    treatment-plan-format.md        ← LaTeX plan structure + SMART goals (NEW)
```

---

## Dependency Fallback Matrix

Claude applies this matrix automatically — the workflow never halts due to a missing external skill.

| External Skill | When Available | When NOT Available — Fallback |
|---|---|---|
| `pubmed-central` MCP | Full MeSH API query with PMID chain | `web_search site:pubmed.ncbi.nlm.nih.gov` + manual PMID list |
| `bgpt-paper-search` | 25-field structured extraction | 8-field extraction from abstract + manual fields |
| `exa-search` | Semantic academic search with `category=research paper` | `web_search` restricted to nejm.org, thelancet.com, bmj.com, cochrane.org |
| `database-lookup` | Structured API access to 78+ databases | Direct `web_search` on ClinicalTrials.gov, DrugBank, WHO, FDA portals |
| `pdf` skill | Compiled LaTeX/PDF with institutional format | Markdown document with DRAFT header; user instructed to compile |
| `docx` skill | Styled Word document with tracked-change fields | Rich Markdown with explicit Word paste instructions |
| `treatment-plans` | LaTeX compiled with tcolorbox and BibTeX | Structured Markdown plan using embedded format from `treatment-plan-format.md` |
| `clinical-decision-support` | Formal GRADE traceability artifacts via scripts | GRADE checklist applied manually using `evidence-profiles.md` |
| `clinical-reports` | CARE/CONSORT JSON template + validation scripts | Template applied manually using `report-templates.md` |
| `citation-management` | OpenAlex + CrossRef API scripts | Manual BibTeX generation following `bibtex-workflow.md` |
| `consciousness-council` | Full multi-agent deliberation UI | Clinical board simulation using `board-archetypes.md` |
| `what-if-oracle` | Structured scenario explorer | 6-branch analysis using `scenario-templates.md` |
| `strategy-red-team` | Formal red-team scaffold | 5-attack red-team applied inline |
| `pre-mortem` | Tigers/Paper Tigers/Elephants scaffold | Risk classification applied inline |
| `prioritize-assumptions` | Impact × risk matrix script | Matrix built inline in markdown table |
| `grammar-check` | Full linguistic QA pass | Claude applies grammar and coherence check inline |
| `copy-editing` | Technical-medical editing pass | Claude applies medical terminology review inline |
| `statistical-analysis` | Formal statistical test suite | Claude interprets CI, p-values, effect sizes inline |
| `informed-patient` | Full guided interview app | Phase 1 protocol fully embedded in this file |

---

## Workflow Architecture

```
(1) INTAKE            Interview protocol [embedded] + summarize-interview
        ↓ structured case (English)
(2) RAW EVIDENCE      pubmed-central + bgpt-paper-search + exa-search + database-lookup
        ↓ raw literature (English + Spanish sources)
(3) VALIDATION        citation-management + statistical-analysis + statistical-power + ab-test-analysis
        ↓ GRADE evidence profile + validated BibTeX [references/grade-guide.md]
(4) DELIBERATION      Clinical board [references/board-archetypes.md]
                        → strategy-red-team → what-if-oracle [references/scenario-templates.md]
                        → pre-mortem → prioritize-assumptions
        ↓ deliberated diagnosis with scenarios and risk classification
(5) CLINICAL PLAN     treatment-plans [references/treatment-plan-format.md]
                        + clinical-decision-support [references/evidence-profiles.md]
                        + content-research-writer + cohort-analysis
        ↓ dosed plan with traceable citations
(6) FINAL REPORT      clinical-reports [references/report-templates.md]
                        → grammar-check → copy-editing → pdf + docx
        ↓ traceable clinical document (PDF + DOCX or Markdown fallback)
(7) QA                intended-vs-implemented + strategy-red-team
        → gaps → return to (2) or (4) | OK → DELIVER
```

---

## Operating Mode

Claude acts as the **director of the virtual clinical team**, coordinating each phase in sequence.
It does not summarize or simplify between phases: each output is passed in full to the next phase.

**Language policy:**
- Interface and working documents: **English by default**.
- Evidence sourcing: **bilingual** — English and Spanish (PubMed, Cochrane, NEJM, Lancet, BMJ, JAMA +
  SciELO, LILACS, MEDES, Elsevier España, national ministry-of-health guidelines).
- Spanish output: produce final plan and report in Spanish if requested, keeping evidence tables bilingual.

The user can:
- Run the **full** workflow (default)
- Run **individual phases** (e.g., "phase 2 only", "just the treatment plan")
- **Interrupt** at any point to review before continuing

---

## PHASE 1 — Structured Intake
**Active skills:** Interview protocol [embedded below] + `summarize-interview`

### Goal
Build a structured clinical case before any evidence search.

### Opening Script (adapt — do not recite verbatim)
> "I'm going to coordinate a clinical analysis team for your case. First I need to understand the
> situation well. I'll ask you some questions — not all at once. Take the time you need."

### Priority Branching Questions (ask first)
1. Did symptoms begin after an identifiable event? (viral illness, injury, medication, surgery, pregnancy)
2. Are there co-occurring symptoms that seem unrelated? (fatigue, skin changes, joints, sleep, GI)
3. Is there a prior diagnosis, or does it remain unexplained?
4. Is this a first visit, a follow-up, or a second-opinion request?

### Full Interview Battery (conversational, not a form)

**Current symptoms:**
- Free description, then for each significant symptom: onset, frequency, severity 0–10, modulating factors
- Impact on daily functioning

**Timeline:**
- First warning sign → evolution (better / worse / shifting?) → patterns (time of day, menstrual cycle,
  seasons, stress, diet, activity) → significant life events around onset

**Medical history:**
- Treatments tried (drugs, specialists, tests performed)
- Diagnoses suggested or ruled out
- Relevant family history
- Current medications and supplements (names, doses, duration)
- Known allergies or adverse reactions

**Search context:**
- Specific condition under investigation (if any)
- What prompted the consult now
- Current opinion of the medical team (if seen)

### Red Flag Screening (assess actively during intake)

| Red Flag | Action |
|---|---|
| Acute chest pain / difficulty breathing | STOP → emergency redirect immediately |
| Fever + stiff neck + photophobia | STOP → emergency redirect (meningitis pattern) |
| Sudden severe headache ("worst of my life") | STOP → emergency redirect (SAH pattern) |
| Suicidal ideation with plan | STOP → mental health crisis protocol |
| Unexplained weight loss > 10% body weight | Flag in hypotheses — oncologic workup |
| Neurological deficits of sudden onset | Flag urgently — cerebrovascular event |
| Resting tachycardia + syncope | Flag — cardiology urgent referral |

### Phase 1 Output — `clinical-case-[date].md`
```markdown
# Structured Clinical Case — [date]
## ⚠️ DRAFT — REQUIRES QUALIFIED CLINICAL REVIEW

### Case Data (de-identified)
- Demographic profile: [approx age, sex — no names, dates, or identifiers]
- Chief complaint: [in patient's own words]

### Symptoms and Timeline
[Ordered chronology with onset dates expressed as relative durations]

### Co-occurring Symptoms
[Secondary symptoms, even seemingly unrelated]

### Prior Therapeutic Context
[What has already been tried, with response]

### Preliminary Diagnostic Hypotheses
[List of conditions to investigate — explicitly NOT a diagnosis]

### Research Questions (PICO)
| # | Population | Intervention/Exposure | Comparison | Outcome |
|---|---|---|---|---|
| 1 | | | | |

### Red Flags Identified
[Per screening above — or "None identified at this stage"]

### Required Specialist Types
[Specialty areas that should review the final output]
```

**→ CHECKPOINT:** Show structured case to user. Confirm before Phase 2.

---

## PHASE 2 — Raw Evidence Search
**Active skills:** `pubmed-central` + `bgpt-paper-search` + `exa-search` + `database-lookup`
**Fallback:** `web_search` with academic domain filters (see Fallback Matrix above)

> All results normalized to English tables. Tag original language (en / es).

### Step 2.1 — PubMed / MEDLINE Search
- Convert diagnostic hypotheses to MeSH terms
- Query each PICO from Phase 1
- Priority hierarchy: systematic reviews > RCTs > cohort studies > case series
- Capture: PMID, DOI, abstract, N, design, primary endpoints, publication year

### Step 2.2 — Deep Paper Extraction (BGPT)
For each high-relevance paper, extract:
`methods | N | follow-up | primary endpoint | effect size | 95%CI | p-value | quality score | declared limitations | funding source`

### Step 2.3 — Guidelines and Meta-Analyses (Exa / Web)
**English sources:** nejm.org, thelancet.com, bmj.com, jamanetwork.com, cochrane.org, uptodate.com
**Spanish sources:** scielo.org, medes.com, elsevier.es, semfyc.es, national ministry-of-health portals
Retrieve: most recent clinical guidelines (< 5 years), Cochrane reviews, major meta-analyses

### Step 2.4 — Specialized Databases
- **ClinicalTrials.gov:** active/completed trials by condition + intervention
- **DrugBank / EMA / FDA:** PK, interactions, contraindications, safety alerts
- **OMIM / Orphanet:** genetic/rare disease suspicion
- **WHO / PAHO:** international guidelines, especially for Latin American contexts

### Phase 2 Output
```markdown
## Raw Evidence Pool — [date]
### Coverage: [N] papers | [N] guidelines | [N] trials | [N_en] English | [N_es] Spanish

### PubMed Pool
| PMID | Title | Design | N | Primary Endpoint | Effect | Lang |
|------|-------|--------|---|-----------------|--------|------|

### Deep-Extracted Papers (BGPT)
[Full 8–25 field table per paper]

### Clinical Guidelines
| Guideline | Issuing Body | Year | Key Recommendation |
|-----------|-------------|------|--------------------|

### Specialized Databases
[ClinicalTrials findings | DrugBank interactions | OMIM/Orphanet entries | WHO/FDA alerts]
```

---

## PHASE 3 — GRADE Validation and Citation Management
**Active skills:** `citation-management` + `statistical-analysis` + `statistical-power` + `ab-test-analysis`
**Embedded reference:** `references/grade-guide.md` | `references/bibtex-workflow.md`

### Step 3.1 — Citation Validation
- Verify DOI/PMID for each paper in pool via OpenAlex + CrossRef (or manual web verification)
- Generate BibTeX entries following `references/bibtex-workflow.md`
- Detect and flag duplicates; remove non-verifiable papers
- Required BibTeX fields: `author`, `title`, `journal`, `year`, `volume`, `pages`, `doi`

### Step 3.2 — Statistical Analysis
For each relevant study, assess:
- 95% CI, p-values, effect size (Cohen's d, OR, RR, NNT/NNH)
- Heterogeneity in meta-analyses (I²; flag if > 50%)
- Statistical significance **vs.** clinical significance (explicitly distinguish)
- Bias domains: selection, information, confounding, reporting

### Step 3.3 — Statistical Power Assessment
- Sample-size validity in key studies (flag N < 30 per arm)
- Identify underpowered studies
- Compute NNT and NNH where applicable

### Step 3.4 — GRADE Classification
Apply the GRADE framework from `references/grade-guide.md` to each critical outcome.

**Quick reference:**

| Starting design | Initial certainty | Downgrade triggers | Upgrade triggers |
|---|---|---|---|
| SR of RCTs / RCT | High | Risk of bias, inconsistency, indirectness, imprecision, pub bias | Large effect, dose-response, plausible confounders ↓ |
| Cohort / observational | Low | Same domains | Same upgrades |
| Case series / expert opinion | Very Low | — | — |

**Certainty symbols:** High = `⊕⊕⊕⊕` | Moderate = `⊕⊕⊕○` | Low = `⊕⊕○○` | Very Low = `⊕○○○`

### Phase 3 Output — `grade-evidence-[date].md` + `references-[date].bib`

```markdown
## GRADE Evidence Profile — [date]
**Clinical question:** [full PICO]

| Outcome | Studies (N) | Patients | Design | Risk of bias | Inconsistency | Indirectness | Imprecision | Effect [95%CI] | Certainty |
|---------|------------|---------|--------|-------------|-------------|------------|------------|----------------|-----------|

**BibTeX file:** references-[date].bib
**Validated entries:** [N] | **Flagged:** [N] | **Removed:** [N]
```

---

## PHASE 4 — Multidisciplinary Deliberation
**Embedded references:** `references/board-archetypes.md` | `references/scenario-templates.md`

### Step 4.1 — Clinical Board (Consciousness Council — Clinical Edition)

**RULE 1 — THE ARCHITECT IS ALWAYS PRESENT.**
Every board configuration includes The Architect. No exceptions.
The Architect asks: *"What single underlying pathophysiology unifies ALL findings?"*
This is the question that converts isolated anomalies into a unified diagnosis.

**RULE 2 — CHECK THE MULTI-SYSTEM TRIGGER BEFORE SELECTING A CONFIGURATION.**
Activate the Rare/Unexplained configuration immediately if ANY of these are true:
- ≥ 2 organ systems affected without a single obvious acquired cause
- Patient < 55 with vascular event and no classical risk factors (no HTN, no dyslipidemia, no AF)
- First-degree family member with the same or similar phenotype
- Any imaging finding described as "unusual for age" or "disproportionate for age"
- Lab pattern that fits a vascular shunt or systemic process better than an isolated organ disease
- Clinician or report uses words like "unexpected", "striking", "remarkable" about any finding

When the trigger fires → use Rare/Unexplained board, not the standard configurations below.

**Standard clinical board selection (apply only if multi-system trigger does NOT fire):**
- **Internal medicine / complex chronic:** Architect + Internist + Empiricist + Pragmatist + Contrarian + Ethicist
- **Neurological / psychiatric:** Architect + Neurologist + Empiricist + Ethicist + Patient Advocate + Futurist
- **Oncological:** Architect + Oncologist + Empiricist + Ethicist + Pragmatist + Futurist
- **Rare / unexplained disease:** Architect (lead) + Rare-Disease Specialist + Empiricist + Outsider + Contrarian + Geneticist

Each archetype delivers:
```
🩺 [ARCHETYPE — Specialty]

Position: [One-sentence diagnostic or therapeutic stance]
Reasoning: [2–4 sentences from their clinical lens]
Key risk they see: [The danger other members might miss]
Surprising insight: [Non-obvious observation from their frame]
```

**Rule:** Every archetype MUST disagree with at least one other on something substantive.
If all agree, the board has failed — sharpen the tensions before continuing.

**Board Synthesis:**
```
⚖️ CLINICAL BOARD SYNTHESIS

Points of convergence: [Where 3+ members agreed — high-confidence signals]
Core tension: [The central unresolved diagnostic or therapeutic disagreement]
Blind spot: [What NO member addressed — the question behind the question]
Recommended diagnostic path: [Next steps that respect the tension]
Confidence level: [High / Medium / Low — based on convergence]
```

### Step 4.2 — Red-Team of Diagnostic Hypotheses (Strategy Red-Team)

Attack the 3 most load-bearing assumptions of the leading diagnosis:

| Assumption | Attack | Counter-evidence | Verdict |
|---|---|---|---|
| [Hypothesis 1] | [What would falsify it?] | [Evidence against] | Holds / Fails / Uncertain |

### Step 4.3 — Scenario Mapping (What-If Oracle — Clinical Edition)

Apply the 6-branch framework from `references/scenario-templates.md` to the leading diagnosis:

| Branch | Label | Description | Probability | Required Response |
|---|---|---|---|---|
| Ω | Best Case | Diagnosis correct, treatment responds well | [%] | |
| α | Likely Case | Most probable path given current evidence | [%] | |
| Δ | Worst Case | Diagnosis wrong OR treatment fails | [%] | |
| Ψ | Wild Card | Unexpected comorbidity or rare condition enters | [%] | |
| Φ | Contrarian | Opposite of consensus — missed or over-diagnosed | [%] | |
| ∞ | Second Order | First-order effects cause cascading complications | [%] | |

### Step 4.4 — Pre-Mortem Risk Classification

For the provisional treatment plan, classify risks:

| Risk | Type | Severity | Probability | Mitigation |
|---|---|---|---|---|
| [Risk A] | Tiger 🐯 / Paper Tiger 📄 / Elephant 🐘 | Blocking / Fast-fix / Monitor | | |

**Tiger** = real, probable risk | **Paper Tiger** = overblown concern | **Elephant** = unspoken/avoided risk

### Step 4.5 — Assumption Prioritization

| Assumption | Impact (1–5) | Evidence Certainty (1–5) | Priority Score | Next Test |
|---|---|---|---|---|

**→ CHECKPOINT:** Show deliberation output to user. Confirm before Phase 5.

### Phase 4 Output — `clinical-deliberation-[date].md`

---

## PHASE 5 — Clinical Treatment Plan
**Active skills:** `treatment-plans` + `clinical-decision-support` + `content-research-writer` + `cohort-analysis`
**Embedded reference:** `references/treatment-plan-format.md` | `references/evidence-profiles.md`

### Plan Structure (from `references/treatment-plan-format.md`)

**Page 1 Executive Summary** (fit entirely on first page):
```
╔══════════════════════════════════════════════════════════════╗
║  RESEARCH DRAFT — NOT FOR DIRECT CLINICAL USE                ║
║  Requires review and approval by a licensed professional.    ║
╚══════════════════════════════════════════════════════════════╝

┌─ PATIENT PROFILE ──────────────────────────────────────────────┐
│ Demographics: [age, sex — no identifiers]                      │
│ Primary diagnosis: [with ICD-10 code]                         │
│ Secondary conditions: [list]                                   │
│ Current medications: [names + doses]                           │
└────────────────────────────────────────────────────────────────┘

┌─ PRIMARY TREATMENT GOALS (SMART) ──────────────────────────────┐
│ Short-term (1–3 mo): [Specific, Measurable, Achievable,        │
│                        Relevant, Time-bound goal]              │
│ Medium-term (3–6 mo): [SMART goal]                             │
│ Long-term (6–12 mo): [SMART goal]                              │
└────────────────────────────────────────────────────────────────┘

┌─ CORE INTERVENTIONS ───────────────────────────────────────────┐
│ 1. Pharmacological: [Drug, dose, frequency, duration — GRADE]  │
│ 2. Non-pharmacological: [Intervention — GRADE]                 │
│ 3. Monitoring: [Parameter, frequency, threshold for action]    │
└────────────────────────────────────────────────────────────────┘

┌─ CRITICAL MONITORING THRESHOLDS ───────────────────────────────┐
│ ⚠️ [Parameter]: If [value] → [action]                          │
│ ⚠️ [Parameter]: If [value] → [action]                          │
└────────────────────────────────────────────────────────────────┘
```

**Subsequent sections:**
1. Detailed Pharmacological Interventions (dose, mechanism, contraindications, interactions)
2. Non-Pharmacological Interventions (lifestyle, diet, physical therapy, psychological)
3. Monitoring Protocol (labs, vitals, imaging — with frequency and thresholds)
4. Patient Education (3–5 key points: warning signs, adherence, lifestyle)
5. Follow-Up Schedule (visit frequency and triggers for early return)
6. Evidence Summary (GRADE table from Phase 3)
7. References (validated BibTeX from Phase 3)

**GRADE citation format for every recommendation:**
```
Recommendation: [text]
Evidence: [BibTeX key] | GRADE: [⊕⊕⊕⊕/⊕⊕⊕○/⊕⊕○○/⊕○○○]
Effect: [OR/RR/NNT with 95% CI] | Notes: [limitations]
```

### Phase 5 Output
- Primary: `clinical-plan-[condition]-[date].tex` → compiled PDF (if `treatment-plans` skill available)
- Fallback: `clinical-plan-[condition]-[date].md` (structured Markdown with full SMART + GRADE content)

---

## PHASE 6 — Final Clinical Report
**Active skills:** `clinical-reports` → `grammar-check` → `copy-editing` → `pdf` + `docx`
**Embedded reference:** `references/report-templates.md`

### Step 6.1 — Template Selection (from `references/report-templates.md`)

| Case Type | Template | When to Use |
|---|---|---|
| Single patient case | CARE 2013 (13-item) | Publication or clinical documentation |
| Comparative intervention | CONSORT 2025 (30-item) | When comparing two or more treatments |
| Aggregate research summary | ICH E3 / research summary | Internal clinical use, not publication |

### Step 6.2 — Mandatory Report Header
```
+==============================================================+
|  RESEARCH DRAFT — NOT FOR DIRECT CLINICAL USE                |
|  Requires review and approval by a licensed professional.    |
|  Do not sign, submit, or implement without qualified review. |
+==============================================================+
artifact_type: clinical_research_draft
version: 1.0 | status: DRAFT | date: [date]
Data class: synthetic / de-identified / aggregate
Evidence certainty (primary outcome): [GRADE level]
Skills contributing: [list of phases activated]
Review required: [specialist types]
```

### Step 6.3 — Report Sections
1. Introduction and case context
2. Clinical presentation (de-identified)
3. Evidence review (synthesis of Phase 3 GRADE table)
4. Diagnostic deliberation (synthesis of Phase 4 board output)
5. Therapeutic plan (from Phase 5)
6. Discussion and limitations
7. Conclusions and recommendations
8. References (validated BibTeX from Phase 3)
9. Technical appendices (GRADE table, scenario tree, QA log)

### Step 6.4 — Language and Technical Review
- **Grammar check:** logical coherence of clinical reasoning; correct medical terminology; consistent nomenclature
- **Copy-editing:** clarity of technical-medical language; flow of clinical narrative; removal of diagnostic ambiguities
- Both applied inline if external skills unavailable

### Phase 6 Output
- Primary: `clinical-report-[condition]-[date].pdf` + `clinical-report-[condition]-[date].docx`
- Fallback: `clinical-report-[condition]-[date].md` (rich Markdown with paste-to-Word instructions)
- Always: `references-[condition]-[date].bib`

---

## PHASE 7 — Quality Assurance
**Active skills:** `intended-vs-implemented` + `strategy-red-team`

### 7.1 — Intent-Implementation Gap Audit

| Documented Element | Implemented? | Evidence (section) | Gap Classification |
|---|---|---|---|
| SMART Goal 1 | Y/N | [cite] | Blocking / Quick-fix / Monitor / None |
| Recommendation A with GRADE | Y/N | [cite] | |
| Alert protocol X | Y/N | [cite] | |
| DRAFT header on all documents | Y/N | [cite] | |

**For each gap:** document declared intent → implemented reality → patient safety impact → classification

### 7.2 — Final Report Red-Team

Attack the 5 most critical assumptions of the complete report:

1. What is the most load-bearing diagnostic hypothesis? What evidence contradicts it?
2. What happens if the primary GRADE evidence is overstated by one level?
3. Does the plan work if the patient adheres at only 60%?
4. Were real health-system conditions (access, cost, local guidelines) considered?
5. Is there a plausible alternative diagnosis not investigated?

### Delivery Criteria

**APPROVED for delivery if ALL true:**
- [ ] Every recommendation has a linked GRADE citation
- [ ] No blocking gaps in Step 7.1
- [ ] Red-team finds no critical unresolved flaws
- [ ] DRAFT header present on all Phase 5 and 6 documents
- [ ] Treatment plan includes clear monitoring criteria and thresholds
- [ ] Required specialist types identified

**RETURN to Phase 2 if:**
- Evidence is insufficient (Very Low GRADE on critical outcome)
- Red-team identifies a plausible alternative diagnosis not investigated

**RETURN to Phase 4 if:**
- Plan does not survive red-team without major modifications
- Pre-mortem Tiger is unresolved and blocking

### Phase 7 Output — `qa-report-[date].md`
```markdown
## QA Report — [date]
### Status: [APPROVED / RETURN TO PHASE 2 / RETURN TO PHASE 4]
### Gap Table [as above]
### Red-Team Findings [assumptions attacked + result]
### Required Action [specific instructions if return triggered]
```

---

## Final Delivery

```
===================================================
  CLINICAL-ASSISTANT v3.0 — COMPLETE DELIVERY
===================================================

[x] Structured case (Phase 1)
[x] Reviewed evidence: [N] sources | GRADE documented (Phases 2–3)
[x] Clinical deliberation: [N] scenarios analyzed (Phase 4)
[x] Therapeutic plan with citations (Phase 5)
[x] Traceable clinical report (Phase 6)
[x] QA approved (Phase 7)

Generated files:
   - clinical-case-[date].md
   - grade-evidence-[date].md + references-[date].bib
   - clinical-deliberation-[date].md
   - clinical-plan-[condition]-[date].pdf/.md
   - clinical-report-[condition]-[date].pdf/.docx/.md
   - qa-report-[date].md

Fallback documents applied for: [list any degraded skills]

REMINDER: All material is a research DRAFT. It requires review by a
licensed healthcare professional before any clinical application.
===================================================
```

---

## Running Individual Phases

| Command | Action |
|---|---|
| `phase 1` / `intake` | Phase 1 only |
| `phase 2` / `search evidence` | Phase 2 only (requires case from Phase 1) |
| `phase 3` / `validate evidence` | Phase 3 only (requires pool from Phase 2) |
| `phase 4` / `deliberate` / `clinical board` | Phase 4 only |
| `phase 5` / `treatment plan` | Phase 5 only |
| `phase 6` / `final report` | Phase 6 only |
| `phase 7` / `QA` / `quality assurance` | Phase 7 only |
| `full workflow` | All phases in sequence |

---

## Special Situations

### Medical Emergency
```
Stop all workflow immediately.
"This situation requires IMMEDIATE medical attention. Please call your emergency number
(911 / 112 / local emergency line) or go to the emergency room NOW."
```

### Mental Health Crisis
```
Acknowledge warmly. Provide crisis resources. Do not continue diagnostic workflow.
"What you're describing sounds very difficult, and I care about how you're doing.
Are you in a safe place right now? [provide local crisis line]"
```

### Insufficient GRADE Evidence
```
In Phase 3, if primary outcome certainty = Very Low:
→ Document explicitly. Do not invent evidence. Estimate is unreliable.
→ Recommend specialist consultation in the relevant area.
→ Continue with explicit uncertainty documented throughout Phases 5–6.
```

### PHI in Input
```
"To protect privacy, I'll work with the case in de-identified form. Please use:
'a 45-year-old female patient' instead of a name; 'about 3 months ago' instead of exact dates."
```

---

## Bundled References (read when needed)

| File | Content |
|---|---|
| `references/grade-guide.md` | Full GRADE domains, effect measure interpretation, red flags |
| `references/safety-boundaries.md` | Hard safety rules, prohibited statements, mandatory stops |
| `references/skill-inventory.md` | Phase → skill map + data flow |
| `references/board-archetypes.md` | 12 council archetypes + clinical board configurations |
| `references/scenario-templates.md` | 6-branch what-if engine + clinical scenario templates |
| `references/evidence-profiles.md` | GRADE profile templates + CONSORT/CARE evidence tables |
| `references/bibtex-workflow.md` | Citation validation workflow + BibTeX formatting rules |
| `references/report-templates.md` | CARE 2013, CONSORT 2025, ICH E3 section-by-section templates |
| `references/treatment-plan-format.md` | LaTeX structure, SMART goals, one-page + 3–4 page formats |
