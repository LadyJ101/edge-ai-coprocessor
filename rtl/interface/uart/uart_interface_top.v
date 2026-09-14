module uart_interface_top (
    input wire clk,
    input wire rst_n,
    
    // External Physical Pins (Connects to JP1 on DE2-70)
    input wire rx_pin,
    output wire tx_pin,
    
    // Internal Interface to Top-Level FSM
    output wire [31:0] rx_packet, // 32-bit output instead of 8-bit
    output wire packet_ready,     // Triggers when 32 bits are validated
    
    input wire [7:0] tx_data,     // 8-bit classification result to send back
    input wire tx_start,
    output wire tx_busy
);

    wire [7:0] raw_rx_byte;
    wire raw_rx_ready;

    // Instantiate 8-bit Receiver
    uart_rx u_rx (
        .clk(clk),
        .rst_n(rst_n),
        .rx_serial(rx_pin),
        .rx_byte(raw_rx_byte),
        .rx_done(raw_rx_ready)
    );
    
    // Instantiate 32-bit Packet Parser
    packet_parser u_parser (
        .clk(clk),
        .rst_n(rst_n),
        .rx_byte(raw_rx_byte),
        .rx_ready(raw_rx_ready),
        .valid_packet(rx_packet),
        .packet_ready(packet_ready)
    );
    
    // Instantiate 8-bit Transmitter
    uart_tx u_tx (
        .clk(clk),
        .rst_n(rst_n),
        .tx_byte(tx_data),
        .tx_start(tx_start),
        .tx_serial(tx_pin),
        .tx_active(tx_busy)
    );

endmodule
