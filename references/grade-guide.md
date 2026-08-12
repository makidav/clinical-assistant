# GRADE Guide for Clinical-Assistant

> GRADE = Grading of Recommendations Assessment, Development and Evaluation

## Core Principle

The GRADE classification in this skill is **preliminary and indicative**.
A qualified human panel must perform the definitive assessment.
The skill documents the domains and their tentative evaluation; humans confirm them.

---

## GRADE Assessment Domains

### For each important outcome, assess:

| Domain | Assess | Downgrades | Upgrades |
|--------|--------|-----------|----------|
| **Risk of bias** | Does the study design have methodological flaws? | Yes (-1 or -2) | — |
| **Inconsistency** | Do results vary widely across studies? (I2 > 50%) | Yes (-1 or -2) | — |
| **Indirectness** | Do the population/intervention/outcome differ from the question? | Yes (-1 or -2) | — |
| **Imprecision** | Is the 95% CI very wide or crossing the clinical threshold? | Yes (-1 or -2) | — |
| **Publication bias** | Any indication of unpublished results? | Yes (-1) | — |
| **Large effect** | OR/RR > 2 or < 0.5 consistently? | — | +1 or +2 |
| **Dose-response gradient** | Higher dose = clearly larger effect? | — | +1 |
| **Plausible confounders** | Would confounders reduce the observed effect? | — | +1 |

### Starting point by study design:

| Design | Initial certainty |
|--------|-------------------|
| Systematic review of RCTs | High |
| Well-conducted RCT | High |
| Cohort / observational study | Low |
| Case series / case report | Very low |
| Expert opinion | Very low |

### Final certainty:

| Level | Meaning | Symbol |
|-------|---------|--------|
| **High** | Further research very unlikely to change the estimate | oooo |
| **Moderate** | Further research may modify the estimate | ooo- |
| **Low** | Further research likely to change the estimate | oo-- |
| **Very Low** | The estimate is very uncertain | o--- |

---

## GRADE Table by Outcome (Template)

```markdown
## Evidence Profile (GRADE)
**Clinical question:** [full PICO]
**Review date:** [date]

| Outcome | N studies | N patients | Design | Risk of bias | Inconsistency | Indirect | Imprecision | Pub bias | Effect | Certainty |
|---------|-----------|------------|--------|--------------|---------------|----------|-------------|----------|--------|-----------|
| [Outcome 1] | [N] | [N] | RCT | Low | No | No | No | No | OR 0.8 [95% CI 0.6-0.9] | High |
| [Outcome 2] | [N] | [N] | Cohort | High | Yes | Yes | Yes | Suspected | OR 0.7 [95% CI 0.3-1.4] | Very Low |

**Reviewer notes:** [specific observations]
**Qualified review pending:** Yes — required before clinical use
```

---

## Interpreting Effect Measures

### For dichotomous outcomes:
- **OR (Odds Ratio):** < 1 = protective; > 1 = risk factor
- **RR (Relative Risk):** interpretation similar to OR
- **NNT (Number Needed to Treat):** patients to treat for 1 benefit -> lower = better
- **NNH (Number Needed to Harm):** patients to treat for 1 harm -> higher = better

### For continuous outcomes:
- **MD (Mean Difference):** difference in the same unit of measure
- **SMD (Standardized Mean Difference) / Cohen's d:**
  - 0.2 = small effect
  - 0.5 = medium effect
  - 0.8 = large effect

### Statistical vs. clinical significance:
- A p < 0.05 does NOT imply clinical relevance
- Always evaluate: is the effect size clinically important?
- Does the 95% CI include effects in both directions (crossing the null)?

---

## Quality Red Flags in Papers

Actively look for these quality problems:

| Flag | Implication |
|------|------------|
| N < 30 per arm | Study very likely underpowered |
| I2 > 75% | Severe heterogeneity; meta-analysis may be inappropriate |
| Follow-up < 6 months for a chronic outcome | Short-term results; limited transferability |
| Manufacturer-funded | Reporting bias risk; check registered protocol |
| No ClinicalTrials.gov registration | Risk of outcome cherry-picking |
| Loss to follow-up > 20% | Attrition bias |
| No ITT (intention-to-treat) | Benefit overestimation |
| Surrogate outcomes only | No evidence of direct clinical benefit |

---

## Required Documentation in the Report

For each clinical recommendation in the treatment plan, include:

```
Recommendation: [recommendation text]
Evidence: [BibTeX citation]
GRADE certainty: [High/Moderate/Low/Very Low]
Effect size: [OR/RR/NNT with 95% CI]
Notes: [relevant limitations]
```
