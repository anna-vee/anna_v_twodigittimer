# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 5)

    # press button
    dut.ui_in.value = 0b00000010
    await ClockCycles(dut.clk, 1200)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 50)

    assert int(dut.ones.value) == 1, f"Expected ones=1, got {int(dut.ones.value)}"
    dut._log.info("Test passed")

    # Set the input values you want to test
    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.
