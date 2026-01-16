#!/usr/bin/env python3
"""
Analyze one gateway baseline run directory.

Inputs (in RESULTS_DIR):
  - ping_gateway_raw.log        # raw ping output
  - gateway_ping_samples.csv    # timestamp_epoch, seq, rtt_ms (optional)

Outputs:
  - metrics_gateway.csv         # one-line CSV with summary stats
  - run_status.txt              # OK / DEGRADED / FAIL

Used later in the Jupyter / offline analysis.
"""

import csv
import math
import re
import sys
from pathlib import Path


def parse_ping_summary(raw_log: Path):
    """
    Parse ping_gateway_raw.log to extract:
      - packets transmitted/received
      - loss percentage
      - rtt min/avg/max/mdev

    Returns a dict or None if not found.
    """
    if not raw_log.exists():
        return None

    stats = {
        "tx": None,
        "rx": None,
        "loss_percent": None,
        "rtt_min_ms": None,
        "rtt_avg_ms": None,
        "rtt_max_ms": None,
        "rtt_std_ms": None,
    }

    txrx_re = re.compile(
        r"(\d+)\s+packets transmitted,\s+(\d+)\s+received.*?(\d+(?:\.\d+)?)% packet loss"
    )
    rtt_re = re.compile(
        r"rtt min/avg/max/mdev = ([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+) ms"
    )

    with raw_log.open() as f:
        for line in f:
            m1 = txrx_re.search(line)
            if m1:
                stats["tx"] = int(m1.group(1))
                stats["rx"] = int(m1.group(2))
                stats["loss_percent"] = float(m1.group(3))
            m2 = rtt_re.search(line)
            if m2:
                stats["rtt_min_ms"] = float(m2.group(1))
                stats["rtt_avg_ms"] = float(m2.group(2))
                stats["rtt_max_ms"] = float(m2.group(3))
                stats["rtt_std_ms"] = float(m2.group(4))

    if stats["tx"] is None or stats["rx"] is None:
        return None
    return stats


def percentile(xs, p):
    if not xs:
        return None
    xs_sorted = sorted(xs)
    k = (len(xs_sorted) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs_sorted[int(k)]
    d0 = xs_sorted[f] * (c - k)
    d1 = xs_sorted[c] * (k - f)
    return d0 + d1


def parse_samples(samples_csv: Path):
    """
    Parse gateway_ping_samples.csv to get all RTT samples and timestamps.
    """
    rtts = []
    timestamps = []

    if not samples_csv.exists():
        return rtts, timestamps

    with samples_csv.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rtt = float(row["rtt_ms"])
                ts = float(row["timestamp_epoch"])
            except (ValueError, KeyError):
                continue
            rtts.append(rtt)
            timestamps.append(ts)

    return rtts, timestamps


def main():
    if len(sys.argv) != 5:
        print(
            f"Usage: {sys.argv[0]} <results_dir> <gateway_ip> <nut_label> <location_label>",
            file=sys.stderr,
        )
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    gateway_ip = sys.argv[2]
    nut_label = sys.argv[3]
    location_label = sys.argv[4]

    raw_log = results_dir / "ping_gateway_raw.log"
    samples_csv = results_dir / "gateway_ping_samples.csv"

    ping_stats = parse_ping_summary(raw_log)
    rtts, timestamps = parse_samples(samples_csv)

    # Derived stats from per-sample RTTs
    if rtts:
        p50 = percentile(rtts, 50)
        p90 = percentile(rtts, 90)
        p95 = percentile(rtts, 95)
        p99 = percentile(rtts, 99)
    else:
        p50 = p90 = p95 = p99 = None

    if rtts and len(rtts) > 1:
        diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]
        jitter_mean_abs = sum(diffs) / len(diffs)
    else:
        jitter_mean_abs = None

    if timestamps:
        duration_s = timestamps[-1] - timestamps[0]
        start_ts = timestamps[0]
        end_ts = timestamps[-1]
    else:
        duration_s = None
        start_ts = None
        end_ts = None

    # Decide run status based on network health
    if ping_stats is None:
        status = "FAIL"
    else:
        tx = ping_stats["tx"]
        rx = ping_stats["rx"]
        loss = ping_stats["loss_percent"]

        if rx == 0:
            # No replies at all -> effectively an outage
            status = "FAIL"
        elif loss is not None and loss > 20.0:
            # Link is up but heavily degraded
            status = "DEGRADED"
        else:
            status = "OK"

    print(f"# Gateway Baseline Summary: {results_dir.name}\n")
    print(f"Gateway IP    : {gateway_ip}")
    print(f"NUT           : {nut_label}")
    print(f"Location      : {location_label}")

    if ping_stats:
        print(
            f"Packets       : tx={ping_stats['tx']} rx={ping_stats['rx']} "
            f"loss={ping_stats['loss_percent']:.2f}%"
        )
        print(
            "RTT ping line : "
            f"min={ping_stats['rtt_min_ms']:.2f} ms, "
            f"avg={ping_stats['rtt_avg_ms']:.2f} ms, "
            f"max={ping_stats['rtt_max_ms']:.2f} ms, "
            f"mdev≈jitter={ping_stats['rtt_std_ms']:.2f} ms"
        )
    else:
        print("Ping summary  : (not available)")

    print()
    if rtts:
        print(f"Samples       : {len(rtts)}")
        print("RTT percentiles (from samples):")
        print(
            f"  p50={p50:.2f} ms, p90={p90:.2f} ms, "
            f"p95={p95:.2f} ms, p99={p99:.2f} ms"
        )
        if jitter_mean_abs is not None:
            print(f"Mean abs ΔRTT : {jitter_mean_abs:.2f} ms (jitter over time)")
        if duration_s is not None:
            print(f"Duration      : {duration_s:.1f} s")
    else:
        print("No RTT samples parsed from gateway_ping_samples.csv")

    print(f"\nRun status    : {status}")

    # Write single-row metrics CSV for Jupyter later
    metrics_path = results_dir / "metrics_gateway.csv"
    with metrics_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "gateway_ip",
                "nut_label",
                "location_label",
                "start_ts",
                "end_ts",
                "duration_s",
                "tx",
                "rx",
                "loss_percent",
                "rtt_min_ms",
                "rtt_avg_ms",
                "rtt_max_ms",
                "rtt_std_ms",
                "rtt_p50_ms",
                "rtt_p90_ms",
                "rtt_p95_ms",
                "rtt_p99_ms",
                "jitter_mean_abs_ms",
                "run_status",
            ]
        )
        writer.writerow(
            [
                gateway_ip,
                nut_label,
                location_label,
                start_ts,
                end_ts,
                duration_s,
                ping_stats["tx"] if ping_stats else None,
                ping_stats["rx"] if ping_stats else None,
                ping_stats["loss_percent"] if ping_stats else None,
                ping_stats["rtt_min_ms"] if ping_stats else None,
                ping_stats["rtt_avg_ms"] if ping_stats else None,
                ping_stats["rtt_max_ms"] if ping_stats else None,
                ping_stats["rtt_std_ms"] if ping_stats else None,
                p50,
                p90,
                p95,
                p99,
                jitter_mean_abs,
                status,
            ]
        )

    # Also write a simple run_status.txt for schedulers
    status_path = results_dir / "run_status.txt"
    with status_path.open("w") as f:
        f.write(status + "\n")


if __name__ == "__main__":
    main()
