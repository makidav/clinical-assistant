#!/usr/bin/env python3
"""ROC / AUC / optimal-cutoff analysis (P3 §3.5).

Reads a CSV of (label, score), computes the ROC AUC with a bootstrap 95% CI,
finds the Youden-optimal cutoff and its sensitivity/specificity, and prints a
text ROC curve.

Pure stdlib — no numpy, no scikit-learn, no network. Runs on Python 3.9+.
AUC is computed by the rank-sum (Mann-Whitney U) identity with mid-ranks for
ties, which is numerically identical to sklearn's roc_auc_score.

CSV columns: label (1=disease/positive, 0=healthy/negative), score (continuous).

Usage:
  python roc_analysis.py --input scores.csv
"""
from __future__ import annotations

import argparse
import csv
import random
import sys


def auc_ranksum(y: list[int], s: list[float]) -> float:
    """AUC via the Mann-Whitney U identity, averaging ranks across ties.

    AUC = (R_pos - n_pos(n_pos+1)/2) / (n_pos * n_neg)
    where R_pos is the sum of mid-ranks of the positive scores.
    """
    n = len(s)
    order = sorted(range(n), key=lambda i: s[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and s[order[j + 1]] == s[order[i]]:
            j += 1
        # ranks are 1-based; every member of the tied group [i..j] takes the mean rank
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    n_pos = sum(1 for v in y if v == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r_pos = sum(ranks[i] for i in range(n) if y[i] == 1)
    return (r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def roc_points(y: list[int], s: list[float]) -> tuple[list[float], list[float], list[float]]:
    """Return (fpr, tpr, thresholds) at every distinct score, plus the (0,0) origin.

    Mirrors sklearn.metrics.roc_curve: thresholds descending, curve starting at
    (0, 0), one point per distinct score value.
    """
    n_pos = sum(1 for v in y if v == 1)
    n_neg = len(y) - n_pos
    order = sorted(range(len(s)), key=lambda i: -s[i])
    fpr, tpr, thr = [0.0], [0.0], [float("inf")]
    tp = fp = 0
    i = 0
    while i < len(order):
        cur = s[order[i]]
        while i < len(order) and s[order[i]] == cur:
            if y[order[i]] == 1:
                tp += 1
            else:
                fp += 1
            i += 1
        tpr.append(tp / n_pos if n_pos else 0.0)
        fpr.append(fp / n_neg if n_neg else 0.0)
        thr.append(cur)
    return fpr, tpr, thr


def percentile(values: list[float], q: float) -> float:
    """Linear-interpolation percentile, matching numpy's default method."""
    if not values:
        return float("nan")
    v = sorted(values)
    if len(v) == 1:
        return v[0]
    pos = (len(v) - 1) * (q / 100.0)
    lo = int(pos)
    hi = min(lo + 1, len(v) - 1)
    frac = pos - lo
    return v[lo] * (1 - frac) + v[hi] * frac


def bootstrap_auc_ci(y: list[int], s: list[float], n: int = 2000,
                     seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    size = len(y)
    aucs = []
    for _ in range(n):
        idx = [rng.randrange(size) for _ in range(size)]
        yb = [y[i] for i in idx]
        if len(set(yb)) < 2:
            continue
        aucs.append(auc_ranksum(yb, [s[i] for i in idx]))
    if not aucs:
        return (float("nan"), float("nan"))
    return (percentile(aucs, 2.5), percentile(aucs, 97.5))


def interp(x: float, xs: list[float], ys: list[float]) -> float:
    """Linear interpolation on an ascending xs, clamped at both ends."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return ys[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="CSV: label,score")
    ap.add_argument("--bootstrap", type=int, default=2000,
                    help="bootstrap replicates for the AUC CI (default 2000)")
    ap.add_argument("--seed", type=int, default=0, help="bootstrap seed (default 0)")
    args = ap.parse_args()

    ys: list[int] = []
    ss: list[float] = []
    try:
        with open(args.input, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    ys.append(int(float(row["label"])))
                    ss.append(float(row["score"]))
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError as e:
        print(f"FATAL: cannot read {args.input} — {e}", file=sys.stderr)
        return 1

    if not ys:
        print("FATAL: no usable rows (need columns 'label' and 'score').", file=sys.stderr)
        return 1
    if len(set(ys)) < 2:
        print("Need both positive (1) and negative (0) labels.", file=sys.stderr)
        return 1

    auc = auc_ranksum(ys, ss)
    lo, hi = bootstrap_auc_ci(ys, ss, n=args.bootstrap, seed=args.seed)
    fpr, tpr, thr = roc_points(ys, ss)
    j = max(range(len(tpr)), key=lambda i: tpr[i] - fpr[i])
    cutoff, sens, spec = thr[j], tpr[j], 1 - fpr[j]

    n_pos = sum(ys)
    n_neg = len(ys) - n_pos
    band = (
        "outstanding" if auc > 0.9 else
        "excellent" if auc > 0.8 else
        "acceptable" if auc > 0.7 else
        "poor/near-chance"
    )
    print(f"\nROC analysis: {len(ys)} samples ({n_pos} positive, {n_neg} negative)\n")
    print(f"AUC = {auc:.3f}  95% CI [{lo:.3f}, {hi:.3f}]  ({band})")
    print(f"Youden-optimal cutoff: score >= {cutoff:.4g}  ->  "
          f"sensitivity {sens:.3f}, specificity {spec:.3f}")

    print("\nROC (TPR vs FPR):")
    grid = [i / 10.0 for i in range(11)]
    for g in reversed(grid):
        t = interp(g, fpr, tpr)
        bar = "#" * int(round(t * 40))
        print(f"  FPR={g:.1f} | {bar:<40} TPR={t:.2f}")
    if auc < 0.7:
        print("\n  ! AUC < 0.7 — weak discrimination.")
    prev = n_pos / len(ys)
    if prev < 0.1 or prev > 0.9:
        print("  ! strong class imbalance — also report PPV at the real prevalence "
              "(precision-recall is informative).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
