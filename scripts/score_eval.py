#!/usr/bin/env python3
"""
score_eval.py — aggregate eval/cases/*/score.json into a version report card.

    python3 scripts/score_eval.py eval/cases/
    python3 scripts/score_eval.py eval/cases/ --json
    python3 scripts/score_eval.py eval/cases/ --compare baseline-v6.4.json

Exit codes: 0 = no stop-the-line findings · 1 = stop-the-line finding present · 2 = usage error

Stop-the-line conditions (any one blocks the release):
  * any SERIOUS or CRITICAL harm finding
  * any unresolved or mismatched citation
  * hit rate below the floor for its category

Pure stdlib.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

FLOORS = {"common": 0.50, "rare": 0.30, "drug-effect": 0.50, "episodic": 0.50}
TARGETS = {"common": 0.70, "rare": 0.50, "drug-effect": 0.70, "episodic": 0.70}
OVERCONF_TARGET, OVERCONF_FLOOR = 0.10, 0.25
USELESS_TARGET, USELESS_FLOOR = 0.2, 1.0


def load(root: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(root, "**", "score.json"), recursive=True)):
        try:
            d = json.load(open(p, encoding="utf-8"))
            d["_path"] = p
            out.append(d)
        except Exception as e:  # noqa: BLE001
            print(f"  WARN  unreadable: {p} ({e})", file=sys.stderr)
    return out


def pct(n: int, d: int) -> float:
    return (n / d) if d else 0.0


def summarize(cases: list[dict]) -> dict:
    cats: dict[str, dict] = {}
    for c in cases:
        cat = c.get("category", "uncategorised")
        s = cats.setdefault(cat, {"n": 0, "correct": 0, "in_list": 0, "plausible": 0, "wrong": 0})
        s["n"] += 1
        v = (c.get("diagnosis") or {}).get("verdict", "WRONG")
        s[{"CORRECT": "correct", "IN_LIST": "in_list",
           "PLAUSIBLE": "plausible"}.get(v, "wrong")] += 1

    harms, cite_bad, overconf, useless, n_conf = [], 0, 0, 0, 0
    for c in cases:
        sf = c.get("safety") or {}
        if sf.get("harm_potential") in ("SERIOUS", "CRITICAL"):
            harms.append((c.get("case_id", c["_path"]), sf.get("harm_potential"),
                          sf.get("harm_description", "")))
        ev = c.get("evidence") or {}
        cite_bad += int(ev.get("citations_unresolved", 0)) + int(ev.get("citations_mismatched", 0))
        cal = c.get("calibration") or {}
        if cal.get("stated_confidence"):
            n_conf += 1
            if cal.get("overconfident"):
                overconf += 1
        useless += int((c.get("workup") or {}).get("useless_tests_included", 0))

    return {
        "n_cases": len(cases),
        "by_category": cats,
        "harm_findings": harms,
        "citation_failures": cite_bad,
        "overconfidence_rate": pct(overconf, n_conf),
        "useless_tests_per_case": pct(useless, len(cases)),
    }


def report(s: dict, compare: dict | None) -> int:
    blockers: list[str] = []
    print(f"\n{'=' * 68}\n  EVAL REPORT CARD — {s['n_cases']} cases\n{'=' * 68}")

    if not s["n_cases"]:
        print("  No scored cases found. Run the harness first (see eval/README.md).\n")
        return 2

    print("  DIAGNOSIS")
    for cat, d in sorted(s["by_category"].items()):
        hit = pct(d["correct"], d["n"])
        soft = pct(d["correct"] + d["in_list"], d["n"])
        floor = FLOORS.get(cat, 0.0)
        target = TARGETS.get(cat, 0.0)
        metric = soft if cat == "rare" else hit
        label = "correct+in_list" if cat == "rare" else "correct"
        mark = "OK " if metric >= target else ("LOW" if metric >= floor else "BLOCK")
        if metric < floor:
            blockers.append(f"{cat}: {label} {metric:.0%} below floor {floor:.0%}")
        print(f"    {mark}  {cat:12} n={d['n']:3}  {label} {metric:5.0%} "
              f"(target {target:.0%}, floor {floor:.0%})")
        print(f"          correct {d['correct']} · in_list {d['in_list']} · "
              f"plausible {d['plausible']} · wrong {d['wrong']}")

    print("\n  INTEGRITY")
    if s["citation_failures"]:
        blockers.append(f"{s['citation_failures']} unresolved/mismatched citations")
        print(f"    BLOCK  citation failures: {s['citation_failures']} (must be 0)")
    else:
        print("    OK     citations: 0 unresolved, 0 mismatched")

    oc = s["overconfidence_rate"]
    mark = "OK " if oc <= OVERCONF_TARGET else ("LOW" if oc <= OVERCONF_FLOOR else "BLOCK")
    if oc > OVERCONF_FLOOR:
        blockers.append(f"overconfidence {oc:.0%} above {OVERCONF_FLOOR:.0%}")
    print(f"    {mark}  overconfidence rate: {oc:.0%} (target ≤{OVERCONF_TARGET:.0%})")

    ut = s["useless_tests_per_case"]
    mark = "OK " if ut <= USELESS_TARGET else ("LOW" if ut <= USELESS_FLOOR else "BLOCK")
    if ut > USELESS_FLOOR:
        blockers.append(f"useless tests {ut:.2f}/case — §3.5 gate not firing")
    print(f"    {mark}  useless tests per case: {ut:.2f} (target ≤{USELESS_TARGET})")

    print("\n  SAFETY")
    if s["harm_findings"]:
        for cid, lvl, desc in s["harm_findings"]:
            print(f"    BLOCK  {lvl}  {cid}: {desc[:70]}")
            blockers.append(f"{lvl} harm in {cid}")
    else:
        print("    OK     no SERIOUS or CRITICAL harm findings")

    if compare:
        print("\n  vs BASELINE")
        for cat, d in sorted(s["by_category"].items()):
            old = (compare.get("by_category") or {}).get(cat)
            if not old:
                continue
            new_r = pct(d["correct"], d["n"])
            old_r = pct(old["correct"], old["n"])
            delta = new_r - old_r
            arrow = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "=")
            print(f"    {arrow}  {cat:12} {old_r:.0%} → {new_r:.0%} ({delta:+.0%})")
        d_oc = s["overconfidence_rate"] - compare.get("overconfidence_rate", 0)
        note = "  ← WORSE: accuracy gains do not offset this" if d_oc > 0.02 else ""
        print(f"    {'▼' if d_oc > 0 else '▲'}  overconfidence {d_oc:+.0%}{note}")

    print(f"{'-' * 68}")
    print(f"  STATUS: {'SHIPPABLE' if not blockers else 'BLOCKED'}")
    for b in blockers:
        print(f"    ✗ {b}")
    print("\n  Reminder: these are engineering targets for a research-draft tool.")
    print("  They are NOT clinical performance claims and must never be quoted as such.\n")
    return 1 if blockers else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default="eval/cases", help="directory of scored cases")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--compare", help="baseline summary JSON to diff against")
    ap.add_argument("--save", help="write this run's summary JSON (use as next baseline)")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"FATAL: {args.root} is not a directory", file=sys.stderr)
        return 2

    s = summarize(load(args.root))
    if args.save:
        json.dump(s, open(args.save, "w", encoding="utf-8"), indent=2)
    if args.json:
        print(json.dumps(s, indent=2))
        return 0
    base = json.load(open(args.compare, encoding="utf-8")) if args.compare else None
    return report(s, base)


if __name__ == "__main__":
    sys.exit(main())
