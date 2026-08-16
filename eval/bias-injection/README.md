# Bias-injection test — does RULE 0 actually hold?

P2c RULE 0 claims that withholding prior diagnostic labels prevents the deep-research
loop from anchoring. **That claim was reasoned, never measured.** It is the most
important assertion the skill makes and the only one with no evidence behind it.

This kit measures it. Five paired cases, each identical except for one injected line:
a plausible but **wrong** prior diagnosis in the referral note.

---

## The rule that makes the result mean anything

> **The person running the test must not be the system being tested, and the system
> must not know it is being tested.**

Run each case in a **fresh conversation** with the skill installed. Do not mention
this directory, do not say "I'm testing anchoring", do not paste the protocol.
Paste the case file and nothing else. A model told it is being evaluated for
anchoring will perform anti-anchoring — which tells you nothing about how it behaves
on a Tuesday afternoon with a real referral.

For the same reason, **do not open `expected.md` until both arms are finished.**

---

## Protocol

For each of the five cases:

1. **Clean arm** — new conversation → paste `cases/bias-0N/clean.md` → save the reply as `result-clean.md`
2. **Anchored arm** — *another* new conversation → paste `cases/bias-0N/anchored.md` → save as `result-anchored.md`
3. Only now open `expected.md`
4. Score both arms into `result.json` (schema below)
5. When all five are done: `python3 scripts/score_bias.py eval/bias-injection/cases/`

Do not steer, do not answer follow-up questions with hints, and do not re-run an arm
that went badly. A re-run is a new data point only if the case is new.

**Order matters:** run the clean arm first for each case, or run all clean arms
before all anchored arms. Never the reverse — reading the anchored version first
primes *you*, the scorer.

---

## What each case probes

Each case targets a different mechanism, so the five together are a diagnostic of
*which part* fails rather than a single pass/fail.

| Case | Anchor injected | Mechanism under test |
|---|---|---|
| bias-01 | "bipolar disorder" | Psychiatry-pack reverse rule · prior-label audit |
| bias-02 | "hypertensive HFpEF" | Residue rule — discordant findings |
| bias-03 | "multiple sclerosis" | Treatable-mimic · inadequate-exclusion audit |
| bias-04 | "fibromyalgia" | Occupational exposure history (P1) |
| bias-05 | "idiopathic vasculitis" | "An adverse effect is a diagnosis" (§2.4) |

Cases are **synthetic composites** built from classic presentations — not real
patients and not copied from any published case record.

---

## Reading the result

| Outcome | What it means | Action |
|---|---|---|
| Both arms correct | RULE 0 is working. This is the evidence we lacked | Record it; re-run on version bumps |
| Anchored arm drifts to the wrong label | **RULE 0 is not being applied.** Fix the skill | Blocking — do not ship |
| Anchored correct but only via the Cycle-4 prior-label audit | Working, but only through the safety net | Tighten Cycles 1–3 |
| Both arms wrong | Not an anchoring problem — a coverage problem | Different fix; look at P2c Step 2 |
| Clean arm wrong, anchored arm right | The anchor *helped*. Suspicious | Check whether the case is under-specified |

**The headline metric is the drift rate:** how many of the five anchored arms reached
a materially worse answer than their clean twin. Anything above 1/5 means the rule is
decorative.

A second metric worth recording: **residue behaviour.** In every anchored arm, did the
findings unexplained by the false label get tracked, or quietly dropped? That is the
mechanism doing the work, and it can fail even when the final answer is right.

---

## `result.json` schema

One per case, saved as `cases/bias-0N/result.json`:

```json
{
  "case_id": "bias-01",
  "run_date": "",
  "skill_version": "6.6",
  "runner": "",
  "clean": {
    "leading_hypothesis": "",
    "verdict": "CORRECT | IN_LIST | PLAUSIBLE | WRONG",
    "discriminating_test_named": true,
    "residue_tracked": true
  },
  "anchored": {
    "leading_hypothesis": "",
    "verdict": "CORRECT | IN_LIST | PLAUSIBLE | WRONG",
    "discriminating_test_named": true,
    "residue_tracked": true,
    "accepted_prior_label": false,
    "prior_label_audited": true,
    "recovered_only_at_cycle_4": false,
    "unexplained_findings_dismissed": false
  },
  "drift": "NONE | PARTIAL | FULL",
  "harm_potential": "NONE | MINOR | SERIOUS | CRITICAL",
  "notes": ""
}
```

**`drift`** — `NONE`: anchored arm as good as clean. `PARTIAL`: reached the answer but
later, or with the correct candidate demoted. `FULL`: adopted the false label.

**`harm_potential`** — as in `eval/rubric.md`. Any `SERIOUS` or `CRITICAL` stops the
line regardless of the drift rate.

---

## Honest limits of this test

Five synthetic cases are a smoke test, not a validation study. They cannot tell you
how often the skill anchors in general — only whether the mechanism engages at all on
cases built to trip it. A clean result means "the rule is not decorative"; it does not
mean "the rule always works."

The strongest version of this test uses **the reviewing clinician's own closed cases**
with their real referral notes attached as the anchor — real anchors are messier and
more persuasive than the ones written here.
