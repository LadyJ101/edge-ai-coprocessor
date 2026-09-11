// Description: Dual-Port M4K RAM for storing incoming image features

module feature_ram #(
    parameter ADDR_WIDTH = 9,
    parameter DATA_WIDTH = 8
)(
    input wire clk,
    
    // Write Port (Driven by Bluetooth UART Receiver)
    input wire write_en,
    input wire [ADDR_WIDTH-1:0] write_addr,
    input wire signed [DATA_WIDTH-1:0] data_in,
    
    // Read Port (Driven by MAC Pipeline)
    input wire [ADDR_WIDTH-1:0] read_addr,
    output reg signed [DATA_WIDTH-1:0] data_out
);

    reg signed [DATA_WIDTH-1:0] ram_memory [0:(2**ADDR_WIDTH)-1];

    always @(posedge clk) begin
        // Port Write
        if (write_en) begin
            ram_memory[write_addr] <= data_in;
        end
        
        // Port Read
        data_out <= ram_memory[read_addr];
    end

endmodule
