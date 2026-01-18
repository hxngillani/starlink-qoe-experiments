

# Client Host (Starlink-side)

This directory contains scripts that run on the **client behind Starlink**.

The client host:

- measures **gateway baseline RTT** (`results_gateway/`)
- runs **active traffic experiments** (RQ1/RQ2) with `iperf3` (`results_starlink/`)
- runs **application-level QoE tests** (RQ3) for web/video/audio (`results_apps_*/`)

---

## Prerequisites

- Linux machine connected through Starlink (Wi-Fi/Ethernet behind Starlink router)
- reachability to the anchor (public IP or VPN)
- `sudo` privileges

Recommended layout:

```bash
git clone https://github.com/hxngillani/starlink-qoe-experiments.git ~/analysis
cd ~/analysis/client
chmod +x *.sh
````

---

## Install

```bash
./install_client.sh
```

Typical dependencies: `iperf3`, `curl`, `jq` (if used), `python3`, and optional media tooling for QoE scripts.

---

## Common configuration

Core parameters live in:

* `common.sh`
* `setup_starlink_scenario_env.sh`

Key variables:

* `GATEWAY` — Starlink gateway IP (e.g., `100.64.0.1`)
* `TECH` — usually `starlink`
* `PLAN` — e.g., `residential`
* `ANCHOR_DIRECT` — anchor public IP
* `ANCHOR_VPN` — anchor VPN IP (Tailscale), optional
* results directories — typically under `~/analysis`

You can either edit the files once, or export vars before running scripts.

---

## Baseline gateway measurements (results_gateway/)

Script: `baseline_gateway_starlink.sh`
Goal: continuous ping to gateway + summary stats.

Example:

```bash
cd ~/analysis/client

export GATEWAY=100.64.0.1
export LOCATION_LABEL=lab_afternoon
export DURATION_S=1800

./baseline_gateway_starlink.sh
```

Creates a run folder under:

```text
~/analysis/results_gateway/
  <timestamp>_starlink_<label>/
    gateway_ping_samples.csv
    metrics_gateway.csv
    run_metadata.txt
    summary_gateway.txt
```

---

## RQ1/RQ2 active runs (results_starlink/)

### Core runner: `run_starlink_scenario.sh`

This is the low-level scenario runner, usually invoked by wrappers. It handles:

* `iperf3` client runs (TCP/UDP)
* DSCP/TOS settings
* per-run gateway ping sampling
* run folder creation + outputs

### Full matrix: `run_starlink_matrix.sh`

Default matrix typically includes:

* TCP ports: `80`, `443`, `6881`, `5201`
* UDP rates: `1M`, `5M`, `10M`
* DSCP/TOS subset on TCP 443 (`TOS=0, 104, 184`)
* mode(s): `direct` (optional `vpn`)

Example:

```bash
cd ~/analysis/client

export REPS=3
export DURATION=60
export SLEEP_BETWEEN=15
export MODES="direct"

./run_starlink_matrix.sh
```

Results:

```text
~/analysis/results_starlink/
  <timestamp>_starlink_<plan>_<mode>_<proto>_<port>_uplink_tosXXX_rN/
    metrics_run.csv
    gw_ping_samples.csv
    iperf_*.json / iperf_*.txt
    run_metadata.txt
```

### Slot-based campaign (optional): `run_starlink_campaign_slot.sh`

Use this if you want a smaller subset per time slot.

```bash
cd ~/analysis/client

export SLOT=evening1
export REPS=2

./run_starlink_campaign_slot.sh
```

The specific scenario subset is defined in the script (customize it to match your needs).

---

## RQ3 application-level QoE (results_apps_web/video/audio)

Scripts:

* `run_starlink_web_qoe.sh`
* `run_starlink_video_qoe.sh`
* `run_starlink_audio_qoe.sh`
* `run_starlink_rq3_slot.sh` (orchestrator)

### Sanity check: single web run

```bash
cd ~/analysis/client

ANCHOR_HTTP=<anchor_public_ip> \
HTTP_PORT=8080 \
HTTP_FILE=synthetic/test_20M.bin \
REPS=1 \
APP_KIND=synthetic \
TECH=starlink \
PLAN=residential \
MODE=direct \
SLOT=test_sanity \
./run_starlink_web_qoe.sh
```

You should get a `web_timing.csv` with timing + metadata columns.

### Full RQ3 slot run

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

This typically:

1. finds synthetic assets under `~/analysis/web_qoe_assets/synthetic/`
2. finds real assets under `~/analysis/web_qoe_assets/real/*`
3. runs web/video/audio scripts per asset for `run_idx=1..REPS`
4. writes results under:

   * `~/analysis/results_apps_web/`
   * `~/analysis/results_apps_video/`
   * `~/analysis/results_apps_audio/`

Repeat with multiple slots (e.g., morning/afternoon/evening) to capture diurnal variation.

---

## VPN mode (optional)

If you use Tailscale:

* set `ANCHOR_VPN` in config
* run with: `MODES="direct vpn"`

Make sure:

* both client and anchor are logged into Tailscale
* services are reachable via the VPN IP (iperf3 + HTTP)

---

## Troubleshooting tips

* If iperf3 fails: confirm anchor ports are open and servers are running.
* If HTTP QoE fails: confirm `ANCHOR_HTTP` and `HTTP_PORT`, and that assets exist under `~/analysis/web_qoe_assets/`.
* If outputs are missing: confirm scripts are writing to `~/analysis` and you have permissions.



