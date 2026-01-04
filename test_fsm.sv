module test_fsm(
    input  logic        clk_in,
    input  logic        sreset_in,
    input  logic [1:0]  a_in,
    output logic [1:0]  b_out
);

    wire clk_internal;

    assign clk_internal = clk_in;

    // ------------------------------------------------------------
    // State encoding
    // ------------------------------------------------------------
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        S1   = 2'b01,
        S2   = 2'b10,
        S3   = 2'b11
    } state_t;

    state_t state_q, state_d;

    // ------------------------------------------------------------
    // State register (synchronous reset)
    // ------------------------------------------------------------
    always_ff @(posedge clk_internal) begin
        if (sreset_in)
            state_q <= IDLE;
        else
            state_q <= state_d;
    end

    // ------------------------------------------------------------
    // Next-state and output logic (Moore FSM)
    // ------------------------------------------------------------
    always_comb begin
        // Defaults
        state_d = state_q;
        b_out   = 2'b00;

        case (state_q)
            IDLE: begin
                b_out = 2'b00;
                case (a_in)
                    2'b01: state_d = S1;
                    2'b10: state_d = S2;
                    2'b11: state_d = S3;
                    default: state_d = IDLE;
                endcase
            end

            S1: begin
                b_out = 2'b01;
                if (a_in == 2'b00)
                    state_d = IDLE;
            end

            S2: begin
                b_out = 2'b10;
                if (a_in == 2'b00)
                    state_d = IDLE;
            end

            S3: begin
                b_out = 2'b11;
                if (a_in == 2'b00)
                    state_d = IDLE;
            end

            default: begin
                state_d = IDLE;
                b_out   = 2'b00;
            end
        endcase
    end

endmodule
