# NOTICE — Third-party components

`clinical-assistant` is licensed CC-BY-4.0. It bundles three offline reference
scripts derived from **ToolUniverse** (Mims Lab, Harvard Medical School),
licensed under the **Apache License 2.0**.

Source: https://github.com/mims-harvard/ToolUniverse (`plugin/skills/`)

| Bundled file | Derived from | License |
|---|---|---|
| `scripts/clinical_patterns.py` | `tooluniverse-rare-disease-diagnosis/scripts/` | Apache-2.0 |
| `scripts/pharmacology_ref.py` | `tooluniverse-drug-drug-interaction/scripts/` | Apache-2.0 |
| `scripts/roc_analysis.py` | `tooluniverse-diagnostic-test-evaluation/scripts/` | Apache-2.0 |

All three are pure-stdlib (`argparse`, `json`, `sys`) and run offline with no
network access, no API keys, and no ToolUniverse installation.

## Modifications from upstream

- `clinical_patterns.py` — **bug fix** in `_fuzzy_find()`: the upstream
  implementation called `.lower()` unconditionally on the `name_field` value,
  which raised `AttributeError` whenever that field held a list rather than a
  string. This made `--type occupational` (whose `diseases` field is a list)
  crash on every invocation. The patched version normalises string and
  list/tuple fields before matching. Marked inline in the source.

`scripts/verify_citations.py`, `scripts/score_eval.py`, `scripts/validate_skill.py`,
`references/` and `eval/` are original to this skill (CC-BY-4.0).

The appraisal instruments referenced in `references/appraisal-instruments.md` — AGREE II,
QUADAS-2, RoB 2, ROBINS-I, AMSTAR-2, and the CONSORT/STARD/TRIPOD/PRISMA/STROBE/CARE reporting
standards — are the work of their respective consortia. This skill describes **when and how to
apply them**; it does not reproduce their instruments, checklists or scoring forms. Retrieve
each from its official source before use.

## AIPOCH medical-research-skills (MIT)

Concepts adapted in v6.6 — retraction/EoC/erratum status taxonomy (§3.1b), citation-drift and
context-transfer taxonomy (§3.1c), contradiction taxonomy and citation roles (M3) — derive from
`retraction-watcher`, `paper-to-claim-verifier`, `contradictory-findings-resolver` and
`evidence-level-ranker` in https://github.com/aipoch/medical-research-skills (MIT, AIPOCH).
**No code was copied.** `scripts/verify_citations.py` is original to this skill; the retraction
check was implemented independently against the PubMed E-utilities and CrossRef APIs.

Clinical reasoning frameworks adapted (not copied verbatim) from the
ToolUniverse skills `rare-disease-diagnosis`, `diagnostic-test-evaluation`,
`clinical-guidelines`, `drug-drug-interaction`, `clinical-risk-scoring`,
`clinical-trial-matching`, and `pharmacovigilance` are credited in
`SKILL.md` § Provenance.
