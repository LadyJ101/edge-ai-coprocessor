// Description: M4K ROM for INT8 Model Weights initialized via .mif

module weight_rom #(
    parameter ADDR_WIDTH = 9,                
    parameter DATA_WIDTH = 8,               
    parameter MIF_FILE = "conv1_weights.mif" 
)(
    input wire clk,
    input wire [ADDR_WIDTH-1:0] read_addr,
    output reg signed [DATA_WIDTH-1:0] data_out
);

    (* ram_init_file = MIF_FILE *) reg signed [DATA_WIDTH-1:0] rom_memory [0:(2**ADDR_WIDTH)-1];

    always @(posedge clk) begin
        data_out <= rom_memory[read_addr];
    end

endmodule
