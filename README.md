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
Scan chain info for top module:
Clock: \clk_in
        FF count: 43
        scan input port: $scan_0_in
        scan output port: $scan_0_out
```

The sw reads `counter_8bit.sv` RTL file, synthesizes it, and inserts schan chain with the needed support logic. After processing it writes the result to `out.rtlil` and `out.sv` files.

Then a wrapper is created around the dut, with standardized interface:
- scan_enable_in (1 bit + 1 extra bit to preserve verilog compatibility)
- scan_in (number_of_clocks bits + 1)
- scan_out (number_of_clocks bits + 1)
- dut_in (all dut inputs concatenated to a vector + 1 bit)
- dut_out (all dut outputs concatenated to vector + 1 bit)

When `scan_enable_in` is '0', the design works as original design.<br>
When `scan_enable_in` is '1', the scan chain is activated and shifted in/out through `scan_in/out` pins, one bit per clock cycle.

Then a C++ header (`wrapper_interface.h`) is generated, which describes the bit positions of all clocks, dut_in vectors and dut_out vectors.

```cpp
/* Auto-generated C++ interface header from Yosys scan-chain JSON description 
 * Do not edit manually! 

 * Source DUT: \counter_8bit 
 * Generated on: Tue Jan  6 00:00:00 2026 
 */ 

#pragma once

#include <array>
#include <cstddef>

#include "fields.h"

class WrapperInterface {
public:
    enum class clk_fields: std::size_t {
        CLK_CLK_IN
    };

    enum class wr_fields: std::size_t {
        IN_EN_IN,
        IN_SRESET_IN
    };

    enum class rd_fields: std::size_t {
        OUT_C2_OUT,
        OUT_C3_OUT,
        OUT_C4,
        OUT_C5,
        OUT_C6,
        OUT_C7,
        OUT_COUNT_OUT
    };

    consteval static
    auto get_clk_specs()
    {
        return std::to_array<FieldSpec<clk_fields>>({
            { clk_fields::CLK_CLK_IN, 1 }
        });
    }

    consteval static
    auto get_wr_specs()
    {
        return std::to_array<FieldSpec<wr_fields>>({
            { wr_fields::IN_EN_IN, 1 },
            { wr_fields::IN_SRESET_IN, 1 }
        });
    }

    consteval static
    auto get_rd_specs()
    {
        return std::to_array<FieldSpec<rd_fields>>({
            { rd_fields::OUT_C2_OUT, 8 },
            { rd_fields::OUT_C3_OUT, 8 },
            { rd_fields::OUT_C4, 1 },
            { rd_fields::OUT_C5, 8 },
            { rd_fields::OUT_C6, 1 },
            { rd_fields::OUT_C7, 8 },
            { rd_fields::OUT_COUNT_OUT, 8 }
        });
    }
};
```