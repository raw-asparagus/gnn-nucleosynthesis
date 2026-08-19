#!/usr/bin/env python3
"""Coverage check: study/tier3.md -> study/tier3-report/.

Asserts that the LaTeX re-architecture omitted nothing from the Markdown
source. This is a study-material check, not a project measurement -- it
produces no RESULTS.md number and deliberately lives beside the report
rather than in scripts/.

The tier-3 report re-architects the source into a PHYSICS ARC rather than
keeping its node-by-node parts: the S11-S16 curriculum labels are
dissolved, the weak sector (source 0.7) is derived before the iron core,
MESA's network solver and its return contract (source I.2, I.2b) join the
computational setting, and the two audit passes (source Parts IX, X)
precede the register and the handoff. The Part-0 self-check is split across
five sections. That makes the concordance in Appendix B load-bearing, and
checks 6 and 10 below are what keep it honest.

Run:  uv run python study/tier3-report/check_coverage.py
      (build the PDF first -- checks 4 and 7 read the .aux files)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "tier3.md"
# _concordance_rows.tex and _register_anchor_rows.tex are generated table
# data, not prose; they are \input by B-concordance.tex and counted through it.
PARTS = sorted(p for p in (HERE / "parts").glob("*.tex")
               if not p.name.startswith("_"))
ROWS = HERE / "parts" / "_concordance_rows.tex"
AROWS = HERE / "parts" / "_register_anchor_rows.tex"

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

    tier3.md has one such false positive (the '# the converters REFUSE ...'
    comment inside the Python fence at line 3373, in the eps_nuc pin).
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
    arows_nc = strip_comments(AROWS.read_text(encoding="utf-8"))
    tex_and_rows = tex_nc + "\n" + rows_nc + "\n" + arows_nc

    print(f"source : {SRC}  ({md.count(chr(10)) + 1} lines)")
    print(f"report : {len(PARTS)} .tex files\n")

    # ---- 0. ASCII -----------------------------------------------------------
    print("0. Encoding (pdfLaTeX + T1: every .tex must be 7-bit)")
    nonascii = {}
    for p in [HERE / "main.tex", *PARTS, ROWS, AROWS]:
        bad = [i for i, b in enumerate(p.read_bytes()) if b > 127]
        if bad:
            nonascii[p.name] = len(bad)
    check("files with non-ASCII bytes", len(nonascii), 0)
    if nonascii:
        print(f"         {nonascii}")

    # ---- 1. self-check blocks and questions -----------------------------
    print("\n1. Self-check coverage")
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

    check("self-check blocks in source", len(md_blocks), 7)
    check("self-check questions in source", md_questions, 55)
    check("self-check questions in report", tex_questions, md_questions)
    # The Part-0 block (16 questions) is split across five sections
    # (Appendix B.2); the other six blocks travel whole.  7 - 1 + 5 = 11.
    check("self-check blocks in report", len(tex_blocks), 11)

    # ---- 2. equations ----------------------------------------------------
    print("\n2. Equations")
    md_display = md.count("\n$$") // 2
    md_boxed = len(re.findall(r"\\boxed", md))
    tex_eqlabels = set(re.findall(r"\\label\{(eq:[a-zA-Z0-9-]+)\}", tex_nc))
    tex_boxed = len(re.findall(r"\\boxed", tex_nc))
    check("$$ display blocks in source", md_display, 57)
    check("\\boxed in source", md_boxed, 3)
    check("\\boxed in report", tex_boxed, md_boxed)
    check_ge("eq: labels in report", len(tex_eqlabels), md_display)
    for k in ("eq:virial", "eq:mch", "eq:ecomp"):
        check(f"boxed label {k} present", k in tex_eqlabels, True)
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
    check("markdown tables in source", md_tables, 63)
    check_ge("LaTeX tables in report", tex_tables, md_tables)

    # ---- 4. bibliography -------------------------------------------------
    print("\n4. Bibliography")
    bib = strip_comments((HERE / "parts" / "bibliography.tex").read_text(encoding="utf-8"))
    md_refs = len(re.findall(r"^- ", md[md.index("\n# References"):], re.M))
    keys = re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", bib)
    check("reference entries in source", md_refs, 169)
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
    listings = (len(re.findall(r"\\begin\{srclisting\}", tex_nc))
                + len(re.findall(r"\\begin\{srclistingtiny\}", tex_nc)))
    check("fenced blocks in source", md_fences, 11)
    check("TikZ figures in report", figs, 3)
    # 11 source blocks: 3 become TikZ figures, 8 are set verbatim.
    check("verbatim listings in report", listings, md_fences - figs)
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
    check("markdown headings in source (fences excluded)", len(heads), 152)
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
    # both sides is the characteristic defect.  Every anchor whose material was
    # re-homed across a source part boundary must be referenced from at least
    # two different part files.
    REHOMED = [
        "sec:netsolver", "sec:netreturns", "sec:callsite", "sec:converging",
        "sec:convergingnow", "sec:register", "sec:epistemics",
        "sec:twodistributions", "sec:yecarriers", "sec:ecratchet",
    ]
    bodies = {p.name: strip_comments(p.read_text(encoding="utf-8")) for p in PARTS}
    unlinked = [a for a in REHOMED
                if sum((f"\\ref{{{a}}}" in b or f"\\hyperref[{a}]" in b
                        or (a == "sec:register" and "\\reg{" in b))
                       for b in bodies.values()) < 2]
    check("re-homed anchors linked from < 2 files", len(unlinked), 0)
    if unlinked:
        print(f"         {unlinked}")

    # ---- 8. provenance tags -----------------------------------------------
    print("\n8. Provenance tags (docs/CLAUDE.md Rule 1 in spirit)")
    md_derived = len(re.findall(r"\[derived here", md))
    md_results = len(re.findall(r"\*\*\[RESULTS\]\*\*", md))
    md_typical = len(re.findall(r"\[typical", md))
    md_assumed = len(re.findall(r"\[assumed", md))
    md_sourced = len(re.findall(r"\[sourced", md))
    md_derivedthere = len(re.findall(r"\[derived there", md))
    check("[derived here in source", md_derived, 28)
    check("**[RESULTS]** in source", md_results, 67)
    check("[typical in source", md_typical, 12)
    check("[assumed in source", md_assumed, 7)
    check("[sourced in source", md_sourced, 3)
    check("[derived there in source", md_derivedthere, 3)
    check_ge("\\derivedhere in report", len(re.findall(r"\\derivedhere", tex_nc)),
             md_derived)
    # Of the source's 67 bold [RESULTS] markers one is the specimen in the
    # status block explaining the convention; the report carries the same
    # specimen (as \resultsref{} with an empty date).  Compare real citations.
    check_ge("\\resultsref in report (real citations)",
             len(re.findall(r"\\resultsref\{20", tex_nc)), md_results - 1)
    check_ge("\\typical in report", len(re.findall(r"\\typical\b", tex_nc)),
             md_typical)
    check_ge("[assumed ...] rendered in report",
             len(re.findall(r"\\assumednote\{|\[\\textsc\{assumed\}|\[assumed",
                            tex_nc)), md_assumed)
    check_ge("[sourced ...] rendered in report",
             len(re.findall(r"\\sourcednote\{|\[\\textsc\{sourced\}|\[sourced",
                            tex_nc)), md_sourced)
    check_ge("\\derivedthere in report",
             len(re.findall(r"\\derivedthere", tex_nc)), md_derivedthere)
    # Audit trail: every correction note survives.
    md_flat = " ".join(md.split())
    tex_flat = " ".join(tex_nc.split())
    md_corr = len(re.findall(r"corrected in the 2026-08-18 audit", md_flat))
    tex_corr = len(re.findall(r"corrected in the 2026-08-18 audit", tex_flat))
    check("'corrected in the 2026-08-18 audit' notes in source", md_corr, 29)
    check_ge("... carried in report", tex_corr, md_corr)
    md_earlier = len(re.findall(r"[Aa]n earlier version", md_flat))
    tex_earlier = len(re.findall(r"[Aa]n earlier version", tex_flat))
    check_ge("'an earlier version' notes carried", tex_earlier, md_earlier)

    # ---- 9. load-bearing caveats survive verbatim -------------------------
    print("\n9. Load-bearing caveats (docs/CLAUDE.md Rule 7)")
    caveats = {
        "not-project-spec": "not project spec",
        "results-md-wins": "\\code{RESULTS.md} wins",
        "typical-easiest-false": "the single easiest way to write something false in this subject",
        "bookkeeping-identity": "a bookkeeping identity, not a test",
        "taken-apart": "It burns by being taken apart",
        "mixing-averages-none": "Mixing averages away almost none of a neural network's error",
        "deployment-host-property": "\\emph{deployment-host} property, not a universal one",
        "input-as-output-tolerance": "an input uncertainty used as an output tolerance",
        "term5-term7-term4": "removes term 5 and pushes term 7 below term 4",
        "ratchet-collapse-phase": "the strict ratchet is a collapse-phase statement",
        "positivity-enforced-nowhere": "positivity is enforced nowhere",
        "better-physics-worse-experiment": "better physics and a worse experiment",
        "labels-may-not-contain": "the labels may not contain the cancellation the model is being asked to learn",
        "vacuous-pass": "the pass is vacuous",
        "relaxing-not-relaxed": "\\emph{relaxing}, not \\emph{relaxed}",
        "not-qse-in-stars": "\\emph{not} a demonstration that QSE does not occur in stars",
        "inferential-language-removed": "its inferential language should be removed",
        "detector-never-shown": "has never been shown to detect a mask",
        "outside-the-gate": "outside the gate this project sets itself",
        "neither-redesigned": "neither has been redesigned",
        "magnitude-qualitative": "a magnitude attached to a correct qualitative claim",
        "nse-switching-hosts": "for NSE-switching hosts",
        "not-source-of-truth": "\\textbf{not} their source of truth",
    }
    flat = " ".join(tex_nc.split())
    for name, needle in caveats.items():
        ok = " ".join(needle.split()) in flat
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
        if not ok:
            failures.append(f"caveat missing: {name}")

    # ---- 10. the open register -------------------------------------------
    print("\n10. Open register")
    md_ids = sorted(set(re.findall(r"\bT-(\d\d)\b", md)))
    want_ids = [f"{i:02d}" for i in range(1, 43)]
    md_ids = [i for i in md_ids if i in want_ids]
    check("register ids in source", md_ids, want_ids)

    reg_at = tex_nc.index("\\label{sec:register}")
    reg = tex_nc[reg_at: tex_nc.index("\\label{sec:ranked}", reg_at)]
    in_table = sorted(set(re.findall(r"\\textbf\{T-(\d\d)\}", reg)))
    check("register ids in the register tables", in_table, want_ids)

    in_anchors = sorted(set(re.findall(r"^T-(\d\d)\b", arows_nc, re.M)))
    check("register ids in the Appendix B anchor map", in_anchors, want_ids)

    # Every foreign-tier R-number must go through \foreignreg, never \reg.
    stray = re.findall(r"\\reg\{R-\d\d\}", tex_nc)
    check("Tier-2 R-numbers rendered through \\reg", len(stray), 0)
    n_foreign = len(set(re.findall(r"\\foreignreg\{2\}\{R-(\d\d)\}", tex_nc)))
    check_ge("distinct Tier-2 R-ids carried", n_foreign, 19)
    # The source cites tier1.md SS VIII in two forms: `tier1.md` SS VIII.x
    # (eleven distinct anchors, rendered \tierone) and plain "Tier 1 SS VIII.x"
    # (rendered as plain text, like every other Tier-0/1/2 pointer).
    n_tierone = len(set(re.findall(r"\\tierone\{(VIII[^}]*)\}", tex_nc)))
    check_ge("distinct tier1.md SS VIII anchors carried", n_tierone, 11)

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
