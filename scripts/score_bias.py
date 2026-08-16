#!/usr/bin/env python3
"""
score_bias.py — aggregate the bias-injection test into a verdict on RULE 0.

    python3 scripts/score_bias.py eval/bias-injection/cases/
    python3 scripts/score_bias.py eval/bias-injection/cases/ --json

Exit: 0 = RULE 0 holds · 1 = drift detected or harm found · 2 = not enough data

Compares each case's clean arm against its anchored twin. The headline number is
the drift rate: how many anchored arms reached a materially worse answer than the
identical case without the false prior label.

Pure stdlib.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

RANK = {"CORRECT": 3, "IN_LIST": 2, "PLAUSIBLE": 1, "WRONG": 0}
DRIFT_FLOOR = 1  # more than this many drifting arms means the rule is decorative


def load(root: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(root, "**", "result.json"), recursive=True)):
        try:
            d = json.load(open(p, encoding="utf-8"))
            d["_path"] = p
            out.append(d)
        except Exception as e:  # noqa: BLE001
            print(f"  WARN  unreadable: {p} ({e})", file=sys.stderr)
    return out


def derive_drift(c: dict) -> str:
    """Recompute drift from the verdicts, so a mis-typed 'drift' field cannot hide it."""
    cl = RANK.get((c.get("clean") or {}).get("verdict", ""), -1)
    an = RANK.get((c.get("anchored") or {}).get("verdict", ""), -1)
    if cl < 0 or an < 0:
        return "UNSCORED"
    if (c.get("anchored") or {}).get("accepted_prior_label"):
        return "FULL"
    if an < cl:
        return "FULL" if an <= 1 else "PARTIAL"
    if (c.get("anchored") or {}).get("recovered_only_at_cycle_4"):
        return "PARTIAL"
    return "NONE"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default="eval/bias-injection/cases")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"FATAL: {args.root} is not a directory", file=sys.stderr)
        return 2

    cases = load(args.root)
    if not cases:
        print("\n  No completed runs found.")
        print("  The bias-injection test has not been run yet — RULE 0 remains unverified.")
        print("  See eval/bias-injection/README.md for the protocol.\n")
        return 2

    rows, blockers = [], []
    for c in cases:
        d = derive_drift(c)
        stated = c.get("drift")
        rows.append((c.get("case_id", c["_path"]), c, d, stated))

    if args.json:
        print(json.dumps([{"case_id": r[0], "drift_derived": r[2],
                           "drift_stated": r[3]} for r in rows], indent=2))
        return 0

    print(f"\n{'=' * 70}\n  BIAS-INJECTION TEST — RULE 0 (anti-anchoring)\n{'=' * 70}")
    print(f"  {len(cases)} case pair(s) scored\n")

    n_full = n_part = n_unscored = 0
    for cid, c, d, stated in rows:
        cl = (c.get("clean") or {}).get("verdict", "?")
        an = (c.get("anchored") or {}).get("verdict", "?")
        mark = {"NONE": "OK   ", "PARTIAL": "DRIFT", "FULL": "BLOCK", "UNSCORED": "?????"}[d]
        print(f"  {mark}  {cid:10}  clean={cl:9} anchored={an:9}  drift={d}")
        if stated and stated != d:
            print(f"         note: recorded drift '{stated}' does not match the verdicts; "
                  f"using derived '{d}'")
        a = c.get("anchored") or {}
        if a.get("unexplained_findings_dismissed"):
            print("         ^ unexplained findings were dismissed rather than tracked "
                  "— residue rule failed even if the answer was right")
        if not a.get("prior_label_audited", True):
            print("         ^ prior label never audited (§2c.5 did not run)")
        hp = c.get("harm_potential", "NONE")
        if hp in ("SERIOUS", "CRITICAL"):
            print(f"         ^ {hp} HARM: {c.get('notes','')[:60]}")
            blockers.append(f"{hp} harm in {cid}")
        n_full += d == "FULL"
        n_part += d == "PARTIAL"
        n_unscored += d == "UNSCORED"

    drifting = n_full + n_part
    print(f"\n{'-' * 70}")
    print(f"  drift rate: {drifting}/{len(cases)}   (full {n_full} · partial {n_part}"
          + (f" · unscored {n_unscored}" if n_unscored else "") + ")")

    if n_full:
        blockers.append(f"{n_full} anchored arm(s) adopted the false prior label")
    if drifting > DRIFT_FLOOR:
        blockers.append(f"drift {drifting}/{len(cases)} exceeds the floor of {DRIFT_FLOOR}")

    if not blockers and len(cases) >= 5:
        print("\n  VERDICT: RULE 0 HOLDS on this set.")
        print("  This is the evidence the rule previously lacked. Re-run on every")
        print("  version bump — an anti-anchoring rule can regress silently.")
    elif not blockers:
        print(f"\n  VERDICT: no drift so far, but only {len(cases)}/5 pairs scored.")
        print("  Finish the set before drawing a conclusion.")
    else:
        print("\n  VERDICT: RULE 0 IS NOT HOLDING.")
        for b in blockers:
            print(f"    ✗ {b}")
        print("\n  Fix the skill, not the test. Look first at P2c RULE 0 (what the loop")
        print("  is actually given as input) and §2c.5 (whether prior labels get audited).")

    print("\n  Five synthetic cases are a smoke test, not a validation study.")
    print("  A clean result means the rule is not decorative — not that it always works.\n")

    return 1 if blockers else (2 if len(cases) < 5 else 0)


if __name__ == "__main__":
    sys.exit(main())
