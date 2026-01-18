
# Starlink QoE Experiments

This repository contains the full measurement + analysis pipeline we used to study Starlink performance and application QoE:

- **RQ1 — Baseline performance** under different protocols/ports  
  (TCP/UDP, ports 80/443/5201/6881, UDP 1M/5M/10M)
- **RQ2 — DSCP/TOS handling** by Starlink  
  (e.g., CS0 / AF31 / EF-like TOS values 0 / 104 / 184)
- **RQ3 — Application-level QoE**
  - web downloads
  - HTTP video-like downloads/streaming
  - audio/music-like traffic

The key idea: a **Starlink-side client** (mini-PC / laptop behind Starlink) generates traffic towards a remote **anchor server** (cloud VM). We log both network-level metrics and app-level QoE, then analyze everything offline with Python.

---

## 1. Architecture overview

### 1.1 Network topology 

![Figure 1 – Network topology](images/fig1_network_topology.png)

**Figure 1 – Network topology.**  
A Linux **client host** sits behind a Starlink dish + router. The client:

- sends **gateway ICMP pings** to the Starlink gateway IP (e.g., `100.64.0.1`) for baseline RTT;
- opens **iperf3 TCP/UDP** and **HTTP QoE** connections to the remote **anchor server** (cloud VM);
- optionally uses a **VPN overlay (Tailscale)**: in *direct* mode, traffic goes to the anchor’s **public IP**; in *VPN* mode, it goes to the anchor’s **VPN IP**, but the physical path is still over Starlink.

The anchor only acts as a controlled endpoint (iperf3 + HTTP server). All measurement control logic runs on the client.

---

### 1.2 Software components & data flow

![Figure 2 – Software components and data flow](images/fig2_software_components.png)

**Figure 2 – Software components and data flow.**

- **client/** (Starlink side)  
  Bash scripts that *generate traffic* and write logs/CSVs under the data directory.

- **anchor/** (cloud VM)  
  Helper scripts to install and run:
  - one HTTP server (for web/video/audio QoE assets),
  - multiple iperf3 servers (TCP/UDP).

- **data/** (or `~/analysis` on a real machine)  
  Where all experiment outputs are written:
  - `results_gateway/` – baseline Starlink gateway pings  
  - `results_starlink/` – active TCP/UDP runs for RQ1/RQ2  
  - `results_apps_web/`, `results_apps_video/`, `results_apps_audio/` – RQ3 HTTP QoE runs  
  - `web_qoe_assets/` – static assets hosted by the anchor (synthetic + real)  
  - `all_starlink_runs.csv` – aggregated table of all active runs (built by analysis scripts)

- **analysis/** (any host)  
  Python scripts and notebooks that read the CSVs and generate figures/tables.

The **client** is the only place where experiment scripts run and where logs are written.  
The **anchor** acts solely as a controlled traffic endpoint.  
The **analysis** scripts are pure offline post-processing.

---

## 2. Repository layout

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

  images/
    fig1_network_topology.png
    fig2_software_components.png
````

---

## 3. Roles and assumptions

* **Client host**: machine behind Starlink (mini-PC or laptop).
* **Anchor host**: remote VM (public IP) running iperf3 + HTTP content.
* **Starlink gateway IP**: ping target for baseline RTT (e.g., `100.64.0.1`).
* **HTTP port**: `8080` by default (adjustable).
* **iperf3 ports**: `80`, `443`, `5201`, `6881`.

Everything targets Linux (Ubuntu/Debian-style) with `bash`, `python3`, and standard CLI tools.

### Data directory convention

All scripts assume a working directory `~/analysis` on both client and anchor. In practice you can either:

* clone this repo as `~/analysis`, or
* clone elsewhere and update the `BASE_DIR` / paths inside `client/common.sh` and related scripts.

---

## 4. High-level workflow (reproduce the experiments)

### 4.1 Step 0 — Clone repo on both machines

On both **client** and **anchor**:

```bash
git clone https://github.com/hxngillani/starlink-qoe-experiments.git ~/analysis
cd ~/analysis
```

If you don’t want `~/analysis`, update the scripts accordingly.

---

### 4.2 Step 1 — Setup the anchor server

On the **anchor VM**:

```bash
cd ~/analysis/anchor
chmod +x *.sh

./install_anchor.sh
./anchor_prepare_rq3_assets.sh
./start_anchor_services.sh
```

Keep these services running while the client executes experiments.

---

### 4.3 Step 2 — Setup the client host

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

### 4.4 Step 3 — Baseline gateway RTT (`results_gateway/`)

Goal: continuous ping to the Starlink gateway and summary stats (RTT/jitter/loss).

```bash
cd ~/analysis/client

export GATEWAY=100.64.0.1
export LOCATION_LABEL=lab_afternoon
export DURATION_S=1800    # seconds (30 minutes)

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

### 4.5 Step 4 — RQ1/RQ2 active tests (`results_starlink/`)

Goal: controlled traffic towards the anchor for:

* TCP ports: `80`, `443`, `6881`, `5201`
* UDP rates: `1M`, `5M`, `10M` (typically on port `5201`)
* DSCP/TOS variants on TCP 443: `TOS=0`, `104`, `184`
* modes: `direct` (optional `vpn` later)

Example run (3 reps, 60 s, direct-only):

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

Slot-based campaigns (optional subset of scenarios):

```bash
cd ~/analysis/client

export SLOT=evening1
export REPS=3

./run_starlink_campaign_slot.sh
```

---

### 4.6 Step 5 — RQ3 application-level QoE (`results_apps_*`)

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

Each folder contains CSV logs with metadata columns (slot, mode, tech, plan, asset_name, run_idx, timings, etc.).

Repeat with different slots:

* `SLOT=afternoon1`
* `SLOT=evening1`
* …

---

### 4.7 Step 6 — Offline analysis (Python)

Once you’ve collected data:

```bash
cd ~/analysis/analysis

# Aggregate active runs to one table
python3 summarize_starlink_metrics.py

# RQ1/RQ2 style analysis / figures
python3 analysis_notebook_rq1_rq2_rq4.py

# Gateway baseline analysis
python3 analyze_gateway_ping.py

# RQ3 aggregation/plots
python3 analyze_rq3_qoe.py   # if present
```

See `analysis/README.md` for more detail on each script and the figures they generate.

---

## 5. Reproducibility knobs

Main parameters you will typically tweak:

* repetitions: `REPS`
* duration: `DURATION`, `DURATION_S`
* time-of-day / location labels: `SLOT`, `LOCATION_LABEL`
* mode: `direct`, `vpn`
* DSCP/TOS values: `TOS` passed to iperf3

If you change ports or paths, update:

* `client/common.sh`, `client/setup_starlink_scenario_env.sh`
* `anchor/start_anchor_services.sh`
* any analysis scripts that assume specific ports/labels.

---
