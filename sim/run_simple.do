# ==============================================================================
# run_simple.do
# Run simple testbench without UVM
# ==============================================================================

# Load simulation
vsim -voptargs=+acc work.neural_compressor_tb_simple

# Load waveform configuration
do wave_simple.do

# Run simulation
run -all

# Zoom to fit
wave zoom full

echo "=============================================="
echo "Simulation complete! Check waveforms and transcript."
echo "=============================================="



