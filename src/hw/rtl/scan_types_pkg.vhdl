library ieee;
use ieee.std_logic_1164.all;

package scan_types_pkg is
    -- Generic array of std_logic values.
    type sl_array_t is array(natural range <>) of std_logic;

    -- Generic array of std_logic_vector with unconstrained element width.
    type slv_array_t is array(natural range <>) of std_logic_vector;

    -- Generic array of positive integers (e.g. per-chain lengths).
    type positive_array_t is array(natural range <>) of positive;
end package;

package body scan_types_pkg is
end package body;
