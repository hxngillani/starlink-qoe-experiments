#!/usr/bin/env bash
# client/run_starlink_video_qoe.sh
#
# "Video" QoE via HTTP download of .mp4 asset.
# Same metrics as web_timing but stored as video_timing.csv.

set -euo pipefail
source "$(dirname "$0")/common.sh"

ANCHOR_HTTP="${ANCHOR_HTTP:-135.116.56.45}"
HTTP_PORT="${HTTP_PORT:-8080}"
HTTP_FILE="${HTTP_FILE:-synthetic/video_30s_1080p.mp4}"
REPS="${REPS:-5}"
APP_KIND="${APP_KIND:-synthetic}"
TECH="${TECH:-starlink}"
PLAN="${PLAN:-residential}"
MODE="${MODE:-direct}"
SLOT="${SLOT:-slot1}"

OUT_DIR="${RESULTS_APPS_VIDEO}"
mkdir -p "${OUT_DIR}"

for r in $(seq 1 "${REPS}"); do
  TS_ID="$(timestamp_id)"
  RUN_DIR="${OUT_DIR}/${TS_ID}_${TECH}_video_${APP_KIND}_$(basename "${HTTP_FILE}")_${MODE}_${SLOT}_r${r}"
  mkdir -p "${RUN_DIR}"

  URL="http://${ANCHOR_HTTP}:${HTTP_PORT}/${HTTP_FILE}"
  CSV="${RUN_DIR}/video_timing.csv"

  echo "[*] Video QoE run ${r}/${REPS}"
  echo "    URL: ${URL}"
  echo "    RUN_DIR: ${RUN_DIR}"

  echo "timestamp,slot,tech,plan,mode,app_class,app_kind,asset_name,anchor_host,anchor_port,run_idx,url,time_namelookup,time_connect,time_appconnect,time_pretransfer,time_starttransfer,time_total,size_download,speed_download" > "${CSV}"

  ts_utc="$(timestamp_utc)"

  tmp_out="${RUN_DIR}/curl_body.tmp"
  tmp_metrics="${RUN_DIR}/curl_metrics.txt"

  curl -sS -o "${tmp_out}" -w \
    "time_namelookup=%{time_namelookup}\n\
time_connect=%{time_connect}\n\
time_appconnect=%{time_appconnect}\n\
time_pretransfer=%{time_pretransfer}\n\
time_starttransfer=%{time_starttransfer}\n\
time_total=%{time_total}\n\
size_download=%{size_download}\n\
speed_download=%{speed_download}\n" \
    "${URL}" > "${tmp_metrics}"

  eval "$(grep '=' "${tmp_metrics}" | tr -d '\r')"

  echo "${ts_utc},${SLOT},${TECH},${PLAN},${MODE},video,${APP_KIND},$(basename "${HTTP_FILE}"),${ANCHOR_HTTP},${HTTP_PORT},${r},${URL},${time_namelookup},${time_connect},${time_appconnect},${time_pretransfer},${time_starttransfer},${time_total},${size_download},${speed_download}" >> "${CSV}"

  rm -f "${tmp_out}" "${tmp_metrics}"
done

echo "[*] Video QoE complete. Results under ${RESULTS_APPS_VIDEO}"
