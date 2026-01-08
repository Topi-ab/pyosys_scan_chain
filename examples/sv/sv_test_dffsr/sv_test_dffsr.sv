module sv_test_dffsr(
    input logic clk_in,
    input logic set_in,
    input logic clr_in,
    input logic a_in,
    output logic a_out,
    input logic[1:0] b_in,
    output logic[1:0] b_out
);
    always_ff @(posedge clk_in, posedge set_in, posedge clr_in) begin
        // $dffsr - SET_POLARITY = 0, CLR_POLARITY = 0
        if (set_in) begin
            a_out <= '1;
            b_out <= '1;
        end else if (clr_in) begin
            a_out <= '0;
            b_out <= '0;
        end else begin
            a_out <= a_in;
            b_out <= b_in;
        end
    end
endmodule
