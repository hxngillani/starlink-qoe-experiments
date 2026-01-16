#!/usr/bin/env bash
# anchor/start_anchor_services.sh
#
# Start anchor-side services:
#   - iperf3 TCP/UDP servers on ports 80, 443, 6881, 5201
#   - HTTP static server on port 8080 serving ~/analysis/web_qoe_assets

set -euo pipefail

BASE_DIR="${HOME}/analysis"
WEB_DIR="${BASE_DIR}/web_qoe_assets"

mkdir -p "${BASE_DIR}"

echo "[*] Starting iperf3 servers (80, 443, 6881, 5201)..."

# Kill any stale iperf3
pkill -f "iperf3 -s" || true

for port in 80 443 6881 5201; do
  log="${BASE_DIR}/iperf3_server_${port}.log"
  echo "  - iperf3 -s -p ${port} -> ${log}"
  nohup iperf3 -s -p "${port}" > "${log}" 2>&1 &
done

echo "[*] Starting HTTP server on port 8080 from ${WEB_DIR}"

if [ ! -d "${WEB_DIR}" ]; then
  echo "[!] WARNING: ${WEB_DIR} does not exist yet. Run anchor_prepare_rq3_assets.sh."
fi

# Kill any old python http.server
pkill -f "python3 -m http.server 8080" || true

(
  cd "${WEB_DIR}"
  nohup python3 -m http.server 8080 > "${BASE_DIR}/http_server_8080.log" 2>&1 &
)

echo "[*] Anchor services started."
echo "    Check logs under: ${BASE_DIR}"
