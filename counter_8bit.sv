module second_level(
    input logic clk_in,
    input logic a_in,
    output logic b_out
);
    always_ff @(posedge clk_in) begin
        b_out <= a_in;
    end
endmodule

module counter_8bit(
    input logic clk_in,
    input logic sreset_in,
    input logic en_in,
    output logic [7:0] count_out,
    output logic [7:0] c2_out,
    output logic [7:0] c3_out,
    output logic c4,
    output logic [7:0] c5,
    output logic c6,
    output logic [7:0] c7
);
    logic en_d1;

    second_level s_i(
        .clk_in(clk_in),
        .a_in(en_in),
        .b_out(en_d1)
    );

    always_ff @(posedge clk_in) begin
        if(en_d1)
            count_out <= count_out + 8'd1;
        
        if(sreset_in)
            count_out <= '0;
    end

    always_ff @(posedge clk_in) begin
        // $dffe - EN_POLARITY = 1
        if (en_d1)
            c2_out <= count_out;
        else
            c2_out <= c2_out;

        // $dffe - EN_POLARITY = 0
        if (~en_d1)
            c3_out <= count_out;
    end

    always_ff @(posedge clk_in, posedge en_in, posedge en_d1) begin
        // $dffsr - SET_POLARITY = 0, CLR_POLARITY = 0
        if (en_in) begin
            c4 <= '1;
            c5 <= '1;
        end else if (en_d1) begin
            c4 <= '0;
            c5 <= '0;
        end else begin
            c4 <= c_out[0];
            c5 <= c_out;
        end
    end

    always_ff @(posedge clk_in, negedge en_in, negedge en_d1) begin
        // $dffsr - SET_POLARITY = 0, CLR_POLARITY = 0
        if (~en_in) begin
            c6 <= '1;
            c7 <= '1;
        end else if (~en_d1) begin
            c6 <= '0;
            c7 <= '0;
        end else begin
            c6 <= c_out[0];
            c7 <= c_out;
        end
    end
endmodule
