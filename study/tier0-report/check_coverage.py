#!/usr/bin/env python3
"""Coverage check: study/tier0.md -> study/tier0-report/.

Asserts that the LaTeX re-architecture omitted nothing from the Markdown
source. This is a study-material check, not a project measurement -- it
produces no RESULTS.md number and deliberately lives beside the report
rather than in scripts/.

Run:  uv run python study/tier0-report/check_coverage.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "tier0.md"
PARTS = sorted((HERE / "parts").glob("*.tex"))

failures: list[str] = []
notes: list[str] = []


def check(label: str, got, want, *, hard: bool = True) -> None:
    ok = got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: {got} (expected {want})")
    if not ok:
        (failures if hard else notes).append(f"{label}: {got} != {want}")


def strip_comments(text: str) -> str:
    """Drop TeX line comments so documentation examples are not counted."""
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in text.splitlines())


def tex_all() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in PARTS)


def main() -> int:
    md = SRC.read_text(encoding="utf-8")
    tex = tex_all()

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

    tex_blocks = re.findall(r"\\begin\{selfcheck\}", tex)
    tex_questions = 0
    for m in re.finditer(r"\\begin\{selfcheck\}(.*?)\\end\{selfcheck\}", tex, re.S):
        tex_questions += len(re.findall(r"^\s*\\item\b", m.group(1), re.M))

    check("self-check blocks in source", len(md_blocks), 12)
    check("self-check questions in source", md_questions, 73)
    check("self-check questions in report", tex_questions, md_questions)
    # 0.7.1 merges into the network block and I.9 splits across two parts,
    # so the block count happens to come out unchanged. Recorded in Appendix B.
    check("self-check blocks in report", len(tex_blocks), len(md_blocks))

    # ---- 2. numbered equations ------------------------------------------
    print("\n2. Numbered equations")
    md_tags = re.findall(r"\\tag\{([^}]*)\}", md)
    tex_eqlabels = set(re.findall(r"\\label\{(eq:[a-z0-9-]+)\}", tex))
    check("\\tag{} equations in source", len(md_tags), 21)
    check("eq: labels in report", len(tex_eqlabels), 25)  # 21 + 4 newly numbered
    missing_eq = [k for k in tex_eqlabels if f"\\eqref{{{k}}}" not in tex
                  and f"\\ref{{{k}}}" not in tex]
    print(f"  [note] eq labels never referenced: {len(missing_eq)}"
          f" {sorted(missing_eq) if missing_eq else ''}")

    # ---- 3. tables -------------------------------------------------------
    print("\n3. Tables")
    md_tables = len(re.findall(r"^\|[^\n]*\|\n\|[\s:|-]+\|$", md, re.M))
    tex_tables = (len(re.findall(r"\\begin\{tabularx\}", tex))
                  + len(re.findall(r"\\begin\{tabular\}", tex))
                  + len(re.findall(r"\\begin\{longtable\}", tex)))
    check("markdown tables in source", md_tables, 29)
    print(f"  [note] LaTeX tables in report: {tex_tables} "
          f"(source tables + concordance/appendix tables)")
    if tex_tables < md_tables:
        failures.append(f"report has fewer tables ({tex_tables}) than source ({md_tables})")

    # ---- 4. bibliography -------------------------------------------------
    print("\n4. Bibliography")
    bib = strip_comments((HERE / "parts" / "bibliography.tex").read_text(encoding="utf-8"))
    md_refs = len(re.findall(r"^- ", md[md.index("\n# References"):], re.M))
    keys = re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", bib)
    check("reference entries in source", md_refs, 89)
    check("\\bibitem entries in report", len(keys), md_refs)

    # \citation{...} lines in the .aux files are what LaTeX actually resolved.
    aux = "\n".join(f.read_text(encoding="utf-8", errors="ignore")
                    for f in [HERE / "main.aux", *(HERE / "parts").glob("*.aux")]
                    if f.exists())
    if not aux:
        failures.append("no .aux files -- build the document first")
        return 1
    cited = set()
    for m in re.finditer(r"\\citation\{([^}]*)\}", aux):
        cited.update(k.strip() for k in m.group(1).split(","))
    # janka2007 appears in the SOURCE document's reference list but is never
    # cited in its body. Preserving it uncited is faithful; inventing a
    # citation would not be.
    SOURCE_SIDE_ORPHANS = {"janka2007"}
    orphans = sorted(set(keys) - cited - SOURCE_SIDE_ORPHANS)
    unknown = sorted(cited - set(keys))
    check("uncited \\bibitem entries", len(orphans), 0)
    if orphans:
        print(f"         {orphans}")
    check("citations with no \\bibitem", len(unknown), 0)
    print(f"  [note] uncited in the source too, preserved verbatim: "
          f"{sorted(SOURCE_SIDE_ORPHANS)}")
    if unknown:
        print(f"         {unknown}")

    # ---- 5. fenced blocks -------------------------------------------------
    print("\n5. Fenced blocks (diagrams and listings)")
    md_fences = md.count("\n```") // 2
    figs = len(re.findall(r"\\label\{fig:[a-z0-9]+\}", tex))
    listings = len(re.findall(r"\\begin\{srclisting\}", tex))
    check("fenced blocks in source", md_fences, 12)
    check("TikZ figures in report", figs, 7)
    check("verbatim listings in report", listings, 2)
    # remaining 3 fenced blocks became tables; verified by the Appendix B
    # diagram table, which must list all 12.
    # level-agnostic: the Diagrams heading may sit at any sectioning depth
    diag_at = re.search(r"\\(?:sub)*section\*?\{Diagrams\}", tex)
    if diag_at is None:
        failures.append("Appendix B has no Diagrams heading")
        return 1
    diag = tex[diag_at.start():]
    diag_rows = len(re.findall(r"&", diag[: diag.index("\\end{tabularx}")])) - 1
    check("blocks listed in Appendix B diagram table", diag_rows, 12)

    # ---- 6. every source heading appears in the concordance ---------------
    print("\n6. Concordance completeness")
    conc = (HERE / "parts" / "B-concordance.tex").read_text(encoding="utf-8")
    headings = re.findall(r"^#{2,3} ((?:0|I|II|III|IV|V|VI|VII)[\.\dIVX]*)\s", md, re.M)
    numbered = sorted(set(headings))
    absent = [h for h in numbered
              if not re.search(rf"(?<![\d.]){re.escape(h)}(?![\d.])", conc)]
    print(f"  [note] numbered source sections: {len(numbered)}")
    check("numbered sections absent from concordance", len(absent), 0)
    if absent:
        print(f"         {absent}")

    # ---- 7. cross-reference targets ---------------------------------------
    print("\n7. Cross-references")
    seclabels = set(re.findall(r"\\label\{(sec:[a-z0-9-]+)\}", tex))
    reffed = set(re.findall(r"\\ref\{(sec:[a-z0-9-]+)\}", tex))
    dangling = sorted(reffed - seclabels)
    check("dangling \\ref targets", len(dangling), 0)
    if dangling:
        print(f"         {dangling}")
    print(f"  [note] sec: labels defined {len(seclabels)}, referenced {len(reffed)}")

    # ---- 8. load-bearing caveats survive verbatim -------------------------
    print("\n8. Load-bearing caveats (docs/CLAUDE.md Rule 7)")
    caveats = {
        "retired-by-measurement": "retired by measurement",
        "no-spectral-gap": "not a spectral gap",
        "convective-range-not-a-point": "Carry the range, not a point value",
        "dN-is-not-the-criterion": "is \\emph{not} the criterion",
        "energy-near-algebraic": "near-algebraic",
        "not-project-spec": "not project spec",
        "results-md-wins": "\\code{RESULTS.md} wins",
        "assumed-stiffness-endpoints": "\\emph{assumed}, pending the",
        "K5-is-margin": "design margin, and should be defended as one",
        "vacuous-sobol-bound": "asymptotic bound is vacuous",
        "T-upper-conservative": "conservative",
        "kappa-vacuous-pass": "\\emph{vacuous} pass",
    }
    flat = " ".join(tex.split())
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
