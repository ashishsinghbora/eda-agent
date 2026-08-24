// ==============================================================================
// Dual-Clock Asynchronous FIFO (fifo_async.v)
// ==============================================================================
// Parameters:
//   DATA_WIDTH : Width of data bus (default 8)
//   ADDR_WIDTH : Address bit width, Depth = 2^ADDR_WIDTH (default 4 -> Depth = 16)
// ==============================================================================

`timescale 1ns / 1ps

module fifo_async #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4
)(
    // Write Domain
    input  wire                  wclk,
    input  wire                  wrst_n,
    input  wire                  winc,
    input  wire [DATA_WIDTH-1:0] wdata,
    output reg                   wfull,

    // Read Domain
    input  wire                  rclk,
    input  wire                  rrst_n,
    input  wire                  rinc,
    output wire [DATA_WIDTH-1:0] rdata,
    output reg                   rempty
);

    localparam DEPTH = 1 << ADDR_WIDTH;

    // Memory array
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // Pointers & Gray codes
    reg [ADDR_WIDTH:0] wbin, rbin;
    reg [ADDR_WIDTH:0] wptr, rptr;
    reg [ADDR_WIDTH:0] wq1_rptr, wq2_rptr;
    reg [ADDR_WIDTH:0] rq1_wptr, rq2_wptr;

    wire [ADDR_WIDTH:0] wbin_next, rbin_next;
    wire [ADDR_WIDTH:0] wgray_next, rgray_next;
    wire wfull_val, rempty_val;

    // --------------------------------------------------------------------------
    // Write Domain Logic
    // --------------------------------------------------------------------------
    assign wbin_next  = wbin + (winc & ~wfull);
    assign wgray_next = (wbin_next >> 1) ^ wbin_next;

    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wbin  <= {(ADDR_WIDTH+1){1'b0}};
            wptr  <= {(ADDR_WIDTH+1){1'b0}};
            wfull <= 1'b0;
        end else begin
            wbin  <= wbin_next;
            wptr  <= wgray_next;
            wfull <= wfull_val;
        end
    end

    // Memory write
    always @(posedge wclk) begin
        if (winc && !wfull) begin
            mem[wbin[ADDR_WIDTH-1:0]] <= wdata;
        end
    end

    // 2FF Synchronizer: Read pointer into Write domain
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wq1_rptr <= {(ADDR_WIDTH+1){1'b0}};
            wq2_rptr <= {(ADDR_WIDTH+1){1'b0}};
        end else begin
            wq1_rptr <= rptr;
            wq2_rptr <= wq1_rptr;
        end
    end

    // Full condition: MSB and MSB-1 inverted, rest equal
    assign wfull_val = (wgray_next == {~wq2_rptr[ADDR_WIDTH:ADDR_WIDTH-1], wq2_rptr[ADDR_WIDTH-2:0]});

    // --------------------------------------------------------------------------
    // Read Domain Logic
    // --------------------------------------------------------------------------
    assign rbin_next  = rbin + (rinc & ~rempty);
    assign rgray_next = (rbin_next >> 1) ^ rbin_next;

    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rbin   <= {(ADDR_WIDTH+1){1'b0}};
            rptr   <= {(ADDR_WIDTH+1){1'b0}};
            rempty <= 1'b1;
        end else begin
            rbin   <= rbin_next;
            rptr   <= rgray_next;
            rempty <= rempty_val;
        end
    end

    // Memory read
    assign rdata = mem[rbin[ADDR_WIDTH-1:0]];

    // 2FF Synchronizer: Write pointer into Read domain
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rq1_wptr <= {(ADDR_WIDTH+1){1'b0}};
            rq2_wptr <= {(ADDR_WIDTH+1){1'b0}};
        end else begin
            rq1_wptr <= wptr;
            rq2_wptr <= rq1_wptr;
        end
    end

    // Empty condition: Read Gray code equals synchronized Write Gray code
    assign rempty_val = (rgray_next == rq2_wptr);

endmodule
