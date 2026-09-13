module uart_rx #(
    parameter CLKS_PER_BIT = 434 // 50 MHz / 115200 Baud = ~434
)(
    input wire clk,
    input wire rst_n,
    input wire rx_serial,        // Incoming serial line from Bluetooth
    
    output reg [7:0] rx_byte,    // 8-bit parallel output
    output reg rx_done           // Pulses high for 1 clock cycle when byte is ready
);

    // FSM States
    localparam IDLE  = 3'b000;
    localparam START = 3'b001;
    localparam DATA  = 3'b010;
    localparam STOP  = 3'b011;

    reg [2:0] state;
    reg [8:0] clock_count;
    reg [2:0] bit_index;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            rx_done <= 1'b0;
            rx_byte <= 8'd0;
            clock_count <= 0;
            bit_index <= 0;
        end else begin
            rx_done <= 1'b0; // Default to 0

            case (state)
                IDLE: begin
                    clock_count <= 0;
                    bit_index <= 0;
                    if (rx_serial == 1'b0) begin // Start bit detected (line pulled low)
                        state <= START;
                    end
                end
                
                START: begin
                    if (clock_count == (CLKS_PER_BIT / 2)) begin
                        if (rx_serial == 1'b0) begin
                            clock_count <= 0;
                            state <= DATA;
                        end else begin
                            state <= IDLE; // False alarm
                        end
                    end else begin
                        clock_count <= clock_count + 1'b1;
                    end
                end
                
                DATA: begin
                    if (clock_count < CLKS_PER_BIT - 1) begin
                        clock_count <= clock_count + 1'b1;
                    end else begin
                        clock_count <= 0;
                        rx_byte[bit_index] <= rx_serial;
                        
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1'b1;
                        end else begin
                            bit_index <= 0;
                            state <= STOP;
                        end
                    end
                end
                
                STOP: begin
                    if (clock_count < CLKS_PER_BIT - 1) begin
                        clock_count <= clock_count + 1'b1;
                    end else begin
                        rx_done <= 1'b1; // Pulse done flag
                        clock_count <= 0;
                        state <= IDLE;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule
