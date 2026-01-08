# pyosys_scan_chain

Generate scan-chain wrappers for synthesizable RTL designs using Yosys via `pyosys`. The flow inserts scan chains, builds a standardized wrapper, and emits C++ headers plus JSON metadata.

## Requirements

- Python 3.10+ (tested on 3.12, Ubuntu 24.04)
- `pyosys` (bundles Yosys; no separate Yosys install required)
- Ubuntu packages:
  - `python3`, `python3-venv`, `python3-pip`
  - `g++`, `make` (for the C++ smoke test)

Install on Ubuntu:

```
sudo apt update && sudo apt install -y python3 python3-venv python3-pip g++ make
```

## Getting started

### 1) Install (pyproject.toml)

```
make venv
. venv/bin/activate
```

This installs the CLI entry point:

```
scan-chain-builder --help
```

### 2) Quick run via Makefile

```
make
```

Other built-in examples:

```
make example-sv_8bit_counter
make example-sv_pipeline_2x2
make example-sv_axi_gpio_10x16
```

### 3) Run with explicit inputs

```
scan-chain-builder \
  --design examples/sv/sv_pipeline_2x2/sv_pipeline_2x2.sv \
  --top sv_pipeline_2x2 \
  --pre-script examples/sv/sv_pipeline_2x2/pre_scan.ys \
  --post-script examples/sv/sv_pipeline_2x2/post_scan.ys \
  --log-dir generated/log \
  --json generated/wrapper.json
```

## Examples layout

- SystemVerilog examples live under `examples/sv/`
- Each example directory is named `sv_<name>` and contains:
  - `sv_<name>.sv` (module name matches file name)
  - `pre_scan.ys`
  - `post_scan.ys`
- Placeholders for future work:
  - `examples/vhdl/`
  - `examples/mixed/`

### pre_scan.ys and post_scan.ys

- `pre_scan.ys` runs before scan-chain insertion. It should read the RTL, set the top module, and perform any required prep/cleanup passes.
- `post_scan.ys` runs after scan-chain insertion and wrapper generation. It typically writes the final RTLIL/SystemVerilog outputs.

## Outputs

Generated outputs are placed under `generated/`:

- `generated/rtl/emulator_wrapper.sv`
- `generated/rtl/emulator_wrapper.rtlil`
- `generated/include/wrapper_interface.h`
- `generated/include/wrapper_field_callers.h`
- `generated/wrapper.json`
- `generated/log/` (separate pre/post/hash logs)

## Wrapper interface overview

The wrapper provides a consistent external interface:

- `scan_enable_in`
- `scan_in` / `scan_out`
- `dut_in` / `dut_out`
- `dut_hash_out` (64-bit hash of RTLIL after scan-chain insertion)

When `scan_enable_in` is `0`, the design behaves normally. When `scan_enable_in` is `1`, the scan chain is active and shifts data through `scan_in/out`.

The C++ header `generated/include/wrapper_interface.h` describes bit positions for clocks and DUT I/O fields.

## Development helpers

- `make clean` removes generated artifacts (keeps `venv/`).
- `make build-debug` builds with `WRAPPER_CALLERS_DEBUG` for extra C++ logging.
- Docker smoke test: `scripts/docker/test_in_docker.sh`

## Vivado project creation (Linux)

1) Generate RTL first:

```
make
```

2) Run the helper script (opens existing project if present):

```
scripts/vivado/run_vivado.sh
```

To force a clean rebuild of the project:

```
scripts/vivado/run_vivado.sh --recreate-project
```

This creates/opens the project under `generated/vivado` and opens the elaborated RTL view.
