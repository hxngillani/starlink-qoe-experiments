#!/usr/bin/env bash
# anchor/stop_anchor_services.sh
#
# Stop iperf3 servers and HTTP QoE server.

set -euo pipefail

echo "[*] Stopping iperf3 servers..."
pkill -f "iperf3 -s" || true

echo "[*] Stopping HTTP server on port 8080..."
pkill -f "python3 -m http.server 8080" || true

echo "[*] Anchor services stopped."
