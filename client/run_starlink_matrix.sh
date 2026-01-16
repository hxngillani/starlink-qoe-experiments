#!/usr/bin/env bash
# client/run_starlink_matrix.sh
#
# Run a default matrix of Starlink scenarios:
#  - TCP: ports 80, 443, 6881, 5201 (direct-only for now)
#  - UDP: 1M, 5M, 10M (direct-only)
#  - DSCP subset: TCP 443, direct, TOS=0/104/184
#
# Usage:
#   REPS=3 DURATION=60 SLEEP_BETWEEN=15 MODES="direct" ./run_starlink_matrix.sh

set -euo pipefail

source "$(dirname "$0")/common.sh"

BASE_DIR="${HOME}/analysis"
SCENARIO_SCRIPT="${BASE_DIR}/run_starlink_scenario.sh"

ANCHOR_DIRECT="135.116.56.45"
ANCHOR_VPN="100.116.112.113"  # placeholder for future VPN
GATEWAY="100.64.0.1"
TECH="starlink"
PLAN="residential"

: "${REPS:=3}"
: "${DURATION:=60}"
: "${SLEEP_BETWEEN:=15}"
: "${MODES:=direct}"   # later: "direct vpn"

if [ ! -x "${SCENARIO_SCRIPT}" ]; then
  echo "[!] Scenario script not found or not executable: ${SCENARIO_SCRIPT}"
  exit 1
fi

echo "[*] Running Starlink scenario matrix..."
echo "    ANCHOR_DIRECT = ${ANCHOR_DIRECT}"
echo "    ANCHOR_VPN    = ${ANCHOR_VPN}"
echo "    GATEWAY       = ${GATEWAY}"
echo "    TECH          = ${TECH}"
echo "    PLAN          = ${PLAN}"
echo "    REPS          = ${REPS}"
echo "    DURATION      = ${DURATION}s"
echo "    SLEEP_BETWEEN = ${SLEEP_BETWEEN}s"
echo "    MODES         = ${MODES}"

# --- 1. TCP ports (RQ1) --------------------------------------------

TCP_PORTS=(80 443 6881 5201)

for mode in ${MODES}; do
  if [ "${mode}" = "direct" ]; then
    anchor="${ANCHOR_DIRECT}"
  else
    anchor="${ANCHOR_VPN}"
  fi

  for port in "${TCP_PORTS[@]}"; do
    for r in $(seq 1 "${REPS}"); do
      echo
      echo "[*] TCP scenario: mode=${mode} port=${port} run=${r}"
      "${SCENARIO_SCRIPT}" \
        -a "${anchor}" \
        -g "${GATEWAY}" \
        -M "${mode}" \
        -P tcp \
        -p "${port}" \
        -t "${TECH}" \
        -L "${PLAN}" \
        -D uplink \
        -d "${DURATION}" \
        -n "${r}" \
        -T 0

      echo "[*] Sleeping ${SLEEP_BETWEEN}s..."
      sleep "${SLEEP_BETWEEN}"
    done
  done
done

# --- 2. UDP rates (RQ1) --------------------------------------------

UDP_RATES=("1M" "5M" "10M")

for mode in ${MODES}; do
  if [ "${mode}" = "direct" ]; then
    anchor="${ANCHOR_DIRECT}"
  else
    anchor="${ANCHOR_VPN}"
  fi

  for rate in "${UDP_RATES[@]}"; do
    for r in $(seq 1 "${REPS}"); do
      echo
      echo "[*] UDP scenario: mode=${mode} rate=${rate} run=${r}"
      "${SCENARIO_SCRIPT}" \
        -a "${anchor}" \
        -g "${GATEWAY}" \
        -M "${mode}" \
        -P udp \
        -p 5201 \
        -R "${rate}" \
        -t "${TECH}" \
        -L "${PLAN}" \
        -D uplink \
        -d "${DURATION}" \
        -n "${r}" \
        -T 0

      echo "[*] Sleeping ${SLEEP_BETWEEN}s..."
      sleep "${SLEEP_BETWEEN}"
    done
  done
done

# --- 3. DSCP subset (TOS) on port 443, direct mode -----------------

TOS_VALUES=(0 104 184)  # CS0, AF31, EF-ish

for tos in "${TOS_VALUES[@]}"; do
  for r in $(seq 1 "${REPS}"); do
    echo
    echo "[*] DSCP scenario: mode=direct port=443 tos=${tos} run=${r}"
    "${SCENARIO_SCRIPT}" \
      -a "${ANCHOR_DIRECT}" \
      -g "${GATEWAY}" \
      -M direct \
      -P tcp \
      -p 443 \
      -t "${TECH}" \
      -L "${PLAN}" \
      -D uplink \
      -d "${DURATION}" \
      -n "${r}" \
      -T "${tos}"

    echo "[*] Sleeping ${SLEEP_BETWEEN}s..."
    sleep "${SLEEP_BETWEEN}"
  done
done

echo
echo "[*] Matrix run complete. Results under: ${RESULTS_STARLINK}"
