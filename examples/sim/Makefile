# ==============================================================================
# Cocotb Simulation Makefile for EDA-Agent Examples
# ==============================================================================

# Simulator: icarus (default), verilator, etc.
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Paths
RTL_DIR = ../rtl

# Defaults for async FIFO simulation
TOPLEVEL ?= fifo_async
MODULE ?= test_fifo_async
SIM_BUILD ?= sim_build_$(TOPLEVEL)

VERILOG_SOURCES = $(RTL_DIR)/$(TOPLEVEL).v

# Waveform dumping flags for Icarus
COMPILE_ARGS += -g2012
PLUSARGS += -fst

# Include cocotb standard simulation makefile
include $(shell cocotb-config --makefiles)/Makefile.sim
