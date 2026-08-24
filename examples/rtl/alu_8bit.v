// ==============================================================================
// 8-bit Arithmetic Logic Unit (alu_8bit.v)
// ==============================================================================

`timescale 1ns / 1ps

module alu_8bit #(
    parameter DATA_WIDTH = 8
)(
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire [DATA_WIDTH-1:0] a,
    input  wire [DATA_WIDTH-1:0] b,
    input  wire [2:0]            opcode,
    output reg  [DATA_WIDTH-1:0] result,
    output reg                   zero,
    output reg                   carry,
    output reg                   overflow
);

    localparam OP_ADD = 3'b000;
    localparam OP_SUB = 3'b001;
    localparam OP_AND = 3'b010;
    localparam OP_OR  = 3'b011;
    localparam OP_XOR = 3'b100;
    localparam OP_SHL = 3'b101;
    localparam OP_SHR = 3'b110;
    localparam OP_NOT = 3'b111;

    reg [DATA_WIDTH:0] ext_result;

    always @(*) begin
        case (opcode)
            OP_ADD: ext_result = {1'b0, a} + {1'b0, b};
            OP_SUB: ext_result = {1'b0, a} - {1'b0, b};
            OP_AND: ext_result = {1'b0, a & b};
            OP_OR:  ext_result = {1'b0, a | b};
            OP_XOR: ext_result = {1'b0, a ^ b};
            OP_SHL: ext_result = {1'b0, a << b[2:0]};
            OP_SHR: ext_result = {1'b0, a >> b[2:0]};
            OP_NOT: ext_result = {1'b0, ~a};
            default: ext_result = {(DATA_WIDTH+1){1'b0}};
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result   <= {DATA_WIDTH{1'b0}};
            zero     <= 1'b0;
            carry    <= 1'b0;
            overflow <= 1'b0;
        end else begin
            result   <= ext_result[DATA_WIDTH-1:0];
            zero     <= (ext_result[DATA_WIDTH-1:0] == {DATA_WIDTH{1'b0}});
            carry    <= (opcode == OP_ADD || opcode == OP_SUB) ? ext_result[DATA_WIDTH] : 1'b0;
            overflow <= (opcode == OP_ADD) ? ((a[7] == b[7]) && (ext_result[7] != a[7])) :
                        (opcode == OP_SUB) ? ((a[7] != b[7]) && (ext_result[7] != a[7])) : 1'b0;
        end
    end

endmodule
