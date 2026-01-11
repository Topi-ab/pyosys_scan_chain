module sv_scan_executor #(
    parameter int unsigned NUM_CHAINS = 1,


    parameter int SCAN_CHAIN_LEN [NUM_CHAINS]   = '{default: 792},


    parameter int DATA_BITS = 16
) (
    input  logic clk_in,
    input  logic sreset_in,

    output logic execute_ready_out,
    input  logic execute_valid_in,

    output logic scan_enable_out,
    output logic [NUM_CHAINS-1:0] scan_clk_en_out,
    input  logic [NUM_CHAINS-1:0] from_chain_in,
    output logic [NUM_CHAINS-1:0] to_chain_out,

    input  logic [NUM_CHAINS-1:0] captured_ready_in,
    output logic [NUM_CHAINS-1:0] captured_valid_out,
    output logic [NUM_CHAINS-1:0][DATA_BITS-1:0] captured_data_out
);

    initial begin
        if (DATA_BITS < 2) begin
            $fatal(1, "scan_executor: DATA_BITS must be >= 2 (got %0d)", DATA_BITS);
        end
        if (SCAN_CHAIN_LEN < 1) begin
            $fatal(1, "scan_executor: SCAN_CHAIN_LEN must be >= 1 (got %0d)", SCAN_CHAIN_LEN);
        end
    end

    localparam int SCAN_CNT_W = (SCAN_CHAIN_LEN <= 1) ? 1 : $clog2(SCAN_CHAIN_LEN);
    localparam int BIT_CNT_W  = (DATA_BITS <= 1) ? 1 : $clog2(DATA_BITS);

    typedef enum logic [1:0] { S_IDLE, S_RUNNING, S_TX } state_t;

    typedef struct packed {
        state_t state;
        logic execute_ready;
        logic [SCAN_CNT_W-1:0] scan_cnt;
        logic [BIT_CNT_W-1:0] bit_cnt;
        logic scan_enable;
        logic clk_enable;
        logic tx_valid;
        logic [DATA_BITS-1:0] tx_data;
    } execute_t;

    execute_t execute, next_execute;

    always_comb begin : execute_async_pr
        logic [DATA_BITS-1:0] v_data;

        next_execute = execute;

        case (execute.state)
            S_IDLE: begin
                next_execute.execute_ready = 1'b1;

                if (execute_ready_out == 1'b1 && execute_valid_in == 1'b1) begin
                    next_execute.execute_ready = 1'b0;
                    next_execute.state = S_RUNNING;
                    next_execute.bit_cnt = '0;
                    next_execute.scan_cnt = '0;
                    next_execute.scan_enable = 1'b1;
                    next_execute.clk_enable = 1'b1;
                end
            end

            S_RUNNING: begin
                v_data[DATA_BITS-1:1] = execute.tx_data[DATA_BITS-2:0];
                v_data[0] = from_chain_in;

                next_execute.tx_data = v_data;

                if (execute.bit_cnt == logic'(DATA_BITS-1) ||
                    execute.scan_cnt == logic'(SCAN_CHAIN_LEN-1)) begin
                    next_execute.state = S_TX;
                    next_execute.tx_valid = 1'b1;
                    next_execute.tx_data = v_data;
                    next_execute.clk_enable = 1'b0;
                end
                else begin
                    next_execute.bit_cnt = execute.bit_cnt + 1'b1;
                end

                if (execute.scan_cnt != logic'(SCAN_CHAIN_LEN-1)) begin
                    next_execute.scan_cnt = execute.scan_cnt + 1'b1;
                end

                if (execute.scan_cnt == logic'(SCAN_CHAIN_LEN-1)) begin

                end
                else begin
                end
            end

            S_TX: begin
                if (captured_ready_in == 1'b1 && captured_valid_out == 1'b1) begin
                    next_execute.tx_valid = 1'b0;

                    if (execute.scan_cnt != logic'(SCAN_CHAIN_LEN-1)) begin
                        next_execute.state = S_RUNNING;
                        next_execute.clk_enable = 1'b1;
                        next_execute.bit_cnt = '0;
                        next_execute.tx_data = '0;
                    end
                    else begin
                        next_execute.state = S_IDLE;
                        next_execute.clk_enable = 1'b0;
                        next_execute.scan_enable = 1'b0;
                    end
                end
            end

            default: begin
                // No change
            end
        endcase

        if (sreset_in == 1'b1) begin
            next_execute.state = S_IDLE;
            next_execute.scan_enable = 1'b0;
            next_execute.clk_enable = 1'b0;
            next_execute.tx_valid = 1'b0;
        end
    end

    always_ff @(posedge clk_in) begin : execute_sync_pr
        execute <= next_execute;
    end

    always_comb begin
        execute_ready_out = execute.execute_ready;
        captured_valid_out = execute.tx_valid;
        captured_data_out = execute.tx_data;

        scan_enable_out = next_execute.scan_enable;
        scan_clk_en_out = next_execute.clk_enable;

        to_chain_out = from_chain_in;
    end
endmodule
