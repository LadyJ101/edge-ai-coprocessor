module mac_pipeline (
    input wire clk,
    input wire rst_n,
    input wire pipeline_en,          
    input wire clear_accum,          
    input wire signed [7:0] feature, 
    input wire signed [7:0] weight, 
    
    output wire signed [31:0] raw_mac_out, 
    output wire signed [31:0] relu_out    
);

    // Internal pipeline interconnect wires
    wire signed [15:0] stage1_product;
    wire signed [31:0] stage2_accum;

    // ---------------------------------------------------------
    // Stage 1: INT8 Multiplier
    // ---------------------------------------------------------
    multiplier u_mult (
        .clk(clk),
        .rst_n(rst_n),
        .enable(pipeline_en),
        .feat_in(feature),
        .wght_in(weight),
        .prod_out(stage1_product)
    );

    // ---------------------------------------------------------
    // Stage 2: 32-bit Accumulator
    // ---------------------------------------------------------
    accumulator u_accum (
        .clk(clk),
        .rst_n(rst_n),
        .enable(pipeline_en),
        .clear(clear_accum),
        .prod_in(stage1_product),
        .acc_out(stage2_accum)
    );

    // ---------------------------------------------------------
    // Post-Processing: ReLU Activation
    // ---------------------------------------------------------
    relu_activation u_relu (
        .data_in(stage2_accum),
        .data_out(relu_out)
    );

    // Continuous assignment for raw MAC output mapping
    assign raw_mac_out = stage2_accum;

endmodule
