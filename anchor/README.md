
---
# Anchor Host (Remote Server)

This directory turns a remote VM into the **anchor** for the Starlink experiments.

The anchor host:

- runs `iperf3` servers on specific ports (80, 443, 5201, 6881)
- serves QoE assets (synthetic + real) over HTTP (default: 8080)
- keeps the QoE asset manifest under `~/analysis/web_qoe_assets`

---

## Prerequisites

- Linux VM (Ubuntu/Debian tested)
- public IP reachable from the Starlink client (or via Tailscale later)
- `sudo` privileges

Recommended layout:

```bash
git clone https://github.com/hxngillani/starlink-qoe-experiments.git ~/analysis
cd ~/analysis/anchor
````

---

## Install

```bash
cd ~/analysis/anchor
chmod +x *.sh
./install_anchor.sh
```

`install_anchor.sh` typically installs: `iperf3`, `curl`, `python3`, and optional media tooling (ffmpeg/gstreamer) if needed.

---

## Prepare QoE assets (RQ3)

For application QoE we use a fixed set of assets:

* **Synthetic** (generated):

  * `synthetic/test_5M.bin`
  * `synthetic/test_20M.bin`
  * `synthetic/video_30s_1080p.mp4`
  * `synthetic/audio_60s.mp3`
* **Real** (optional):

  * `real/audio/*.mp3`
  * `real/video/*.mp4`

Run:

```bash
cd ~/analysis/anchor
./anchor_prepare_rq3_assets.sh
```

This script creates:

```text
~/analysis/web_qoe_assets/
  synthetic/
  real/audio/
  real/video/
  manifest.csv
  manifest.json
```

Inspect:

```bash
cd ~/analysis/web_qoe_assets
tree
cat manifest.csv
```

---

## Start/stop services

### Start

```bash
cd ~/analysis/anchor
./start_anchor_services.sh
```

Expected behavior:

* starts iperf3 servers on: `80`, `443`, `5201`, `6881`
* starts HTTP server serving `~/analysis/web_qoe_assets` on `8080`
* writes logs (depending on implementation)

Leave this running while the client performs tests.

### Stop

```bash
cd ~/analysis/anchor
./stop_anchor_services.sh
```

---

## Optional: extra synthetic blobs

`generate_test_content.sh` is a helper for additional synthetic objects (older experiments).
For RQ3, the recommended script is `anchor_prepare_rq3_assets.sh`.

---

## Configuration knobs

Things you may customize inside scripts:

* HTTP port (default `8080`)
* `web_qoe_assets` path (default `~/analysis/web_qoe_assets`)
* iperf3 port list

If you change ports or paths, update:

* `client/common.sh`
* client QoE scripts (`run_starlink_*`)
* any analysis code that assumes specific filenames or directories
