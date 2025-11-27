// Delta encoding + Run-length encoding compression engine

module delta_compressor
    import neural_compressor_pkg::*;
(
    input  logic                    clk,
    input  logic                    rst_n,
    
    // Input stream
    input  logic [DATA_WIDTH-1:0]   data_in,
    input  logic                    spike_in,
    input  logic                    valid_in,
    output logic                    ready_out,
    
    // Output compressed stream
    output logic [DATA_WIDTH-1:0]   compressed_out,
    output logic [1:0]              packet_type,  // 00=delta, 01=run, 10=spike, 11=literal
    output logic                    valid_out,
    input  logic                    ready_in,
    
    // Statistics
    output compress_stats_t         stats
);

    // Previous value for delta calculation
    logic [DATA_WIDTH-1:0] prev_value;
    logic signed [DATA_WIDTH-1:0] delta;
    
    // Compression statistics
    logic [15:0] input_count, output_count, local_spike_count;
    
    // First sample flag
    logic first_sample;
    
    // Calculate delta
    always_comb begin
        delta = $signed(data_in) - $signed(prev_value);
    end
    
    // Simplified: always ready, always output delta
    assign ready_out = ready_in;
    
    // Simplified datapath - just delta encoding for every sample
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prev_value <= '0;
            compressed_out <= '0;
            packet_type <= '0;
            valid_out <= '0;
            first_sample <= '1;
            input_count <= '0;
            output_count <= '0;
            local_spike_count <= '0;
        end else begin
            if (valid_in && ready_out) begin
                input_count <= input_count + 1;
                
                if (spike_in) begin
                    // Spike packet
                    compressed_out <= data_in;
                    packet_type <= 2'b10; // Spike
                    valid_out <= '1;
                    output_count <= output_count + 1;
                    local_spike_count <= local_spike_count + 1;
                    prev_value <= data_in;
                    first_sample <= '0;
                end else if (first_sample) begin
                    // First sample - output as literal
                    compressed_out <= data_in;
                    packet_type <= 2'b11; // Literal
                    valid_out <= '1;
                    output_count <= output_count + 1;
                    prev_value <= data_in;
                    first_sample <= '0;
                end else begin
                    // Delta encoding
                    compressed_out <= delta;
                    packet_type <= 2'b00; // Delta
                    valid_out <= '1;
                    output_count <= output_count + 1;
                    prev_value <= data_in;
                end
            end else begin
                valid_out <= '0;
            end
        end
    end
    
    // Calculate compression ratio (output/input * 100)
    logic [31:0] ratio_calc;
    always_comb begin
        if (input_count > 0)
            ratio_calc = (output_count * 100) / input_count;
        else
            ratio_calc = 100;
    end
    
    // Statistics output
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stats <= '0;
        end else begin
            stats.sample_count <= input_count;
            stats.spike_count <= local_spike_count;
            stats.compression_ratio <= ratio_calc[7:0];
            stats.overflow <= (output_count > input_count); // Should never happen
        end
    end

endmodule : delta_compressor

