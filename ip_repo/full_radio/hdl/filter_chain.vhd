library IEEE;
use IEEE.STD_LOGIC_1164.all;

entity filter_chain is
  port (
    aclk               : in std_logic;
    s_axis_data_tvalid : in std_logic;
    s_axis_data_tdata  : in std_logic_vector(15 downto 0);
    m_axis_data_tdata  : out std_logic_vector(15 downto 0);
    m_axis_data_tvalid : out std_logic
  );
end filter_chain;

architecture rtl of filter_chain is
  component fir_stage1
    port (
      aclk               : in std_logic;
      s_axis_data_tvalid : in std_logic;
      s_axis_data_tready : out std_logic;
      s_axis_data_tdata  : in std_logic_vector(15 downto 0);
      m_axis_data_tvalid : out std_logic;
      m_axis_data_tdata  : out std_logic_vector(39 downto 0)
    );
  end component;
  component fir_stage2
    port (
      aclk               : in std_logic;
      s_axis_data_tvalid : in std_logic;
      s_axis_data_tready : out std_logic;
      s_axis_data_tdata  : in std_logic_vector(15 downto 0);
      m_axis_data_tvalid : out std_logic;
      m_axis_data_tdata  : out std_logic_vector(39 downto 0)
    );
  end component;

  signal filter_1_out_tdata  : std_logic_vector(39 downto 0);
  signal filter_2_out_tdata  : std_logic_vector(39 downto 0);
  signal filter_1_out_tvalid : std_logic;
  signal filter_2_out_tvalid : std_logic;

begin

  m_axis_data_tdata  <= filter_2_out_tdata(31 downto 16);
  m_axis_data_tvalid <= filter_2_out_tvalid;

  fir_1_inst : fir_stage1
  port map
  (
    aclk               => aclk,
    s_axis_data_tvalid => s_axis_data_tvalid,
    s_axis_data_tready => open,
    s_axis_data_tdata  => s_axis_data_tdata,
    m_axis_data_tvalid => filter_1_out_tvalid,
    m_axis_data_tdata  => filter_1_out_tdata
  );

  fir_2_inst : fir_stage2
  port map
  (
    aclk               => aclk,
    s_axis_data_tvalid => filter_1_out_tvalid,
    s_axis_data_tready => open,
    s_axis_data_tdata  => filter_1_out_tdata(31 downto 16),
    m_axis_data_tvalid => filter_2_out_tvalid,
    m_axis_data_tdata  => filter_2_out_tdata
  );

end rtl;
