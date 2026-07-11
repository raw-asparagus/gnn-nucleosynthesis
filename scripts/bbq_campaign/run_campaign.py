#!/usr/bin/env python
"""Execute the Step-6 bbq rerun campaign: resumable priority-ordered queue.

Reads data/bbq_reruns/<net>/campaign.yaml (made by make_campaign.py), runs
every run directory lacking a DONE sentinel through run_one.sh, --workers at
a time, lowest priority number first. A run is complete iff bbq exits 0 AND
output.txt has n_times+1 rows (bbq aborts a hydrostatic run mid-way when a
step hits max_steps — the row count catches truncation). Wall time per run
is appended to runtimes.csv and written into DONE.

Usage:
  uv run python scripts/bbq_campaign/run_campaign.py --net both --pilot
  uv run python scripts/bbq_campaign/run_campaign.py --net both --workers 10
"""

from __future__ import annotations

import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def output_rows(path: Path) -> int:
    if not path.exists():
        return -1
    with open(path, "rb") as fh:
        return sum(1 for _ in fh) - 1  # minus header


def run_one(net_dir: Path, spec: dict, timeout: float) -> dict:
    rd = net_dir / spec["run_key"]
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            ["bash", str(HERE / "run_one.sh"), str(rd)], timeout=timeout
        )
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = -9
    wall = time.perf_counter() - t0
    rows = output_rows(rd / "output.txt")
    ok = rc == 0 and rows == spec["n_times"] + 1
    if ok:
        (rd / "DONE").write_text(f"wall_seconds: {wall:.1f}\nrows: {rows}\n")
    with open(net_dir / "runtimes.csv", "a") as fh:
        fh.write(f"{spec['run_key']},{wall:.1f},{rc},{rows},{int(ok)}\n")
    return dict(run_key=spec["run_key"], ok=ok, rc=rc, rows=rows, wall=wall)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", default="both", choices=["mesa_80", "mesa_151", "both"])
    ap.add_argument("--root", default=str(REPO / "data" / "bbq_reruns"))
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--pilot", action="store_true", help="pilot-flagged runs only")
    ap.add_argument("--run-timeout", type=float, default=14400.0,
                    help="per-run wall-time cap in seconds")
    args = ap.parse_args()

    nets = ["mesa_80", "mesa_151"] if args.net == "both" else [args.net]
    queue: list[tuple[int, Path, dict]] = []
    for net in nets:
        net_dir = Path(args.root) / net
        manifest = yaml.safe_load((net_dir / "campaign.yaml").read_text())
        for spec in manifest["runs"]:
            if args.pilot and not spec.get("pilot"):
                continue
            if (net_dir / spec["run_key"] / "DONE").exists():
                continue
            queue.append((spec["priority"], net_dir, spec))
    queue.sort(key=lambda q: (q[0], q[2]["run_key"]))
    print(f"{len(queue)} runs pending, {args.workers} workers", flush=True)
    if not queue:
        return

    t0 = time.perf_counter()
    n_ok = n_fail = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [
            ex.submit(run_one, net_dir, spec, args.run_timeout)
            for _, net_dir, spec in queue
        ]
        for fut in as_completed(futs):
            r = fut.result()
            n_ok += r["ok"]
            n_fail += not r["ok"]
            status = "OK" if r["ok"] else f"FAIL(rc={r['rc']}, rows={r['rows']})"
            print(
                f"  [{n_ok + n_fail:>4}/{len(queue)}] {r['run_key']:<40} "
                f"{status} {r['wall']:.1f}s",
                flush=True,
            )
    print(
        f"campaign pass done: {n_ok} ok, {n_fail} failed, "
        f"{time.perf_counter() - t0:.0f}s wall"
    )


if __name__ == "__main__":
    main()
