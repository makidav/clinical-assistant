#!/usr/bin/env python3
"""
validate_skill.py — structural linter for clinical-assistant/SKILL.md

Checks the invariants that break a skill at install time or silently degrade it
at run time. Exit 0 = clean, 1 = errors present.

Usage:  python3 scripts/validate_skill.py [path/to/SKILL.md]

Pure stdlib. Run this after EVERY edit to the skill.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

DESC_LIMIT = 1024  # hard install-time limit
NAME_LIMIT = 64

errors: list[str] = []
warnings: list[str] = []
passed: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def ok(msg: str) -> None:
    passed.append(msg)


# ---------------------------------------------------------------- frontmatter
def check_frontmatter(text: str) -> None:
    if not text.startswith("---"):
        err("Frontmatter: file does not start with '---'")
        return
    parts = text.split("---", 2)
    if len(parts) < 3:
        err("Frontmatter: no closing '---'")
        return
    fm = parts[1]

    m = re.search(r"^name:\s*(.+)$", fm, re.M)
    if not m:
        err("Frontmatter: missing 'name'")
    else:
        name = m.group(1).strip()
        if len(name) > NAME_LIMIT:
            err(f"Frontmatter: name is {len(name)} chars (limit {NAME_LIMIT})")
        elif not re.fullmatch(r"[a-z0-9-]+", name):
            err(f"Frontmatter: name '{name}' must be lowercase letters/digits/hyphens")
        else:
            ok(f"name '{name}' valid ({len(name)} chars)")

    # description: either 'description: >' block or single line
    block = re.search(r"^description:\s*>\s*\n((?:[ \t]+.*\n)+)", fm, re.M)
    line = re.search(r"^description:\s*(?!>)(.+)$", fm, re.M)
    if block:
        desc = " ".join(l.strip() for l in block.group(1).strip().split("\n"))
    elif line:
        desc = line.group(1).strip()
    else:
        err("Frontmatter: missing 'description'")
        return

    n = len(desc)
    if n > DESC_LIMIT:
        err(f"Frontmatter: description is {n} chars — EXCEEDS {DESC_LIMIT} LIMIT, "
            f"skill WILL NOT INSTALL (over by {n - DESC_LIMIT})")
    elif n > DESC_LIMIT - 25:
        warn(f"description is {n}/{DESC_LIMIT} chars — under 25 chars of headroom")
    else:
        ok(f"description {n}/{DESC_LIMIT} chars ({DESC_LIMIT - n} headroom)")

    if "DRAFT" not in desc.upper():
        warn("description does not mention DRAFT-only output (safety framing)")


# --------------------------------------------------------------- markdown
def check_fences(text: str) -> None:
    n = text.count("```")
    if n % 2:
        err(f"Markdown: unbalanced code fences ({n} found, must be even)")
    else:
        ok(f"code fences balanced ({n // 2} blocks)")


def check_tables(text: str) -> None:
    """Every markdown table must have a consistent column count."""
    lines = text.split("\n")
    bad = 0
    in_fence = False
    block: list[tuple[int, str]] = []

    def flush(blk: list[tuple[int, str]]) -> int:
        if len(blk) < 2:
            return 0
        counts = {}
        for ln, row in blk:
            # `\|` is a legitimately escaped pipe in markdown and does NOT open a
            # new cell — strip escapes before counting, or valid tables read as broken.
            unescaped = row.replace(r"\|", "")
            c = unescaped.strip().strip("|").count("|") + 1
            counts.setdefault(c, []).append(ln)
        if len(counts) > 1:
            dominant = max(counts, key=lambda k: len(counts[k]))
            offenders = [ln for c, lns in counts.items() if c != dominant for ln in lns]
            err(f"Table near line {blk[0][0]}: inconsistent columns "
                f"(expected {dominant}, offending lines {offenders[:5]})")
            return 1
        return 0

    for i, raw in enumerate(lines, 1):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if raw.strip().startswith("|") and raw.strip().endswith("|"):
            block.append((i, raw))
        else:
            bad += flush(block)
            block = []
    bad += flush(block)
    if not bad:
        ok("all markdown tables have consistent column counts")


def check_duplicate_lines(text: str) -> None:
    """Catch accidentally duplicated directive lines from edits."""
    seen: dict[str, int] = {}
    dupes = []
    in_fence = False
    for i, raw in enumerate(text.split("\n"), 1):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        s = raw.strip()
        if in_fence or len(s) < 40 or not s.startswith("**"):
            continue
        if s in seen:
            dupes.append((seen[s], i, s[:60]))
        else:
            seen[s] = i
    if dupes:
        for a, b, snippet in dupes:
            err(f"Duplicated directive at lines {a} and {b}: '{snippet}...'")
    else:
        ok("no duplicated directive lines")


# --------------------------------------------------------------- references
def check_scripts(text: str, base: str) -> None:
    refs = sorted(set(re.findall(r"scripts/[A-Za-z0-9_]+\.py", text)))
    if not refs:
        warn("no bundled scripts referenced")
        return
    for r in refs:
        p = os.path.join(base, r)
        if not os.path.exists(p):
            err(f"Referenced script missing from bundle: {r}")
            continue
        try:
            res = subprocess.run([sys.executable, p, "--help"],
                                 capture_output=True, timeout=20)
            if res.returncode != 0:
                err(f"Script fails to run: {r} (exit {res.returncode})")
            else:
                ok(f"script runs: {r}")
        except Exception as e:  # noqa: BLE001
            err(f"Script errored: {r} — {e}")


def check_reference_files(text: str, base: str) -> None:
    refs = sorted(set(re.findall(r"`((?:references|eval)/[A-Za-z0-9_./-]+\.md)`", text)))
    if not refs:
        warn("no reference files linked from SKILL.md")
        return
    missing = [r for r in refs if not os.path.exists(os.path.join(base, r))]
    if missing:
        for m in missing:
            err(f"Referenced resource missing from bundle: {m}")
    else:
        ok(f"all {len(refs)} referenced resource files present")


def check_phase_sections(text: str) -> None:
    required = ["P0", "P1", "P2b", "P2", "P2c", "P3", "P4", "P5", "P6", "P7", "P8"]
    heads = re.findall(r"^##\s+(P\d[a-c]?)\s*·", text, re.M)
    for p in required:
        if p not in heads:
            err(f"Missing phase section: ## {p} ·")
    if len(set(heads)) == len(heads):
        ok(f"all {len(heads)} phase sections present and unique")
    else:
        err(f"Duplicate phase headings: {heads}")


def check_section_refs(text: str) -> None:
    """Every §X.Y cross-reference must have a matching '### X.Y' heading."""
    refs = set(re.findall(r"§(\d+(?:\.\d+)?[a-z]?)", text))
    heads = set(re.findall(r"^###\s+(\d+\.\d+[a-z]?)", text, re.M))
    missing = sorted(r for r in refs if r not in heads)
    if missing:
        err(f"Dangling section references (no matching heading): {missing}")
    else:
        ok(f"all {len(refs)} §-references resolve")


def check_modes(text: str) -> None:
    """Every mode in the router table must be defined and reachable."""
    defined = set(re.findall(r"\*\*(M\d+)\s*·", text))
    referenced = set(re.findall(r"\b(M\d+)\b", text))
    undefined = sorted(referenced - defined, key=lambda s: int(s[1:]))
    # M# used generically in templates is fine; flag only if never defined at all
    real = [m for m in undefined if m not in ("M#",)]
    if real:
        warn(f"Modes referenced but never defined with '**M#·': {real}")
    if not defined:
        err("No modes defined — router table missing")
    else:
        ok(f"{len(defined)} modes defined: {sorted(defined, key=lambda s: int(s[1:]))}")


def check_outputs(text: str) -> None:
    """Filenames promised in Delivery should be produced by some phase."""
    produced = set(re.findall(r"`([a-z0-9-]+)-\[", text))
    for key in ("clinical-case", "raw-evidence", "clinical-plan", "qa-report"):
        if key not in produced:
            warn(f"Delivery names '{key}' but no phase output defines it")
    ok(f"{len(produced)} named output artifacts defined")


def check_safety_invariants(text: str) -> None:
    must_have = {
        "DRAFT header": "RESEARCH DRAFT — NOT FOR DIRECT CLINICAL USE",
        "emergency protocol": "Emergency protocols",
        "PHI rule": "de-identified",
        "novelty ladder": "NOVELTY MATURITY LADDER",
        "N3 block": "BLOCKED from any treatment recommendation",
        "anti-anchoring": "ANTI-ANCHORING",
        "post-test engine": "post-test probability",
        "English queries": "QUERY IN ENGLISH",
        "occupational history": "Occupational & environmental",
        "bidirectional DDI": "A→B and B→A",
        "residue rule": "UNEXPLAINED FINDING IS DATA",
        "open requests": "OPEN REQUESTS",
        "personal baseline": "Personal baseline & rate of change",
        "episodic intake": "Episodic & relapsing presentations",
        "guideline hierarchy": "Guideline hierarchy",
        "threshold rule": "does not belong in the workup",
        "citation hard gate": "HARD GATE",
        "citation removal rule": "REMOVE the reference",
        "calibration protocol": "CALIBRATE, DON'T REASSURE",
        "would-change-if": "Would change if",
        "appraisal instruments": "AGREE II",
        "QUADAS-2 gate": "QUADAS-2",
        "appraisal supervision": "not automated verdicts",
        "specialty routing": "Specialty routing",
        "retraction gate": "Retraction status",
        "resolution-not-validity": "resolution is not validity",
        "retraction outranks": "outranks every other verdict",
        "citation drift": "Citation drift",
        "context transfer": "Context transfer mismatch",
        "contradiction taxonomy": "Contradiction taxonomy",
        "citation roles": "Citation roles",
        "trajectory axis": "Functional trajectory & goals of care",
        "palliative trigger": "Palliative-parallel trigger",
        "proportionality gate": "proportionality gate",
        "two-axis plan": "ARM B · COMFORT-DIRECTED",
        "concurrent option": "CONCURRENT",
        "no-assumed-maximal": "maximal intervention is the default",
        "positive ceiling": "stated positively",
        "prognosis range": "never a single number",
    }
    for label, needle in must_have.items():
        if needle not in text:
            err(f"Safety/quality invariant missing: {label} ('{needle}')")
    if not any(f"Safety/quality invariant missing" in e for e in errors):
        ok(f"all {len(must_have)} safety/quality invariants present")


def check_stale_versions(text: str) -> None:
    m = re.search(r'version:\s*"([\d.]+)"', text)
    if not m:
        err("No version in metadata")
        return
    cur = m.group(1)
    title = re.search(r"^#\s+Clinical-Assistant v([\d.]+)", text, re.M)
    if not title:
        err("No version in H1 title")
    elif title.group(1) != cur:
        err(f"Version mismatch: metadata {cur} vs title {title.group(1)}")
    # delivery blocks
    for v in set(re.findall(r"CLINICAL-ASSISTANT v([\d.]+)", text)):
        if v != cur:
            err(f"Stale version '{v}' in a Delivery block (current {cur})")
    if not [e for e in errors if "ersion" in e]:
        ok(f"version {cur} consistent across title, metadata and delivery blocks")


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = sys.argv[1] if len(sys.argv) > 1 else "SKILL.md"
    if not os.path.exists(path):
        print(f"FATAL: {path} not found")
        return 1
    base = os.path.dirname(os.path.abspath(path)) or "."
    text = open(path, encoding="utf-8").read()

    check_frontmatter(text)
    check_fences(text)
    check_tables(text)
    check_duplicate_lines(text)
    check_scripts(text, base)
    check_reference_files(text, base)
    check_phase_sections(text)
    check_section_refs(text)
    check_modes(text)
    check_outputs(text)
    check_safety_invariants(text)
    check_stale_versions(text)

    print(f"\n{'=' * 62}\n  SKILL VALIDATION — {path}\n{'=' * 62}")
    for p in passed:
        print(f"  PASS  {p}")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    print(f"{'-' * 62}")
    print(f"  {len(passed)} passed · {len(warnings)} warnings · {len(errors)} errors")
    print(f"  STATUS: {'CLEAN' if not errors else 'BLOCKED'}\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
