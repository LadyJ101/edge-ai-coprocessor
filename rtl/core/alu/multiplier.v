module multiplier (
    input wire clk,
    input wire rst_n,                
    input wire enable,               
    input wire signed [7:0] feat_in, 
    input wire signed [7:0] wght_in, 
  output reg signed [15:0] prod_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prod_out <= 16'd0;
        end else if (enable) begin
            prod_out <= feat_in * wght_in;
        end
    end

endmodule
