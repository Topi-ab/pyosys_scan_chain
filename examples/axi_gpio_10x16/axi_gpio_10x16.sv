module axi_gpio_10x16 (
    input  logic        clk_in,
    input  logic        sreset_in,

    // AXI4-Lite write address channel
    input  logic [7:0]  s_axi_awaddr,
    input  logic        s_axi_awvalid,
    output logic        s_axi_awready,

    // AXI4-Lite write data channel
    input  logic [31:0] s_axi_wdata,
    input  logic [3:0]  s_axi_wstrb,
    input  logic        s_axi_wvalid,
    output logic        s_axi_wready,

    // AXI4-Lite write response channel
    output logic [1:0]  s_axi_bresp,
    output logic        s_axi_bvalid,
    input  logic        s_axi_bready,

    // AXI4-Lite read address channel
    input  logic [7:0]  s_axi_araddr,
    input  logic        s_axi_arvalid,
    output logic        s_axi_arready,

    // AXI4-Lite read data channel
    output logic [31:0] s_axi_rdata,
    output logic [1:0]  s_axi_rresp,
    output logic        s_axi_rvalid,
    input  logic        s_axi_rready,

    // GPIO outputs
    output logic [15:0] gpio0_out,
    output logic [15:0] gpio1_out,
    output logic [15:0] gpio2_out,
    output logic [15:0] gpio3_out,
    output logic [15:0] gpio4_out,
    output logic [15:0] gpio5_out,
    output logic [15:0] gpio6_out,
    output logic [15:0] gpio7_out,
    output logic [15:0] gpio8_out,
    output logic [15:0] gpio9_out
);
    logic [15:0] regs [0:9];

    logic [7:0]  awaddr_q;
    logic        write_fire;
    logic        read_fire;

    assign s_axi_awready = ~s_axi_bvalid;
    assign s_axi_wready  = ~s_axi_bvalid;
    assign s_axi_bresp   = 2'b00;

    assign s_axi_arready = ~s_axi_rvalid;
    assign s_axi_rresp   = 2'b00;

    assign write_fire = s_axi_awvalid && s_axi_wvalid && s_axi_awready && s_axi_wready;
    assign read_fire  = s_axi_arvalid && s_axi_arready;

    function automatic logic [3:0] reg_index(input logic [7:0] addr);
        reg_index = addr[5:2];
    endfunction

    function automatic logic [15:0] apply_wstrb(input logic [15:0] cur, input logic [31:0] data, input logic [3:0] strb);
        logic [15:0] masked;
        begin
            masked = cur;
            if (strb[0]) masked[7:0]  = data[7:0];
            if (strb[1]) masked[15:8] = data[15:8];
            apply_wstrb = masked;
        end
    endfunction

    always_ff @(posedge clk_in) begin
        if (sreset_in) begin
            integer i;
            for (i = 0; i < 10; i = i + 1) begin
                regs[i] <= 16'h0000;
            end
            s_axi_bvalid <= 1'b0;
            s_axi_rvalid <= 1'b0;
            s_axi_rdata  <= 32'h0000_0000;
            awaddr_q <= 8'h00;
        end
        else begin
            if (write_fire) begin
                awaddr_q <= s_axi_awaddr;
                case (reg_index(s_axi_awaddr))
                    4'd0: regs[0] <= apply_wstrb(regs[0], s_axi_wdata, s_axi_wstrb);
                    4'd1: regs[1] <= apply_wstrb(regs[1], s_axi_wdata, s_axi_wstrb);
                    4'd2: regs[2] <= apply_wstrb(regs[2], s_axi_wdata, s_axi_wstrb);
                    4'd3: regs[3] <= apply_wstrb(regs[3], s_axi_wdata, s_axi_wstrb);
                    4'd4: regs[4] <= apply_wstrb(regs[4], s_axi_wdata, s_axi_wstrb);
                    4'd5: regs[5] <= apply_wstrb(regs[5], s_axi_wdata, s_axi_wstrb);
                    4'd6: regs[6] <= apply_wstrb(regs[6], s_axi_wdata, s_axi_wstrb);
                    4'd7: regs[7] <= apply_wstrb(regs[7], s_axi_wdata, s_axi_wstrb);
                    4'd8: regs[8] <= apply_wstrb(regs[8], s_axi_wdata, s_axi_wstrb);
                    4'd9: regs[9] <= apply_wstrb(regs[9], s_axi_wdata, s_axi_wstrb);
                    default: begin end
                endcase
                s_axi_bvalid <= 1'b1;
            end
            else if (s_axi_bvalid && s_axi_bready) begin
                s_axi_bvalid <= 1'b0;
            end

            if (read_fire) begin
                case (reg_index(s_axi_araddr))
                    4'd0: s_axi_rdata <= {16'h0000, regs[0]};
                    4'd1: s_axi_rdata <= {16'h0000, regs[1]};
                    4'd2: s_axi_rdata <= {16'h0000, regs[2]};
                    4'd3: s_axi_rdata <= {16'h0000, regs[3]};
                    4'd4: s_axi_rdata <= {16'h0000, regs[4]};
                    4'd5: s_axi_rdata <= {16'h0000, regs[5]};
                    4'd6: s_axi_rdata <= {16'h0000, regs[6]};
                    4'd7: s_axi_rdata <= {16'h0000, regs[7]};
                    4'd8: s_axi_rdata <= {16'h0000, regs[8]};
                    4'd9: s_axi_rdata <= {16'h0000, regs[9]};
                    default: s_axi_rdata <= 32'h0000_0000;
                endcase
                s_axi_rvalid <= 1'b1;
            end
            else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
            end
        end
    end

    assign gpio0_out = regs[0];
    assign gpio1_out = regs[1];
    assign gpio2_out = regs[2];
    assign gpio3_out = regs[3];
    assign gpio4_out = regs[4];
    assign gpio5_out = regs[5];
    assign gpio6_out = regs[6];
    assign gpio7_out = regs[7];
    assign gpio8_out = regs[8];
    assign gpio9_out = regs[9];
endmodule
