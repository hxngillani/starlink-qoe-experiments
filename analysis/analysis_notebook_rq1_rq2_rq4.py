#!/usr/bin/env python3
"""
Offline analysis for:
- RQ1: Baseline capacity (TCP/UDP)
- RQ2: DSCP / QoS impact
- RQ4: Gateway RTT / latency behavior

Assumptions:
- Summary file: ~/analysis/all_starlink_runs.csv
- It contains at least: tech, plan, mode, proto, port, udp_rate, dscp, direction
- It *may* contain throughput / loss columns; we autodetect them.
- It already contains gw_rtt_* columns from previous processing.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ----------------------------------------------------------------------
# Paths & basic load
# ----------------------------------------------------------------------

BASE_DIR = Path.home() / "analysis"
SUMMARY_CSV = BASE_DIR / "all_starlink_runs.csv"
FIG_DIR = BASE_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

print(f"[*] Loading summary from: {SUMMARY_CSV}")
df = pd.read_csv(SUMMARY_CSV)

print(f"[+] Loaded {len(df)} runs")
print("\n[+] First 5 rows:")
print(df.head())
print("\n[+] Columns:")
print(df.columns.tolist())


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def pick_column(df: pd.DataFrame, candidates, what: str):
    """
    Try multiple possible column names and return the first that exists.
    """
    for c in candidates:
        if c in df.columns:
            print(f"[+] Using '{c}' as {what}")
            return c
    print(f"[!] No column found for {what}. Tried: {candidates}")
    return None


def save_fig(fig, name: str):
    out = FIG_DIR / name
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[+] Saved figure: {out}")


# ----------------------------------------------------------------------
# Quick high-level distributions (sanity)
# ----------------------------------------------------------------------

print("\n=== HIGH-LEVEL DISTRIBUTIONS ===")

for col in ["tech", "plan", "mode", "proto", "port", "udp_rate", "dscp", "direction"]:
    if col in df.columns:
        print(f"\n[+] Distribution of {col}:")
        print(df[col].value_counts(dropna=False))
    else:
        print(f"[!] Column '{col}' not found")


# ----------------------------------------------------------------------
# RQ1: Baseline capacity (TCP and UDP)
# ----------------------------------------------------------------------

print("\n=== RQ1: Baseline capacity (TCP/UDP) ===")

# ---- TCP throughput by port / mode -----------------------------------
if "proto" in df.columns:
    tcp = df[df["proto"] == "tcp"].copy()
else:
    tcp = pd.DataFrame()

tcp_thr_col = pick_column(
    tcp,
    candidates=[
        "iperf_avg_throughput_Mbps",  # our metrics_run column
        "tcp_sender_Mbps",
        "sender_Mbps",
        "throughput_Mbps",
        "bw_Mbps",
        "avg_Mbps",
        "goodput_Mbps",
    ],
    what="TCP throughput (Mbps)",
)

if not tcp.empty and tcp_thr_col is not None and "port" in tcp.columns:
    # Boxplot: TCP throughput by port
    fig, ax = plt.subplots(figsize=(6, 4))
    tcp.boxplot(column=tcp_thr_col, by="port", ax=ax)
    ax.set_title("TCP throughput by port")
    ax.set_xlabel("Port")
    ax.set_ylabel("Throughput (Mbps)")
    plt.suptitle("")
    save_fig(fig, "rq1_tcp_throughput_by_port_box.png")

    # Optional: split by mode if available
    if "mode" in tcp.columns:
        fig, ax = plt.subplots(figsize=(7, 4))
        for mode, sub in tcp.groupby("mode"):
            ax.scatter(
                sub["port"],
                sub[tcp_thr_col],
                label=str(mode),
                alpha=0.6,
            )
        ax.set_title("TCP throughput by port and mode")
        ax.set_xlabel("Port")
        ax.set_ylabel("Throughput (Mbps)")
        ax.legend()
        save_fig(fig, "rq1_tcp_throughput_by_port_mode_scatter.png")
else:
    print("[!] Skipping TCP RQ1 plots (missing proto/port/throughput column).")

# ---- UDP loss vs rate ------------------------------------------------
if "proto" in df.columns:
    udp = df[df["proto"] == "udp"].copy()
else:
    udp = pd.DataFrame()

udp_loss_col = pick_column(
    udp,
    candidates=[
        "iperf_udp_loss_pct",  # our metrics_run field
        "udp_loss_percent",
        "loss_percent",
        "udp_loss",
        "loss",
    ],
    what="UDP loss (%)",
)

if not udp.empty and udp_loss_col is not None and "udp_rate" in udp.columns:
    # Try to normalize udp_rate to numeric (1M,5M,10M -> 1,5,10)
    rate_map = {"1M": 1, "5M": 5, "10M": 10}
    udp["udp_rate_Mbps"] = udp["udp_rate"].map(rate_map)

    fig, ax = plt.subplots(figsize=(6, 4))
    for rate, sub in udp.groupby("udp_rate"):
        ax.scatter(
            [str(rate)] * len(sub),
            sub[udp_loss_col],
            alpha=0.6,
            label=str(rate),
        )
    ax.set_title("UDP loss vs sending rate")
    ax.set_xlabel("UDP rate label")
    ax.set_ylabel("Loss (%)")
    save_fig(fig, "rq1_udp_loss_vs_rate_scatter.png")
else:
    print("[!] Skipping UDP RQ1 plots (missing proto/udp_rate/loss column).")


# ----------------------------------------------------------------------
# RQ2: DSCP / QoS impact (mainly TCP 443)
# ----------------------------------------------------------------------

print("\n=== RQ2: DSCP / QoS impact ===")

if (
    "proto" in df.columns
    and "port" in df.columns
    and "dscp" in df.columns
    and tcp_thr_col is not None
):
    tcp443 = df[(df["proto"] == "tcp") & (df["port"] == 443)].copy()
    if not tcp443.empty:
        # Boxplot throughput by DSCP
        fig, ax = plt.subplots(figsize=(6, 4))
        tcp443.boxplot(column=tcp_thr_col, by="dscp", ax=ax)
        ax.set_title("TCP 443 throughput by DSCP")
        ax.set_xlabel("DSCP")
        ax.set_ylabel("Throughput (Mbps)")
        plt.suptitle("")
        save_fig(fig, "rq2_tcp443_throughput_by_dscp_box.png")

        # If modes exist, do a scatter / swarm-style plot
        if "mode" in tcp443.columns:
            fig, ax = plt.subplots(figsize=(7, 4))
            for (mode, dscp), sub in tcp443.groupby(["mode", "dscp"]):
                x = f"{mode}_dscp{dscp}"
                ax.scatter(
                    [x] * len(sub),
                    sub[tcp_thr_col],
                    alpha=0.6,
                    label=None,
                )
            ax.set_title("TCP 443 throughput by DSCP and mode")
            ax.set_xlabel("Mode + DSCP")
            ax.set_ylabel("Throughput (Mbps)")
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            save_fig(fig, "rq2_tcp443_throughput_mode_dscp_scatter.png")
    else:
        print("[!] No TCP 443 rows found; skipping RQ2.")
else:
    print("[!] Missing proto/port/dscp or TCP throughput column; skipping RQ2.")


# ----------------------------------------------------------------------
# RQ4: Gateway RTT / latency behavior
# ----------------------------------------------------------------------

print("\n=== RQ4: Gateway RTT / latency behavior ===")

gw_rtt_col = pick_column(
    df,
    candidates=[
        "gw_rtt_p95_ms",
        "gw_rtt_p90_ms",
        "gw_rtt_p99_ms",
        "gw_rtt_p50_ms",
        "gw_rtt_avg_ms",
    ],
    what="gateway RTT representative (ms)",
)

if gw_rtt_col is not None:
    # RTT by mode
    if "mode" in df.columns:
        fig, ax = plt.subplots(figsize=(6, 4))
        df.boxplot(column=gw_rtt_col, by="mode", ax=ax)
        ax.set_title(f"Gateway {gw_rtt_col} by mode")
        ax.set_xlabel("Mode")
        ax.set_ylabel("RTT (ms)")
        plt.suptitle("")
        save_fig(fig, "rq4_gw_rtt_by_mode_box.png")

    # RTT by port
    if "port" in df.columns:
        fig, ax = plt.subplots(figsize=(6, 4))
        df.boxplot(column=gw_rtt_col, by="port", ax=ax)
        ax.set_title(f"Gateway {gw_rtt_col} by port")
        ax.set_xlabel("Port")
        ax.set_ylabel("RTT (ms)")
        plt.suptitle("")
        save_fig(fig, "rq4_gw_rtt_by_port_box.png")

    # Optional: relationship between RTT and throughput if we found TCP thr
    if tcp_thr_col is not None:
        tcp_for_rtt = df[df["proto"] == "tcp"].dropna(
            subset=[gw_rtt_col, tcp_thr_col]
        )
        if not tcp_for_rtt.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(tcp_for_rtt[gw_rtt_col], tcp_for_rtt[tcp_thr_col], alpha=0.6)
            ax.set_title("TCP throughput vs gateway RTT")
            ax.set_xlabel(f"Gateway {gw_rtt_col} (ms)")
            ax.set_ylabel("Throughput (Mbps)")
            save_fig(fig, "rq4_tcp_throughput_vs_gw_rtt_scatter.png")
else:
    print("[!] No gw_rtt_* columns found; skipping RQ4.")

print("\n[*] Analysis complete. Figures are under:", FIG_DIR)
