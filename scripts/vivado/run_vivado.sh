#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../.." && pwd))
PROJ_DIR="$ROOT_DIR/generated/vivado"
PROJ_NAME="emulator_wrapper"
PART_NAME="xc7a200tsbg484-1"
XPR_PATH="$PROJ_DIR/$PROJ_NAME.xpr"
LOG_DIR="$ROOT_DIR/generated/log"
RTL_FILE="$ROOT_DIR/generated/rtl/emulator_wrapper.sv"
XILINX_DATA_DIR="$ROOT_DIR/generated/vivado/.Xil"

recreate_project=0

for arg in "$@"; do
  case "$arg" in
    --recreate-project)
      recreate_project=1
      ;;
    -h|--help)
      echo "Usage: $(basename "$0") [--recreate-project]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $(basename "$0") [--recreate-project]" >&2
      exit 2
      ;;
  esac
  shift || true
 done

mkdir -p "$LOG_DIR"
mkdir -p "$XILINX_DATA_DIR"

if [[ $recreate_project -eq 1 ]]; then
  rm -rf "$PROJ_DIR"
fi

if [[ ! -f "$RTL_FILE" ]]; then
  echo "ERROR: Missing RTL file: $RTL_FILE" >&2
  echo "Run an example first, e.g.:" >&2
  echo >&2
  echo "  make example-sv_8bit_counter" >&2
  exit 1
fi

mkdir -p "$PROJ_DIR"
cd "$PROJ_DIR"

if [[ -f "$XPR_PATH" && $recreate_project -eq 0 ]]; then
  exec env XILINX_LOCAL_USER_DATA="$XILINX_DATA_DIR" \
    vivado -log "$LOG_DIR/vivado.log" -jou "$LOG_DIR/vivado.jou" "$XPR_PATH"
fi

exec env XILINX_LOCAL_USER_DATA="$XILINX_DATA_DIR" \
  vivado \
  -log "$LOG_DIR/vivado.log" \
  -jou "$LOG_DIR/vivado.jou" \
  -source "$ROOT_DIR/scripts/vivado/create_project.tcl" \
  -tclargs "$PROJ_DIR" "$PROJ_NAME" "$PART_NAME" "$ROOT_DIR"
