
---

# Analysis Scripts

This folder contains Python scripts to analyze datasets produced by the `client/` and `anchor/` pipelines.

We assume raw results live under `~/analysis` (same layout used during measurement), or that you copied them into `../data` (and updated paths inside scripts).

---

## Files overview

- `analyze_gateway_ping.py`  
  Parses gateway ping logs and computes RTT statistics.

- `analyze_starlink_run.py`  
  Parses a single active run (iperf3 TCP/UDP) and produces `metrics_run.csv`.

- `summarize_starlink_metrics.py`  
  Aggregates all `metrics_run.csv` into one table (e.g., `all_starlink_runs.csv`).

- `analysis_notebook_rq1_rq2_rq4.py`  
  Script/notebook-like analysis driver:
  - loads aggregated active-run tables
  - produces RQ1/RQ2 plots (and optionally RQ4-style views)

- `analyze_rq3_qoe.py` (if present)  
  Aggregates application-level QoE logs from:
  - `results_apps_web/`
  - `results_apps_video/`
  - `results_apps_audio/`
  into clean tables + plots.

---

## Typical analysis workflow

### 1) Gateway baseline (results_gateway/)

Baseline folders look like:

```text
~/analysis/results_gateway/<timestamp>_starlink_<label>/
  gateway_ping_samples.csv
  metrics_gateway.csv
  ...
````

Often the baseline script generates metrics during measurement, but you can re-run or load them in a notebook.

Example notebook pattern:

```python
import pandas as pd
from pathlib import Path

gw_root = Path('~/analysis/results_gateway').expanduser()

dfs = []
for run_dir in gw_root.glob('*_starlink_*'):
    f = run_dir / 'metrics_gateway.csv'
    if f.exists():
        df = pd.read_csv(f)
        df['run_dir'] = run_dir.name
        dfs.append(df)

df_gw = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
df_gw.head()
```

---

### 2) Active runs (RQ1/RQ2 — results_starlink/)

Active run folders look like:

```text
~/analysis/results_starlink/<timestamp>_starlink_<plan>_<mode>_<proto>_<port>_uplink_tosXXX_rN/
  metrics_run.csv
  gw_ping_samples.csv
  ...
```

To aggregate all runs into one table:

```bash
cd ~/analysis/analysis
python3 summarize_starlink_metrics.py
```

This typically scans `~/analysis/results_starlink/` and writes an output like:

* `all_starlink_runs.csv`

Then run the main analysis driver:

```bash
python3 analysis_notebook_rq1_rq2_rq4.py
```

Examples of questions answered:

* **RQ1:** Throughput/loss by port and protocol
* **RQ2:** DSCP/TOS impact on throughput/RTT/loss
* (Optional) time-of-day comparisons if slot labels are included in metadata

---

### 3) Application-level QoE (RQ3 — results_apps_web/video/audio)

RQ3 outputs include CSVs such as:

* web: `web_timing.csv`
* video: `video_timing.csv` (and possibly segment-level logs)
* audio: `audio_udp.csv`

They include both:

* QoE metrics (e.g., `time_total`, `speed_download`, `loss_percent`, etc.)
* metadata columns (`slot`, `mode`, `tech`, `plan`, `asset_name`, `run_idx`, timestamps)

To aggregate:

```bash
cd ~/analysis/analysis
python3 analyze_rq3_qoe.py
```

Typical outputs:

* `web_qoe_all.csv`
* `video_qoe_all.csv`
* `audio_qoe_all.csv`
* figures (CDFs, distributions, time-of-day comparisons), depending on the script

---

## Plot outputs

Most scripts write figures under a `figures/` directory (location depends on config inside scripts).

Common plots:

* RQ1: TCP goodput vs port, UDP loss vs rate
* RQ2: throughput/RTT vs DSCP/TOS
* RQ3: download time CDFs, segment-level goodput distributions, audio loss/jitter comparisons

---

## Colab / Jupyter usage

All scripts can be used in notebooks by importing functions or copying logic:

* mount dataset (Drive / local)
* point paths to `results_*`
* reuse aggregation steps
* generate plots for the paper
