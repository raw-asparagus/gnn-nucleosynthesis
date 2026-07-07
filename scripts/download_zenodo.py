#!/usr/bin/env python
"""Zenodo record 14873443 (Grichener et al. 2025 NNN reproducibility package).

Default (no flags): fetch record METADATA only and write/refresh
``data/MANIFEST.yaml`` with per-file name, size, md5, download URL, and
status. Downloads nothing.

Selective download: ``--file <name>`` streams one named file into
``data/zenodo/`` with md5 verification, then updates its manifest status to
``downloaded``. Files over ``LARGE_BYTES`` (1 GB) are refused without
``--yes-large`` — the main zip is ~49 GB.

Downloads are resumable: data streams into ``<name>.part`` and interrupted
transfers continue from the current offset via an HTTP Range request (with
retry/backoff around transient network errors). md5 is verified in a separate
full-file pass once the transfer completes, then ``.part`` is renamed into
place. Re-running with the same ``--file`` resumes or, if the file is already
present and verified, is a no-op.

Run via:  uv run python scripts/download_zenodo.py [--file README.txt]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

RECORD_ID = 14873443
API_URL = f"https://zenodo.org/api/records/{RECORD_ID}"
RECORD_URL = f"https://zenodo.org/records/{RECORD_ID}"
REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "MANIFEST.yaml"
DOWNLOAD_DIR = REPO_ROOT / "data" / "zenodo"
LARGE_BYTES = 1_000_000_000
CHUNK = 1 << 20
MAX_RETRIES = 30
PROGRESS_EVERY = 512 << 20  # one progress line per 512 MiB


def fetch_record() -> dict:
    """Fetch record metadata from the Zenodo API (metadata only, ~kB)."""
    with urllib.request.urlopen(API_URL, timeout=60) as resp:
        return json.load(resp)


def build_manifest(record: dict, existing: dict | None = None) -> dict:
    """Build the manifest dict, preserving statuses from an existing manifest."""
    prior = {f["name"]: f for f in (existing or {}).get("files", [])}
    files = []
    for f in record.get("files", []):
        name = f["key"]
        md5 = f["checksum"].removeprefix("md5:")
        # Start from the prior entry so extra keys (e.g. zip_deleted,
        # extracted_utc) survive a manifest rebuild.
        entry = dict(prior.get(name, {}))
        entry.update(
            {
                "name": name,
                "size_bytes": f["size"],
                "md5": md5,
                "url": f["links"]["self"],
                "status": entry.get("status", "not_downloaded"),
            }
        )
        files.append(entry)
    return {
        "zenodo_record": RECORD_ID,
        "record_url": RECORD_URL,
        "title": record["metadata"]["title"],
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_size_bytes": sum(f["size_bytes"] for f in files),
        "note": (
            "data/zenodo/ is READ-ONLY raw ground truth once downloaded. "
            "Statuses: not_downloaded | downloaded | extracted. "
            "Update only via this script."
        ),
        "files": files,
    }


def load_manifest() -> dict | None:
    if MANIFEST_PATH.exists():
        return yaml.safe_load(MANIFEST_PATH.read_text())
    return None


def write_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(yaml.safe_dump(manifest, sort_keys=False, width=100))
    print(f"wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")


def file_md5(path: Path) -> str:
    """md5 of a file in a streaming full-file pass (resume-safe, unlike
    hashing chunks during a transfer that may restart mid-way)."""
    md5 = hashlib.md5()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            md5.update(chunk)
    return md5.hexdigest()


def _stream_from(url: str, part: Path, total: int) -> None:
    """Append the remainder of ``url`` to ``part``, resuming at its size.

    Sends ``Range: bytes=<offset>-``; a server that ignores it (HTTP 200
    instead of 206) forces a restart from byte 0.
    """
    offset = part.stat().st_size if part.exists() else 0
    if offset >= total:
        return
    headers = {"Range": f"bytes={offset}-"} if offset else {}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        if offset and resp.status == 200:
            print("  server ignored Range request; restarting from byte 0")
            offset = 0
            mode = "wb"
        else:
            mode = "ab"
        done = offset
        next_mark = (done // PROGRESS_EVERY + 1) * PROGRESS_EVERY
        with open(part, mode) as out:
            while chunk := resp.read(CHUNK):
                out.write(chunk)
                done += len(chunk)
                if done >= next_mark or done >= total:
                    pct = done / max(total, 1) * 100
                    print(f"  {pct:5.1f} %  ({done / 1e9:.2f} GB)", flush=True)
                    next_mark = (done // PROGRESS_EVERY + 1) * PROGRESS_EVERY


def download_file(manifest: dict, name: str, yes_large: bool) -> None:
    entry = next((f for f in manifest["files"] if f["name"] == name), None)
    if entry is None:
        known = ", ".join(f["name"] for f in manifest["files"])
        sys.exit(f"unknown file {name!r}; record has: {known}")
    if entry["size_bytes"] > LARGE_BYTES and not yes_large:
        sys.exit(
            f"{name} is {entry['size_bytes'] / 1e9:.2f} GB; re-run with --yes-large "
            "if you really mean it (check disk first)."
        )
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = DOWNLOAD_DIR / name
    part = DOWNLOAD_DIR / (name + ".part")
    total = entry["size_bytes"]

    if dest.exists():
        if dest.stat().st_size == total and file_md5(dest) == entry["md5"]:
            if entry["status"] == "not_downloaded":
                entry["status"] = "downloaded"
            print(f"{name} already present, md5 OK ({entry['md5']})")
            return
        print(f"{name} present but wrong size/md5; re-downloading")
        dest.unlink()

    print(f"downloading {name} ({total / 1e9:.2f} GB) -> {dest}")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _stream_from(entry["url"], part, total)
            break
        except OSError as exc:
            have = part.stat().st_size if part.exists() else 0
            wait = min(60, 2**attempt)
            print(
                f"  transfer error at {have / 1e9:.2f} GB (attempt {attempt}/{MAX_RETRIES}): "
                f"{exc}; retrying in {wait}s",
                flush=True,
            )
            time.sleep(wait)
    else:
        sys.exit(f"gave up after {MAX_RETRIES} attempts; partial file kept at {part}")

    have = part.stat().st_size
    if have != total:
        sys.exit(f"size mismatch after transfer: {have} != {total}; partial file kept at {part}")
    print("verifying md5 (full-file pass)...", flush=True)
    got = file_md5(part)
    if got != entry["md5"]:
        part.unlink()
        sys.exit(f"md5 MISMATCH for {name}: got {got}, expected {entry['md5']}")
    part.rename(dest)
    entry["status"] = "downloaded"
    print(f"md5 OK ({entry['md5']})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="download this single file from the record")
    ap.add_argument(
        "--yes-large",
        action="store_true",
        help=f"allow downloads over {LARGE_BYTES / 1e9:.0f} GB (the main zip is ~49 GB)",
    )
    args = ap.parse_args()

    try:
        record = fetch_record()
    except OSError as exc:
        print(f"Zenodo API unreachable ({exc}); manual URL: {RECORD_URL}", file=sys.stderr)
        if MANIFEST_PATH.exists():
            print("keeping existing MANIFEST.yaml", file=sys.stderr)
            return 1
        raise SystemExit(1) from exc

    manifest = build_manifest(record, load_manifest())
    if args.file:
        download_file(manifest, args.file, args.yes_large)
    write_manifest(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
