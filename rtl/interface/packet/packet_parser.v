module packet_parser (
    input wire clk,
    input wire rst_n,
    input wire [7:0] rx_byte,
    input wire rx_ready,          // Pulses high when UART RX has a new byte
    
    output reg [31:0] valid_packet,
    output reg packet_ready       // Pulses high when a full 32-bit frame is verified
);

    localparam HEADER_BYTE = 8'hAA; // Start of Frame marker

    reg [1:0] byte_count;
    reg [23:0] shift_reg;         // Holds the first 3 bytes while waiting for checksum

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            byte_count <= 2'd0;
            shift_reg <= 24'd0;
            valid_packet <= 32'd0;
            packet_ready <= 1'b0;
        end else begin
            packet_ready <= 1'b0; // Default to 0

            if (rx_ready) begin
                case (byte_count)
                    2'd0: begin
                        if (rx_byte == HEADER_BYTE) begin
                            shift_reg[23:16] <= rx_byte;
                            byte_count <= 2'd1;
                        end
                    end
                    2'd1: begin
                        shift_reg[15:8] <= rx_byte;
                        byte_count <= 2'd2;
                    end
                    2'd2: begin
                        shift_reg[7:0] <= rx_byte;
                        byte_count <= 2'd3;
                    end
                    2'd3: begin
                        // Validate XOR Checksum: Header ^ Data1 ^ Data2 == Checksum
                        if ((shift_reg[23:16] ^ shift_reg[15:8] ^ shift_reg[7:0]) == rx_byte) begin
                            valid_packet <= {shift_reg, rx_byte};
                            packet_ready <= 1'b1; // Signal main FSM that data is safe to use
                        end
                        byte_count <= 2'd0; // Reset for the next packet
                    end
                endcase
            end
        end
    end

endmodule
