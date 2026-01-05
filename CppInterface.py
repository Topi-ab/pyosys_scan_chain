import json
import re
import time

class CppInterface:
    @staticmethod
    def yosys2cpp_name(name: str) -> str:
        """
        Convert a Yosys (escaped) net name to a C++ enum-style identifier using the rule:
        \\res_data_out[ylow_seg1_sum] -> RES_DATA_OUT__YLOW_SEG1_SUM

        Rules implemented:
        - Strip leading backslash '\' (Yosys escaped identifier marker), and trim whitespace.
        - Treat bracket nesting as hierarchy: each [...] segment becomes a '__' separated part.
        - Within each part, replace any non-alphanumeric/_ with '_' and collapse repeats.
        - Uppercase everything.
        """
        s = name.strip()
        if s.startswith("\\"):
            s = s[1:]

        # Split into base + bracketed segments: "base[seg1][seg2]" -> ["base", "seg1", "seg2"]
        parts = []
        m = re.match(r'^([^\[]+)', s)
        if m:
            parts.append(m.group(1))
        parts.extend(re.findall(r'\[([^\]]*)\]', s))

        def sanitize(part: str) -> str:
            # Replace non [A-Za-z0-9_] with underscore, collapse, strip underscores, uppercase
            part = re.sub(r'[^0-9A-Za-z_]+', '_', part)
            part = re.sub(r'_+', '_', part).strip('_')
            return part.upper()

        parts = [sanitize(p) for p in parts if p is not None and p != ""]
        return "__".join(parts)

    def CreateCppInterface(json: dict) -> str:
        """
        """

        r = "/* Auto-generated C++ interface header from Yosys scan-chain JSON description \n"
        r += " * Do not edit manually! \n\n"
        r += f" * Source DUT: {json['dut_name']} \n"
        r += f" * Generated on: {time.ctime()} \n"
        r += " */ \n\n"

        r += """#pragma once

#include <array>
#include <cstddef>

#include "fields.h"

class WrapperInterface {
public:
"""
        r += """    enum class clk_fields: std::size_t {
"""
        first = True
        for f in json["clocks"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        CLK_{CppInterface.yosys2cpp_name(f['clk_in'])}"
        r += "\n    };\n\n"

        r += """    enum class wr_fields: std::size_t {
"""
        first = True
        for f in json["inputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        IN_{CppInterface.yosys2cpp_name(f['dut_in'])}"
        r += "\n    };\n\n"

        r += """    enum class rd_fields: std::size_t {
"""
        first = True
        for f in json["outputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        OUT_{CppInterface.yosys2cpp_name(f['dut_out'])}"
        r += "\n    };\n\n"

        r += """    consteval static
    auto get_clk_specs()
    {
        return std::to_array<FieldSpec<clk_fields>>({
"""
        first = True
        for f in json["clocks"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"            {{ clk_fields::CLK_{CppInterface.yosys2cpp_name(f['clk_in'])}, 1 }}"
        r += """\n        });
    }\n\n"""

        r += """    consteval static
    auto get_wr_specs()
    {
        return std::to_array<FieldSpec<wr_fields>>({
"""
        first = True
        for f in json["inputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"            {{ wr_fields::IN_{CppInterface.yosys2cpp_name(f['dut_in'])}, {f['width']} }}"
        r += """\n        });
    }\n\n"""

        r += """    consteval static
    auto get_rd_specs()
    {
        return std::to_array<FieldSpec<rd_fields>>({
"""
        first = True
        for f in json["outputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"            {{ rd_fields::OUT_{CppInterface.yosys2cpp_name(f['dut_out'])}, {f['width']} }}"
        r += """\n        });
    }\n"""
        r += "};\n"

        return r
