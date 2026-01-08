CXX ?= g++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic
INCLUDES := -I. -Igenerated/include -Isrc -Isrc/hw_regs/include

BIN_DIR := generated/bin
SMOKE_BIN := $(BIN_DIR)/test_wrapper_interface
DEBUG_BIN := $(BIN_DIR)/test_wrapper_interface.debug
SMOKE_SRC := src/tests/cpp/test_wrapper_interface.cpp
GENERATOR := venv/bin/python
GEN_SCRIPT := src/python/scan_chain_builder.py
PRE_SCRIPT ?= examples/8bit_counter/pre_scan.ys
POST_SCRIPT ?= examples/8bit_counter/post_scan.ys
EXAMPLE ?= counter_8bit
LOG_DIR ?= generated/log
JSON_OUT ?= generated/wrapper.json

GEN_FILES := generated/include/wrapper_interface.h generated/include/wrapper_field_callers.h

.PHONY: all clean run build-debug run-debug

all: $(SMOKE_BIN) $(DEBUG_BIN)

$(SMOKE_BIN): $(SMOKE_SRC) $(GEN_FILES)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $< -o $@

$(GEN_FILES): $(GEN_SCRIPT) src/python/cpp_interface.py
	$(GENERATOR) $(GEN_SCRIPT) --example $(EXAMPLE) --pre-script $(PRE_SCRIPT) --post-script $(POST_SCRIPT) --log-dir $(LOG_DIR) --json $(JSON_OUT)

run: $(SMOKE_BIN)
	$(SMOKE_BIN)

run-debug: $(DEBUG_BIN)
	$(DEBUG_BIN)

build-debug: $(DEBUG_BIN)

$(DEBUG_BIN): $(SMOKE_SRC) $(GEN_FILES)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -DWRAPPER_CALLERS_DEBUG $(INCLUDES) $< -o $@

clean:
	rm -f $(SMOKE_BIN) $(DEBUG_BIN) $(GEN_FILES) generated/rtl/out.rtlil generated/rtl/out.sv out.rtlil out.sv
	rm -f generated/rtl/scan_chain.rtlil
	rm -f generated/log/yosys_pre.log generated/log/yosys_pre.err.log generated/log/yosys_post.log generated/log/yosys_post.err.log
	rm -f generated/log/yosys_hash.log generated/log/yosys_hash.err.log
