#!/usr/bin/env bash
# anchor/anchor_prepare_rq3_assets.sh
#
# Prepare assets for RQ3 HTTP QoE:
#   ~/analysis/web_qoe_assets/
#     synthetic/test_5M.bin
#     synthetic/test_20M.bin
#     synthetic/video_30s_1080p.mp4
#     synthetic/audio_60s.mp3
#     real/video/*.mp4        (optional: copy your real video here)
#     real/audio/*.mp3        (optional: copy your real audio here)
#
# You can later run a manifest builder (qoe_manifest.py) if you want.

set -euo pipefail

BASE_DIR="${HOME}/analysis"
WEB_DIR="${BASE_DIR}/web_qoe_assets"

SYN_DIR="${WEB_DIR}/synthetic"
REAL_VIDEO_DIR="${WEB_DIR}/real/video"
REAL_AUDIO_DIR="${WEB_DIR}/real/audio"

mkdir -p "${SYN_DIR}" "${REAL_VIDEO_DIR}" "${REAL_AUDIO_DIR}"

echo "[*] Preparing synthetic assets under: ${SYN_DIR}"

# 1) Binary blobs for "web" tests
if [ ! -f "${SYN_DIR}/test_5M.bin" ]; then
  echo "  - Creating test_5M.bin"
  dd if=/dev/urandom of="${SYN_DIR}/test_5M.bin" bs=1M count=5 status=progress
fi

if [ ! -f "${SYN_DIR}/test_20M.bin" ]; then
  echo "  - Creating test_20M.bin"
  dd if=/dev/urandom of="${SYN_DIR}/test_20M.bin" bs=1M count=20 status=progress
fi

# 2) Synthetic video (30s, 1080p, H.264)
if [ ! -f "${SYN_DIR}/video_30s_1080p.mp4" ]; then
  echo "  - Creating video_30s_1080p.mp4"
  ffmpeg -y -f lavfi -i testsrc=size=1920x1080:rate=30 \
         -t 30 \
         -c:v libx264 -preset veryfast -pix_fmt yuv420p \
         "${SYN_DIR}/video_30s_1080p.mp4"
fi

# 3) Synthetic audio (60s sine, MP3)
if [ ! -f "${SYN_DIR}/audio_60s.mp3" ]; then
  echo "  - Creating audio_60s.mp3"
  ffmpeg -y -f lavfi -i "sine=frequency=440:sample_rate=48000" \
         -t 60 \
         -ac 2 \
         "${SYN_DIR}/audio_60s.mp3"
fi

echo "[*] You can now drop REAL assets here if you want:"
echo "    Real video: ${REAL_VIDEO_DIR}/your_video.mp4"
echo "    Real audio: ${REAL_AUDIO_DIR}/your_audio.mp3"

echo
echo "[*] Current tree:"
ls -R "${WEB_DIR}"
