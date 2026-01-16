#!/usr/bin/env python3
"""
RQ3 HTTP QoE analysis.

Expected inputs (produced by run_starlink_*_qoe.sh):
  - ~/analysis/results_apps_web/*/web_timing.csv
  - ~/analysis/results_apps_video/*/video_timing.csv
  - ~/analysis/results_apps_audio/*/audio_timing.csv

Outputs:
  - ~/analysis/rq3_all_qoe.csv
  - ~/analysis/rq3_plots/*.png
"""

import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.expanduser("~/analysis")
RESULT_DIRS = {
    "web": os.path.join(BASE_DIR, "results_apps_web"),
    "video": os.path.join(BASE_DIR, "results_apps_video"),
    "audio": os.path.join(BASE_DIR, "results_apps_audio"),
}

OUT_COMBINED_CSV = os.path.join(BASE_DIR, "rq3_all_qoe.csv")
PLOT_DIR = os.path.join(BASE_DIR, "rq3_plots")

os.makedirs(PLOT_DIR, exist_ok=True)


def load_all_results():
    dfs = []
    for app_class, rdir in RESULT_DIRS.items():
        if not os.path.isdir(rdir):
            print(f"[!] Missing results dir for {app_class}: {rdir}")
            continue

        csv_files = glob.glob(os.path.join(rdir, "**", "*.csv"), recursive=True)
        if not csv_files:
            print(f"[!] No CSVs found in {rdir}")
            continue

        print(f"[*] Loading {len(csv_files)} CSVs from {rdir}")
        for path in csv_files:
            try:
                df = pd.read_csv(path)
                # Ensure app_class column is set (in case scripts missed it)
                if "app_class" not in df.columns:
                    df["app_class"] = app_class
                dfs.append(df)
            except Exception as e:
                print(f"[!] Failed to load {path}: {e}")

    if not dfs:
        raise SystemExit("[!] No RQ3 CSVs found, nothing to analyze.")

    combined = pd.concat(dfs, ignore_index=True)
    return combined


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    # Defensive: ensure numeric
    numeric_cols = [
        "time_total",
        "size_download",
        "speed_download",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Goodput in Mbps (bits/s / 1e6), avoid divide-by-zero
    df["goodput_mbps"] = np.where(
        (df["time_total"] > 0) & (df["size_download"] > 0),
        df["size_download"] * 8.0 / df["time_total"] / 1e6,
        np.nan,
    )

    # Parse timestamp if present
    if "timestamp" in df.columns:
        try:
            df["timestamp_dt"] = pd.to_datetime(df["timestamp"], format="%Y%m%d-%H%M%S")
        except Exception:
            # If format differs somewhere, ignore conversion errors
            df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


def plot_cdf(data, label, ax):
    data = np.asarray(data)
    data = data[~np.isnan(data)]
    if data.size == 0:
        return
    data = np.sort(data)
    y = np.linspace(0, 1, len(data))
    ax.plot(data, y, label=label)


def plot_time_total_by_app_class(df: pd.DataFrame):
    fig, ax = plt.subplots()
    for app_class in sorted(df["app_class"].dropna().unique()):
        sub = df[df["app_class"] == app_class]
        plot_cdf(sub["time_total"], label=app_class, ax=ax)

    ax.set_xlabel("Total transfer time (s)")
    ax.set_ylabel("CDF")
    ax.set_title("RQ3: CDF of total transfer time by application class")
    ax.grid(True)
    ax.legend()
    out_path = os.path.join(PLOT_DIR, "rq3_cdf_time_total_by_app_class.png")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[*] Saved {out_path}")


def plot_goodput_by_app_class(df: pd.DataFrame):
    fig, ax = plt.subplots()
    for app_class in sorted(df["app_class"].dropna().unique()):
        sub = df[df["app_class"] == app_class]
        plot_cdf(sub["goodput_mbps"], label=app_class, ax=ax)

    ax.set_xlabel("Goodput (Mbps)")
    ax.set_ylabel("CDF")
    ax.set_title("RQ3: CDF of HTTP goodput by application class")
    ax.grid(True)
    ax.legend()
    out_path = os.path.join(PLOT_DIR, "rq3_cdf_goodput_by_app_class.png")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[*] Saved {out_path}")


def plot_video_synthetic_vs_real(df: pd.DataFrame):
    sub = df[df["app_class"] == "video"]
    if sub.empty:
        print("[!] No video rows, skipping video-specific plots.")
        return

    fig, ax = plt.subplots()
    for kind in ["synthetic", "real"]:
        subk = sub[sub["app_kind"] == kind]
        if subk.empty:
            continue
        plot_cdf(subk["goodput_mbps"], label=f"video-{kind}", ax=ax)

    ax.set_xlabel("Goodput (Mbps)")
    ax.set_ylabel("CDF")
    ax.set_title("RQ3: Video goodput, synthetic vs real")
    ax.grid(True)
    ax.legend()
    out_path = os.path.join(PLOT_DIR, "rq3_cdf_video_goodput_synthetic_vs_real.png")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[*] Saved {out_path}")


def plot_audio_time(df: pd.DataFrame):
    sub = df[df["app_class"] == "audio"]
    if sub.empty:
        print("[!] No audio rows, skipping audio-specific plots.")
        return

    fig, ax = plt.subplots()
    for kind in ["synthetic", "real"]:
        subk = sub[sub["app_kind"] == kind]
        if subk.empty:
            continue
        plot_cdf(subk["time_total"], label=f"audio-{kind}", ax=ax)

    ax.set_xlabel("Total transfer time (s)")
    ax.set_ylabel("CDF")
    ax.set_title("RQ3: Audio transfer time, synthetic vs real")
    ax.grid(True)
    ax.legend()
    out_path = os.path.join(PLOT_DIR, "rq3_cdf_audio_time_synthetic_vs_real.png")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[*] Saved {out_path}")


def main():
    df = load_all_results()
    df = add_derived_metrics(df)

    # Save raw + derived metrics for paper / notebook use
    df.to_csv(OUT_COMBINED_CSV, index=False)
    print(f"[*] Wrote combined CSV: {OUT_COMBINED_CSV}")
    print(f"    Rows: {len(df)}")

    # Basic CDFs
    plot_time_total_by_app_class(df)
    plot_goodput_by_app_class(df)
    plot_video_synthetic_vs_real(df)
    plot_audio_time(df)


if __name__ == "__main__":
    main()
