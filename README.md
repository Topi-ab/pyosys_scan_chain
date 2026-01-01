# pyosys_scan_chain

This codebase demonstrates how to create a scan chain to an synthesizable RTL design using yosys through pyosys (python package).

## Prerequisities

- Tested with python 3.12 on Ubuntu 24.04.
- Yosys installation not required (it is part of pyosys package)

## How to run

```
python3 -m venv venv
. venv/bin/activate
pip install pyosys
python scan_chain.py
```

This should print:
```
...
Total DFFs processed: 43
SCAN CHAIN ADDITION COMPLETED
```

The sw reads `counter_8bit.sv` RTL file, synthesizes it, and inserts schan chain with the needed support logic. After processing it writes the result to `out.rtlil` and `out.sv` files.

The generated logic has additional ports:
- scan_enable_in
- scan_in
- scan_out

When `scan_enable_in` is '0', the design works as original design.<br>
When `scan_enable_in` is '1', the scan chain is activated and shifted in/out through `scan_in/out` pins, one bit per clock cycle.
