# ==============================================================================
# compile_simple.do
# Compile simple testbench (no UVM)
# ==============================================================================

# Create work library
vlib work
vmap work work

# Compile RTL
vlog -sv +acc \
    ../rtl/neural_compressor_pkg.sv \
    ../rtl/fixed_point_filter.sv \
    ../rtl/spike_detector.sv \
    ../rtl/delta_compressor.sv \
    ../rtl/neural_compressor_top.sv

# Compile simple testbench (no UVM)
vlog -sv +acc \
    ../tb/neural_compressor_tb_simple.sv

echo "Compilation complete!"



