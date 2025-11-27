// IIR bandpass filter for neural signal preprocessing

module fixed_point_filter
    import neural_compressor_pkg::*;
#(
    parameter int ORDER = FILTER_ORDER
)(
    input  logic                    clk,
    input  logic                    rst_n,
    
    // Input stream
    input  logic [DATA_WIDTH-1:0]   data_in,
    input  logic                    valid_in,
    output logic                    ready_out,
    
    // Output stream
    output logic [DATA_WIDTH-1:0]   data_out,
    output logic                    valid_out,
    input  logic                    ready_in
);

    // State registers for x[n-k] and y[n-k]
    logic [DATA_WIDTH-1:0] x_delay [0:ORDER];
    logic [DATA_WIDTH-1:0] y_delay [0:ORDER];
    
    // Accumulator for MAC operations (extended precision)
    logic signed [63:0] acc_b, acc_a;
    logic signed [63:0] mac_result;
    
    // Pipeline stages
    typedef enum logic [1:0] {
        IDLE,
        COMPUTE_B,
        COMPUTE_A,
        OUTPUT
    } state_t;
    
    state_t state, next_state;
    logic [2:0] mac_counter;
    
    // Fixed-point multiply: (Q16.16) * (Q16.16) = (Q32.32) >> 16 = (Q16.16)
    function automatic logic signed [63:0] fixed_mult(
        input logic signed [31:0] a,
        input logic signed [31:0] b
    );
        logic signed [63:0] prod;
        prod = $signed(a) * $signed(b);
        return prod >>> 16; // Shift right to maintain Q16.16 format
    endfunction
    
    // State machine
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            mac_counter <= 0;
        end else begin
            state <= next_state;
            
            case (state)
                COMPUTE_B, COMPUTE_A: begin
                    if (mac_counter < ORDER)
                        mac_counter <= mac_counter + 1;
                    else
                        mac_counter <= 0;
                end
                default: mac_counter <= 0;
            endcase
        end
    end
    
    // Next state logic
    always_comb begin
        next_state = state;
        
        case (state)
            IDLE: begin
                if (valid_in && ready_out)
                    next_state = COMPUTE_B;
            end
            
            COMPUTE_B: begin
                if (mac_counter == ORDER)
                    next_state = COMPUTE_A;
            end
            
            COMPUTE_A: begin
                if (mac_counter == ORDER)
                    next_state = OUTPUT;
            end
            
            OUTPUT: begin
                if (ready_in)
                    next_state = IDLE;
            end
        endcase
    end
    
    // Datapath
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i <= ORDER; i++) begin
                x_delay[i] <= '0;
                y_delay[i] <= '0;
            end
            acc_b <= '0;
            acc_a <= '0;
            data_out <= '0;
            valid_out <= '0;
        end else begin
            case (state)
                IDLE: begin
                    valid_out <= '0;
                    if (valid_in && ready_out) begin
                        // Shift delay lines
                        for (int i = ORDER; i > 0; i--) begin
                            x_delay[i] <= x_delay[i-1];
                        end
                        x_delay[0] <= data_in;
                        acc_b <= '0;
                        acc_a <= '0;
                    end
                end
                
                COMPUTE_B: begin
                    // Accumulate b[k] * x[n-k]
                    acc_b <= acc_b + fixed_mult(B_COEFF[mac_counter], x_delay[mac_counter]);
                end
                
                COMPUTE_A: begin
                    // Accumulate a[k] * y[n-k] (skip a[0] = 1.0)
                    if (mac_counter > 0)
                        acc_a <= acc_a + fixed_mult(A_COEFF[mac_counter], y_delay[mac_counter]);
                end
                
                OUTPUT: begin
                    // y[n] = acc_b - acc_a
                    mac_result = acc_b - acc_a;
                    data_out <= mac_result[31:0]; // Extract Q16.16 portion
                    valid_out <= '1;
                    
                    // Update y delay line
                    if (ready_in) begin
                        for (int i = ORDER; i > 0; i--) begin
                            y_delay[i] <= y_delay[i-1];
                        end
                        y_delay[0] <= mac_result[31:0];
                    end
                end
            endcase
        end
    end
    
    // Flow control
    assign ready_out = (state == IDLE);

endmodule : fixed_point_filter

