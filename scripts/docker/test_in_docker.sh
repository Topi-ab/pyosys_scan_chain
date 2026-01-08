#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

exec docker run --rm \
  -v "$ROOT_DIR:$ROOT_DIR" \
  -w "$ROOT_DIR" \
  ubuntu:24.04 bash -lc \
    "apt update && apt install -y python3 python3-venv python3-pip g++ make \
    && make VENV_DIR=/root/venv venv && \
    make VENV_DIR=/root/venv && \
    chown -R $(id -u):$(id -g) generated build dist . 2>/dev/null || true"
