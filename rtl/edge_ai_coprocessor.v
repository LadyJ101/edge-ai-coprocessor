module edge_ai_coprocessor (
    input wire CLOCK_50,  // 50 MHz On-board Oscillator
    input wire [0:0] KEY, // Pushbutton [0] used as active-low reset
    
    // UART Interface (Connects to JP1 GPIO Expansion)
    input wire UART_RXD,  // PIN_D25
    output wire UART_TXD  // PIN_E25
);

    // Global Signals
    wire clk = CLOCK_50;
    wire rst_n = KEY[0];

    // UART <-> FSM Signals
    wire [31:0] rx_packet;
    wire packet_ready;
    wire [7:0] tx_data;
    wire tx_start;
    wire tx_busy;

    // FSM <-> Memory Control Signals
    wire addr_gen_en;
    wire clear_accum;
    wire mac_done;
    wire pipeline_en;

    // Memory Data Signals
    wire [8:0] current_addr;
    wire signed [7:0] current_feature;
    wire signed [7:0] current_weight;
    wire signed [31:0] final_relu_out;

    // Feature RAM Write Signals
    wire ram_write_en;
    wire [8:0] ram_write_addr;
    wire signed [7:0] ram_write_data;
  
    // --- INTERFACE SUBSYSTEM ---
    uart_interface_top u_uart (
        .clk(clk),
        .rst_n(rst_n),
        .rx_pin(UART_RXD),
        .tx_pin(UART_TXD),
        .rx_packet(rx_packet),
        .packet_ready(packet_ready),
        .tx_data(tx_data),
        .tx_start(tx_start),
        .tx_busy(tx_busy)
    );

    // --- CONTROL SUBSYSTEM ---
    main_fsm u_fsm (
        .clk(clk),
        .rst_n(rst_n),
        .rx_packet(rx_packet),
        .packet_ready(packet_ready),
        .mac_done(mac_done),
        .addr_gen_en(addr_gen_en),
        .clear_accum(clear_accum),
        .pipeline_en(pipeline_en),
        .relu_out(final_relu_out),
        .tx_busy(tx_busy),
        .tx_start(tx_start),
        .tx_data(tx_data)
        .ram_write_en(ram_write_en),
        .ram_write_addr(ram_write_addr),
        .ram_write_data(ram_write_data)
    );

    // --- MEMORY SUBSYSTEM ---
    address_generator #(
        .ADDR_WIDTH(9),
        .VECTOR_SIZE(432)
    ) u_addr_gen (
        .clk(clk),
        .rst_n(rst_n),
        .enable(addr_gen_en),
        .clear(clear_accum),
        .current_addr(current_addr),
        .done_flag(mac_done)
    );

    weight_rom #(
        .ADDR_WIDTH(9),
        .DATA_WIDTH(8),
        .MIF_FILE("conv1_weights.mif")
    ) u_weights (
        .clk(clk),
        .read_addr(current_addr),
        .data_out(current_weight)
    );

    feature_ram #(
        .ADDR_WIDTH(9),
        .DATA_WIDTH(8)
    ) u_features (
        .clk(clk),
        .write_en(ram_write_en),
        .write_addr(ram_write_addr),
        .data_in(ram_write_data),
        .read_addr(current_addr),
        .data_out(current_feature)
    );

    // --- CORE DATAPATH (ALU) ---
    pipeline u_mac_pipeline (
        .clk(clk),
        .rst_n(rst_n),
        .enable(pipeline_en),
        .clear(clear_accum),
        .feature(current_feature),
        .weight(current_weight),
        .final_out(final_relu_out)
    );

endmodule
