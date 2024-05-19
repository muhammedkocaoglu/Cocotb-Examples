TOPLEVEL_LANG = verilog
GUI=0
SIM=questa
PWD=$(shell pwd)

# set parameters
export PYTHONPATH := $(PWD)/../model:$(PYTHONPATH)

VERILOG_SOURCES = $(PWD)/bus_slave.sv

TOPLEVEL := bus_slave
MODULE   := pyuvm_basic_ral
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps
include $(shell cocotb-config --makefiles)\Makefile.sim