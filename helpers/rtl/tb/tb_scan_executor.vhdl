library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_scan_executor is
end;

architecture tb of tb_scan_executor is
    constant SCAN_CHAIN_LEN: positive := 43;

    constant DATA_BITS: positive := 8;

    signal clk: std_logic;
    signal sreset: std_logic;

    signal execute_ready: std_logic;
    signal execute_valid: std_logic;

    signal captured_ready: std_logic;
    signal captured_valid: std_logic;
    signal captured_data: std_logic_vector(DATA_BITS-1 downto 0);

    signal scan_enable: std_logic;
    signal scan_clk_en: std_logic;
    signal from_chain: std_logic;
    signal to_chain: std_logic;

    signal emu_clk_en: std_logic;
    signal emu_clk: std_logic;

    signal run_en: std_logic;

    signal emu_sreset: std_logic;

    component counter_8bit is
        port(
            scan_enable_in: in std_logic;
            scan_in: in std_logic;
            scan_out: out std_logic;

            clk_in: in std_logic;
            sreset_in: in std_logic;
            en_in: in std_logic;
            count_out: out std_logic_vector(7 downto 0);
            c2_out: out std_logic_vector(7 downto 0);
            c3_out: out std_logic_vector(7 downto 0);
            c4: out std_logic;
            c5: out std_logic_vector(7 downto 0);
            c6: out std_logic;
            c7: out std_logic_vector(7 downto 0)
        );
    end component;
begin
    clk_pr: process
    begin
        clk <= '0';
        wait for 0.5 ns;
        clk <= '1';
        wait for 0.5 ns;
    end process;

    rst_pr: process
    begin
        sreset <= '1';
        wait for 20 ns;
        wait until rising_edge(clk);
        sreset <= '0';
        wait;
    end process;

    executor_pr: process
    begin
        execute_valid <= '0';
        run_en <= '0';

        wait until sreset = '0' and rising_edge(clk);
        
        run_en <= '1';
        wait until rising_edge(clk);
        emu_sreset <= '1';
        wait until rising_edge(clk);
        emu_sreset <= '0';

        for i in 1 to 100 loop
            wait until rising_edge(clk);
        end loop;

        run_en <= '0';

        wait until rising_edge(clk);

        execute_valid <= '1';
        wait until rising_edge(clk) and execute_valid = '1' and execute_ready = '1';
        
        execute_valid <= '0';
        
        wait;
    end process;

    /*scan_pr: process
        variable k: integer range 0 to 6;
    begin
        k := 0;
        loop
            case k is
                when 0 =>
                    from_chain <= '0';
                when 1 =>
                    from_chain <= '1';
                when 2 =>
                    from_chain <= 'L';
                when 3 =>
                    from_chain <= 'H';
                when 4 =>
                    from_chain <= 'Z';
                when 5 =>
                    from_chain <= 'X';
                when 6 =>
                    from_chain <= 'U';
            end case;

            wait until rising_edge(clk) and scan_enable = '1' and scan_clk_en = '1';
            k := (k + 1) mod 6;
        end loop;
    end process;*/

    process(clk)
    begin
        if rising_edge(clk) then
            if scan_clk_en = '1' then
                emu_clk <= '1';
            end if;

            if run_en = '1' then
                emu_clk <= '1';
            end if;
        end if;

        if falling_edge(clk) then
            emu_clk <= '0';
        end if;
    end process;

    scan_dut: entity work.counter_8bit
        port map(
            scan_enable_in => scan_enable,
            scan_in => to_chain,
            scan_out => from_chain,
            clk_in => emu_clk,
            sreset_in => emu_sreset,
            en_in => '1',
            count_out => open,
            c2_out => open,
            c3_out => open,
            c4 => open,
            c5 => open,
            c6 => open,
            c7 => open
        );

    capture_pr: process
    begin
        loop
            captured_ready <= '1';
            wait until rising_edge(clk);
            captured_ready <= '0';
            captured_ready <= '1';
            for i in 1 to 10 loop
                wait until rising_edge(clk);
            end loop;
        end loop;

        wait;
    end process;

    dut: entity work.scan_executor
        generic map(
            SCAN_CHAIN_LEN => SCAN_CHAIN_LEN,
            DATA_BITS => DATA_BITS
        )
        port map(
            clk_in => clk,
            sreset_in => sreset,
            execute_ready_out => execute_ready,
            execute_valid_in => execute_valid,
            scan_enable_out => scan_enable,
            scan_clk_en_out => scan_clk_en,
            from_chain_in => from_chain,
            to_chain_out => to_chain,
            captured_ready_in => captured_ready,
            captured_valid_out => captured_valid,
            captured_data_out => captured_data
        );
end;
