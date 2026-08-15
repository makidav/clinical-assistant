#!/usr/bin/env python3
"""
verify_citations.py — hard gate against fabricated references.

Extracts every PMID and DOI from a file (markdown or .bib) and checks that each
one RESOLVES to a real record, then compares the retrieved title/year against
what the document claims. A reference that does not resolve is not "flagged" —
it is reported as REMOVE.

    python3 scripts/verify_citations.py clinical-report.md
    python3 scripts/verify_citations.py references.bib --json
    python3 scripts/verify_citations.py doc.md --offline   # extract only, no network
    python3 scripts/verify_citations.py --selftest         # verify retraction logic offline

Beyond existence, every resolved reference is checked for RETRACTION, EXPRESSION
OF CONCERN and ERRATUM status. A retracted paper resolves perfectly and matches
its own title — resolution is not validity, and this is the check that catches it.

Exit codes: 0 = all resolved · 1 = at least one unresolved/mismatched · 2 = usage error

NETWORK: needs api.ncbi.nlm.nih.gov (PubMed E-utilities) and api.crossref.org.
If the network is unavailable the script says so and exits 1 — it never reports
an unchecked citation as verified. Set a contact email for polite API use:
    export CITEVERIFY_EMAIL="you@example.org"

Pure stdlib (urllib, json, re). No API key required.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
CROSSREF = "https://api.crossref.org/works/"

# --- retraction status ---------------------------------------------------
# A retracted paper RESOLVES PERFECTLY in PubMed and CrossRef. Checking that an
# identifier exists says nothing about whether the science still stands. These
# are the markers that do.
RETRACTED, CONCERN, CORRECTED, CLEAR, UNKNOWN = (
    "RETRACTED", "EXPRESSION_OF_CONCERN", "CORRECTED", "CLEAR", "UNKNOWN")

# PubMed <CommentsCorrections RefType="..."> on the *cited* article.
# The "...In" forms point forward from the article to the notice about it.
PM_REFTYPE = {
    "RetractionIn": RETRACTED,
    "ExpressionOfConcernIn": CONCERN,
    "ErratumIn": CORRECTED,
    "RepublishedIn": CORRECTED,
}
# PubMed publication types carried by the article record itself.
PM_PUBTYPE = {
    "Retracted Publication": RETRACTED,
    "Expression of Concern": CONCERN,
}
# CrossRef update-to types (present on the notice, and mirrored on some records).
CR_UPDATE = {
    "retraction": RETRACTED,
    "withdrawal": RETRACTED,
    "removal": RETRACTED,
    "expression_of_concern": CONCERN,
    "correction": CORRECTED,
    "erratum": CORRECTED,
    "corrigendum": CORRECTED,
}
SEVERITY = {RETRACTED: 3, CONCERN: 2, CORRECTED: 1, CLEAR: 0, UNKNOWN: 0}
UA = "clinical-assistant-citation-verifier/1.0 (mailto:{})"
TIMEOUT = 20

# DOIs: per the Crossref pattern, stop before whitespace and common trailing punctuation
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
PMID_RE = re.compile(r"\bPMID:?\s*(\d{6,8})\b", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _clean_doi(d: str) -> str:
    return d.rstrip(".,;:)]}>'\"")


def _get(url: str) -> dict | None:
    email = os.environ.get("CITEVERIFY_EMAIL", "unset@example.org")
    req = urllib.request.Request(url, headers={"User-Agent": UA.format(email)})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return {"__http_error__": e.code}
    except Exception as e:  # noqa: BLE001
        return {"__error__": str(e)}


def check_pmid(pmid: str) -> dict:
    url = f"{PUBMED}?db=pubmed&id={pmid}&retmode=json"
    data = _get(url)
    if data is None or "__error__" in data:
        return {"status": "NETWORK_ERROR", "detail": (data or {}).get("__error__", "no response")}
    if "__http_error__" in data:
        return {"status": "NETWORK_ERROR", "detail": f"HTTP {data['__http_error__']}"}
    rec = (data.get("result") or {}).get(pmid)
    if not rec or rec.get("error") or not rec.get("title"):
        return {"status": "UNRESOLVED"}
    out = {
        "status": "RESOLVED",
        "title": rec.get("title", ""),
        "year": (rec.get("pubdate") or "")[:4],
        "journal": rec.get("fulljournalname") or rec.get("source", ""),
    }
    st, notes = fetch_pubmed_status(pmid)
    out["retraction_status"], out["retraction_notes"] = st, notes
    return out


def check_doi(doi: str) -> dict:
    url = CROSSREF + urllib.parse.quote(doi, safe="")
    data = _get(url)
    if data is None or "__error__" in data:
        return {"status": "NETWORK_ERROR", "detail": (data or {}).get("__error__", "no response")}
    if "__http_error__" in data:
        code = data["__http_error__"]
        return {"status": "UNRESOLVED"} if code == 404 else {
            "status": "NETWORK_ERROR", "detail": f"HTTP {code}"}
    msg = data.get("message") or {}
    title = (msg.get("title") or [""])[0]
    if not title:
        return {"status": "UNRESOLVED"}
    parts = (msg.get("issued") or {}).get("date-parts") or [[""]]
    out = {
        "status": "RESOLVED",
        "title": title,
        "year": str(parts[0][0]) if parts and parts[0] else "",
        "journal": (msg.get("container-title") or [""])[0],
    }
    st, notes = parse_crossref_status(msg)
    # PubMed carries richer retraction metadata; prefer it when the DOI maps to a PMID
    pmid = doi_to_pmid(doi)
    if pmid:
        pst, pnotes = fetch_pubmed_status(pmid)
        if SEVERITY.get(pst, 0) > SEVERITY.get(st, 0):
            st, notes = pst, pnotes + [f"via PMID {pmid}"]
        elif pst == CLEAR and st == CLEAR:
            notes.append(f"PubMed clear (PMID {pmid})")
    out["retraction_status"], out["retraction_notes"] = st, notes
    return out


def parse_pubmed_status(xml_text: str) -> tuple[str, list[str]]:
    """Classify retraction status from a PubMed efetch XML record.

    Returns (status, notes). Parsed separately from the network call so the
    logic is testable offline — see --selftest.
    """
    notes: list[str] = []
    status = CLEAR
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return UNKNOWN, [f"unparseable XML: {e}"]

    for cc in root.iter("CommentsCorrections"):
        rt = cc.get("RefType", "")
        mapped = PM_REFTYPE.get(rt)
        if mapped and SEVERITY[mapped] > SEVERITY[status]:
            status = mapped
        if mapped:
            ref = (cc.findtext("PMID") or "").strip()
            notes.append(f"{rt}" + (f" (notice PMID {ref})" if ref else ""))

    for pt in root.iter("PublicationType"):
        mapped = PM_PUBTYPE.get((pt.text or "").strip())
        if mapped and SEVERITY[mapped] > SEVERITY[status]:
            status = mapped
            notes.append(f"PublicationType: {(pt.text or '').strip()}")

    return status, notes


def parse_crossref_status(msg: dict) -> tuple[str, list[str]]:
    """Classify retraction status from a CrossRef `message` object."""
    notes: list[str] = []
    status = CLEAR
    for upd in (msg.get("update-to") or []):
        mapped = CR_UPDATE.get(str(upd.get("type", "")).lower())
        if mapped:
            if SEVERITY[mapped] > SEVERITY[status]:
                status = mapped
            notes.append(f"update-to: {upd.get('type')} → {upd.get('DOI', '')}")
    for k in ("update-policy",):
        if msg.get(k):
            notes.append(f"{k} present")
    return status, notes


def fetch_pubmed_status(pmid: str) -> tuple[str, list[str]]:
    url = f"{EFETCH}?db=pubmed&id={pmid}&retmode=xml"
    email = os.environ.get("CITEVERIFY_EMAIL", "unset@example.org")
    req = urllib.request.Request(url, headers={"User-Agent": UA.format(email)})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return parse_pubmed_status(r.read().decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        return UNKNOWN, [f"lookup failed: {e}"]


def doi_to_pmid(doi: str) -> str | None:
    """Resolve a DOI to a PMID so the richer PubMed retraction data can be used."""
    q = urllib.parse.quote(f"{doi}[AID]", safe="")
    data = _get(f"{ESEARCH}?db=pubmed&term={q}&retmode=json")
    if not data or "__error__" in data or "__http_error__" in data:
        return None
    ids = ((data.get("esearchresult") or {}).get("idlist") or [])
    return ids[0] if ids else None


def _context(text: str, idx: int, span: int = 240) -> str:
    lo = max(0, idx - span)
    return text[lo: idx + span].replace("\n", " ")


def _title_agrees(claimed_ctx: str, real_title: str) -> bool:
    """Loose check: do enough distinctive words of the real title appear nearby?"""
    words = [w.lower() for w in re.findall(r"[A-Za-z]{5,}", real_title)]
    if not words:
        return True
    ctx = claimed_ctx.lower()
    hits = sum(1 for w in set(words) if w in ctx)
    return hits >= max(2, len(set(words)) // 4)


# --------------------------------------------------------------- self-test
# Fixtures mirror the shape of real PubMed efetch XML / CrossRef JSON so the
# classification logic can be verified with no network access.
_FX_RETRACTED = """<PubmedArticleSet><PubmedArticle><MedlineCitation>
<PMID>11111111</PMID><Article><ArticleTitle>A study later retracted</ArticleTitle>
<PublicationTypeList><PublicationType>Journal Article</PublicationType>
<PublicationType>Retracted Publication</PublicationType></PublicationTypeList></Article>
<CommentsCorrectionsList><CommentsCorrections RefType="RetractionIn">
<PMID>22222222</PMID></CommentsCorrections></CommentsCorrectionsList>
</MedlineCitation></PubmedArticle></PubmedArticleSet>"""

_FX_CONCERN = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>33333333</PMID>
<Article><ArticleTitle>A study under concern</ArticleTitle><PublicationTypeList>
<PublicationType>Journal Article</PublicationType></PublicationTypeList></Article>
<CommentsCorrectionsList><CommentsCorrections RefType="ExpressionOfConcernIn">
<PMID>44444444</PMID></CommentsCorrections></CommentsCorrectionsList>
</MedlineCitation></PubmedArticle></PubmedArticleSet>"""

_FX_ERRATUM = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>55555555</PMID>
<Article><ArticleTitle>A study with an erratum</ArticleTitle><PublicationTypeList>
<PublicationType>Randomized Controlled Trial</PublicationType></PublicationTypeList></Article>
<CommentsCorrectionsList><CommentsCorrections RefType="ErratumIn">
<PMID>66666666</PMID></CommentsCorrections></CommentsCorrectionsList>
</MedlineCitation></PubmedArticle></PubmedArticleSet>"""

_FX_CLEAN = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>77777777</PMID>
<Article><ArticleTitle>An ordinary paper</ArticleTitle><PublicationTypeList>
<PublicationType>Journal Article</PublicationType></PublicationTypeList></Article>
</MedlineCitation></PubmedArticle></PubmedArticleSet>"""

# A retracted paper commented on by an unrelated note: severity must take the max,
# not the last-seen marker.
_FX_MIXED = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>88888888</PMID>
<Article><ArticleTitle>Mixed markers</ArticleTitle><PublicationTypeList>
<PublicationType>Journal Article</PublicationType></PublicationTypeList></Article>
<CommentsCorrectionsList>
<CommentsCorrections RefType="RetractionIn"><PMID>99999999</PMID></CommentsCorrections>
<CommentsCorrections RefType="ErratumIn"><PMID>10101010</PMID></CommentsCorrections>
</CommentsCorrectionsList></MedlineCitation></PubmedArticle></PubmedArticleSet>"""


def selftest() -> int:
    cases = [
        ("pubmed retracted (pubtype + RetractionIn)", parse_pubmed_status, _FX_RETRACTED, RETRACTED),
        ("pubmed expression of concern", parse_pubmed_status, _FX_CONCERN, CONCERN),
        ("pubmed erratum only", parse_pubmed_status, _FX_ERRATUM, CORRECTED),
        ("pubmed clean article", parse_pubmed_status, _FX_CLEAN, CLEAR),
        ("severity takes max, not last", parse_pubmed_status, _FX_MIXED, RETRACTED),
        ("malformed XML -> UNKNOWN, never CLEAR", parse_pubmed_status, "<not xml", UNKNOWN),
        ("crossref retraction", parse_crossref_status,
         {"update-to": [{"type": "retraction", "DOI": "10.1/x"}]}, RETRACTED),
        ("crossref correction", parse_crossref_status,
         {"update-to": [{"type": "correction", "DOI": "10.1/y"}]}, CORRECTED),
        ("crossref expression of concern", parse_crossref_status,
         {"update-to": [{"type": "expression_of_concern", "DOI": "10.1/z"}]}, CONCERN),
        ("crossref no updates", parse_crossref_status, {"title": ["x"]}, CLEAR),
    ]
    fails = 0
    print(f"\n{'=' * 66}\n  RETRACTION LOGIC SELF-TEST (offline)\n{'=' * 66}")
    for name, fn, arg, expect in cases:
        got, _ = fn(arg)
        good = got == expect
        fails += 0 if good else 1
        print(f"  {'PASS' if good else 'FAIL'}  {name:44} → {got}"
              + ("" if good else f"  (expected {expect})"))
    print(f"{'-' * 66}\n  {len(cases) - fails}/{len(cases)} passed · "
          f"STATUS: {'CLEAN' if not fails else 'BROKEN'}\n")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="markdown or .bib file to check")
    ap.add_argument("--selftest", action="store_true",
                    help="verify retraction-classification logic offline (no network)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--offline", action="store_true",
                    help="extract identifiers only; make no network calls")
    ap.add_argument("--delay", type=float, default=0.34,
                    help="seconds between API calls (default 0.34, ~3/s)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.path:
        ap.print_help()
        return 2
    if not os.path.exists(args.path):
        print(f"FATAL: {args.path} not found", file=sys.stderr)
        return 2

    text = open(args.path, encoding="utf-8", errors="replace").read()

    found: list[tuple[str, str, int]] = []
    for m in PMID_RE.finditer(text):
        found.append(("pmid", m.group(1), m.start()))
    for m in DOI_RE.finditer(text):
        found.append(("doi", _clean_doi(m.group(0)), m.start()))

    # de-duplicate on (kind, value), keep first occurrence
    seen: set[tuple[str, str]] = set()
    unique = []
    for kind, val, pos in found:
        if (kind, val) not in seen:
            seen.add((kind, val))
            unique.append((kind, val, pos))

    if not unique:
        msg = "No PMIDs or DOIs found. If this document makes clinical claims, that is itself a finding."
        print(json.dumps({"status": "NO_CITATIONS", "note": msg}) if args.json else f"\n  {msg}\n")
        return 0

    if args.offline:
        out = [{"kind": k, "id": v} for k, v, _ in unique]
        print(json.dumps(out, indent=2) if args.json
              else "\n".join(f"  {k.upper():5} {v}" for k, v, _ in unique))
        print(f"\n  {len(unique)} identifiers extracted (offline mode — NOT verified)\n")
        return 0

    results = []
    for kind, val, pos in unique:
        r = check_pmid(val) if kind == "pmid" else check_doi(val)
        r.update({"kind": kind, "id": val})
        if r["status"] == "RESOLVED":
            ctx = _context(text, pos)
            r["title_agrees"] = _title_agrees(ctx, r.get("title", ""))
            yrs = YEAR_RE.findall(ctx)
            claimed_years = {y for y in re.findall(r"\b(?:19|20)\d{2}\b", ctx)}
            r["year_agrees"] = (not r.get("year")) or (r["year"] in claimed_years) or not claimed_years
            rs = r.get("retraction_status", UNKNOWN)
            # Retraction outranks every other verdict: a retracted paper resolves
            # perfectly and matches its title. Resolution is not validity.
            if rs == RETRACTED:
                r["verdict"] = "RETRACTED"
            elif rs == CONCERN:
                r["verdict"] = "CONCERN"
            elif not r["title_agrees"]:
                r["verdict"] = "MISMATCH"
            elif not r["year_agrees"]:
                r["verdict"] = "YEAR_MISMATCH"
            elif rs == CORRECTED:
                r["verdict"] = "CORRECTED"
            else:
                r["verdict"] = "OK"
        elif r["status"] == "UNRESOLVED":
            r["verdict"] = "REMOVE"
        else:
            r["verdict"] = "UNCHECKED"
        results.append(r)
        time.sleep(args.delay)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'=' * 66}\n  CITATION VERIFICATION — {args.path}\n{'=' * 66}")
        for r in results:
            tag = {"OK": "OK      ", "MISMATCH": "MISMATCH", "YEAR_MISMATCH": "YEAR    ",
                   "REMOVE": "REMOVE  ", "UNCHECKED": "UNCHECK ",
                   "RETRACTED": "RETRACTED", "CONCERN": "CONCERN ",
                   "CORRECTED": "CORRECTED"}[r["verdict"]]
            line = f"  {tag} {r['kind'].upper():4} {r['id']}"
            if r.get("title"):
                line += f"  — {r['title'][:64]}"
            if r["verdict"] == "MISMATCH":
                line += "\n           ^ resolves, but the cited context does not match this record"
            if r["verdict"] == "REMOVE":
                line += "\n           ^ DOES NOT RESOLVE — remove this reference, do not merely flag it"
            if r["verdict"] == "RETRACTED":
                line += ("\n           ^ THIS PAPER HAS BEEN RETRACTED — remove the citation AND every"
                         "\n             claim resting on it. It resolved and matched: resolution is not validity."
                         f"\n             {'; '.join(r.get('retraction_notes') or [])}")
            if r["verdict"] == "CONCERN":
                line += ("\n           ^ EXPRESSION OF CONCERN — do not use as a load-bearing source."
                         "\n             Keep only with an explicit written justification."
                         f"\n             {'; '.join(r.get('retraction_notes') or [])}")
            if r["verdict"] == "CORRECTED":
                line += ("\n           ^ CORRECTED/ERRATUM published — check whether the correction touches"
                         "\n             the specific claim cited here. An erratum may leave it intact, or invert it."
                         f"\n             {'; '.join(r.get('retraction_notes') or [])}")
            if r["verdict"] == "UNCHECKED":
                line += f"\n           ^ could not verify ({r.get('detail', '')}) — treat as UNVERIFIED, never as OK"
            print(line)
        n_ret = sum(1 for r in results if r["verdict"] == "RETRACTED")
        n_con = sum(1 for r in results if r["verdict"] == "CONCERN")
        n_cor = sum(1 for r in results if r["verdict"] == "CORRECTED")
        n_bad = sum(1 for r in results if r["verdict"] in ("REMOVE", "MISMATCH"))
        n_unk = sum(1 for r in results if r["verdict"] == "UNCHECKED")
        print(f"{'-' * 66}")
        print(f"  {len(results)} checked · {n_bad} unresolved/mismatched · {n_ret} RETRACTED · "
              f"{n_con} concern · {n_cor} corrected · {n_unk} unverified")
        blocking = n_bad + n_ret + n_con + n_unk
        print(f"  GATE: {'PASS' if blocking == 0 else 'FAIL'}"
              + ("   (corrected items need a claim-level check, not removal)" if n_cor and not blocking else "")
              + "\n")

    bad = any(r["verdict"] in ("REMOVE", "MISMATCH", "UNCHECKED", "RETRACTED", "CONCERN")
              for r in results)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
