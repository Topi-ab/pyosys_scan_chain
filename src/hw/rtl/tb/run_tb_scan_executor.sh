#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)"
TMP_DIR="${SCRIPT_DIR}/tmp"
WAVE_OUT="${SCRIPT_DIR}/out.ghw"

IMAGE="${IMAGE:-ghdl/ghdl:6.0.0-dev-llvm-ubuntu-22.04}"

mkdir -p "${TMP_DIR}"

docker run --rm -t -u "$(id -u):$(id -g)" \
  -v "${ROOT_DIR}:${ROOT_DIR}" \
  -w "${SCRIPT_DIR}" \
  "${IMAGE}" \
  bash -lc "mkdir -p ${TMP_DIR} \
    && cd ${TMP_DIR} \
    && ghdl -a --std=08 ${ROOT_DIR}/src/hw/rtl/scan_types_pkg.vhdl \
    && ghdl -a --std=08 ${ROOT_DIR}/src/hw/rtl/scan_executor.vhdl \
    && ghdl -a --std=08 ${ROOT_DIR}/src/hw/rtl/tb/tb_scan_executor.vhdl \
    && ghdl -e --std=08 tb_scan_executor \
    && ghdl -r --std=08 tb_scan_executor --wave=${WAVE_OUT} --stop-time=2us"
