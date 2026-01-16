
---

# Starlink QoE Experiments

This repository contains the full measurement + analysis pipeline we used to study Starlink performance and application QoE:

- **RQ1 — Baseline performance** under different protocols/ports  
  (TCP/UDP, ports 80/443/5201/6881, UDP 1M/5M/10M)
- **RQ2 — DSCP/TOS handling** by Starlink  
  (e.g., CS0 / AF31 / EF-like)
- **RQ3 — Application-level QoE**
  - web downloads
  - HTTP video-like downloads/streaming
  - audio/music-like traffic

**Key idea:** a **Starlink-side client** (mini-PC / laptop behind Starlink) generates traffic towards a remote **anchor server** (cloud VM). We log both network-level metrics and app-level QoE, then analyze everything offline with Python.

---

## Repository layout

```text
starlink-qoe-experiments/
  README.md

  anchor/
    README.md
    install_anchor.sh
    anchor_prepare_rq3_assets.sh
    generate_test_content.sh
    start_anchor_services.sh
    stop_anchor_services.sh

  client/
    README.md
    install_client.sh
    common.sh
    setup_starlink_scenario_env.sh
    baseline_gateway_starlink.sh
    run_starlink_scenario.sh
    run_starlink_matrix.sh
    run_starlink_campaign_slot.sh
    run_starlink_web_qoe.sh
    run_starlink_video_qoe.sh
    run_starlink_audio_qoe.sh
    run_starlink_rq3_slot.sh

  analysis/
    README.md
    analyze_gateway_ping.py
    analyze_starlink_run.py
    summarize_starlink_metrics.py
    analysis_notebook_rq1_rq2_rq4.py
    analyze_rq3_qoe.py   # if present

  data/
    .gitignore
````

---

## Roles and assumptions

* **Client host**: the machine behind Starlink (mini-PC/laptop).
* **Anchor host**: remote VM (public IP) running iperf3 + HTTP content.
* **Starlink gateway IP**: ping target for baseline RTT (e.g., `100.64.0.1`).
* **HTTP port**: `8080` by default (adjustable).
* **iperf3 ports**: `80`, `443`, `5201`, `6881`.

Everything targets Linux (Ubuntu/Debian-style) + bash + python3 + standard CLI tools.

### Data directory convention

All scripts assume a working directory `~/analysis` on both client and anchor. You can either:

* clone this repo as `~/analysis`, or
* clone elsewhere and update `BASE_DIR` / paths inside `client/common.sh` and related scripts.

---

## High-level workflow (reproduce the experiments)

### Step 0 — Clone repo on both machines

On both **client** and **anchor**:

```bash
git clone https://github.com/<your-user>/starlink-qoe-experiments.git ~/analysis
cd ~/analysis
```

If you don’t want `~/analysis`, update the scripts accordingly.

---

### Step 1 — Setup the anchor server

On the **anchor VM**:

```bash
cd ~/analysis/anchor
chmod +x *.sh

./install_anchor.sh
./anchor_prepare_rq3_assets.sh
./start_anchor_services.sh
```

Keep services running while the client executes experiments.

---

### Step 2 — Setup the client host

On the **Starlink client**:

```bash
cd ~/analysis/client
chmod +x *.sh

./install_client.sh
```

Configure environment variables (edit `common.sh` / `setup_starlink_scenario_env.sh`, or export in shell):

* `GATEWAY` (e.g., `100.64.0.1`)
* `ANCHOR_DIRECT` (anchor public IP)
* `ANCHOR_VPN` (optional, if using Tailscale later)
* labels like `TECH=starlink`, `PLAN=residential`

---

### Step 3 — Baseline gateway RTT (results_gateway/)

Goal: continuous ping to the Starlink gateway and summary stats (RTT/jitter/loss).

```bash
cd ~/analysis/client

export GATEWAY=100.64.0.1
export LOCATION_LABEL=lab_afternoon
export DURATION_S=1800     # seconds (30 minutes)

./baseline_gateway_starlink.sh
```

Outputs:

```text
~/analysis/results_gateway/<timestamp>_starlink_<label>/
  gateway_ping_samples.csv
  metrics_gateway.csv
  run_metadata.txt
  summary_gateway.txt
```

Repeat with different labels:

* `LOCATION_LABEL=lab_morning`
* `LOCATION_LABEL=lab_evening`
* etc.

---

### Step 4 — RQ1/RQ2 active tests (results_starlink/)

Goal: controlled traffic towards the anchor for:

* TCP ports: `80`, `443`, `6881`, `5201`
* UDP rates: `1M`, `5M`, `10M` (typically on port `5201`)
* DSCP/TOS variants (example on TCP 443): `TOS=0, 104, 184`
* modes: `direct` (optional `vpn`)

Example run (3 reps, 60s, direct-only):

```bash
cd ~/analysis/client

export REPS=3
export DURATION=60
export SLEEP_BETWEEN=15
export MODES="direct"

./run_starlink_matrix.sh
```

Outputs per run folder:

```text
~/analysis/results_starlink/<timestamp>_starlink_<plan>_<mode>_<proto>_<port>_uplink_tosXXX_rN/
  metrics_run.csv
  gw_ping_samples.csv
  iperf_*.json / iperf_*.txt
  run_metadata.txt
```

If you want slot-based campaigns (subset of scenarios):

```bash
cd ~/analysis/client

export SLOT=evening1
export REPS=3

./run_starlink_campaign_slot.sh
```

---

### Step 5 — RQ3 application-level QoE (results_apps_*)

Goal: fetch HTTP assets (web/video/audio), repeated in time slots.

Example slot run (5 reps per asset):

```bash
cd ~/analysis/client

SLOT=morning1 \
REPS=5 \
ANCHOR_HTTP=<anchor_public_ip> \
HTTP_PORT=8080 \
TECH=starlink \
PLAN=residential \
MODE=direct \
./run_starlink_rq3_slot.sh
```

Outputs:

* `~/analysis/results_apps_web/`
* `~/analysis/results_apps_video/`
* `~/analysis/results_apps_audio/`

Each contains CSV logs with metadata columns (slot, mode, tech, plan, asset_name, run_idx, timestamps, etc.).

Repeat with different slots:

* `SLOT=afternoon1`
* `SLOT=evening1`
* etc.

---

### Step 6 — Offline analysis (Python)

Once you’ve collected data:

```bash
cd ~/analysis/analysis

# Aggregate active runs to one table
python3 summarize_starlink_metrics.py

# RQ1/RQ2 style analysis / figures
python3 analysis_notebook_rq1_rq2_rq4.py

# Gateway baseline analysis (optional re-run)
python3 analyze_gateway_ping.py

# RQ3 aggregation/plots (if available)
python3 analyze_rq3_qoe.py
```

See `analysis/README.md` for details.

---

## Data storage notes

By default, raw experiment outputs are written under `~/analysis`:

* `results_gateway/`
* `results_starlink/`
* `results_apps_web/`
* `results_apps_video/`
* `results_apps_audio/`
* `web_qoe_assets/`

The repo’s `data/` directory is ignored by Git and can be used as a local mount/copy location if desired.

---

## Reproducibility knobs

Main parameters you will tweak:

* repetitions: `REPS`
* duration: `DURATION`, `DURATION_S`
* time-of-day / location labels: `SLOT`, `LOCATION_LABEL`
* mode: `direct`, `vpn`
* DSCP/TOS values: `TOS` passed to iperf3

If you change ports/paths, update:

* `client/common.sh`, `client/setup_starlink_scenario_env.sh`
* `anchor/start_anchor_services.sh`
* analysis scripts
