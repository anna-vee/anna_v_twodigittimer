# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

MUX_PERIOD = 1024

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 5)

    # press button
    dut.ui_in.value = 0b00000010
    await ClockCycles(dut.clk, 1200)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 50)

    # wait for mux to show ones digit
    await ClockCycles(dut.clk, MUX_PERIOD * 2)
    seg = int(dut.uo_out.value) & 0x7F
    assert seg == 0b0110000, f"Expected digit 1 on display, got {seg:07b}"
    dut._log.info("Test passed")
