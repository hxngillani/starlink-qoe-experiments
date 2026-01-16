#!/usr/bin/env bash
# client/setup_starlink_scenario_env.sh
#
# One-time helper to create directories and check for analysis scripts.

set -euo pipefail

source "$(dirname "$0")/common.sh"

echo "[*] Creating result directories under ${BASE_DIR}..."
echo "    - ${RESULTS_STARLINK}"
echo "    - ${RESULTS_GATEWAY}"
echo "    - ${RESULTS_APPS_WEB}"
echo "    - ${RESULTS_APPS_VIDEO}"
echo "    - ${RESULTS_APPS_AUDIO}"

mkdir -p \
  "${RESULTS_STARLINK}" \
  "${RESULTS_GATEWAY}" \
  "${RESULTS_APPS_WEB}" \
  "${RESULTS_APPS_VIDEO}" \
  "${RESULTS_APPS_AUDIO}"

for f in analyze_gateway_ping.py analyze_starlink_run.py summarize_starlink_metrics.py; do
  if [ ! -f "${BASE_DIR}/${f}" ]; then
    echo "[!] WARNING: Missing ${BASE_DIR}/${f}. Copy it from the repo analysis/ directory."
  fi
done

echo "[*] Environment setup done."
