// Description: Counter to generate read addresses for ROM and RAM

module address_generator #(
    parameter ADDR_WIDTH = 9,
    parameter VECTOR_SIZE = 432 
)(
    input wire clk,
    input wire rst_n,
    input wire enable,           
    input wire clear,            
    
    output reg [ADDR_WIDTH-1:0] current_addr,
    output reg done_flag         
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_addr <= {ADDR_WIDTH{1'b0}};
            done_flag <= 1'b0;
        end else if (clear) begin
            current_addr <= {ADDR_WIDTH{1'b0}};
            done_flag <= 1'b0;
        end else if (enable) begin
            if (current_addr == VECTOR_SIZE - 1) begin
                done_flag <= 1'b1;
            end else begin
                current_addr <= current_addr + 1'b1;
                done_flag <= 1'b0;
            end
        end
    end

endmodule
