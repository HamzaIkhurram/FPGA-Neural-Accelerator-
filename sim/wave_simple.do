# ==============================================================================
# wave_simple.do
# Waveform configuration for simple testbench (neural_compressor_tb_simple)
# ==============================================================================

onerror {resume}
quietly WaveActivateNextPane {} 0

add wave -noupdate -divider {Clock and Reset}
add wave -noupdate /neural_compressor_tb_simple/clk
add wave -noupdate /neural_compressor_tb_simple/rst_n

add wave -noupdate -divider {Input AXI-Stream}
add wave -noupdate -radix hexadecimal /neural_compressor_tb_simple/s_axis_tdata
add wave -noupdate /neural_compressor_tb_simple/s_axis_tvalid
add wave -noupdate /neural_compressor_tb_simple/s_axis_tready
add wave -noupdate /neural_compressor_tb_simple/s_axis_tlast

add wave -noupdate -divider {Filter Stage}
add wave -noupdate -radix hexadecimal /neural_compressor_tb_simple/dut/filtered_data
add wave -noupdate /neural_compressor_tb_simple/dut/filtered_valid
add wave -noupdate /neural_compressor_tb_simple/dut/filtered_ready

add wave -noupdate -divider {Spike Detector}
add wave -noupdate -radix hexadecimal /neural_compressor_tb_simple/dut/detected_data
add wave -noupdate /neural_compressor_tb_simple/dut/spike_detected
add wave -noupdate /neural_compressor_tb_simple/dut/detected_valid
add wave -noupdate /neural_compressor_tb_simple/dut/detected_ready
add wave -noupdate -radix unsigned /neural_compressor_tb_simple/spike_count

add wave -noupdate -divider {Compressor}
add wave -noupdate -radix hexadecimal /neural_compressor_tb_simple/dut/compressed_data
add wave -noupdate -radix binary /neural_compressor_tb_simple/dut/packet_type
add wave -noupdate /neural_compressor_tb_simple/dut/compressed_valid
add wave -noupdate /neural_compressor_tb_simple/dut/compressed_ready

add wave -noupdate -divider {Output AXI-Stream}
add wave -noupdate -radix hexadecimal /neural_compressor_tb_simple/m_axis_tdata
add wave -noupdate -radix binary /neural_compressor_tb_simple/m_axis_tuser
add wave -noupdate /neural_compressor_tb_simple/m_axis_tvalid
add wave -noupdate /neural_compressor_tb_simple/m_axis_tready
add wave -noupdate /neural_compressor_tb_simple/m_axis_tlast

add wave -noupdate -divider {Statistics}
add wave -noupdate -radix unsigned /neural_compressor_tb_simple/spike_count
add wave -noupdate /neural_compressor_tb_simple/stats

add wave -noupdate -divider {Configuration}
add wave -noupdate -radix hexadecimal /neural_compressor_tb_simple/cfg_threshold
add wave -noupdate /neural_compressor_tb_simple/cfg_enable

TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {0 ns} 0}
quietly wave cursor active 1
configure wave -namecolwidth 300
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 0
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -gridoffset 0
configure wave -gridperiod 1
configure wave -griddelta 40
configure wave -timeline 0
configure wave -timelineunits ns
update
WaveRestoreZoom {0 ns} {1000 ns}

