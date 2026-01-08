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
#include <string_view>

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
            r += f"        {CppInterface.yosys2cpp_name(f['clk_in'])}"
        r += "\n    };\n\n"

        r += """    enum class wr_fields: std::size_t {
"""
        first = True
        for f in json["inputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        {CppInterface.yosys2cpp_name(f['dut_in'])}"
        r += "\n    };\n\n"

        r += """    enum class rd_fields: std::size_t {
"""
        first = True
        for f in json["outputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        {CppInterface.yosys2cpp_name(f['dut_out'])}"
        r += "\n    };\n\n"

        r += """    consteval static
    auto get_clk_names()
    {
        return std::to_array<std::string_view>({
"""
        first = True
        for f in json["clocks"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"            \"{CppInterface.yosys2cpp_name(f['clk_in'])}\""
        r += """\n        });
    }\n\n"""

        r += """    consteval static
    auto get_wr_names()
    {
        return std::to_array<std::string_view>({
"""
        first = True
        for f in json["inputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"            \"{CppInterface.yosys2cpp_name(f['dut_in'])}\""
        r += """\n        });
    }\n\n"""

        r += """    consteval static
    auto get_rd_names()
    {
        return std::to_array<std::string_view>({
"""
        first = True
        for f in json["outputs"]:
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"            \"{CppInterface.yosys2cpp_name(f['dut_out'])}\""
        r += """\n        });
    }\n\n"""

        r += """    static constexpr std::string_view clk_name(clk_fields f) {
        return get_clk_names()[static_cast<size_t>(f)];
    }

    static constexpr std::string_view wr_name(wr_fields f) {
        return get_wr_names()[static_cast<size_t>(f)];
    }

    static constexpr std::string_view rd_name(rd_fields f) {
        return get_rd_names()[static_cast<size_t>(f)];
    }

"""

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
            r += f"            {{ clk_fields::{CppInterface.yosys2cpp_name(f['clk_in'])}, 1 }}"
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
            r += f"            {{ wr_fields::{CppInterface.yosys2cpp_name(f['dut_in'])}, {f['width']} }}"
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
            r += f"            {{ rd_fields::{CppInterface.yosys2cpp_name(f['dut_out'])}, {f['width']} }}"
        r += """\n        });
    }\n"""
        r += "};\n"

        return r

    def CreateFieldCallersHeader(json: dict) -> str:
        """
        """
        r = "/* Auto-generated emulator field callers from Yosys scan-chain JSON description \n"
        r += " * Do not edit manually! \n\n"
        r += f" * Source DUT: {json['dut_name']} \n"
        r += f" * Generated on: {time.ctime()} \n"
        r += " */ \n\n"

        r += """#pragma once

#include <array>
#include <cstdint>
#include <iostream>

#include "emulator_fields.h"
#include "wrapper_interface.h"

template <typename HW>
class WrapperFieldCallers {
public:
    using emu_t = emulator_fields<HW, WrapperInterface>;
    using wr_fn_t = void (*)(uint64_t);
    using rd_fn_t = uint64_t (*)();

    static void init(HW &hw) {
        static emu_t inst(hw);
        s_fields = &inst;
    }

    static constexpr size_t num_wr_fields = WrapperInterface::get_wr_specs().size();
    static constexpr size_t num_rd_fields = WrapperInterface::get_rd_specs().size();

"""
        for f in json["inputs"]:
            name = CppInterface.yosys2cpp_name(f["dut_in"])
            r += f"""    static void write_{name}(uint64_t value) {{
#ifdef WRAPPER_CALLERS_DEBUG
        std::cout << "write_{name}(" << value << ")\\n";
#endif
        s_fields->wr_field(WrapperInterface::wr_fields::{name}, value);
    }}

"""

        for f in json["outputs"]:
            name = CppInterface.yosys2cpp_name(f["dut_out"])
            r += f"""    static uint64_t read_{name}() {{
        uint64_t value = 0;
        s_fields->rd_field(WrapperInterface::rd_fields::{name}, value);
#ifdef WRAPPER_CALLERS_DEBUG
        std::cout << "read_{name}() -> " << value << "\\n";
#endif
        return value;
    }}

"""

        r += "    inline static constexpr std::array<wr_fn_t, num_wr_fields> wr_callers = {\n"
        first = True
        for f in json["inputs"]:
            name = CppInterface.yosys2cpp_name(f["dut_in"])
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        &write_{name}"
        r += "\n    };\n\n"

        r += "    inline static constexpr std::array<rd_fn_t, num_rd_fields> rd_callers = {\n"
        first = True
        for f in json["outputs"]:
            name = CppInterface.yosys2cpp_name(f["dut_out"])
            if not first:
                r += ",\n"
            else:
                first = False
            r += f"        &read_{name}"
        r += "\n    };\n\n"

        r += """private:
    inline static emu_t *s_fields = nullptr;
};
"""
        return r
