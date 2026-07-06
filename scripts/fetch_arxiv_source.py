#!/usr/bin/env python3
"""Fetch arXiv e-print (LaTeX) source into the local literature cache.

Why: agents read TeX source directly (Read/Grep) instead of parsing PDFs —
exact equations, exact thresholds, and the .bbl/.bib reference lists come for
free. PDFs are the fallback only when a paper was submitted PDF-only.

Usage:
    uv run python scripts/fetch_arxiv_source.py 2606.04491
    uv run python scripts/fetch_arxiv_source.py 2503.00115 2508.16114 --meta

Output layout (data/literature/ is gitignored cache):
    data/literature/<id>/src/          extracted .tex/.bbl/.bib/figures
    data/literature/<id>/MANIFEST.md   what was fetched, when, format, file list
    data/literature/<id>/meta.xml      arXiv API metadata (with --meta)

Behaviour notes:
- Uses export.arxiv.org (the mirror arXiv designates for programmatic access)
  with a descriptive User-Agent, and sleeps 3 s between requests — be polite;
  arXiv rate-limits and blocks abusive clients.
- The e-print endpoint may return: a gzipped tar (usual), a single gzipped .tex,
  or a raw PDF (PDF-only submissions). All three are detected by magic bytes.
- stdlib only (urllib/tarfile/gzip): no extra dependencies.
- Extraction is hardened against path traversal (members escaping the target dir
  are rejected).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import io
import re
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

BASE = "https://export.arxiv.org"
UA = "gnn-nucleosynthesis literature cache (contact: repo owner; polite client, 1 req/3s)"
CACHE = Path("data/literature")
SLEEP_S = 3.0

ARXIV_ID = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?$|^([a-z-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$")


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _safe_extract_tar(data: bytes, dest: Path) -> list[str]:
    names: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        for m in tf.getmembers():
            target = (dest / m.name).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise RuntimeError(f"path traversal in tar member: {m.name}")
        tf.extractall(dest)  # noqa: S202 — members validated above
        names = tf.getnames()
    return names


def fetch_source(arxiv_id: str, meta: bool = False) -> Path:
    if not ARXIV_ID.match(arxiv_id):
        raise SystemExit(f"'{arxiv_id}' does not look like an arXiv id")

    out = CACHE / arxiv_id
    src = out / "src"
    if src.exists() and any(src.iterdir()):
        print(f"[skip] {arxiv_id}: already cached at {src}")
        return out
    src.mkdir(parents=True, exist_ok=True)

    print(f"[get ] {BASE}/e-print/{arxiv_id}")
    blob = _get(f"{BASE}/e-print/{arxiv_id}")

    fmt: str
    files: list[str]
    if blob[:4] == b"%PDF":
        fmt = "pdf-only"
        (src / f"{arxiv_id}.pdf").write_bytes(blob)
        files = [f"{arxiv_id}.pdf"]
        print(f"[warn] {arxiv_id} is a PDF-only submission — no TeX source exists; "
              "prefer the arxiv.org/html/ rendering for reading.", file=sys.stderr)
    elif blob[:2] == b"\x1f\x8b":  # gzip
        inner = gzip.decompress(blob)
        if inner[:5] == b"%PDF-":
            fmt = "pdf-only(gz)"
            (src / f"{arxiv_id}.pdf").write_bytes(inner)
            files = [f"{arxiv_id}.pdf"]
        else:
            try:
                files = _safe_extract_tar(blob, src)
                fmt = "tar.gz"
            except tarfile.ReadError:
                fmt = "single-tex(gz)"
                (src / f"{arxiv_id}.tex").write_bytes(inner)
                files = [f"{arxiv_id}.tex"]
    else:
        # Rare: uncompressed tar
        files = _safe_extract_tar(blob, src)
        fmt = "tar"

    if meta:
        time.sleep(SLEEP_S)
        print(f"[get ] metadata for {arxiv_id}")
        xml = _get(f"{BASE}/api/query?id_list={arxiv_id}")
        (out / "meta.xml").write_bytes(xml)

    tex = sorted(f for f in files if f.endswith(".tex"))
    bib = sorted(f for f in files if f.endswith((".bbl", ".bib")))
    manifest = out / "MANIFEST.md"
    manifest.write_text(
        f"# {arxiv_id}\n\n"
        f"- fetched: {_dt.date.today().isoformat()} from {BASE}/e-print/{arxiv_id}\n"
        f"- format: {fmt}\n"
        f"- tex files: {', '.join(tex) or '(none)'}\n"
        f"- references: {', '.join(bib) or '(none)'}\n"
        f"- all files ({len(files)}): {', '.join(sorted(files))}\n\n"
        "Cache only — cite the paper, never this snapshot. Do not commit.\n"
    )
    print(f"[ok  ] {arxiv_id}: {fmt}; {len(tex)} tex, {len(bib)} ref files -> {src}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="+", help="arXiv ids, e.g. 2606.04491")
    ap.add_argument("--meta", action="store_true",
                    help="also fetch arXiv API metadata (title/authors/dates)")
    args = ap.parse_args()

    for i, aid in enumerate(args.ids):
        if i:
            time.sleep(SLEEP_S)
        try:
            fetch_source(aid, meta=args.meta)
        except Exception as exc:  # keep batch going; report at end
            print(f"[FAIL] {aid}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
