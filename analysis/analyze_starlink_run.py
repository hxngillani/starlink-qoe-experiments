#!/usr/bin/env python3
"""
Analyze one Starlink scenario run directory.

Inputs (in RUN_DIR):
  - meta.txt
  - iperf3_raw.json
  - ping_gw_raw.log

Outputs:
  - gw_ping_samples.csv   (seq,rtt_ms for each gateway ping reply)
  - metrics_run.csv       (one-line CSV with metadata + metrics)
"""

import json
import math
import os
import re
import statistics
import sys
from datetime import datetime


def read_meta(meta_path):
    meta = {}
    if not os.path.isfile(meta_path):
        return meta
    with open(meta_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            meta[k.strip()] = v.strip()
    return meta


def parse_iperf3(json_path, proto):
    """
    Returns a dict with:
      iperf_success (0/1),
      iperf_avg_throughput_Mbps,
      iperf_retrans_total,
      iperf_udp_jitter_ms,
      iperf_udp_loss_pct
    Missing/non-applicable values are None.
    """
    res = {
        "iperf_success": 0,
        "iperf_avg_throughput_Mbps": None,
        "iperf_retrans_total": None,
        "iperf_udp_jitter_ms": None,
        "iperf_udp_loss_pct": None,
    }

    if not os.path.isfile(json_path):
        return res

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except Exception:
        return res

    if "error" in data:
        # iperf3 reported an error
        return res

    end = data.get("end", {})
    res["iperf_success"] = 1

    if proto == "tcp":
        # Typical: end["sum_sent"]["bits_per_second"]
        sum_sent = end.get("sum_sent")
        if sum_sent and "bits_per_second" in sum_sent:
            res["iperf_avg_throughput_Mbps"] = sum_sent["bits_per_second"] / 1e6
            if "retransmits" in sum_sent:
                res["iperf_retrans_total"] = sum_sent["retransmits"]
        else:
            # fallback: maybe "sum_received"
            sum_recv = end.get("sum_received")
            if sum_recv and "bits_per_second" in sum_recv:
                res["iperf_avg_throughput_Mbps"] = sum_recv["bits_per_second"] / 1e6
                if "retransmits" in sum_recv:
                    res["iperf_retrans_total"] = sum_recv["retransmits"]

    else:  # udp
        # Typical: end["sum"]["bits_per_second"], ["jitter_ms"], ["lost_percent"]
        s = end.get("sum")
        if s:
            if "bits_per_second" in s:
                res["iperf_avg_throughput_Mbps"] = s["bits_per_second"] / 1e6
            if "jitter_ms" in s:
                res["iperf_udp_jitter_ms"] = s["jitter_ms"]
            if "lost_percent" in s:
                res["iperf_udp_loss_pct"] = s["lost_percent"]

    return res


def percentile(data, p):
    """
    Compute p-th percentile (0-100) of a list using linear interpolation.
    Returns None if data is empty.
    """
    if not data:
        return None
    if p <= 0:
        return min(data)
    if p >= 100:
        return max(data)
    x = sorted(data)
    k = (len(x) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return x[int(k)]
    d0 = x[f] * (c - k)
    d1 = x[c] * (k - f)
    return d0 + d1


def parse_ping_gateway(ping_path, samples_out_path):
    """
    Parse ping_gw_raw.log and write gw_ping_samples.csv (seq,rtt_ms).
    Returns dict with RTT stats and loss estimate.
    """
    rtts = []
    seqs = []

    if not os.path.isfile(ping_path):
        return {
            "gw_ping_tx": None,
            "gw_ping_rx": None,
            "gw_ping_loss_pct": None,
            "gw_rtt_min_ms": None,
            "gw_rtt_avg_ms": None,
            "gw_rtt_max_ms": None,
            "gw_rtt_p50_ms": None,
            "gw_rtt_p90_ms": None,
            "gw_rtt_p95_ms": None,
            "gw_rtt_p99_ms": None,
            "gw_jitter_mean_abs_dRTT_ms": None,
        }

    line_re = re.compile(r"icmp_seq=(\d+).*time=([\d\.]+)\s*ms")

    with open(ping_path, "r") as f:
        for line in f:
            m = line_re.search(line)
            if not m:
                continue
            seq = int(m.group(1))
            rtt = float(m.group(2))
            seqs.append(seq)
            rtts.append(rtt)

    # Write samples CSV
    if rtts:
        with open(samples_out_path, "w") as out:
            out.write("seq,rtt_ms\n")
            for s, r in zip(seqs, rtts):
                out.write(f"{s},{r:.3f}\n")

    if not rtts:
        return {
            "gw_ping_tx": 0,
            "gw_ping_rx": 0,
            "gw_ping_loss_pct": 100.0,
            "gw_rtt_min_ms": None,
            "gw_rtt_avg_ms": None,
            "gw_rtt_max_ms": None,
            "gw_rtt_p50_ms": None,
            "gw_rtt_p90_ms": None,
            "gw_rtt_p95_ms": None,
            "gw_rtt_p99_ms": None,
            "gw_jitter_mean_abs_dRTT_ms": None,
        }

    # Estimate transmitted pings by max icmp_seq
    tx = max(seqs)
    rx = len(rtts)
    loss_pct = 0.0
    if tx > 0:
        loss_pct = (tx - rx) * 100.0 / tx

    # RTT stats
    rtt_min = min(rtts)
    rtt_max = max(rtts)
    rtt_avg = statistics.mean(rtts)
    p50 = percentile(rtts, 50)
    p90 = percentile(rtts, 90)
    p95 = percentile(rtts, 95)
    p99 = percentile(rtts, 99)

    # Mean abs delta RTT
    if len(rtts) >= 2:
        diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]
        jitter_mean = statistics.mean(diffs)
    else:
        jitter_mean = 0.0

    return {
        "gw_ping_tx": tx,
        "gw_ping_rx": rx,
        "gw_ping_loss_pct": loss_pct,
        "gw_rtt_min_ms": rtt_min,
        "gw_rtt_avg_ms": rtt_avg,
        "gw_rtt_max_ms": rtt_max,
        "gw_rtt_p50_ms": p50,
        "gw_rtt_p90_ms": p90,
        "gw_rtt_p95_ms": p95,
        "gw_rtt_p99_ms": p99,
        "gw_jitter_mean_abs_dRTT_ms": jitter_mean,
    }


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <run_dir>", file=sys.stderr)
        sys.exit(1)

    run_dir = sys.argv[1]
    if not os.path.isdir(run_dir):
        print(f"[!] {run_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    meta = read_meta(os.path.join(run_dir, "meta.txt"))
    proto = meta.get("proto", "tcp")
    tos_str = meta.get("tos", "0")
    try:
        tos_val = int(tos_str)
    except ValueError:
        tos_val = 0
    dscp_val = tos_val >> 2

    # iperf3 metrics
    iperf_path = os.path.join(run_dir, "iperf3_raw.json")
    iperf_res = parse_iperf3(iperf_path, proto)

    # ping gateway metrics
    ping_gw_path = os.path.join(run_dir, "ping_gw_raw.log")
    samples_out = os.path.join(run_dir, "gw_ping_samples.csv")
    gw_res = parse_ping_gateway(ping_gw_path, samples_out)

    # Build metrics row
    now_iso = datetime.utcnow().isoformat()

    fields = {
        "timestamp_utc": now_iso,
        "run_dir": os.path.basename(run_dir),
        "tech": meta.get("tech", ""),
        "plan": meta.get("plan", ""),
        "mode": meta.get("mode", ""),
        "proto": proto,
        "port": meta.get("port", ""),
        "udp_rate": meta.get("udp_rate", ""),
        "direction": meta.get("direction", ""),
        "anchor": meta.get("anchor", ""),
        "gateway": meta.get("gateway", ""),
        "duration_sec": meta.get("duration_sec", ""),
        "run_idx": meta.get("run_idx", ""),
        "tos": tos_val,
        "dscp": dscp_val,
        "iperf_success": iperf_res["iperf_success"],
        "iperf_avg_throughput_Mbps": iperf_res["iperf_avg_throughput_Mbps"],
        "iperf_retrans_total": iperf_res["iperf_retrans_total"],
        "iperf_udp_jitter_ms": iperf_res["iperf_udp_jitter_ms"],
        "iperf_udp_loss_pct": iperf_res["iperf_udp_loss_pct"],
        "gw_ping_tx": gw_res["gw_ping_tx"],
        "gw_ping_rx": gw_res["gw_ping_rx"],
        "gw_ping_loss_pct": gw_res["gw_ping_loss_pct"],
        "gw_rtt_min_ms": gw_res["gw_rtt_min_ms"],
        "gw_rtt_avg_ms": gw_res["gw_rtt_avg_ms"],
        "gw_rtt_max_ms": gw_res["gw_rtt_max_ms"],
        "gw_rtt_p50_ms": gw_res["gw_rtt_p50_ms"],
        "gw_rtt_p90_ms": gw_res["gw_rtt_p90_ms"],
        "gw_rtt_p95_ms": gw_res["gw_rtt_p95_ms"],
        "gw_rtt_p99_ms": gw_res["gw_rtt_p99_ms"],
        "gw_jitter_mean_abs_dRTT_ms": gw_res["gw_jitter_mean_abs_dRTT_ms"],
    }

    # Write metrics_run.csv (overwrite each time)
    out_path = os.path.join(run_dir, "metrics_run.csv")
    headers = list(fields.keys())
    with open(out_path, "w") as f:
        f.write(",".join(headers) + "\n")
        row = []
        for h in headers:
            v = fields[h]
            row.append("" if v is None else str(v))
        f.write(",".join(row) + "\n")

    print(f"[*] Wrote metrics_run.csv in {run_dir}")


if __name__ == "__main__":
    main()
