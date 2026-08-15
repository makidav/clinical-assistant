# Appraisal instruments — how to judge the *quality* of a source, not its brand

> **Supervision rule (applies to every instrument here).** These are structured aids for a
> human reviewer, not automated verdicts. Published evaluation of LLM-applied risk-of-bias
> assessment finds only *moderate* agreement with expert judgment. Therefore: produce the
> domain judgments **with the signalling question and the sentence of evidence that drove
> each one**, so a reviewer can overturn any of them in seconds. Never report a bias rating
> without its justification. Never collapse domains into a single quality score.

---

## AGREE II — appraising a clinical practice guideline

Replaces "NICE outranks a society guideline" (a reputation heuristic) with an assessment of
what the guideline actually did. Use whenever two guidelines conflict, when a guideline
carries a load-bearing recommendation, or when the guideline is > 3 years old.

| # | Domain | The question that matters |
|---|---|---|
| 1 | Scope & purpose | Are the objective, question and population explicit? |
| 2 | Stakeholder involvement | Were all relevant professional groups — and patients — included? |
| 3 | **Rigour of development** | Systematic search? Explicit evidence-selection criteria? Strengths/limits of the evidence stated? Explicit link from evidence to each recommendation? External review? Updating procedure? |
| 4 | Clarity of presentation | Are recommendations specific, unambiguous, and are options presented? |
| 5 | Applicability | Facilitators/barriers, resource implications, monitoring criteria? |
| 6 | **Editorial independence** | Funding source stated? Competing interests recorded **and addressed**? |

**Practical shortcut (report these five, always):**
`Systematic search? · Evidence→recommendation link explicit? · Strength grading used? ·
COI declared and managed? · Update procedure and date?`

Domains 3 and 6 carry most of the signal. A guideline scoring low on **rigour of development**
should not outrank a well-conducted one merely because its issuing body is better known — say
so explicitly when it happens.

**Conflict protocol:** when guidelines disagree, appraise both, present both positions with
year and grade, and state *which domain explains the disagreement* (usually different evidence
cut-off dates, different populations, or different value judgments about the same evidence).
Do not resolve it silently.

---

## QUADAS-2 — appraising a diagnostic accuracy study

**This is the gate on every sensitivity/specificity number used in P3 §3.5.** A post-test
probability computed from a biased study is a precise wrong answer.

Four domains, each rated **low / high / unclear** risk of bias; the first three also rated for
**applicability** to our patient. Rate per domain — never as a composite score.

| Domain | Signalling questions | Bias it detects |
|---|---|---|
| **1 · Patient selection** | Consecutive or random sample? Case-control design avoided? Inappropriate exclusions avoided? | **Spectrum bias** — sens/spec measured on clearly-sick vs clearly-well subjects overestimate real-world performance on the borderline patients we actually face |
| **2 · Index test** | Interpreted without knowledge of the reference standard? Threshold pre-specified? | Review bias; **optimistic thresholds** chosen post hoc on the same data |
| **3 · Reference standard** | Does it correctly classify the target condition? Interpreted blind to the index test? | An imperfect gold standard silently caps measured accuracy |
| **4 · Flow & timing** | Appropriate interval between index test and reference standard? Did *all* patients get the same reference standard? Were all included in the analysis? | **Partial/differential verification bias** — only test-positives get the gold standard, inflating sensitivity |

**Applicability check (the one most often skipped):** were the study's patients, test version,
and target condition definition the same as *this* patient's situation? A test validated in a
tertiary referral population behaves differently in primary care — which is a prevalence
change, and therefore a PPV change (§3.5).

**Reporting rule:** when citing sens/spec, attach the tag
`[QUADAS-2: selection ⬤ · index ⬤ · reference ⬤ · flow ⬤ | applicability: ⬤]` using
low ○ / unclear ◐ / high ⬤. If any domain is high risk, state the direction of the likely
distortion, not just its presence.

*Extensions:* QUADAS-C for comparing two index tests; PRISMA-DTA governs how these ratings are
reported in a diagnostic systematic review.

---

## RoB 2 — appraising a randomised trial (therapy evidence)

Five domains → **low risk / some concerns / high risk**, with an overall judgment driven by
the worst domain (not an average):

1. Randomisation process (sequence generation, allocation concealment, baseline imbalance)
2. Deviations from intended interventions (blinding, ITT vs per-protocol)
3. Missing outcome data (attrition, differential loss)
4. Measurement of the outcome (blinded assessment; subjective outcomes are more vulnerable)
5. Selection of the reported result (pre-registered protocol vs what was published)

Domain 5 is where **outcome switching** hides — check the registry entry against the paper.

## ROBINS-I — non-randomised studies of interventions
Seven domains; crucially includes **confounding** and **selection into the study** (pre-intervention),
plus classification of interventions and deviations, missing data, outcome measurement and
reported-result selection. Judged against a hypothetical target trial. Note: a study can be
rated *critical* risk — meaning it should not be included in the synthesis at all.

## AMSTAR-2 — appraising a systematic review
Seven **critical** items: protocol registered *a priori* · adequacy of the literature search ·
justification for excluding individual studies · risk of bias in included studies ·
appropriateness of meta-analytic methods · consideration of risk of bias when interpreting
results · assessment of publication bias. One critical flaw → confidence *low*; more than one →
*critically low*, and the review should not be used as the basis of a recommendation.

---

## Reporting standards — what a paper should contain (use to spot omissions)

| Standard | Applies to | The omission it exposes |
|---|---|---|
| **CONSORT** | Randomised trials | Missing flow diagram, unreported harms |
| **STARD** | Diagnostic accuracy studies | No 2×2 table, undefined threshold, no CIs |
| **TRIPOD** | Prediction/risk models | No calibration reporting, no external validation |
| **PRISMA** (+ **-DTA**) | Systematic reviews | Unregistered protocol, no bias assessment |
| **STROBE** | Observational studies | Unstated confounders, undeclared sample-size logic |
| **CARE** | Case reports | Missing timeline, no patient perspective |
| **ARRIVE** | Animal studies | Relevant when the only evidence is preclinical — flag it as such |

**TRIPOD is the one to remember for AI/risk-score claims:** a model reported without
**calibration** and without **external validation** should never drive a clinical
recommendation, however impressive its AUC. Discrimination and calibration are different
properties — a well-discriminating model can output badly calibrated probabilities.

---

## Where each instrument attaches in the workflow

| Instrument | Phase | Consequence of a bad rating |
|---|---|---|
| AGREE II | P2 §2.3 | Guideline loses precedence; conflict must be surfaced |
| QUADAS-2 | P3 §3.5 | Sens/spec flagged; post-test probability reported as a range, not a point |
| RoB 2 / ROBINS-I | P3 §3.2 → GRADE | Feeds the GRADE "risk of bias" downgrade directly |
| AMSTAR-2 | P3 §3.1 | Critically-low review cannot anchor a recommendation |
| Reporting standards | P3, P6 | Missing element → stated as a limitation, not silently ignored |

GRADE already asks "risk of bias?" — these instruments are **how that question gets answered
reproducibly** instead of by impression.
