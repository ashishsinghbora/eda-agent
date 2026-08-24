# ==============================================================================
# Cocotb Simulation Makefile for EDA-Agent Examples
# ==============================================================================

# Simulator: icarus (default), verilator, etc.
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Paths
PWD = $(shell pwd)
RTL_DIR = $(PWD)/../rtl

# Defaults for async FIFO simulation
TOPLEVEL ?= fifo_async
MODULE ?= test_fifo_async
SIM_BUILD ?= sim_build_$(TOPLEVEL)

ifeq ($(TOPLEVEL),fifo_async)
    VERILOG_SOURCES = $(RTL_DIR)/fifo_async.v
else ifeq ($(TOPLEVEL),alu_8bit)
    VERILOG_SOURCES = $(RTL_DIR)/alu_8bit.v
    MODULE = test_alu_8bit
endif

# Waveform dumping flags for Icarus
ifeq ($(SIM),icarus)
    COMPILE_ARGS += -g2012
    PLUSARGS += -fst
endif

# Include cocotb standard simulation makefile
include $(shell cocotb-config --makefiles)/Makefile.sim
