#include <cstddef>
#include <cstdint>
#include <iostream>
#include <string_view>

#include "generated/include/wrapper_field_callers.h"
#include "generated/include/wrapper_interface.h"
#include "hw_regs/include/hw_access_debug.h"

int main() {
    // Smoke-test enum name helpers from generated interface.
    auto clk_name = WrapperInterface::clk_name(WrapperInterface::clk_fields::CLK_IN);
    std::cout << "clk name: " << clk_name << "\n";

    hw_access_debug hw("debug");
    WrapperFieldCallers<hw_access_debug>::init(hw);

    const auto wr_names = WrapperInterface::get_wr_names();
    for (size_t i = 0; i < wr_names.size(); ++i) {
        std::cout << "wr name[" << i << "]: " << wr_names[i] << "\n";
        WrapperFieldCallers<hw_access_debug>::wr_callers[i](static_cast<uint64_t>(i + 1));
    }

    const auto rd_names = WrapperInterface::get_rd_names();
    for (size_t i = 0; i < rd_names.size(); ++i) {
        auto v = WrapperFieldCallers<hw_access_debug>::rd_callers[i]();
        std::cout << "rd name[" << i << "]: " << rd_names[i] << " value: " << v << "\n";
    }

    return 0;
}
