module submod(
    input logic a_clk_in,
    input logic a_data_in,
    output logic a_data_out,

    input logic b_clk_in,
    input logic [7:0] b_data_in,
    output logic [7:0] b_data_out,

    input logic c_clk_in,
    input logic c_data_in,
    output logic c_data_out,
);

    always_ff @(posedge a_clk_in) begin
        a_data_out <= a_data_in;
    end

    always_ff @(posedge b_clk_in) begin
        b_data_out <= b_data_in;
    end

    always_ff @(posedge c_clk_in) begin
        c_data_out <= c_data_in;
    end
endmodule

module sv_test_multiclock(
    input logic areset_in,

    input logic a_clk_in,
    input logic a_data_in,
    output logic a_data_out,

    input logic b_clk_in,
    input logic [7:0] b_data_in,
    output logic [7:0] b_data_out,

    input logic c_data_in,
    output logic c_data_out
);
    logic sub_a_i;
    logic [7:0] sub_b_i;
    logic sub_c_i;

    always_ff @(posedge a_clk_in) begin
        if(areset_in)
            sub_a_i <= 0;
        else
            sub_a_i <= a_data_in;
    end

    always_ff @(posedge b_clk_in) begin
        if(areset_in)
            sub_b_i <= '0;
        else
            sub_b_i <= b_data_in;
    end

    assign sub_c_i = c_data_in;

    submod sub_i(
        .a_clk_in(a_clk_in),
        .a_data_in(sub_a_i),
        .a_data_out(a_data_out),
        .b_clk_in(b_clk_in),
        .b_data_in(sub_b_i),
        .b_data_out(b_data_out),
        .c_clk_in(b_clk_in),
        .c_data_in(sub_c_i),
        .c_data_out(c_data_out),
    );
endmodule
