# Skill Inventory — Clinical-Assistant

## Skill Map by Phase

### PHASE 1 — Intake
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `informed-patient` | Guides the structured clinical interview; organizes symptoms, history, hypotheses | Conversation with user | Structured case in markdown |
| `summarize-interview` | Synthesizes the intake into a structured record with JTBD, signals, action items | Interview transcript / notes | Clinical summary with key sections |

### PHASE 2 — Raw Evidence
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `pubmed-central` | MEDLINE/PMC API: MeSH search, PMID, citation network | MeSH terms + PICO questions | Paper pool with PMID/DOI |
| `bgpt-paper-search` | 25+ fields per paper: methods, n, quality score, quantitative results | PMIDs from the pool | Structured data for each study |
| `exa-search` | Semantic search with `category=research paper` filter | Clinical queries | Recent guidelines + meta-analyses |
| `database-lookup` | 78 documented public DBs: ClinicalTrials.gov, DrugBank, OMIM, Orphanet, FDA, WHO | Condition + drugs | Active trials, alerts, guidelines |

> **Bilingual sourcing:** In Phase 2, query both English sources (PubMed, Cochrane, NEJM, Lancet, BMJ, JAMA)
> and Spanish sources (SciELO, LILACS, MEDES, Elsevier España, national ministry-of-health guidelines) to
> maximize evidence coverage. Normalize all results into English tables, tagging original language.

### PHASE 3 — GRADE Validation
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `citation-management` | Validates DOIs/PMIDs via OpenAlex+CrossRef; generates BibTeX | Paper pool | Verified BibTeX bibliography |
| `statistical-analysis` | Interprets 95% CI, p-values, effect sizes, biases | Study data | Annotated statistical analysis |
| `statistical-power` | Assesses power and sample-size validity | Pool studies | Statistical robustness assessment |
| `ab-test-analysis` | Validates RCTs and comparative trials | Comparative studies | Significance assessment |

### PHASE 4 — Multidisciplinary Deliberation
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `consciousness-council` | Virtual clinical board with 6 specialized archetypes | Case + GRADE evidence | Multidisciplinary consensus |
| `strategy-red-team` | Attacks diagnostic assumptions; finds flaws in the plan | Diagnostic hypotheses | List of vulnerabilities |
| `what-if-oracle` | 4-6 scenarios: best/worst case, wild card, 2nd-order effects | Likely diagnosis | Scenario tree with probabilities |
| `pre-mortem` | Tigers/Paper Tigers/Elephants of the plan before implementing | Provisional plan | Risks classified by severity |
| `prioritize-assumptions` | Impact x risk matrix of diagnostic hypotheses | Hypothesis list | Prioritized ranking to investigate |

### PHASE 5 — Clinical Plan
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `treatment-plans` | Generates LaTeX/PDF plan with SMART goals, dosing, monitoring | Diagnosis + evidence | Structured therapeutic plan |
| `clinical-decision-support` | GRADE profile, decision traceability, governance artifacts | Plan + evidence | GRADE traceability artifacts |
| `content-research-writer` | Writes clinical narrative with iterative citations | Plan + deliberation | Clinical text with integrated citations |
| `cohort-analysis` | Survival/retention curves by subgroup if data available | Epidemiological data | Contextual cohort analysis |

### PHASE 6 — Final Report
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `clinical-reports` | CARE/CONSORT/ACR structure; generates traceable template | Complete plan | Structured report draft |
| `grammar-check` | Logical coherence and flow of clinical reasoning | Draft report | Report with flagged corrections |
| `copy-editing` | Technical-medical language review; clarity and precision | Revised report | Polished report |
| `pdf` | Generates professional PDF with institutional clinical format | Final report | Downloadable PDF |
| `docx` | Clinical Word with styles for signature and annotation | Final report | Downloadable DOCX |

### PHASE 7 — Quality Assurance
| Skill | Function | Input | Output |
|-------|----------|-------|--------|
| `intended-vs-implemented` | Detects gaps between documented plan and implemented plan | Complete report | Gap table with classification |
| `strategy-red-team` | Final red-team of the complete report | Complete report | Vulnerability report |

---

## Optional / Extension Skills

These skills can be incorporated for specific cases:

| Skill | When to use |
|-------|-------------|
| `exploratory-data-analysis` | If the user provides cohort datasets or clinical registries |
| `depmap` | Oncology cases: genetic vulnerabilities of cell lines |
| `drugbank-database` | Deep pharmacological interaction lookups |
| `biopython` | If genomic sequence analysis is involved |
| `statistical-power` | Already in Phase 3; can extend for future study design |
| `summarize-meeting` | For minutes of real multidisciplinary meetings |
| `citation-management` | Extend to SciELO/LILACS export for Spanish-language references |

---

## Data Flow Between Phases

```
User
  v
[1] clinical-case-[date].md
  v
[2] raw-evidence-[date].md (English + Spanish sources, normalized to English)
  v
[3] grade-evidence-[date].md + references.bib
  v
[4] clinical-deliberation-[date].md
  v
[5] clinical-plan-[condition]-[date].tex -> .pdf
  v
[6] clinical-report-[condition]-[date].pdf + .docx
  v
[7] qa-report-[date].md
  -> if gaps -> return to (2) or (4)
  -> if OK -> DELIVER
```

---

## Implementation Notes

1. **Language:** Interface and working documents are in English by default. Evidence sourcing (Phases 2-3) is
   bilingual (English + Spanish) to maximize coverage. The user may request the final plan/report in Spanish.

2. **De-identification:** Phase 1 captures information; Phases 6-7 only work with de-identified or synthetic data.

3. **Draft header:** Mandatory on all Phase 5 and Phase 6 documents.

4. **Preliminary GRADE:** The skill's GRADE classification is indicative. It requires review by a qualified
   human panel.

5. **User checkpoint:** At the end of Phases 1 and 4, confirm with the user before continuing.

6. **Emergencies:** If signs of medical urgency appear in any phase, stop everything and refer.
