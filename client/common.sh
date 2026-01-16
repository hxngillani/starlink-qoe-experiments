#!/usr/bin/env bash
# client/common.sh
#
# Common paths and helpers for all client scripts.

set -euo pipefail

BASE_DIR="${HOME}/analysis"

RESULTS_STARLINK="${BASE_DIR}/results_starlink"
RESULTS_GATEWAY="${BASE_DIR}/results_gateway"
RESULTS_APPS_WEB="${BASE_DIR}/results_apps_web"
RESULTS_APPS_VIDEO="${BASE_DIR}/results_apps_video"
RESULTS_APPS_AUDIO="${BASE_DIR}/results_apps_audio"

mkdir -p \
  "${RESULTS_STARLINK}" \
  "${RESULTS_GATEWAY}" \
  "${RESULTS_APPS_WEB}" \
  "${RESULTS_APPS_VIDEO}" \
  "${RESULTS_APPS_AUDIO}"

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%S"
}

timestamp_id() {
  date -u +"%Y%m%d-%H%M%S"
}
