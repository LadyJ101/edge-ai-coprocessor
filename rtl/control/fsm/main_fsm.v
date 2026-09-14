module main_fsm (
    input wire clk,
    input wire rst_n,
    
    // Interface to UART Packet Parser
    input wire [31:0] rx_packet,
    input wire packet_ready,
    
    // Interface to Address Generator
    input wire mac_done,         
    output reg addr_gen_en,      
    output reg clear_accum,      
    
    // Interface to MAC Pipeline
    output reg pipeline_en,      
    input wire signed [31:0] relu_out, 
    
    // Interface to UART TX
    input wire tx_busy,
    output reg tx_start,         
    output reg [7:0] tx_data,    
    
    // Interface to Feature RAM (Write Port) - 10 Bits for 864 Features
    output reg ram_write_en,
    output reg [9:0] ram_write_addr,
    output reg signed [7:0] ram_write_data
);

    // FSM State Encodings
    localparam STATE_IDLE    = 3'd0;
    localparam STATE_LOAD_1  = 3'd1;
    localparam STATE_LOAD_2  = 3'd2;
    localparam STATE_EXECUTE = 3'd3;
    localparam STATE_TX      = 3'd4;

    reg [2:0] current_state, next_state;

    // Command Headers
    localparam CMD_START_INFERENCE = 8'h01;
    localparam CMD_LOAD_FEATURE    = 8'h02;

    // Internal Registers for RAM Loading
    reg [9:0] next_ram_addr; // Keeps track of where we are in memory (10 bits)
    reg [7:0] latched_feature_2; // Holds the 2nd feature while the 1st is saving


    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= STATE_IDLE;
            ram_write_addr <= 10'd0; // UPDATED to 10 bits
            latched_feature_2 <= 8'd0;
        end else begin
            current_state <= next_state;
            
            // Address tracking logic
            if (current_state == STATE_TX) begin
                // Reset RAM address pointer when inference finishes
                // so the next image starts loading at address 0
                ram_write_addr <= 10'd0; // UPDATED to 10 bits
            end else if (current_state == STATE_LOAD_1 || current_state == STATE_LOAD_2) begin
                // Move to the next memory slot after every write
                ram_write_addr <= next_ram_addr;
            end
            
            // Latch the second feature so we don't lose it when packet_ready drops
            if (packet_ready && rx_packet[31:24] == CMD_LOAD_FEATURE) begin
                latched_feature_2 <= rx_packet[15:8];
            end
        end
    end

    always @(*) begin
        next_state = current_state;
        next_ram_addr = ram_write_addr;
        
        case (current_state)
            STATE_IDLE: begin
                if (packet_ready) begin
                    if (rx_packet[31:24] == CMD_LOAD_FEATURE) begin
                        next_state = STATE_LOAD_1;
                    end else if (rx_packet[31:24] == CMD_START_INFERENCE) begin
                        next_state = STATE_EXECUTE;
                    end
                end
            end
            
            STATE_LOAD_1: begin
                next_ram_addr = ram_write_addr + 1'b1;
                next_state = STATE_LOAD_2;
            end
            
            STATE_LOAD_2: begin
                next_ram_addr = ram_write_addr + 1'b1;
                next_state = STATE_IDLE;
            end
            
            STATE_EXECUTE: begin
                if (mac_done) next_state = STATE_TX;
            end
            
            STATE_TX: begin
                if (!tx_busy) next_state = STATE_IDLE;
            end
            
            default: next_state = STATE_IDLE;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            addr_gen_en <= 1'b0;
            clear_accum <= 1'b1;
            pipeline_en <= 1'b0;
            tx_start    <= 1'b0;
            tx_data     <= 8'd0;
            ram_write_en <= 1'b0;
            ram_write_data <= 8'd0;
        end else begin
            // Default pulse assignments
            tx_start <= 1'b0;
            ram_write_en <= 1'b0;
            
            case (current_state)
                STATE_IDLE: begin
                    addr_gen_en <= 1'b0;
                    pipeline_en <= 1'b0;
                    clear_accum <= 1'b1; 
                end
                
                STATE_LOAD_1: begin
                    // Write Feature 1 (from rx_packet[23:16])
                    ram_write_en <= 1'b1;
                    ram_write_data <= rx_packet[23:16]; 
                end
                
                STATE_LOAD_2: begin
                    // Write Feature 2 (from the latch)
                    ram_write_en <= 1'b1;
                    ram_write_data <= latched_feature_2; 
                end
                
                STATE_EXECUTE: begin
                    clear_accum <= 1'b0;
                    addr_gen_en <= 1'b1; 
                    pipeline_en <= 1'b1; 
                end
                
                STATE_TX: begin
                    addr_gen_en <= 1'b0;
                    pipeline_en <= 1'b0;
                    clear_accum <= 1'b1;
                    
                    if (next_state == STATE_TX && current_state != STATE_TX) begin
                        tx_data  <= (relu_out > 0) ? 8'd1 : 8'd0; 
                        tx_start <= 1'b1; 
                    end
                end
            endcase
        end
    end

endmodule
