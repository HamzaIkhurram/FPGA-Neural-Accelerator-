// Simple testbench without UVM for neural compressor

`timescale 1ns/1ps

module neural_compressor_tb_simple;
    
    import neural_compressor_pkg::*;
    
    // Clock and reset
    logic clk;
    logic rst_n;
    
    // Clock generation - 100MHz
    initial begin
        clk = 0;
        forever #5ns clk = ~clk;
    end
    
    // Reset generation
    initial begin
        rst_n = 0;
        repeat(10) @(posedge clk);
        rst_n = 1;
        $display("[%0t] Reset released", $time);
    end
    
    // AXI-Stream signals
    logic [DATA_WIDTH-1:0] s_axis_tdata;
    logic                  s_axis_tvalid;
    logic                  s_axis_tready;
    logic                  s_axis_tlast;
    
    logic [DATA_WIDTH-1:0] m_axis_tdata;
    logic [1:0]            m_axis_tuser;
    logic                  m_axis_tvalid;
    logic                  m_axis_tready;
    logic                  m_axis_tlast;
    
    // Configuration
    logic [DATA_WIDTH-1:0] cfg_threshold;
    logic                  cfg_enable;
    
    // Status
    compress_stats_t stats;
    logic [15:0] spike_count;
    
    // DUT instantiation
    neural_compressor_top dut (
        .clk            (clk),
        .rst_n          (rst_n),
        .s_axis_tdata   (s_axis_tdata),
        .s_axis_tvalid  (s_axis_tvalid),
        .s_axis_tready  (s_axis_tready),
        .s_axis_tlast   (s_axis_tlast),
        .m_axis_tdata   (m_axis_tdata),
        .m_axis_tuser   (m_axis_tuser),
        .m_axis_tvalid  (m_axis_tvalid),
        .m_axis_tready  (m_axis_tready),
        .m_axis_tlast   (m_axis_tlast),
        .cfg_threshold  (cfg_threshold),
        .cfg_enable     (cfg_enable),
        .stats          (stats),
        .spike_count    (spike_count)
    );
    
    // Always ready to receive output
    assign m_axis_tready = 1'b1;
    
    // Configuration
    initial begin
        cfg_threshold = SPIKE_THRESHOLD;
        cfg_enable = 1'b1;
    end
    
    // Test stimulus
    logic [31:0] eeg_data [0:999];
    int sample_count = 0;
    int output_count = 0;
    
    // Load EEG data
    initial begin
        $readmemh("../processed_data/eeg_data_Fc5.mem", eeg_data);
        $display("[%0t] Loaded 1000 EEG samples", $time);
    end
    
    // Drive input
    initial begin
        s_axis_tdata = '0;
        s_axis_tvalid = '0;
        s_axis_tlast = '0;
        
        @(posedge rst_n);
        repeat(5) @(posedge clk);
        
        $display("[%0t] Starting EEG data transmission...", $time);
        
        for (int i = 0; i < 1000; i++) begin
            @(posedge clk);
            s_axis_tdata <= eeg_data[i];
            s_axis_tvalid <= 1'b1;
            s_axis_tlast <= (i == 999);
            
            // Wait for ready
            @(posedge clk);
            while (!s_axis_tready) @(posedge clk);
            
            sample_count++;
            
            if (sample_count % 100 == 0) begin
                $display("[%0t] Sent %0d samples", $time, sample_count);
            end
        end
        
        s_axis_tvalid <= 1'b0;
        $display("[%0t] All samples sent", $time);
        
        // Wait for pipeline to flush
        repeat(100) @(posedge clk);
        
        // Print results
        $display("");
        $display("============================================================");
        $display("  Neural Compressor Test Results");
        $display("============================================================");
        $display("Input samples:        %0d", stats.sample_count);
        $display("Output packets:       %0d", output_count);
        $display("Compression ratio:    %0d%%", stats.compression_ratio);
        $display("Spikes detected:      %0d", spike_count);
        $display("============================================================");
        
        if (output_count > 0 && output_count < sample_count) begin
            $display("TEST PASSED - Compression achieved!");
        end else begin
            $display("TEST WARNING - Check compression efficiency");
        end
        
        $finish;
    end
    
    // Monitor output
    always @(posedge clk) begin
        if (m_axis_tvalid && m_axis_tready) begin
            output_count++;
            
            case (m_axis_tuser)
                2'b00: $display("[%0t] Delta packet: %h", $time, m_axis_tdata);
                2'b01: $display("[%0t] RLE packet: count=%0d", $time, m_axis_tdata[31:24]);
                2'b10: $display("[%0t] SPIKE detected: %h", $time, m_axis_tdata);
                2'b11: $display("[%0t] Literal packet: %h", $time, m_axis_tdata);
            endcase
        end
    end
    
    // Timeout
    initial begin
        #100us;
        $display("ERROR: Simulation timeout");
        $finish;
    end
    
    // Waveform dump
    initial begin
        $dumpfile("neural_compressor_waves.vcd");
        $dumpvars(0, neural_compressor_tb_simple);
    end

endmodule : neural_compressor_tb_simple



