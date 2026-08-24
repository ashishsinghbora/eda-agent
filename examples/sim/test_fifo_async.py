"""Automated cocotb testbench for fifo_async."""

import random
from collections import deque
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Apply asynchronous reset to both write and read clock domains."""
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.winc.value = 0
    dut.rinc.value = 0
    dut.wdata.value = 0

    await Timer(50, unit="ns")
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await RisingEdge(dut.wclk)
    await RisingEdge(dut.rclk)


@cocotb.test()
async def test_fifo_async_reset(dut):
    """Verify FIFO reset states."""
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 15, unit="ns").start())
    await reset_dut(dut)

    assert dut.wfull.value == 0, f"Expected wfull=0, got {dut.wfull.value}"
    assert dut.rempty.value == 1, f"Expected rempty=1, got {dut.rempty.value}"
    dut._log.info("Reset test passed!")


@cocotb.test()
async def test_fifo_async_fill_to_full(dut):
    """Verify FIFO capacity and full flag assertion."""
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 15, unit="ns").start())
    await reset_dut(dut)

    depth = 16
    for i in range(depth):
        await RisingEdge(dut.wclk)
        dut.wdata.value = i & 0xFF
        dut.winc.value = 1

    await RisingEdge(dut.wclk)
    dut.winc.value = 0
    await RisingEdge(dut.wclk)

    assert dut.wfull.value == 1, f"Expected wfull=1 after writing {depth} elements"
    dut._log.info("Fill to full test passed!")


@cocotb.test()
async def test_fifo_async_concurrent_traffic(dut):
    """Verify randomized concurrent read/write cross-clock traffic."""
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 13, unit="ns").start())
    await reset_dut(dut)

    golden_queue = deque()
    num_items = 50

    async def writer():
        for _ in range(num_items):
            await RisingEdge(dut.wclk)
            while dut.wfull.value == 1:
                dut.winc.value = 0
                await RisingEdge(dut.wclk)

            val = random.randint(0, 255)
            dut.wdata.value = val
            dut.winc.value = 1
            golden_queue.append(val)
            await RisingEdge(dut.wclk)
            dut.winc.value = 0

            if random.random() < 0.3:
                for _ in range(random.randint(1, 2)):
                    await RisingEdge(dut.wclk)
        dut.winc.value = 0

    async def reader():
        received = 0
        while received < num_items:
            await RisingEdge(dut.rclk)
            while dut.rempty.value == 1:
                dut.rinc.value = 0
                await RisingEdge(dut.rclk)

            expected = golden_queue.popleft()
            actual = int(dut.rdata.value)
            assert actual == expected, f"Mismatch at item {received}: expected {expected}, got {actual}"

            dut.rinc.value = 1
            await RisingEdge(dut.rclk)
            dut.rinc.value = 0
            received += 1

            if random.random() < 0.3:
                for _ in range(random.randint(1, 2)):
                    await RisingEdge(dut.rclk)
        dut.rinc.value = 0

    w_task = cocotb.start_soon(writer())
    r_task = cocotb.start_soon(reader())
    await w_task
    await r_task
    dut._log.info("Concurrent cross-clock traffic test passed!")