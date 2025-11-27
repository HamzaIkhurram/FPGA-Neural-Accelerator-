// AXI-Stream interface for UVM testbench

`timescale 1ns/1ps

interface axis_if #(
    parameter int DATA_WIDTH = 32
)(
    input logic clk,
    input logic rst_n
);

    logic [DATA_WIDTH-1:0]  tdata;
    logic                   tvalid;
    logic                   tready;
    logic                   tlast;
    logic [1:0]             tuser;
    
    // Clocking block for driver
    clocking drv_cb @(posedge clk);
        default input #1step output #1ns;
        output tdata;
        output tvalid;
        output tlast;
        input  tready;
    endclocking
    
    // Clocking block for monitor
    clocking mon_cb @(posedge clk);
        default input #1step;
        input tdata;
        input tvalid;
        input tready;
        input tlast;
        input tuser;
    endclocking
    
    modport master (
        clocking drv_cb,
        input clk, rst_n, tready,
        output tdata, tvalid, tlast
    );
    
    modport slave (
        clocking drv_cb,
        input clk, rst_n, tdata, tvalid, tlast,
        output tready
    );
    
    modport monitor (
        clocking mon_cb,
        input clk, rst_n
    );

endinterface : axis_if

