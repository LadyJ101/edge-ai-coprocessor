module uart_tx #(
    parameter CLKS_PER_BIT = 434 // 50 MHz / 115200 Baud = ~434
)(
    input wire clk,
    input wire rst_n,
    input wire [7:0] tx_byte,    // The 8-bit data to send (e.g., inference result)
    input wire tx_start,         // Pulse high to start transmitting
    
    output reg tx_serial,        // Outgoing serial line to Bluetooth
    output reg tx_active         // High while transmitting
);

    localparam IDLE  = 3'b000;
    localparam START = 3'b001;
    localparam DATA  = 3'b010;
    localparam STOP  = 3'b011;

    reg [2:0] state;
    reg [8:0] clock_count;
    reg [2:0] bit_index;
    reg [7:0] tx_data_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            tx_serial <= 1'b1; // Line idles high
            tx_active <= 1'b0;
            clock_count <= 0;
            bit_index <= 0;
            tx_data_reg <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx_serial <= 1'b1;
                    tx_active <= 1'b0;
                    clock_count <= 0;
                    bit_index <= 0;
                    
                    if (tx_start) begin
                        tx_data_reg <= tx_byte; // Lock in the data
                        tx_active <= 1'b1;
                        tx_serial <= 1'b0; // Send start bit (line goes low)
                        state <= START;
                    end
                end
                
                START: begin
                    if (clock_count < CLKS_PER_BIT - 1) begin
                        clock_count <= clock_count + 1'b1;
                    end else begin
                        clock_count <= 0;
                        tx_serial <= tx_data_reg[0]; // Send LSB first
                        state <= DATA;
                    end
                end
                
                DATA: begin
                    if (clock_count < CLKS_PER_BIT - 1) begin
                        clock_count <= clock_count + 1'b1;
                    end else begin
                        clock_count <= 0;
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1'b1;
                            tx_serial <= tx_data_reg[bit_index + 1'b1];
                        end else begin
                            bit_index <= 0;
                            tx_serial <= 1'b1; // Send stop bit (line goes high)
                            state <= STOP;
                        end
                    end
                end
                
                STOP: begin
                    if (clock_count < CLKS_PER_BIT - 1) begin
                        clock_count <= clock_count + 1'b1;
                    end else begin
                        tx_active <= 1'b0;
                        state <= IDLE;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule
