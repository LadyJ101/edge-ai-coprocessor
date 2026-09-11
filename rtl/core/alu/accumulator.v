module accumulator (
    input wire clk,
    input wire rst_n,
    input wire enable,
    input wire clear,                
    input wire signed [15:0] prod_in,
    output reg signed [31:0] acc_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_out <= 32'd0;
        end else if (clear) begin
            acc_out <= 32'd0;
        end else if (enable) begin
            acc_out <= acc_out + prod_in;
        end
    end

endmodule
