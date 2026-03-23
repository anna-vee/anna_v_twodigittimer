# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# 7-segment expected values (segments a-g)
SEG7 = {
    0: 0b1111110,
    1: 0b0110000,
    2: 0b1101101,
    3: 0b1111001,
    4: 0b0110011,
    5: 0b1011011,
    6: 0b1011111,
    7: 0b1110000,
    8: 0b1111111,
    9: 0b1111011,
}

async def reset(dut):
    """Reset the design."""
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

async def press_button(dut):
    """Simulate a button press (hold for > 999 cycles to pass debounce)."""
    dut.ui_in.value = 0b00000010  # ui_in[1] = 1
    await ClockCycles(dut.clk, 1100)  # hold past debounce (999 cycles)
    dut.ui_in.value = 0b00000000  # release
    await ClockCycles(dut.clk, 20)

def get_segments(dut):
    """Get the 7-segment value from uo_out[6:0]."""
    return int(dut.uo_out.value) & 0b1111111

def get_digit_select(dut):
    """Get dig1, dig2 from uio_out[1:0]."""
    return int(dut.uio_out.value) & 0b11

@cocotb.test()
async def test_reset(dut):
    """Test that after reset, display shows 00."""
    dut._log.info("Test 1: Reset shows 00")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)
    await ClockCycles(dut.clk, 10)

    segs = get_segments(dut)
    assert segs == SEG7[0], f"Expected 0 ({SEG7[0]:07b}), got ({segs:07b})"
    dut._log.info("PASS: Display shows 0 after reset")

@cocotb.test()
async def test_button_increments(dut):
    """Test that button press increments ones digit."""
    dut._log.info("Test 2: Button increments ones digit")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)

    for expected in range(1, 5):
        await press_button(dut)
        await ClockCycles(dut.clk, 20)

        # Wait for mux to show dig1 (ones digit)
        for _ in range(2000):
            if get_digit_select(dut) == 0b01:  # dig1=1, dig2=0
                break
            await ClockCycles(dut.clk, 1)

        segs = get_segments(dut)
        assert segs == SEG7[expected], \
            f"After {expected} presses: expected {SEG7[expected]:07b}, got {segs:07b}"
        dut._log.info(f"PASS: ones digit = {expected}")

@cocotb.test()
async def test_ones_rolls_to_tens(dut):
    """Test that ones rolls over to tens at 10."""
    dut._log.info("Test 3: Ones rolls over to tens at 10")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)

    # Press button 10 times
    for _ in range(10):
        await press_button(dut)

    await ClockCycles(dut.clk, 50)

    # Wait for mux to show dig2 (tens digit)
    for _ in range(2000):
        if get_digit_select(dut) == 0b10:  # dig1=0, dig2=1
            break
        await ClockCycles(dut.clk, 1)

    segs = get_segments(dut)
    assert segs == SEG7[1], \
        f"Expected tens=1 ({SEG7[1]:07b}), got ({segs:07b})"
    dut._log.info("PASS: tens digit = 1 after 10 presses")

@cocotb.test()
async def test_countdown(dut):
    """Test that switch starts countdown and ones decrements."""
    dut._log.info("Test 4: Switch starts countdown")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)

    # Set count to 02 by pressing button twice
    await press_button(dut)
    await press_button(dut)
    await ClockCycles(dut.clk, 50)

    # Enable switch to start countdown
    dut.ui_in.value = 0b00000100  # ui_in[2] = 1

    # Wait one full countdown tick (6,000,000 cycles)
    await ClockCycles(dut.clk, 6_000_010)

    # Wait for mux to show dig1 (ones)
    for _ in range(2000):
        if get_digit_select(dut) == 0b01:
            break
        await ClockCycles(dut.clk, 1)

    segs = get_segments(dut)
    assert segs == SEG7[1], \
        f"Expected ones=1 after countdown tick ({SEG7[1]:07b}), got ({segs:07b})"
    dut._log.info("PASS: ones decremented to 1 after one tick")

    # Stop countdown
    dut.ui_in.value = 0b00000000
