module second_level (
    input logic clk_in,
    input logic a_in,
    output logic b_out
);
    always_ff @(posedge clk_in) begin
        b_out <= a_in;
    end
endmodule

module counter_8bit (
    input logic clk_in,
    input logic en_in,
    output logic [7:0] count_out
);
    logic en_d1;

    second_level s_i (
        .clk_in(clk_in),
        .a_in(en_in),
        .b_out(en_d1)
    );

    always_ff @(posedge clk_in) begin
        if (en_d1)
            count_out <= count_out + 8'd1;
    end

endmodule