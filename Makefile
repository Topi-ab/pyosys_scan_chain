CXX ?= g++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic
INCLUDES := -I. -Igenerated/include -Isrc -Isrc/hw_regs/include

BIN_DIR := generated/bin
SMOKE_BIN := $(BIN_DIR)/test_wrapper_interface
DEBUG_BIN := $(BIN_DIR)/test_wrapper_interface.debug
SMOKE_SRC := src/tests/cpp/test_wrapper_interface.cpp
GENERATOR := venv/bin/python
GEN_SCRIPT := src/python/scan_chain.py

GEN_FILES := generated/include/wrapper_interface.h generated/include/wrapper_field_callers.h

.PHONY: all clean run build-debug run-debug

all: $(SMOKE_BIN) $(DEBUG_BIN)

$(SMOKE_BIN): $(SMOKE_SRC) $(GEN_FILES)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $< -o $@

$(GEN_FILES): $(GEN_SCRIPT) src/python/cpp_interface.py
	$(GENERATOR) $(GEN_SCRIPT)

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
