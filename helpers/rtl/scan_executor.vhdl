library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity scan_executor is
    generic(
        SCAN_CHAIN_LEN: positive := 43;
        DATA_BITS: positive
    );
    port(
        clk_in: in std_logic;
        sreset_in: in std_logic;

        execute_ready_out: out std_logic;
        execute_valid_in: in std_logic;

        scan_enable_out: out std_logic;
        scan_clk_en_out: out std_logic;
        from_chain_in: in std_logic;
        to_chain_out: out std_logic;

        captured_ready_in: in std_logic;
        captured_valid_out: out std_logic;
        captured_data_out: out std_logic_vector(DATA_BITS-1 downto 0)
    );
end;

architecture rtl of scan_executor is
    type state_t is (S_IDLE, S_RUNNING, S_TX);
    type execute_t is record
        state: state_t;
        execute_ready: std_logic;
        scan_cnt: integer range 0 to SCAN_CHAIN_LEN-1;
        bit_cnt: integer range 0 to DATA_BITS-1;
        scan_enable: std_logic;
        clk_enable: std_logic;
        tx_valid: std_logic;
        tx_data: std_logic_vector(DATA_BITS-1 downto 0);
    end record;

    signal execute, next_execute: execute_t;
begin
    execute_async_pr: process(all)
        variable v_data: std_logic_vector(DATA_BITS-1 downto 0);
    begin
        next_execute <= execute;

        case execute.state is
            when S_IDLE =>
                next_execute.execute_ready <= '1';

                if execute_ready_out = '1' and execute_valid_in = '1' then
                    next_execute.execute_ready <= '0';
                    next_execute.state <= S_RUNNING;
                    next_execute.bit_cnt <= 0;
                    next_execute.scan_cnt <= 0;
                    next_execute.scan_enable <= '1';
                    next_execute.clk_enable <= '1';
                end if;
            when S_RUNNING =>
                v_data(DATA_BITS-1 downto 1) := execute.tx_data(DATA_BITS-2 downto 0);
                v_data(0) := from_chain_in;
                next_execute.tx_data <= v_data;
                if execute.bit_cnt = DATA_BITS-1 or execute.scan_cnt = SCAN_CHAIN_LEN-1 then
                    next_execute.state <= S_TX;
                    next_execute.tx_valid <= '1';
                    next_execute.tx_data <= v_data;
                    next_execute.clk_enable <= '0';
                else
                    next_execute.bit_cnt <= execute.bit_cnt + 1;
                end if;

                if execute.scan_cnt /= SCAN_CHAIN_LEN-1 then
                    next_execute.scan_cnt <= execute.scan_cnt + 1;
                end if;

                if execute.scan_cnt = SCAN_CHAIN_LEN-1 then

                else
                end if;
            when S_TX =>
                if captured_ready_in = '1' and captured_valid_out = '1' then
                    next_execute.tx_valid <= '0';
                    if execute.scan_cnt /= SCAN_CHAIN_LEN-1 then
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
        end if;
    end process;

    execute_sync_pr: process(clk_in)
    begin
        if rising_edge(clk_in) then
            execute <= next_execute; 
        end if;
    end process;

    process(all)
    begin
        execute_ready_out <= execute.execute_ready;
        captured_valid_out <= execute.tx_valid;
        captured_data_out <= execute.tx_data;

        scan_enable_out <= next_execute.scan_enable;
        scan_clk_en_out <= next_execute.clk_enable;
    end process;
end;
