#!/usr/bin/env python
"""Zenodo record 14873443 (Grichener et al. 2025 NNN reproducibility package).

Default (no flags): fetch record METADATA only and write/refresh
``data/MANIFEST.yaml`` with per-file name, size, md5, download URL, and
status. Downloads nothing.

Selective download: ``--file <name>`` streams one named file into
``data/zenodo/`` with md5 verification, then updates its manifest status to
``downloaded``. Files over ``LARGE_BYTES`` (1 GB) are refused without
``--yes-large`` — the main zip is ~49 GB.

Run via:  uv run python scripts/download_zenodo.py [--file README.txt]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
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
        files.append(
            {
                "name": name,
                "size_bytes": f["size"],
                "md5": md5,
                "url": f["links"]["self"],
                "status": prior.get(name, {}).get("status", "not_downloaded"),
            }
        )
    return {
        "zenodo_record": RECORD_ID,
        "record_url": RECORD_URL,
        "title": record["metadata"]["title"],
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_size_bytes": sum(f["size_bytes"] for f in files),
        "note": (
            "data/zenodo/ is READ-ONLY raw ground truth once downloaded. "
            "Statuses: not_downloaded | downloaded. Update only via this script."
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
    md5 = hashlib.md5()
    done = 0
    print(f"downloading {name} ({entry['size_bytes'] / 1e6:.1f} MB) -> {dest}")
    with urllib.request.urlopen(entry["url"], timeout=60) as resp, open(dest, "wb") as out:
        while chunk := resp.read(CHUNK):
            out.write(chunk)
            md5.update(chunk)
            done += len(chunk)
            print(f"\r  {done / max(entry['size_bytes'], 1) * 100:5.1f} %", end="")
    print()
    if md5.hexdigest() != entry["md5"]:
        dest.unlink()
        sys.exit(f"md5 MISMATCH for {name}: got {md5.hexdigest()}, expected {entry['md5']}")
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
