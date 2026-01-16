#!/usr/bin/env python3
import csv
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path.home() / "analysis"
RESULTS_DIR = BASE_DIR / "results_starlink"
OUT_ALL = BASE_DIR / "all_starlink_runs.csv"


def load_all_runs():
    rows = []
    header = None

    if not RESULTS_DIR.exists():
        print(f"[!] Results dir not found: {RESULTS_DIR}")
        return header, rows

    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        metrics_file = run_dir / "metrics_run.csv"
        if not metrics_file.exists():
            continue

        with metrics_file.open("r", newline="") as f:
            reader = csv.reader(f)
            this_header = next(reader, None)
            this_row = next(reader, None)

        if this_header is None or this_row is None:
            continue

        if header is None:
            header = this_header
        else:
            # basic sanity: same header?
            if this_header != header:
                print(f"[!] Header mismatch in {metrics_file}, skipping")
                continue

        rows.append(this_row)

    return header, rows


def write_all_csv(header, rows):
    if header is None:
        print("[!] No runs found, nothing to write.")
        return

    with OUT_ALL.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"[*] Wrote {len(rows)} rows to {OUT_ALL}")


def float_or_none(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def summarize_by_key(header, rows):
    # Map header -> index
    idx = {name: i for i, name in enumerate(header)}

    # Group by (proto, port, tos, mode)
    groups = defaultdict(list)
    for r in rows:
        proto = r[idx["proto"]]
        port = r[idx["port"]]
        tos = r[idx["tos"]]
        mode = r[idx["mode"]]
        key = (proto, port, tos, mode)
        groups[key].append(r)

    print("\n=== Aggregate summary by (proto, port, tos, mode) ===")
    print(
        "proto,port,tos,mode,count,avg_thr_Mbps,std_thr_Mbps,"
        "avg_gw_rtt_ms,std_gw_rtt_ms"
    )

    for key, rs in sorted(groups.items()):
        thr_vals = []
        rtt_vals = []
        for r in rs:
            thr = float_or_none(r[idx["iperf_avg_throughput_Mbps"]])
            rtt = float_or_none(r[idx["gw_rtt_avg_ms"]])
            if thr is not None:
                thr_vals.append(thr)
            if rtt is not None:
                rtt_vals.append(rtt)

        def mean(vals):
            return sum(vals) / len(vals) if vals else None

        def std(vals):
            if len(vals) < 2:
                return 0.0
            m = mean(vals)
            return (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5

        m_thr = mean(thr_vals)
        s_thr = std(thr_vals)
        m_rtt = mean(rtt_vals)
        s_rtt = std(rtt_vals)

        print(
            "{},{},{},{},{},{:.3f},{:.3f},{:.3f},{:.3f}".format(
                key[0],
                key[1],
                key[2],
                key[3],
                len(rs),
                m_thr if m_thr is not None else 0.0,
                s_thr if s_thr is not None else 0.0,
                m_rtt if m_rtt is not None else 0.0,
                s_rtt if s_rtt is not None else 0.0,
            )
        )


if __name__ == "__main__":
    print(f"[*] Aggregating results under: {RESULTS_DIR}")
    header, rows = load_all_runs()
    write_all_csv(header, rows)
    summarize_by_key(header, rows)

    now = datetime.now(timezone.utc).isoformat()
    print(f"[*] Summary done at {now}")
