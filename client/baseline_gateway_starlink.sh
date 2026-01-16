#!/usr/bin/env bash
# client/baseline_gateway_starlink.sh
#
# Run Starlink gateway baseline (ping-only) and generate:
#   results_gateway/<run_id>/metrics_gateway.csv
#   results_gateway/<run_id>/gateway_ping_samples.csv
#
# Usage:
#   ./baseline_gateway_starlink.sh -g 100.64.0.1 -l lab_afternoon -c 1800
#
#   -g gateway IP (default 100.64.0.1)
#   -l location label (e.g., lab_morning, lab_afternoon)
#   -c duration seconds (ping count ~= duration, default 1800)

set -euo pipefail

source "$(dirname "$0")/common.sh"

GATEWAY_IP="100.64.0.1"
LOCATION_LABEL="lab"
DURATION_S=1800

while getopts "g:l:c:" opt; do
  case "$opt" in
    g) GATEWAY_IP="$OPTARG" ;;
    l) LOCATION_LABEL="$OPTARG" ;;
    c) DURATION_S="$OPTARG" ;;
    *) echo "Usage: $0 -g <gateway_ip> -l <location_label> -c <duration_s>"; exit 1 ;;
  esac
done

RUN_ID="$(date -u +"%Y%m%d-%H%M%S")_starlink_${LOCATION_LABEL}"
RUN_DIR="${RESULTS_GATEWAY}/${RUN_ID}"
mkdir -p "${RUN_DIR}"

echo "[*] Baseline gateway run:"
echo "    GATEWAY   = ${GATEWAY_IP}"
echo "    LOCATION  = ${LOCATION_LABEL}"
echo "    DURATION  = ${DURATION_S}s"
echo "    RUN_DIR   = ${RUN_DIR}"

META="${RUN_DIR}/run_metadata.txt"
{
  echo "gateway_ip=${GATEWAY_IP}"
  echo "nut_label=starlink"
  echo "location_label=${LOCATION_LABEL}"
  echo "duration_s=${DURATION_S}"
  echo "start_ts=$(date -u +%s)"
} > "${META}"

PING_LOG="${RUN_DIR}/raw_ping.log"
PING_SAMPLES="${RUN_DIR}/gateway_ping_samples.csv"

echo "[*] Running ping..."
# 1 ping per second for ~DURATION_S seconds
timeout "${DURATION_S}" ping -i 1 "${GATEWAY_IP}" > "${PING_LOG}" 2>&1 || true

# Convert to CSV: seq,rtt_ms
echo "seq,rtt_ms" > "${PING_SAMPLES}"
awk '/icmp_seq=/ && /time=/{ 
  match($0, /icmp_seq=([0-9]+)/, a);
  match($0, /time=([0-9.]+)/, b);
  if (a[1] != "" && b[1] != "") { printf "%s,%s\n", a[1], b[1]; }
}' "${PING_LOG}" >> "${PING_SAMPLES}"

echo "[*] Raw ping samples -> ${PING_SAMPLES}"

ANALYZER="${BASE_DIR}/analyze_gateway_ping.py"
if [ -f "${ANALYZER}" ]; then
  echo "[*] Running analyze_gateway_ping.py..."
  python3 "${ANALYZER}" "${RUN_DIR}" || echo "[!] analyze_gateway_ping.py failed; check logs."
else
  echo "[!] Missing ${ANALYZER}, skipping gateway metrics generation."
fi

echo "[*] Baseline gateway run complete."
