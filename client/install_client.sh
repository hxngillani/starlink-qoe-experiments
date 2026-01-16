#!/usr/bin/env bash
# client/install_client.sh
#
# One-time setup on the mini-PC:
#  - installs iperf3, curl, jq, python, gstreamer, etc.
#  - prepares ~/analysis.

set -euo pipefail

sudo apt-get update

sudo apt-get install -y \
  iperf3 \
  curl \
  jq \
  bc \
  gawk \
  python3 python3-pip \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav

mkdir -p "${HOME}/analysis"
echo "[*] Client base directory: ${HOME}/analysis"

echo "[*] Client install complete."
