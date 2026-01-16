#!/usr/bin/env bash
# client/run_starlink_rq3_slot.sh
#
# Run an RQ3 "slot" campaign: web+video+audio, synthetic + real (if present).
#
# Env:
#   SLOT, REPS, ANCHOR_HTTP, HTTP_PORT, TECH, PLAN, MODE

set -euo pipefail
source "$(dirname "$0")/common.sh"

BASE_DIR="${HOME}/analysis"
ASSETS_BASE="${BASE_DIR}/web_qoe_assets"

SLOT="${SLOT:-slot1}"
REPS="${REPS:-5}"
ANCHOR_HTTP="${ANCHOR_HTTP:-135.116.56.45}"
HTTP_PORT="${HTTP_PORT:-8080}"
TECH="${TECH:-starlink}"
PLAN="${PLAN:-residential}"
MODE="${MODE:-direct}"

echo "[*] RQ3 slot run:"
echo "    SLOT        = ${SLOT}"
echo "    REPS        = ${REPS}"
echo "    ANCHOR      = ${ANCHOR_HTTP}:${HTTP_PORT}"
echo "    TECH/PLAN   = ${TECH}/${PLAN}"
echo "    MODE        = ${MODE}"
echo

if [ ! -d "${ASSETS_BASE}" ]; then
  echo "[!] Assets base not found: ${ASSETS_BASE}"
  echo "    You should have copied web_qoe_assets/ from the anchor or created it locally."
  exit 1
fi

# Helper: pick first file matching pattern
pick_first() {
  local pattern="$1"
  shopt -s nullglob
  local files=( $pattern )
  shopt -u nullglob
  if [ "${#files[@]}" -gt 0 ]; then
    echo "$(basename "${files[0]}")"
  else
    echo ""
  fi
}

# --- Synthetic set ------------------------------------------------------

echo "[*] Synthetic assets:"

# 1) Web synthetic
SYN_WEB_FILE="synthetic/test_20M.bin"
if [ -f "${ASSETS_BASE}/${SYN_WEB_FILE}" ]; then
  echo "    - Web synthetic: ${SYN_WEB_FILE}"
  ANCHOR_HTTP="${ANCHOR_HTTP}" \
  HTTP_PORT="${HTTP_PORT}" \
  HTTP_FILE="${SYN_WEB_FILE}" \
  REPS="${REPS}" \
  APP_KIND="synthetic" \
  TECH="${TECH}" \
  PLAN="${PLAN}" \
  MODE="${MODE}" \
  SLOT="${SLOT}" \
  "${BASE_DIR}/run_starlink_web_qoe.sh"
else
  echo "    [!] Missing synthetic web file: ${SYN_WEB_FILE}"
fi

# 2) Video synthetic
SYN_VIDEO_FILE="synthetic/video_30s_1080p.mp4"
if [ -f "${ASSETS_BASE}/${SYN_VIDEO_FILE}" ]; then
  echo "    - Video synthetic: ${SYN_VIDEO_FILE}"
  ANCHOR_HTTP="${ANCHOR_HTTP}" \
  HTTP_PORT="${HTTP_PORT}" \
  HTTP_FILE="${SYN_VIDEO_FILE}" \
  REPS="${REPS}" \
  APP_KIND="synthetic" \
  TECH="${TECH}" \
  PLAN="${PLAN}" \
  MODE="${MODE}" \
  SLOT="${SLOT}" \
  "${BASE_DIR}/run_starlink_video_qoe.sh"
else
  echo "    [!] Missing synthetic video file: ${SYN_VIDEO_FILE}"
fi

# 3) Audio synthetic
SYN_AUDIO_FILE="synthetic/audio_60s.mp3"
if [ -f "${ASSETS_BASE}/${SYN_AUDIO_FILE}" ]; then
  echo "    - Audio synthetic: ${SYN_AUDIO_FILE}"
  ANCHOR_HTTP="${ANCHOR_HTTP}" \
  HTTP_PORT="${HTTP_PORT}" \
  HTTP_FILE="${SYN_AUDIO_FILE}" \
  REPS="${REPS}" \
  APP_KIND="synthetic" \
  TECH="${TECH}" \
  PLAN="${PLAN}" \
  MODE="${MODE}" \
  SLOT="${SLOT}" \
  "${BASE_DIR}/run_starlink_audio_qoe.sh"
else
  echo "    [!] Missing synthetic audio file: ${SYN_AUDIO_FILE}"
fi

# --- Real set (if available) -------------------------------------------

echo
echo "[*] Real assets (if present):"

REAL_VIDEO_NAME="$(pick_first "${ASSETS_BASE}/real/video/*.mp4")"
REAL_AUDIO_NAME="$(pick_first "${ASSETS_BASE}/real/audio/*.mp3")"

# 1) Web "real" placeholder: use test_5M.bin but mark as real
REAL_WEB_FILE="synthetic/test_5M.bin"
if [ -f "${ASSETS_BASE}/${REAL_WEB_FILE}" ]; then
  echo "    - Web 'real' placeholder: ${REAL_WEB_FILE}"
  ANCHOR_HTTP="${ANCHOR_HTTP}" \
  HTTP_PORT="${HTTP_PORT}" \
  HTTP_FILE="${REAL_WEB_FILE}" \
  REPS="${REPS}" \
  APP_KIND="real" \
  TECH="${TECH}" \
  PLAN="${PLAN}" \
  MODE="${MODE}" \
  SLOT="${SLOT}" \
  "${BASE_DIR}/run_starlink_web_qoe.sh"
fi

# 2) Video real
if [ -n "${REAL_VIDEO_NAME}" ]; then
  REAL_VIDEO_FILE="real/video/${REAL_VIDEO_NAME}"
  echo "    - Video real: ${REAL_VIDEO_FILE}"
  ANCHOR_HTTP="${ANCHOR_HTTP}" \
  HTTP_PORT="${HTTP_PORT}" \
  HTTP_FILE="${REAL_VIDEO_FILE}" \
  REPS="${REPS}" \
  APP_KIND="real" \
  TECH="${TECH}" \
  PLAN="${PLAN}" \
  MODE="${MODE}" \
  SLOT="${SLOT}" \
  "${BASE_DIR}/run_starlink_video_qoe.sh"
else
  echo "    [!] No real video found under real/video/*.mp4"
fi

# 3) Audio real
if [ -n "${REAL_AUDIO_NAME}" ]; then
  REAL_AUDIO_FILE="real/audio/${REAL_AUDIO_NAME}"
  echo "    - Audio real: ${REAL_AUDIO_FILE}"
  ANCHOR_HTTP="${ANCHOR_HTTP}" \
  HTTP_PORT="${HTTP_PORT}" \
  HTTP_FILE="${REAL_AUDIO_FILE}" \
  REPS="${REPS}" \
  APP_KIND="real" \
  TECH="${TECH}" \
  PLAN="${PLAN}" \
  MODE="${MODE}" \
  SLOT="${SLOT}" \
  "${BASE_DIR}/run_starlink_audio_qoe.sh"
else
  echo "    [!] No real audio found under real/audio/*.mp3"
fi

echo
echo "[*] RQ3 slot complete."
echo "    Check results under:"
echo "      ${RESULTS_APPS_WEB}"
echo "      ${RESULTS_APPS_VIDEO}"
echo "      ${RESULTS_APPS_AUDIO}"
