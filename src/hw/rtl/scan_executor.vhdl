library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.scan_types_pkg.all;

entity scan_executor is
    generic(
        NUM_CHAINS: positive := 1;
        SCAN_CHAIN_LEN: positive_array_t(0 to NUM_CHAINS-1) := (others => 43);
        DATA_BITS: positive
    );
    port(
        clk_in: in std_logic;
        sreset_in: in std_logic;

        execute_ready_out: out std_logic;
        execute_valid_in: in std_logic;

        scan_enable_out: out std_logic;
        scan_clk_en_out: out std_logic_vector(NUM_CHAINS-1 downto 0);
        from_chain_in: in std_logic_vector(NUM_CHAINS-1 downto 0);
        to_chain_out: out std_logic_vector(NUM_CHAINS-1 downto 0);

        captured_ready_in: in std_logic_vector(NUM_CHAINS-1 downto 0);
        captured_valid_out: out std_logic_vector(NUM_CHAINS-1 downto 0);
        captured_data_out: out slv_array_t(0 to NUM_CHAINS-1)(DATA_BITS-1 downto 0)
    );
end;

architecture rtl of scan_executor is
    signal can_start: std_logic;
    signal execute_ready_vec: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal scan_enable_vec: std_logic_vector(NUM_CHAINS-1 downto 0);
begin
    can_start_pr: process(all)
    begin
        can_start <= execute_valid_in;
        for i in execute_ready_vec'range loop
            if execute_ready_vec(i) = '0' then
                can_start <= '0';
            end if;
        end loop;
    end process;

    chains_g: for i in 0 to NUM_CHAINS-1 generate
        chain_blk: block
            type state_t is (S_IDLE, S_RUNNING, S_TX);
            subtype data_t is std_logic_vector(DATA_BITS-1 downto 0);
            type execute_t is record
                state: state_t;
                execute_ready: std_logic;
                scan_cnt: integer range 0 to SCAN_CHAIN_LEN(i)-1;
                bit_cnt: integer range 0 to DATA_BITS-1;
                scan_enable: std_logic;
                clk_enable: std_logic;
                tx_valid: std_logic;
                tx_data: data_t;
            end record;

            signal execute, next_execute: execute_t;
        begin
            execute_async_pr: process(all)
                variable v_data: data_t;
            begin
                next_execute <= execute;

                case execute.state is
                    when S_IDLE =>
                        next_execute.execute_ready <= '1';
                        next_execute.tx_valid <= '0';
                        next_execute.clk_enable <= '0';
                        next_execute.scan_enable <= '0';
                        next_execute.bit_cnt <= 0;
                        next_execute.scan_cnt <= 0;

                        if can_start = '1' then
                            next_execute.execute_ready <= '0';
                            next_execute.state <= S_RUNNING;
                            next_execute.scan_enable <= '1';
                            next_execute.clk_enable <= '1';
                        end if;
                    when S_RUNNING =>
                        v_data := execute.tx_data;
                        v_data(DATA_BITS-1 downto 1) := execute.tx_data(DATA_BITS-2 downto 0);
                        v_data(0) := from_chain_in(i);
                        next_execute.tx_data <= v_data;

                        if execute.bit_cnt = DATA_BITS-1 or execute.scan_cnt = SCAN_CHAIN_LEN(i)-1 then
                            next_execute.state <= S_TX;
                            next_execute.tx_valid <= '1';
                            next_execute.tx_data <= v_data;
                            next_execute.clk_enable <= '0';
                        else
                            next_execute.bit_cnt <= execute.bit_cnt + 1;
                        end if;

                        if execute.scan_cnt /= SCAN_CHAIN_LEN(i)-1 then
                            next_execute.scan_cnt <= execute.scan_cnt + 1;
                        end if;
                    when S_TX =>
                        if captured_ready_in(i) = '1' and captured_valid_out(i) = '1' then
                            next_execute.tx_valid <= '0';
                            if execute.scan_cnt /= SCAN_CHAIN_LEN(i)-1 then
                                next_execute.state <= S_RUNNING;
                                next_execute.clk_enable <= '1';
                                next_execute.bit_cnt <= 0;
                                next_execute.tx_data <= (others => '0');
                            else
                                next_execute.state <= S_IDLE;
                                next_execute.clk_enable <= '0';
                                next_execute.scan_enable <= '0';
                            end if;
                        end if;
                end case;

                if sreset_in = '1' then
                    next_execute.state <= S_IDLE;
                    next_execute.scan_enable <= '0';
                    next_execute.clk_enable <= '0';
                    next_execute.tx_valid <= '0';
                    next_execute.tx_data <= (others => '0');
                    next_execute.execute_ready <= '1';
                    next_execute.bit_cnt <= 0;
                    next_execute.scan_cnt <= 0;
                end if;
            end process;

            execute_sync_pr: process(clk_in)
            begin
                if rising_edge(clk_in) then
                    execute <= next_execute;
                end if;
            end process;

            execute_ready_vec(i) <= execute.execute_ready;
            scan_enable_vec(i) <= next_execute.scan_enable;
            captured_valid_out(i) <= execute.tx_valid;
            captured_data_out(i) <= execute.tx_data;
            scan_clk_en_out(i) <= next_execute.clk_enable;
        end block;
    end generate;

    process(all)
        variable v_ready: std_logic;
        variable v_scan_enable: std_logic;
    begin
        v_ready := '1';
        v_scan_enable := '0';

        for i in execute_ready_vec'range loop
            if execute_ready_vec(i) = '0' then
                v_ready := '0';
            end if;
            if scan_enable_vec(i) = '1' then
                v_scan_enable := '1';
            end if;
        end loop;

        execute_ready_out <= v_ready;
        scan_enable_out <= v_scan_enable;
        to_chain_out <= from_chain_in;
    end process;
end;
