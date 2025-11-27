// Top-level neural signal compressor with AXI-Stream interface

module neural_compressor_top
    import neural_compressor_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,
    
    // AXI-Stream Slave (input)
    input  logic [DATA_WIDTH-1:0]   s_axis_tdata,
    input  logic                    s_axis_tvalid,
    output logic                    s_axis_tready,
    input  logic                    s_axis_tlast,
    
    // AXI-Stream Master (compressed output)
    output logic [DATA_WIDTH-1:0]   m_axis_tdata,
    output logic [1:0]              m_axis_tuser,  // packet_type
    output logic                    m_axis_tvalid,
    input  logic                    m_axis_tready,
    output logic                    m_axis_tlast,
    
    // Configuration registers (APB/AXI-Lite would go here)
    input  logic [DATA_WIDTH-1:0]   cfg_threshold,
    input  logic                    cfg_enable,
    
    // Status outputs
    output compress_stats_t         stats,
    output logic [15:0]             spike_count
);

    // Inter-stage signals
    logic [DATA_WIDTH-1:0] filtered_data;
    logic filtered_valid, filtered_ready;
    
    logic [DATA_WIDTH-1:0] detected_data;
    logic spike_detected;
    logic detected_valid, detected_ready;
    
    logic [DATA_WIDTH-1:0] compressed_data;
    logic [1:0] packet_type;
    logic compressed_valid, compressed_ready;
    
    // Module enable gating
    logic s_axis_tvalid_gated;
    assign s_axis_tvalid_gated = s_axis_tvalid && cfg_enable;
    
    // Stage 1: IIR Bandpass Filter
    fixed_point_filter u_filter (
        .clk        (clk),
        .rst_n      (rst_n),
        .data_in    (s_axis_tdata),
        .valid_in   (s_axis_tvalid_gated),
        .ready_out  (s_axis_tready),
        .data_out   (filtered_data),
        .valid_out  (filtered_valid),
        .ready_in   (filtered_ready)
    );
    
    // Stage 2: Spike Detector
    spike_detector u_detector (
        .clk            (clk),
        .rst_n          (rst_n),
        .data_in        (filtered_data),
        .valid_in       (filtered_valid),
        .ready_out      (filtered_ready),
        .data_out       (detected_data),
        .spike_detected (spike_detected),
        .valid_out      (detected_valid),
        .ready_in       (detected_ready),
        .threshold      (cfg_threshold),
        .spike_count    (spike_count)
    );
    
    // Stage 3: Delta/Run-Length Compressor
    delta_compressor u_compressor (
        .clk            (clk),
        .rst_n          (rst_n),
        .data_in        (detected_data),
        .spike_in       (spike_detected),
        .valid_in       (detected_valid),
        .ready_out      (detected_ready),
        .compressed_out (compressed_data),
        .packet_type    (packet_type),
        .valid_out      (compressed_valid),
        .ready_in       (compressed_ready),
        .stats          (stats)
    );
    
    // Output AXI-Stream assignments
    assign m_axis_tdata = compressed_data;
    assign m_axis_tuser = packet_type;
    assign m_axis_tvalid = compressed_valid;
    assign compressed_ready = m_axis_tready;
    
    // TLAST propagation (simplified - set on packet boundaries)
    logic tlast_pending;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tlast_pending <= '0;
            m_axis_tlast <= '0;
        end else begin
            if (s_axis_tvalid && s_axis_tready && s_axis_tlast)
                tlast_pending <= '1;
            
            if (m_axis_tvalid && m_axis_tready && tlast_pending) begin
                m_axis_tlast <= '1;
                tlast_pending <= '0;
            end else begin
                m_axis_tlast <= '0;
            end
        end
    end

endmodule : neural_compressor_top

