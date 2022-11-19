import queue
from cocotb.clock import Clock
import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_fifo(dut):
    
    q1 = queue.Queue()
    
    dut.wr_en.value = 0;
    dut.rd_en.value = 0;
    dut.din.value = 0;
    
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())    
    
    dut.srstn.value = 0
    await Timer(20, units="ns")
    dut.srstn.value = 1
    await Timer(20, units="ns")

    
    
    i=0
    await Timer(5, units="ns")
    while dut.full.value == 0:
        q1.put(i) # this will additem from 0 to 20 to the queue
        dut.din.value = i;
        dut.wr_en.value = 1;
        await Timer(10, units="ns")
        i = i + 1;
        
    dut.wr_en.value = 0;
    
    await Timer(100, units="ns")
    
    golden_dout=0
    
    while dut.empty.value == 0:
        dut.rd_en.value = 1
        golden_dout = q1.get()
        await Timer(10, units="ns")
        print("FIFO Dout Value=",int(dut.dout.value), "Queue Value=",int(golden_dout))
        assert dut.dout.value == golden_dout, "test failed"
        
    dut.rd_en.value = 0

    await Timer(500, units="ns")
    