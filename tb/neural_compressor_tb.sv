// Top-level testbench module

`timescale 1ns/1ps

module neural_compressor_tb;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    
    import neural_compressor_pkg::*;
    import neural_compressor_pkg_tb::*;
    
    // Clock and reset
    logic clk;
    logic rst_n;
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5ns clk = ~clk; // 100MHz
    end
    
    // Reset generation
    initial begin
        rst_n = 0;
        repeat(10) @(posedge clk);
        rst_n = 1;
    end
    
    // Interfaces
    axis_if input_if(clk, rst_n);
    axis_if output_if(clk, rst_n);
    
    // DUT signals
    logic [DATA_WIDTH-1:0] cfg_threshold;
    logic cfg_enable;
    compress_stats_t stats;
    logic [15:0] spike_count;
    
    // Output connections from DUT
    logic [DATA_WIDTH-1:0] m_axis_tdata;
    logic [1:0]            m_axis_tuser;
    logic                  m_axis_tvalid;
    logic                  m_axis_tlast;
    
    // DUT instantiation
    neural_compressor_top dut (
        .clk            (clk),
        .rst_n          (rst_n),
        
        // Input AXI-Stream
        .s_axis_tdata   (input_if.tdata),
        .s_axis_tvalid  (input_if.tvalid),
        .s_axis_tready  (input_if.tready),
        .s_axis_tlast   (input_if.tlast),
        
        // Output AXI-Stream
        .m_axis_tdata   (m_axis_tdata),
        .m_axis_tuser   (m_axis_tuser),
        .m_axis_tvalid  (m_axis_tvalid),
        .m_axis_tready  (output_if.tready),
        .m_axis_tlast   (m_axis_tlast),
        
        // Configuration
        .cfg_threshold  (cfg_threshold),
        .cfg_enable     (cfg_enable),
        
        // Status
        .stats          (stats),
        .spike_count    (spike_count)
    );
    
    // Connect DUT outputs to monitor interface
    assign output_if.tdata = m_axis_tdata;
    assign output_if.tuser = m_axis_tuser;
    assign output_if.tvalid = m_axis_tvalid;
    assign output_if.tlast = m_axis_tlast;
    
    // Default output ready (can be randomized in advanced tests)
    assign output_if.tready = 1'b1;
    
    // Configuration defaults
    initial begin
        cfg_threshold = SPIKE_THRESHOLD; // From package
        cfg_enable = 1'b1;
    end
    
    // UVM configuration
    initial begin
        uvm_config_db#(virtual axis_if)::set(null, "uvm_test_top.env.input_agent.*", "vif", input_if);
        uvm_config_db#(virtual axis_if)::set(null, "uvm_test_top.env.output_agent.*", "vif", output_if);
        
        // Run the test
        run_test();
    end
    
    // Waveform dumping
    initial begin
        if ($test$plusargs("DUMP_WAVES")) begin
            $dumpfile("waves.vcd");
            $dumpvars(0, neural_compressor_tb);
        end
    end
    
    // Timeout watchdog
    initial begin
        #100us;
        `uvm_error("TIMEOUT", "Simulation timeout reached")
        $finish;
    end
    
    // Statistics monitor
    initial begin
        forever begin
            @(posedge clk);
            if (stats.sample_count > 0 && stats.sample_count % 100 == 0) begin
                $display("[%0t] Stats: Samples=%0d, Spikes=%0d, Compression=%0d%%", 
                         $time, stats.sample_count, stats.spike_count, stats.compression_ratio);
            end
        end
    end

endmodule : neural_compressor_tb

