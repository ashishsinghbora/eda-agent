module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build_fifo_async/fifo_async.fst");
    $dumpvars(0, fifo_async);
end
endmodule
