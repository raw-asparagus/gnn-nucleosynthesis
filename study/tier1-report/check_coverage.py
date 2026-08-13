#!/usr/bin/env python3
"""Coverage check: study/tier1.md -> study/tier1-report/.

Asserts that the LaTeX re-architecture omitted nothing from the Markdown
source. This is a study-material check, not a project measurement -- it
produces no RESULTS.md number and deliberately lives beside the report
rather than in scripts/.

The tier-1 report re-architects the source into epistemic LAYERS (theory,
the compiled evaluator, verification, policy, the open register) rather
than keeping its node-by-node parts, so a single source part's argument
can land in three sections. That makes the concordance in Appendix B
load-bearing, and check 6 below is what keeps it honest.

Run:  uv run python study/tier1-report/check_coverage.py
      (build the PDF first -- checks 4 and 7 read the .aux files)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "tier1.md"
# _concordance_rows.tex is generated table data, not prose; it is \input by
# B-concordance.tex and counted through it.
PARTS = sorted(p for p in (HERE / "parts").glob("*.tex")
               if not p.name.startswith("_"))
ROWS = HERE / "parts" / "_concordance_rows.tex"

failures: list[str] = []
notes: list[str] = []


def check(label: str, got, want, *, hard: bool = True) -> None:
    ok = got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: {got} (expected {want})")
    if not ok:
        (failures if hard else notes).append(f"{label}: {got} != {want}")


def check_ge(label: str, got, want, *, hard: bool = True) -> None:
    ok = got >= want
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: {got} (expected >= {want})")
    if not ok:
        (failures if hard else notes).append(f"{label}: {got} < {want}")


def strip_comments(text: str) -> str:
    """Drop TeX line comments so documentation examples are not counted."""
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in text.splitlines())


def tex_all() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in PARTS)


def md_headings(md: str) -> list[tuple[int, str]]:
    """Markdown headings, excluding '#' comment lines inside fenced blocks.

    tier1.md has six such false positives (lines 2502, 2504, 2505 inside a
    Python fence in V.1; 3099-3101 inside a fence in VI.3).
    """
    out, inb = [], False
    for i, line in enumerate(md.split("\n"), 1):
        if line.startswith("```"):
            inb = not inb
            continue
        if inb:
            continue
        if re.match(r"^#{1,3} ", line):
            out.append((i, line))
    return out


def main() -> int:
    md = SRC.read_text(encoding="utf-8")
    tex = tex_all()
    tex_nc = strip_comments(tex)

    print(f"source : {SRC}  ({md.count(chr(10)) + 1} lines)")
    print(f"report : {len(PARTS)} .tex files\n")

    # ---- 1. self-check blocks and questions -----------------------------
    print("1. Self-check coverage")
    md_blocks = re.findall(r"^#{2,3} .*[Ss]elf-check.*$", md, re.M)
    md_questions = 0
    for m in re.finditer(r"^#{2,3} .*[Ss]elf-check.*$", md, re.M):
        tail = md[m.end():]
        nxt = re.search(r"^#{1,3} ", tail, re.M)
        body = tail[: nxt.start()] if nxt else tail
        md_questions += len(re.findall(r"^\d+\. ", body, re.M))

    tex_blocks = re.findall(r"\\begin\{selfcheck\}", tex_nc)
    tex_questions = 0
    for m in re.finditer(r"\\begin\{selfcheck\}(.*?)\\end\{selfcheck\}", tex_nc, re.S):
        tex_questions += len(re.findall(r"^\s*\\item\b", m.group(1), re.M))

    check("self-check blocks in source", len(md_blocks), 6)
    check("self-check questions in source", md_questions, 44)
    check("self-check questions in report", tex_questions, md_questions)
    # Layering adds one block: the compiled-evaluator section acquires its own,
    # built entirely from questions relocated out of the Part-I/II/V blocks.
    # Every relocation is listed in Appendix B.
    check("self-check blocks in report", len(tex_blocks), len(md_blocks) + 1)

    # ---- 2. numbered equations ------------------------------------------
    print("\n2. Numbered equations")
    md_tags = re.findall(r"\\tag\{([^}]*)\}", md)
    md_boxed = len(re.findall(r"\\boxed", md))
    tex_eqlabels = set(re.findall(r"\\label\{(eq:[a-zA-Z0-9-]+)\}", tex_nc))
    tex_boxed = len(re.findall(r"\\boxed", tex_nc))
    check("\\tag{} equations in source", len(md_tags), 29)
    check("\\boxed in source", md_boxed, 12)
    # 29 tagged + the gh-575 displacement, boxed but untagged in the source.
    check_ge("eq: labels in report", len(tex_eqlabels), len(md_tags) + 1)
    check_ge("\\boxed in report", tex_boxed, md_boxed)
    missing_eq = [k for k in tex_eqlabels
                  if f"\\eqref{{{k}}}" not in tex_nc and f"\\ref{{{k}}}" not in tex_nc]
    print(f"  [note] eq labels never referenced: {len(missing_eq)}"
          f" {sorted(missing_eq) if missing_eq else ''}")

    # ---- 3. tables -------------------------------------------------------
    print("\n3. Tables")
    md_tables = len(re.findall(r"^\|[^\n]*\|\n\|[\s:|-]+\|$", md, re.M))
    tex_tables = (len(re.findall(r"\\begin\{tabularx\}", tex_nc))
                  + len(re.findall(r"\\begin\{tabular\}", tex_nc))
                  + len(re.findall(r"\\begin\{longtable\}", tex_nc)))
    check("markdown tables in source", md_tables, 47)
    check_ge("LaTeX tables in report", tex_tables, md_tables)

    # ---- 4. bibliography -------------------------------------------------
    print("\n4. Bibliography")
    bib = strip_comments((HERE / "parts" / "bibliography.tex").read_text(encoding="utf-8"))
    md_refs = len(re.findall(r"^- ", md[md.index("\n# References"):], re.M))
    keys = re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", bib)
    check("reference entries in source", md_refs, 37)
    check("\\bibitem entries in report", len(keys), md_refs)

    aux = "\n".join(f.read_text(encoding="utf-8", errors="ignore")
                    for f in [HERE / "main.aux", *(HERE / "parts").glob("*.aux")]
                    if f.exists())
    if not aux:
        failures.append("no .aux files -- build the document first")
        return 1
    cited = set()
    for m in re.finditer(r"\\citation\{([^}]*)\}", aux):
        cited.update(k.strip() for k in m.group(1).split(","))
    orphans = sorted(set(keys) - cited)
    unknown = sorted(cited - set(keys))
    check("uncited \\bibitem entries", len(orphans), 0)
    if orphans:
        print(f"         {orphans}")
    check("citations with no \\bibitem", len(unknown), 0)
    if unknown:
        print(f"         {unknown}")

    # ---- 5. fenced blocks -------------------------------------------------
    print("\n5. Fenced blocks (diagrams and listings)")
    md_fences = md.count("\n```") // 2
    figs = len(re.findall(r"\\label\{fig:[a-z0-9]+\}", tex_nc))
    listings = len(re.findall(r"\\begin\{srclisting\}", tex_nc))
    check("fenced blocks in source", md_fences, 34)
    check("TikZ figures in report", figs, 4)
    # 30 unindented fences become listings, plus the two indented fences the
    # source nests inside list items (lines 293-297 and 1730-1733).
    check("verbatim listings in report", listings, 32)
    # Appendix B's diagram table must disposition all 34 unindented blocks.
    diag_at = re.search(r"\\(?:sub)*section\{Diagrams[^}]*\}", tex_nc)
    if diag_at is None:
        failures.append("Appendix B has no Diagrams section")
        return 1
    diag = tex_nc[diag_at.start():]
    diag = diag[: diag.index("\\end{longtable}")]
    diag_rows = len(re.findall(r"\\\\\s*$", diag, re.M)) - 2  # two header rows
    check("blocks listed in Appendix B diagram table", diag_rows, md_fences)

    # ---- 6. every source heading appears in the concordance ---------------
    print("\n6. Concordance completeness")
    heads = md_headings(md)
    check("markdown headings in source (fences excluded)", len(heads), 128)
    rows = [ln for ln in ROWS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    check("rows in the Appendix B heading table", len(rows), len(heads))
    # every row must point at a label that exists
    seclabels = set(re.findall(r"\\label\{((?:sec|part|app|fig|tmp):[a-zA-Z0-9-]+)\}", tex_nc))
    bad = []
    for r in rows:
        for tgt in re.findall(r"\\ref\{([^}]+)\}", r):
            if tgt not in seclabels:
                bad.append(tgt)
    check("concordance rows pointing at a missing label", len(bad), 0)
    if bad:
        print(f"         {sorted(set(bad))}")
    # and every source line number must be a real heading line
    srclines = {ln for ln, _ in heads}
    rowlines = [int(m.group(1)) for r in rows
                if (m := re.search(r"&\s*(\d+)\s*&", r))]
    check("concordance line numbers that are not headings",
          len([x for x in rowlines if x not in srclines]), 0)

    # ---- 7. cross-reference targets ---------------------------------------
    print("\n7. Cross-references")
    reffed = set(re.findall(r"\\(?:eq)?ref\{([a-zA-Z]+:[a-zA-Z0-9-]+)\}", tex_nc))
    alllabels = seclabels | set(re.findall(r"\\label\{([a-zA-Z]+:[a-zA-Z0-9-]+)\}", tex_nc))
    dangling = sorted(reffed - alllabels)
    check("dangling \\ref targets", len(dangling), 0)
    if dangling:
        print(f"         {dangling}")
    print(f"  [note] labels defined {len(alllabels)}, referenced {len(reffed)}")

    # Under a layered architecture a split argument that is not linked from both
    # sides is the characteristic defect.  There is no principled floor on a
    # bare \ref count, so check the thing that actually matters: every anchor
    # whose material was re-homed out of its source part must be referenced from
    # at least two different part files.
    REHOMED = [
        "sec:two-kappa", "sec:nse-coulomb", "sec:weak-screening",
        "sec:code-contract", "sec:coefftensor", "sec:lambda-range",
        "sec:pf-spline", "sec:db-replacement", "sec:screening-code",
        "sec:tabular-path", "sec:ledger-enforcement", "sec:duplicate-links",
        "sec:codepath", "sec:oracle-compile", "sec:oracles-db",
        "sec:oracle-screening", "sec:interp-error", "sec:guard-pf",
        "sec:guard-appendixb", "sec:guard-screening", "sec:guard-reconciled",
    ]
    bodies = {p.name: strip_comments(p.read_text(encoding="utf-8")) for p in PARTS}
    unlinked = [a for a in REHOMED
                if sum(f"\\ref{{{a}}}" in b for b in bodies.values()) < 2]
    check("re-homed anchors linked from < 2 files", len(unlinked), 0)
    if unlinked:
        print(f"         {unlinked}")

    # ---- 8. provenance tags -----------------------------------------------
    print("\n8. Provenance tags (docs/CLAUDE.md Rule 1 in spirit)")
    md_derived = len(re.findall(r"\[derived here\]", md))
    # note the missing trailing space: two of the source tags are line-wrapped
    md_results = len(re.findall(r"\[RESULTS", md))
    check("[derived here] in source", md_derived, 34)
    check("[RESULTS ...] in source", md_results, 34)
    check_ge("\\derivedhere in report", len(re.findall(r"\\derivedhere", tex_nc)), md_derived)
    # Both sides carry one specimen use: the source's bare "[RESULTS]" at line 28
    # and the front matter's \resultsref{date}, each explaining the convention
    # rather than citing a measurement.  Compare the real citations.
    check("\\resultsref in report (real citations)",
          len(re.findall(r"\\resultsref\{", tex_nc)) - 1, md_results - 1)

    # ---- 9. load-bearing caveats survive verbatim -------------------------
    print("\n9. Load-bearing caveats (docs/CLAUDE.md Rule 7)")
    caveats = {
        "not-project-spec": "not project spec",
        "results-md-wins": "\\code{RESULTS.md} wins",
        "reproduces-mesa-not-nature": "reproduces MESA, not nature",
        "vflag-structurally-incapable": "structurally incapable",
        "screened-kappa-doc-discrepancy": "characterisation} next to it is loose",
        "qse-onset-is-a-band": "not a fixed temperature",
        "sef-probably-small": "``probably small'' on a systematic multiplier is not a\nmeasurement",
        "gh575-completeness": "not because the mechanism\nspares them",
        "coulomb-nse-order-ten": "Order\n10, not $10^2$",
        "hot-thin-not-degenerate": "not\ndegenerate at all",
        "invariant5-near-algebraic": "near-algebraic",
        "common-mode": "common-mode",
        "labels-not-nature": "fidelity-to-MESA",
    }
    flat = " ".join(tex_nc.split())
    for name, needle in caveats.items():
        ok = " ".join(needle.split()) in flat
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
        if not ok:
            failures.append(f"caveat missing: {name}")

    # ---- verdict ----------------------------------------------------------
    print("\n" + "=" * 62)
    if failures:
        print(f"FAIL  ({len(failures)} problem(s))")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS  nothing omitted by these checks")
    for n in notes:
        print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
