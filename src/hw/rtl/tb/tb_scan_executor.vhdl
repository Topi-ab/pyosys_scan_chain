library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use work.scan_types_pkg.all;

entity tb_scan_executor is
    generic(
        NUM_CHAINS: positive := 2;
        SCAN_CHAIN_LEN: positive_array_t(0 to NUM_CHAINS-1) := (0 => 63, 1 => 96)
    );
end;

architecture tb of tb_scan_executor is
    constant NUM_CLOCKS: positive := 1;
    constant DATA_BITS: positive := 8;

    signal clk: std_logic;

    signal sreset: std_logic;

    signal execute_ready: std_logic;
    signal execute_valid: std_logic;

    signal captured_ready: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal captured_valid: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal captured_data: slv_array_t(0 to NUM_CHAINS-1)(DATA_BITS-1 downto 0);

    signal scan_enable: std_logic;
    signal scan_clk_en: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal from_chain: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal to_chain: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal run_en: std_logic_vector(NUM_CHAINS-1 downto 0);
    signal emu_clk: std_logic_vector(NUM_CHAINS-1 downto 0);

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
        run_en <= (others => '0');

        wait until sreset = '0' and rising_edge(clk);

        run_en <= (others => '1');
        for i in 1 to 100 loop
            wait until rising_edge(clk);
        end loop;

        run_en <= (others => '0');
        wait until rising_edge(clk);

        for scan_idx in 0 to 2 loop
            execute_valid <= '1';
            wait until rising_edge(clk) and execute_valid = '1' and execute_ready = '1';
            execute_valid <= '0';

            wait until rising_edge(clk) and scan_enable = '1';
            wait until rising_edge(clk) and scan_enable = '0';
        end loop;

        wait;
    end process;

    gen_chain_model: for i in 0 to NUM_CHAINS-1 generate
        chain_model_blk: block
            constant CH_LEN: positive := SCAN_CHAIN_LEN(i);
            signal shift_reg: std_logic_vector(CH_LEN-1 downto 0);
            signal expected_chunk: std_logic_vector(DATA_BITS-1 downto 0);
            signal expected_latched: std_logic_vector(DATA_BITS-1 downto 0);
            signal scan_cnt: integer range 0 to CH_LEN-1;
            signal bit_cnt: integer range 0 to DATA_BITS-1;
            signal scan_index: integer;
            signal check_enable: std_logic;
        begin
            process(clk)
            begin
                if rising_edge(clk) then
                    if scan_clk_en(i) = '1' or run_en(i) = '1' then
                        emu_clk(i) <= '1';
                    end if;
                end if;

                if falling_edge(clk) then
                    emu_clk(i) <= '0';
                end if;
            end process;

            process(emu_clk(i), sreset)
                variable seed1: positive := 1357 + (i * 17);
                variable seed2: positive := 2467 + (i * 31);
                variable rand_val: real;
                variable in_bit: std_logic;
                variable out_bit: std_logic;
                variable next_expected: std_logic_vector(DATA_BITS-1 downto 0);
            begin
                if sreset = '1' then
                    from_chain(i) <= '0';
                    shift_reg <= (others => '0');
                    expected_chunk <= (others => '0');
                    expected_latched <= (others => '0');
                    scan_cnt <= 0;
                    bit_cnt <= 0;
                    scan_index <= 0;
                    check_enable <= '0';
                elsif rising_edge(emu_clk(i)) then
                    if scan_enable = '1' and scan_clk_en(i) = '1' then
                        out_bit := shift_reg(CH_LEN-1);
                        if scan_index = 0 then
                            uniform(seed1, seed2, rand_val);
                            if rand_val < 0.5 then
                                in_bit := '0';
                            else
                                in_bit := '1';
                            end if;
                        else
                            in_bit := '0';
                        end if;

                        from_chain(i) <= out_bit;
                        next_expected := expected_chunk(DATA_BITS-2 downto 0) & out_bit;

                        if CH_LEN = 1 then
                            shift_reg(0) <= in_bit;
                        else
                            shift_reg <= shift_reg(CH_LEN-2 downto 0) & in_bit;
                        end if;

                        if bit_cnt = DATA_BITS-1 or scan_cnt = CH_LEN-1 then
                            expected_latched <= next_expected;
                            expected_chunk <= (others => '0');
                            bit_cnt <= 0;
                        else
                            expected_chunk <= next_expected;
                            bit_cnt <= bit_cnt + 1;
                        end if;

                        if scan_cnt = CH_LEN-1 then
                            scan_cnt <= 0;
                            if scan_index = 0 then
                                check_enable <= '1';
                            end if;
                            scan_index <= scan_index + 1;
                        else
                            scan_cnt <= scan_cnt + 1;
                        end if;
                    end if;
                end if;
            end process;

            process(captured_valid(i))
            begin
                if captured_valid(i) = '1' and check_enable = '1' then
                    assert captured_data(i) = expected_latched
                        report "Chain " & integer'image(i) & " data mismatch"
                        severity error;
                end if;
            end process;
        end block;
    end generate;

    capture_pr: process
    begin
        loop
            captured_ready <= (others => '1');
            wait until rising_edge(clk);
            captured_ready <= (others => '0');
            captured_ready <= (others => '1');
            for i in 1 to 10 loop
                wait until rising_edge(clk);
            end loop;
        end loop;

        wait;
    end process;

    dut: entity work.scan_executor
        generic map(
            NUM_CHAINS => NUM_CHAINS,
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
