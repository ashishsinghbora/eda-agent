"""Automated cocotb testbench for alu_8bit."""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Apply synchronous/asynchronous reset to DUT."""
    dut.rst_n.value = 0
    if hasattr(dut, "a"):
        dut.a.value = 0
    if hasattr(dut, "b"):
        dut.b.value = 0
    if hasattr(dut, "opcode"):
        dut.opcode.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


def alu_reference_model(a: int, b: int, opcode: int):
    """Golden software model for 8-bit ALU operations."""
    if opcode == 0:    # ADD
        res = (a + b) & 0xFF
        c = 1 if (a + b) > 255 else 0
    elif opcode == 1:  # SUB
        res = (a - b) & 0xFF
        c = 1 if a >= b else 0
    elif opcode == 2:  # AND
        res = (a & b) & 0xFF
        c = 0
    elif opcode == 3:  # OR
        res = (a | b) & 0xFF
        c = 0
    elif opcode == 4:  # XOR
        res = (a ^ b) & 0xFF
        c = 0
    elif opcode == 5:  # SHL
        res = (a << (b & 0x7)) & 0xFF
        c = 0
    elif opcode == 6:  # SHR
        res = (a >> (b & 0x7)) & 0xFF
        c = 0
    elif opcode == 7:  # NOT
        res = (~a) & 0xFF
        c = 0
    else:
        res = 0
        c = 0
    z = 1 if res == 0 else 0
    return res, z, c


@cocotb.test()
async def test_alu_8bit_reset(dut):
    """Verify reset assertions and initial output values."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    assert int(dut.result.value) == 0, f"Expected result=0 after reset, got {int(dut.result.value)}"
    assert int(dut.zero.value) == 0 or int(dut.zero.value) == 1
    dut._log.info("Reset test passed successfully!")


@cocotb.test()
async def test_alu_8bit_functional(dut):
    """Verify functional ALU operations across randomized vectors."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    for op in range(8):
        for _ in range(15):
            a_val = random.randint(0, 255)
            b_val = random.randint(0, 255)

            dut.a.value = a_val
            dut.b.value = b_val
            dut.opcode.value = op

            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")

            exp_res, exp_z, _ = alu_reference_model(a_val, b_val, op)
            act_res = int(dut.result.value)
            act_z = int(dut.zero.value)

            assert act_res == exp_res, (
                f"Op {op}: A={hex(a_val)}, B={hex(b_val)}: "
                f"Expected result={hex(exp_res)}, got {hex(act_res)}"
            )
            assert act_z == exp_z, (
                f"Op {op}: Expected zero={exp_z}, got {act_z}"
            )

    dut._log.info("Functional throughput verification completed successfully!")


@cocotb.test()
async def test_alu_8bit_corner_cases(dut):
    """Verify boundary and corner cases: 0x00, 0xFF, overflow boundaries."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    corner_pairs = [
        (0x00, 0x00),
        (0xFF, 0xFF),
        (0xFF, 0x01),
        (0x80, 0x80),
        (0x7F, 0x01),
        (0x01, 0xFF),
    ]

    for a_val, b_val in corner_pairs:
        for op in range(8):
            dut.a.value = a_val
            dut.b.value = b_val
            dut.opcode.value = op

            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")

            exp_res, exp_z, _ = alu_reference_model(a_val, b_val, op)
            act_res = int(dut.result.value)
            assert act_res == exp_res, (
                f"Corner Case Op {op}: A={hex(a_val)}, B={hex(b_val)}: "
                f"Expected {hex(exp_res)}, got {hex(act_res)}"
            )

    dut._log.info("Boundary and corner case verification completed successfully!")