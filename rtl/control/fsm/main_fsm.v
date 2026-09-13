module main_fsm (
    input wire clk,
    input wire rst_n,
    
    // Interface to UART Packet Parser
    input wire [31:0] rx_packet,
    input wire packet_ready,
    
    // Interface to Address Generator
    input wire mac_done,         // Pulses high when all 432 weights are processed
    output reg addr_gen_en,      // Enables the memory counters
    output reg clear_accum,      // Resets the MAC accumulator
    
    // Interface to MAC Pipeline
    output reg pipeline_en,      // Enables the multiplier and accumulator
    input wire signed [31:0] relu_out, // Final classification result
    
    // Interface to UART TX
    input wire tx_busy,
    output reg tx_start,         // Pulses high to transmit
    output reg [7:0] tx_data     // Data to send to phone
);

    // FSM State Encodings
    localparam STATE_IDLE    = 2'd0;
    localparam STATE_EXECUTE = 2'd1;
    localparam STATE_TX      = 2'd2;

    reg [1:0] current_state, next_state;

    // Command Header (e.g., 0x01 means "Start Inference")
    localparam CMD_START_INFERENCE = 8'h01;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= STATE_IDLE;
        end else begin
            current_state <= next_state;
        end
    end

    always @(*) begin
        // Default assignment to hold state
        next_state = current_state;
        
        case (current_state)
            STATE_IDLE: begin
                // Wait for a valid packet with the "Start" command
                if (packet_ready && rx_packet[31:24] == CMD_START_INFERENCE) begin
                    next_state = STATE_EXECUTE;
                end
            end
            
            STATE_EXECUTE: begin
                // Wait until the address generator finishes the neuron
                if (mac_done) begin
                    next_state = STATE_TX;
                end
            end
            
            STATE_TX: begin
                // Wait for the transmitter to finish sending
                if (!tx_busy) begin
                    next_state = STATE_IDLE;
                end
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
        end else begin
            // Default assignments
            tx_start <= 1'b0;
            
            case (current_state)
                STATE_IDLE: begin
                    addr_gen_en <= 1'b0;
                    pipeline_en <= 1'b0;
                    
                    // Clear accumulator while idle so it is ready for the next run
                    clear_accum <= 1'b1; 
                end
                
                STATE_EXECUTE: begin
                    clear_accum <= 1'b0;
                    addr_gen_en <= 1'b1; // Start counting through memory
                    pipeline_en <= 1'b1; // Turn on the MAC units
                end
                
                STATE_TX: begin
                    addr_gen_en <= 1'b0;
                    pipeline_en <= 1'b0;
                    clear_accum <= 1'b1;
                    
                    // Send a single pulse to start UART transmission
                    // Convert the 32-bit result down to an 8-bit health score
                    if (next_state == STATE_TX && current_state != STATE_TX) begin
                        tx_data  <= (relu_out > 0) ? 8'd1 : 8'd0; // 1 = Healthy, 0 = Diseased
                        tx_start <= 1'b1; 
                    end
                end
            endcase
        end
    end

endmodule
