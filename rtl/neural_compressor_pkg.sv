// Package containing parameters and types for neural signal compressor

package neural_compressor_pkg;

    // Data width parameters
    parameter int DATA_WIDTH = 32;        // Q16.16 fixed-point
    parameter int ADDR_WIDTH = 10;        // Memory address width
    parameter int FIFO_DEPTH = 16;        // Internal FIFO depth
    
    // Signal processing parameters
    parameter int FILTER_ORDER = 4;       // IIR filter order
    parameter int WINDOW_SIZE = 32;       // Spike detection window
    parameter int SPIKE_THRESHOLD = 32'h00050000; // Q16.16 = 5.0
    
    // Compression parameters
    parameter int MAX_RUN_LENGTH = 255;   // Max run-length for RLE
    parameter int DELTA_BITS = 16;        // Delta encoding bit width
    
    // AXI-Stream signal structure
    typedef struct packed {
        logic [DATA_WIDTH-1:0] tdata;
        logic                   tvalid;
        logic                   tlast;
        logic [DATA_WIDTH/8-1:0] tkeep;
    } axis_t;
    
    // Compression metadata
    typedef struct packed {
        logic [15:0] sample_count;
        logic [15:0] spike_count;
        logic [7:0]  compression_ratio;
        logic        overflow;
    } compress_stats_t;
    
    // Filter coefficients (Q16.16 fixed-point)
    // 4th order Butterworth bandpass 1-40Hz @ 160Hz sampling
    parameter logic [DATA_WIDTH-1:0] B_COEFF [0:4] = '{
        32'h00000D6B,  // b0 = 0.003435
        32'h00000000,  // b1 = 0
        32'hFFFF5A5A,  // b2 = -0.006870
        32'h00000000,  // b3 = 0
        32'h00000D6B   // b4 = 0.003435
    };
    
    parameter logic [DATA_WIDTH-1:0] A_COEFF [0:4] = '{
        32'h00010000,  // a0 = 1.0 (normalized)
        32'hFFFD8F5C,  // a1 = -2.609375
        32'h0002B852,  // a2 = 2.696289
        32'hFFFE4CCD,  // a3 = -1.658203
        32'h00003D71   // a4 = 0.239258
    };

endpackage : neural_compressor_pkg

