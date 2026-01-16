#!/usr/bin/env bash
# client/run_starlink_scenario.sh
#
# Run a single Starlink scenario (TCP/UDP, with DSCP).
# Produces: results_starlink/<run_id>/metrics_run.csv + iperf3_raw.json
#
# Parameters:
#   -a anchor host/IP
#   -g gateway IP
#   -M mode (direct|vpn)
#   -P proto (tcp|udp)
#   -p port
#   -R udp_rate (e.g., 1M, 5M) [UDP only]
#   -t tech label (default starlink)
#   -L plan label (default residential)
#   -D direction (uplink/downlink label; measurement is always from client->anchor)
#   -d duration_sec (iperf runtime, default 60)
#   -n run_idx
#   -T tos (TOS byte / DSCP*4, default 0)

set -euo pipefail
source "$(dirname "$0")/common.sh"

ANCHOR=""
GATEWAY_IP="100.64.0.1"
MODE="direct"
PROTO="tcp"
PORT=""
UDP_RATE=""
TECH="starlink"
PLAN="residential"
DIRECTION="uplink"
DURATION=60
RUN_IDX=1
TOS=0

while getopts "a:g:M:P:p:R:t:L:D:d:n:T:" opt; do
  case "$opt" in
    a) ANCHOR="$OPTARG" ;;
    g) GATEWAY_IP="$OPTARG" ;;
    M) MODE="$OPTARG" ;;
    P) PROTO="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    R) UDP_RATE="$OPTARG" ;;
    t) TECH="$OPTARG" ;;
    L) PLAN="$OPTARG" ;;
    D) DIRECTION="$OPTARG" ;;
    d) DURATION="$OPTARG" ;;
    n) RUN_IDX="$OPTARG" ;;
    T) TOS="$OPTARG" ;;
    *) echo "Usage: $0 -a anchor -g gw -M mode -P proto -p port [-R udp_rate] -t tech -L plan -D direction -d duration -n run_idx -T tos"; exit 1 ;;
  esac
done

if [ -z "${ANCHOR}" ] || [ -z "${PORT}" ]; then
  echo "[!] Missing required params. See usage."
  exit 1
fi

TS_ID="$(timestamp_id)"
RUN_ID="${TS_ID}_${TECH}_${PLAN}_${MODE}_${PROTO}_${PORT}_${DIRECTION}_tos${TOS}_r${RUN_IDX}"
RUN_DIR="${RESULTS_STARLINK}/${RUN_ID}"
mkdir -p "${RUN_DIR}"

echo "[*] Starlink scenario:"
echo "    RUN_ID   = ${RUN_ID}"
echo "    ANCHOR   = ${ANCHOR}:${PORT}"
echo "    GATEWAY  = ${GATEWAY_IP}"
echo "    MODE     = ${MODE}"
echo "    PROTO    = ${PROTO}"
echo "    UDP_RATE = ${UDP_RATE}"
echo "    TOS      = ${TOS}"
echo "    DUR      = ${DURATION}s"

META="${RUN_DIR}/run_metadata.txt"
{
  echo "timestamp_utc=$(timestamp_utc)"
  echo "tech=${TECH}"
  echo "plan=${PLAN}"
  echo "mode=${MODE}"
  echo "proto=${PROTO}"
  echo "port=${PORT}"
  echo "udp_rate=${UDP_RATE}"
  echo "dscp=$((TOS / 4))"
  echo "tos=${TOS}"
  echo "gateway=${GATEWAY_IP}"
  echo "anchor=${ANCHOR}"
  echo "direction=${DIRECTION}"
  echo "duration_sec=${DURATION}"
  echo "run_idx=${RUN_IDX}"
} > "${META}"

IPERF_JSON="${RUN_DIR}/iperf3_raw.json"
IPERF_LOG="${RUN_DIR}/iperf3_stderr.log"

CMD=(iperf3 -c "${ANCHOR}" -p "${PORT}" -t "${DURATION}" -J)

if [ "${PROTO}" = "udp" ]; then
  if [ -z "${UDP_RATE}" ]; then
    echo "[!] UDP mode but no -R udp_rate specified"
    exit 1
  fi
  CMD=(iperf3 -u -b "${UDP_RATE}" -c "${ANCHOR}" -p "${PORT}" -t "${DURATION}" -J)
fi

# Apply TOS/DSCP if non-zero
if [ "${TOS}" -ne 0 ]; then
  CMD+=("--tos" "${TOS}")
fi

echo "[*] Running iperf3: ${CMD[*]}"
"${CMD[@]}" > "${IPERF_JSON}" 2> "${IPERF_LOG}" || echo "[!] iperf3 returned non-zero; check ${IPERF_LOG}"

ANALYZER="${BASE_DIR}/analyze_starlink_run.py"
if [ -f "${ANALYZER}" ]; then
  echo "[*] Running analyze_starlink_run.py..."
  python3 "${ANALYZER}" "${RUN_DIR}" || echo "[!] analyze_starlink_run.py failed."
else
  echo "[!] Missing ${ANALYZER}; metrics_run.csv will not be created."
fi

echo "[*] Scenario done -> ${RUN_DIR}"
