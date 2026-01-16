#!/usr/bin/env bash
# anchor/install_anchor.sh
#
# One-time setup on the anchor (Azure VM).
# - Installs iperf3, Python, HTTP server tools, and GStreamer (for RTP tests).
# - Prepares ~/analysis directory.

set -euo pipefail

sudo apt-get update

sudo apt-get install -y \
  iperf3 \
  python3 python3-pip \
  nginx \
  ffmpeg \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav

mkdir -p "${HOME}/analysis"
echo "[*] Anchor base directory: ${HOME}/analysis"

# Optional: disable nginx if you prefer python http.server
sudo systemctl disable --now nginx || true

echo "[*] Anchor install complete."
echo "   Next: run anchor_prepare_rq3_assets.sh, then start_anchor_services.sh"
