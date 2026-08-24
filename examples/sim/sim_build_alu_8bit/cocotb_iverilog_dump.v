module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build_alu_8bit/alu_8bit.fst");
    $dumpvars(0, alu_8bit);
end
endmodule
