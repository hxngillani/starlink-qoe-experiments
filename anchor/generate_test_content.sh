#!/usr/bin/env bash
# anchor/generate_test_content.sh
#
# Legacy synthetic generator (kept for reproducibility).
# Newer RQ3 flow uses anchor_prepare_rq3_assets.sh.

set -euo pipefail

BASE_DIR="${HOME}/analysis"
WWW_DIR="${BASE_DIR}/starlink_www"

mkdir -p "${WWW_DIR}"
cd "${WWW_DIR}"

echo "[*] Generating legacy synthetic content under: ${WWW_DIR}"

dd if=/dev/urandom of=test_1M.bin   bs=1M count=1   status=progress
dd if=/dev/urandom of=test_5M.bin   bs=1M count=5   status=progress
dd if=/dev/urandom of=test_20M.bin  bs=1M count=20  status=progress
dd if=/dev/urandom of=test_100M.bin bs=1M count=100 status=progress

mkdir -p video_segments_1M
for i in $(seq -w 1 60); do
  dd if=/dev/urandom of="video_segments_1M/seg_${i}.bin" bs=1M count=1 status=none
done

echo "[*] Legacy synthetic content ready."
