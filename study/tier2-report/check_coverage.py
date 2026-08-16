#!/usr/bin/env python3
"""Coverage check: study/tier2.md -> study/tier2-report/.

Asserts that the LaTeX re-architecture omitted nothing from the Markdown
source. This is a study-material check, not a project measurement -- it
produces no RESULTS.md number and deliberately lives beside the report
rather than in scripts/.

The tier-2 report re-architects the source into a PHYSICS ARC rather than
keeping its node-by-node parts: the S7-S10 curriculum labels are
dissolved, equilibrium (source Part III) is derived before the flux
algebra (source Part II), and the two S9 sections that are defined
against kappa travel forward with it. That makes the concordance in
Appendix B load-bearing, and checks 6 and 10 below are what keep it
honest.

Run:  uv run python study/tier2-report/check_coverage.py
      (build the PDF first -- checks 4 and 7 read the .aux files)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "tier2.md"
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

    tier2.md has one such false positive (the '# complexes = ...' comment
    inside the Python fence at line 1331, in the deficiency measurement).
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
    rows_nc = strip_comments(ROWS.read_text(encoding="utf-8"))
    # For reference resolution the generated concordance rows count too: they
    # are the only place many section anchors are linked from.
    tex_and_rows = tex_nc + "\n" + rows_nc

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

    check("self-check blocks in source", len(md_blocks), 5)
    check("self-check questions in source", md_questions, 40)
    check("self-check questions in report", tex_questions, md_questions)
    # The arc redistributes but does not merge or split the blocks: S9's two
    # kappa-dependent questions move into the S8 block (Appendix B.2).
    check("self-check blocks in report", len(tex_blocks), len(md_blocks))

    # ---- 2. equations ----------------------------------------------------
    print("\n2. Equations")
    md_tags = re.findall(r"\\tag\{([^}]*)\}", md)
    md_boxed = len(re.findall(r"\\boxed", md))
    tex_eqlabels = set(re.findall(r"\\label\{(eq:[a-zA-Z0-9-]+)\}", tex_nc))
    tex_boxed = len(re.findall(r"\\boxed", tex_nc))
    # The source numbers no equations at all; it marks its headline identities
    # with \boxed instead.  All five must survive, boxed.
    check("\\tag{} equations in source", len(md_tags), 0)
    check("\\boxed in source", md_boxed, 5)
    check("\\boxed in report", tex_boxed, md_boxed)
    check_ge("eq: labels in report", len(tex_eqlabels), 70)
    missing_eq = [k for k in tex_eqlabels
                  if f"\\eqref{{{k}}}" not in tex_and_rows
                  and f"\\ref{{{k}}}" not in tex_and_rows]
    print(f"  [note] eq labels never referenced: {len(missing_eq)}")

    # ---- 3. tables -------------------------------------------------------
    print("\n3. Tables")
    md_tables = len(re.findall(r"^\|[^\n]*\|\n\|[\s:|-]+\|$", md, re.M))
    tex_tables = (len(re.findall(r"\\begin\{tabularx\}", tex_nc))
                  + len(re.findall(r"\\begin\{tabular\}", tex_nc))
                  + len(re.findall(r"\\begin\{longtable\}", tex_nc)))
    check("markdown tables in source", md_tables, 40)
    check_ge("LaTeX tables in report", tex_tables, md_tables)

    # ---- 4. bibliography -------------------------------------------------
    print("\n4. Bibliography")
    bib = strip_comments((HERE / "parts" / "bibliography.tex").read_text(encoding="utf-8"))
    md_refs = len(re.findall(r"^- ", md[md.index("\n# References"):], re.M))
    keys = re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", bib)
    check("reference entries in source", md_refs, 97)
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
    # Plus one fence indented inside a list item (the Wegscheider top-offender
    # dump at source line 4137), which the unindented count above misses.
    md_blocks_total = md_fences + 1
    figs = len(re.findall(r"\\label\{fig:[a-z0-9]+\}", tex_nc))
    listings = (len(re.findall(r"\\begin\{srclisting\}", tex_nc))
                + len(re.findall(r"\\begin\{srclistingtiny\}", tex_nc)))
    check("unindented fenced blocks in source", md_fences, 32)
    check("TikZ figures in report", figs, 3)
    # 33 source blocks: 3 become TikZ figures, 30 are set verbatim.
    check("verbatim listings in report", listings, md_blocks_total - figs)
    # Appendix B's diagram table must disposition all 33 blocks.
    diag_at = re.search(r"\\(?:sub)*section\{Diagrams[^}]*\}", tex_nc)
    if diag_at is None:
        failures.append("Appendix B has no Diagrams section")
        return 1
    diag = tex_nc[diag_at.start():]
    diag = diag[: diag.index("\\end{longtable}")]
    diag_rows = len(re.findall(r"\\\\\s*$", diag, re.M)) - 2  # two header rows
    check("blocks listed in Appendix B diagram table", diag_rows, md_blocks_total)

    # ---- 6. every source heading appears in the concordance ---------------
    print("\n6. Concordance completeness")
    heads = md_headings(md)
    check("markdown headings in source (fences excluded)", len(heads), 149)
    rows = [ln for ln in rows_nc.splitlines() if ln.strip()]
    check("rows in the Appendix B heading table", len(rows), len(heads))
    seclabels = set(re.findall(
        r"\\label\{((?:sec|part|app|fig|eq):[a-zA-Z0-9-]+)\}", tex_nc))
    bad = []
    for r in rows:
        for tgt in re.findall(r"\\(?:hyper)?ref[\[{]([^\]}]+)[\]}]", r):
            if tgt not in seclabels:
                bad.append(tgt)
    check("concordance rows pointing at a missing label", len(bad), 0)
    if bad:
        print(f"         {sorted(set(bad))}")
    srclines = {ln for ln, _ in heads}
    rowlines = [int(m.group(1)) for r in rows
                if (m := re.search(r"&\s*(\d+)\s*&", r))]
    check("concordance line numbers that are not headings",
          len([x for x in rowlines if x not in srclines]), 0)
    check("source heading lines missing from the concordance",
          len(srclines - set(rowlines)), 0)

    # ---- 7. cross-reference targets ---------------------------------------
    print("\n7. Cross-references")
    reffed = set(re.findall(r"\\(?:eq)?ref\{([a-zA-Z]+:[a-zA-Z0-9-]+)\}",
                            tex_and_rows))
    reffed |= set(re.findall(r"\\hyperref\[([a-zA-Z]+:[a-zA-Z0-9-]+)\]",
                             tex_and_rows))
    alllabels = seclabels | set(
        re.findall(r"\\label\{([a-zA-Z]+:[a-zA-Z0-9-]+)\}", tex_nc))
    dangling = sorted(reffed - alllabels)
    check("dangling \\ref targets", len(dangling), 0)
    if dangling:
        print(f"         {dangling}")
    orphan_labels = sorted(lb for lb in alllabels
                           if lb.startswith(("sec:", "part:")) and lb not in reffed)
    check("section labels never referenced", len(orphan_labels), 0)
    if orphan_labels:
        print(f"         {orphan_labels}")
    print(f"  [note] labels defined {len(alllabels)}, referenced {len(reffed)}")

    # Under a re-ordered architecture a split argument that is not linked from
    # both sides is the characteristic defect.  There is no principled floor on
    # a bare \ref count, so check the thing that actually matters: every anchor
    # whose material was re-homed across a source part boundary must be
    # referenced from at least two different part files.
    REHOMED = [
        "sec:whystructural", "sec:leftnull", "sec:softpenalty",
        "sec:reachable", "sec:departure", "sec:negresults",
        "sec:solververify", "sec:selfcheck-s8",
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
    md_results = len(re.findall(r"\[RESULTS", md))
    check("[derived here] in source", md_derived, 26)
    check("[RESULTS ...] in source", md_results, 47)
    check_ge("\\derivedhere in report", len(re.findall(r"\\derivedhere", tex_nc)),
             md_derived)
    # Of the source's 47 [RESULTS markers, one is the specimen in the status
    # block explaining the convention and two are table COLUMN HEADINGS (the
    # II.8 and II.9 measurement tables), not citations.  The report carries the
    # same specimen and renders the two headings as text.  Compare the real
    # citations.
    check("\\resultsref in report (real citations)",
          len(re.findall(r"\\resultsref\{", tex_nc)) - 1, md_results - 1 - 2)

    # ---- 9. load-bearing caveats survive verbatim -------------------------
    print("\n9. Load-bearing caveats (docs/CLAUDE.md Rule 7)")
    caveats = {
        "not-project-spec": "not project spec",
        "results-md-wins": "\\code{RESULTS.md} wins",
        "vacuous-pass": "the pass is \\textbf{vacuous}",
        "maskable-set-empty": "median 0 at every $\\varepsilon$",
        "not-no-cancellation": "It is \\emph{not} ``there is no\ncancellation''",
        "group-organised-not-equilibrated":
            "group-organised but never\nsingle-cluster-equilibrated",
        "lyapunov-not-ye-drift": "not} a\nbound on \\Ye{} drift",
        "entropy-strong-only":
            "defined on strong\\,/\\,EM paired columns only",
        "weak-never-maskable": "Masking on that basis would be circular",
        "energy-is-a-data-check": "cannot} be measuring integration error",
        "wegscheider-not-our-engine":
            "this is \\emph{not} a problem with the project's own engine",
        "effdim-caveat-shipped": "The number is a lower bound",
        "box-measure-not-support": "Nobody has measured the induced density",
        "cluster-point-estimates-survive":
            "Clustering biases \\emph{precision}",
        "beard-qian-scope": "the $\\tanh$ form of \\S\\ref{sec:kappa-affinity}"
                            " is not in this paper",
        "bcf-single-group": "describes a \\emph{single} quasi-equilibrium group",
        "bethe-yl-not-ye": "quotes trapped \\emph{lepton}\nfraction",
        "monotonicity-tolerance-caveat":
            "The code is right not to trust the proof further than it\ngoes",
        "positivity-not-enforced": "positivity is not enforced at all",
        "labels-bug-displaced": "is not ``physical silicon burning''",
    }
    flat = " ".join(tex_nc.split())
    for name, needle in caveats.items():
        ok = " ".join(needle.split()) in flat
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
        if not ok:
            failures.append(f"caveat missing: {name}")

    # ---- 10. the open register -------------------------------------------
    print("\n10. Open register")
    md_ids = sorted(set(re.findall(r"\bR-(\d\d)\b", md)))
    want_ids = [f"{i:02d}" for i in range(1, 26)]
    # R-00 appears in the source only as part of a heading anchor slug fragment.
    md_ids = [i for i in md_ids if i in want_ids]
    check("register ids in source", md_ids, want_ids)

    reg_at = tex_nc.index("\\label{sec:register}")
    reg = tex_nc[reg_at: tex_nc.index("\\end{longtable}", reg_at)]
    in_table = sorted(set(re.findall(r"\\textbf\{R-(\d\d)\}", reg)))
    check("register ids in the Part 7 table", in_table, want_ids)

    anchors_at = tex_nc.index("\\label{app:registeranchors}")
    anchors = tex_nc[anchors_at: tex_nc.index("\\end{tabularx}", anchors_at)]
    in_anchors = sorted(set(re.findall(r"^R-(\d\d)\b", anchors, re.M)))
    check("register ids in the Appendix B anchor map", in_anchors, want_ids)

    # Every foreign-tier R-number must go through \foreignreg, never \reg.
    stray = re.findall(r"(?<!\\foreignreg\{0\}\{)(?<!\\foreignreg\{1\}\{)"
                       r"\\textbf\{Tier~[01] R-\d\d\}", tex_nc)
    check("foreign R-numbers rendered outside \\foreignreg", len(stray), 0)
    n_foreign = len(re.findall(r"\\foreignreg\{[01]\}\{R-\d\d\}", tex_nc))
    check_ge("cross-tier register citations carried", n_foreign, 5)

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
