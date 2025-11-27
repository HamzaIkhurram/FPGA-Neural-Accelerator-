// Adaptive threshold-based spike detector with windowing

module spike_detector
    import neural_compressor_pkg::*;
#(
    parameter int WINDOW = WINDOW_SIZE
)(
    input  logic                    clk,
    input  logic                    rst_n,
    
    // Input stream (filtered signal)
    input  logic [DATA_WIDTH-1:0]   data_in,
    input  logic                    valid_in,
    output logic                    ready_out,
    
    // Output stream (passthrough + spike flag)
    output logic [DATA_WIDTH-1:0]   data_out,
    output logic                    spike_detected,
    output logic                    valid_out,
    input  logic                    ready_in,
    
    // Configuration
    input  logic [DATA_WIDTH-1:0]   threshold,
    output logic [15:0]             spike_count
);

    // Circular buffer for sliding window
    logic [DATA_WIDTH-1:0] window_buffer [0:WINDOW-1];
    logic [$clog2(WINDOW)-1:0] write_ptr;
    logic window_full;
    logic [$clog2(WINDOW):0] sample_count;
    
    // Statistical metrics
    logic signed [DATA_WIDTH-1:0] mean, variance, std_dev;
    logic signed [63:0] sum, sum_sq;
    
    // Spike detection logic
    logic signed [DATA_WIDTH-1:0] abs_value;
    logic threshold_exceeded;
    logic spike_flag;
    logic [3:0] refractory_counter; // Prevent double-counting
    
    // Calculate absolute value
    always_comb begin
        abs_value = ($signed(data_in) < 0) ? -$signed(data_in) : data_in;
    end
    
    // Threshold comparison
    assign threshold_exceeded = (abs_value > threshold);
    
    // Window management
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            write_ptr <= '0;
            window_full <= '0;
            sample_count <= '0;
            sum <= '0;
            sum_sq <= '0;
            mean <= '0;
            spike_count <= '0;
            spike_flag <= '0;
            refractory_counter <= '0;
            
            for (int i = 0; i < WINDOW; i++)
                window_buffer[i] <= '0;
                
        end else if (valid_in && ready_out) begin
            // Update circular buffer
            window_buffer[write_ptr] <= data_in;
            write_ptr <= (write_ptr == WINDOW-1) ? '0 : write_ptr + 1;
            
            if (!window_full) begin
                sample_count <= sample_count + 1;
                window_full <= (sample_count == WINDOW-1);
            end
            
            // Update running statistics (simplified - full window)
            if (window_full) begin
                // Calculate mean
                sum = '0;
                for (int i = 0; i < WINDOW; i++) begin
                    sum += $signed(window_buffer[i]);
                end
                mean <= sum / WINDOW;
            end
            
            // Spike detection with refractory period
            if (refractory_counter > 0) begin
                refractory_counter <= refractory_counter - 1;
                spike_flag <= '0;
            end else if (threshold_exceeded && window_full) begin
                spike_flag <= '1;
                spike_count <= spike_count + 1;
                refractory_counter <= 8; // 8-sample refractory period
            end else begin
                spike_flag <= '0;
            end
        end else begin
            spike_flag <= '0;
        end
    end
    
    // Simplified output assignment - just pass through
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= '0;
            spike_detected <= '0;
            valid_out <= '0;
        end else begin
            if (valid_in && ready_out) begin
                data_out <= data_in;
                spike_detected <= spike_flag;
                valid_out <= '1;
            end else if (ready_in || !valid_in) begin
                valid_out <= '0;
            end
        end
    end
    
    // Ready when downstream is ready
    assign ready_out = ready_in;

endmodule : spike_detector

