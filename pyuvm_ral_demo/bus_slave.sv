module bus_slave (
  input  logic        clk,
  input  logic        rstn,
  input  logic        rd,
  input  logic        wr,
  input  logic [1:0]  addr,
  input  logic [31:0] din,
  output logic [31:0] dout
);

  logic [31:0] regs_array [0:3];

  always_ff @(posedge clk) begin
    if (!rstn)  begin
      dout <= 0;
    end else begin
      if (wr) begin
        regs_array[addr] = din;
      end else if (rd) begin
        dout <= regs_array[addr];
      end
    end
  end
endmodule