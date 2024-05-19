from pyuvm import uvm_reg, uvm_reg_field, uvm_reg_map
from pyuvm import uvm_reg_block
from pyuvm import uvm_agent
from pyuvm import uvm_sequence_item
from pyuvm import uvm_test
from pyuvm import uvm_reg_adapter
from pyuvm import uvm_reg_bus_op
from pyuvm.s24_uvm_reg_includes import access_e, status_t
from pyuvm.s24_uvm_reg_includes import path_t, check_t
from pyuvm import uvm_driver
from pyuvm import uvm_env, uvm_sequencer
from pyuvm import uvm_analysis_port
from pyuvm import ConfigDB
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
import cocotb
import pyuvm


class REG0(uvm_reg):
  def __init__(self, name="REG0", reg_width=32):
    super().__init__(name, reg_width)
    self.f0 = uvm_reg_field('f0')
  def build(self):
    self.f0.configure(self, 32, 0, 'RW', 0, 0)
    self._set_lock()

class REG1(uvm_reg):
  def __init__(self, name="REG1", reg_width=32):
    super().__init__(name, reg_width)
    self.f1 = uvm_reg_field('f1')
  def build(self):
    self.f1.configure(self, 32, 0, 'RW', 0, 0)
    self._set_lock()

class REG2(uvm_reg):
  def __init__(self, name="REG2", reg_width=32):
    super().__init__(name, reg_width)
    self.f2 = uvm_reg_field('f2')
  def build(self):
    self.f2.configure(self, 32, 0, 'RW', 0, 0)
    self._set_lock()

class REG3(uvm_reg):
  def __init__(self, name="REG3", reg_width=32):
    super().__init__(name, reg_width)
    self.f3 = uvm_reg_field('f3')
  def build(self):
    self.f3.configure(self, 32, 0, 'RW', 0, 0)
    self._set_lock()

class reg_block(uvm_reg_block):
  def __init__(self, name="reg_block"):
    super().__init__(name)
    self.def_map = uvm_reg_map('map')
    self.def_map.configure(self, 0)

    # reg0
    self.reg0 = REG0('reg0')
    self.reg0.configure(self, "0x0", "", False, False)
    self.def_map.add_reg(self.reg0, "0x0", "RW")
    # reg1
    self.reg1 = REG1('reg1')
    self.reg1.configure(self, "0x1", "", False, False)
    self.def_map.add_reg(self.reg1, "0x0", "RW")
    # reg2
    self.reg2 = REG2('reg2')
    self.reg2.configure(self, "0x2", "", False, False)
    self.def_map.add_reg(self.reg2, "0x0", "RW")
    # reg3
    self.reg3 = REG3('reg3')
    self.reg3.configure(self, "0x3", "", False, False)
    self.def_map.add_reg(self.reg3, "0x0", "RW")


# ADAPATER
class bus_adapter(uvm_reg_adapter):
  def __init__(self, name="bus_adapter"):
    super().__init__(name)
  def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
    item = simple_bus_item("item")
    if (rw.kind == access_e.UVM_READ):
      item.rd = 1
      item.rdata = rw.data
    else:
      item.rd = 0
      item.wdata = rw.data
    item.addr = rw.addr
    return item
  def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op):
    if bus_item.rd == 1:
      rw.kind = access_e.UVM_READ
      rw.data = bus_item.rdata
    else:
      rw.data = bus_item.wdata
      rw.kind = access_e.UVM_WRITE
    rw.addr = bus_item.addr

# SEQUENCE ITEM
class simple_bus_item(uvm_sequence_item):
  def __init__(self, name):
    super().__init__(name)
    self.rdata: int = 0
    self.rd: int = 0
    self.addr: int = 0
    self.wdata: int = 0

# DRIVER
class Driver(uvm_driver):
  def build_phase(self):
    self.ap = uvm_analysis_port("ap", self)
  def start_of_simulation_phase(self):
    self.dut = cocotb.top
  async def run_phase(self):
    self.reset()
    while True:
      cmd = await self.seq_item_port.get_next_item()
      if (cmd.rd == 0):
        await self.write_reg(int(cmd.addr, 16), cmd.wdata)
      else:
        read_data = await self.read_reg(int(cmd.addr, 16))
        cmd.rdata = read_data
      self.seq_item_port.item_done()
  
  async def reset(self):
    self.dut.rstn.value = 0
    self.dut.wr.value = 0
    self.dut.rd.value = 0
    await FallingEdge(self.dut.clk)
    await FallingEdge(self.dut.clk)
    self.dut.rstn.value = 1
    await FallingEdge(self.dut.clk)
    await FallingEdge(self.dut.clk)

  async def write_reg(self, addr: int, din: int):
    await FallingEdge(self.dut.clk)
    self.dut.din.value = din
    self.dut.wr.value = 1
    self.dut.addr.value = addr
    await FallingEdge(self.dut.clk)
    self.dut.wr.value = 0

  async def read_reg(self, addr: int):
    await FallingEdge(self.dut.clk)
    self.dut.rd.value = 1
    self.dut.addr.value = addr
    await FallingEdge(self.dut.clk)
    self.dut.rd.value = 0
    return self.dut.dout.value

#AGENT
class Agent(uvm_agent):
  def build_phase(self):
    self.seqr = uvm_sequencer("seqr", self)
    self.drv = Driver.create("drv", self)
  def connect_phase(self):
    self.drv.seq_item_port.connect(self.seqr.seq_item_export)

# ENVIRONMENT
class Env(uvm_env):
  def build_phase(self):
    self.agt         = Agent.create("agt", self)
    self.reg_adapter = bus_adapter("reg_adapter")
    self.reg_block   = reg_block("reg_block")
  def connect_phase(self):
    self.reg_block.def_map.set_sequencer(self.agt.seqr)
    self.reg_block.def_map.set_adapter(self.reg_adapter)

@pyuvm.test()
class RegModelTest(uvm_test):
  def build_phase(self):
    self.env = Env("env", self)

  async def run_phase(self):
    self.raise_objection()

    clock = Clock(cocotb.top.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    status = await self.env.reg_block.reg0.write(15,self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    (status, rdata) = await self.env.reg_block.reg0.read(self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    self.logger.info(f"reg model rdata: {int(rdata)} @addr: {self.env.reg_block.reg0.get_address()}")

    status = await self.env.reg_block.reg1.write(25,self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    (status, rdata) = await self.env.reg_block.reg1.read(self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    self.logger.info(f"reg model rdata: {int(rdata)} @addr: {self.env.reg_block.reg1.get_address()}")

    status = await self.env.reg_block.reg2.write(35,self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    (status, rdata) = await self.env.reg_block.reg2.read(self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    self.logger.info(f"reg model rdata: {int(rdata)} @addr: {self.env.reg_block.reg2.get_address()}")

    status = await self.env.reg_block.reg3.write(45,self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    (status, rdata) = await self.env.reg_block.reg3.read(self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    self.logger.info(f"reg model rdata: {int(rdata)} @addr: {self.env.reg_block.reg3.get_address()}")

    (status, rdata) = await self.env.reg_block.reg1.read(self.env.reg_block.def_map,path_t.FRONTDOOR,check_t.NO_CHECK)
    self.logger.info(f"reg model rdata: {int(rdata)} @addr: {self.env.reg_block.reg1.get_address()}")

    self.drop_objection()
