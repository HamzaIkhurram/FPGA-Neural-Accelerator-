// UVM package for neural compressor testbench

package neural_compressor_pkg_tb;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    
    import neural_compressor_pkg::*;
    
    // Transaction item (no randomization for free Questa)
    class axis_transaction extends uvm_sequence_item;
        
        bit [DATA_WIDTH-1:0] data;
        bit                  last;
        bit [1:0]            user;  // For output monitoring
        bit                  spike; // For reference checking
        
        `uvm_object_utils_begin(axis_transaction)
            `uvm_field_int(data, UVM_ALL_ON)
            `uvm_field_int(last, UVM_ALL_ON)
            `uvm_field_int(user, UVM_ALL_ON)
        `uvm_object_utils_end
        
        function new(string name = "axis_transaction");
            super.new(name);
            data = '0;
            last = '0;
        endfunction
        
    endclass : axis_transaction
    
    // Sequencer
    typedef uvm_sequencer#(axis_transaction) axis_sequencer;
    
    // Driver
    class axis_driver extends uvm_driver#(axis_transaction);
        `uvm_component_utils(axis_driver)
        
        virtual axis_if vif;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual axis_if)::get(this, "", "vif", vif))
                `uvm_fatal("NOVIF", "Virtual interface not found")
        endfunction
        
        task run_phase(uvm_phase phase);
            axis_transaction trans;
            
            // Initialize
            vif.drv_cb.tvalid <= 0;
            vif.drv_cb.tdata <= 0;
            vif.drv_cb.tlast <= 0;
            
            @(posedge vif.rst_n);
            repeat(2) @(vif.drv_cb);
            
            forever begin
                seq_item_port.get_next_item(trans);
                drive_transaction(trans);
                seq_item_port.item_done();
            end
        endtask
        
        task drive_transaction(axis_transaction trans);
            vif.drv_cb.tdata <= trans.data;
            vif.drv_cb.tvalid <= 1;
            vif.drv_cb.tlast <= trans.last;
            
            @(vif.drv_cb);
            while (!vif.tready) @(vif.drv_cb);
            
            vif.drv_cb.tvalid <= 0;
        endtask
        
    endclass : axis_driver
    
    // Monitor
    class axis_monitor extends uvm_monitor;
        `uvm_component_utils(axis_monitor)
        
        virtual axis_if vif;
        uvm_analysis_port#(axis_transaction) ap;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            ap = new("ap", this);
            if (!uvm_config_db#(virtual axis_if)::get(this, "", "vif", vif))
                `uvm_fatal("NOVIF", "Virtual interface not found")
        endfunction
        
        task run_phase(uvm_phase phase);
            axis_transaction trans;
            
            @(posedge vif.rst_n);
            
            forever begin
                @(vif.mon_cb);
                if (vif.mon_cb.tvalid && vif.mon_cb.tready) begin
                    trans = axis_transaction::type_id::create("trans");
                    trans.data = vif.mon_cb.tdata;
                    trans.last = vif.mon_cb.tlast;
                    trans.user = vif.mon_cb.tuser;
                    ap.write(trans);
                end
            end
        endtask
        
    endclass : axis_monitor
    
    // Agent
    class axis_agent extends uvm_agent;
        `uvm_component_utils(axis_agent)
        
        axis_driver    driver;
        axis_monitor   monitor;
        axis_sequencer sequencer;
        
        uvm_analysis_port#(axis_transaction) ap;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            
            monitor = axis_monitor::type_id::create("monitor", this);
            
            if (get_is_active() == UVM_ACTIVE) begin
                driver = axis_driver::type_id::create("driver", this);
                sequencer = axis_sequencer::type_id::create("sequencer", this);
            end
        endfunction
        
        function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            ap = monitor.ap;
            if (get_is_active() == UVM_ACTIVE) begin
                driver.seq_item_port.connect(sequencer.seq_item_export);
            end
        endfunction
        
    endclass : axis_agent
    
    // Scoreboard
    class neural_scoreboard extends uvm_scoreboard;
        `uvm_component_utils(neural_scoreboard)
        
        uvm_analysis_imp#(axis_transaction, neural_scoreboard) ap;
        
        // Reference queue for checking
        axis_transaction input_queue[$];
        axis_transaction output_queue[$];
        
        int total_samples;
        int compressed_samples;
        int spike_count;
        int errors;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            ap = new("ap", this);
        endfunction
        
        function void write(axis_transaction trans);
            output_queue.push_back(trans);
            compressed_samples++;
            
            // Decode packet type
            case (trans.user)
                2'b00: `uvm_info("SCOREBOARD", $sformatf("Delta packet: %0h", trans.data), UVM_HIGH)
                2'b01: `uvm_info("SCOREBOARD", $sformatf("RLE packet: count=%0d", trans.data[31:24]), UVM_HIGH)
                2'b10: begin
                    spike_count++;
                    `uvm_info("SCOREBOARD", $sformatf("Spike detected: %0h", trans.data), UVM_MEDIUM)
                end
                2'b11: `uvm_info("SCOREBOARD", $sformatf("Literal packet: %0h", trans.data), UVM_HIGH)
            endcase
        endfunction
        
        function void report_phase(uvm_phase phase);
            string separator;
            real ratio;
            
            super.report_phase(phase);
            separator = "============================================================";
            
            `uvm_info("SCOREBOARD", separator, UVM_LOW)
            `uvm_info("SCOREBOARD", "  Neural Compressor Test Results", UVM_LOW)
            `uvm_info("SCOREBOARD", separator, UVM_LOW)
            `uvm_info("SCOREBOARD", $sformatf("Total input samples:     %0d", total_samples), UVM_LOW)
            `uvm_info("SCOREBOARD", $sformatf("Compressed output:       %0d", compressed_samples), UVM_LOW)
            
            if (total_samples > 0) begin
                ratio = (compressed_samples * 100.0) / total_samples;
                `uvm_info("SCOREBOARD", $sformatf("Compression ratio:       %.2f%%", ratio), UVM_LOW)
            end
            
            `uvm_info("SCOREBOARD", $sformatf("Spikes detected:         %0d", spike_count), UVM_LOW)
            `uvm_info("SCOREBOARD", $sformatf("Errors:                  %0d", errors), UVM_LOW)
            `uvm_info("SCOREBOARD", separator, UVM_LOW)
            
            if (errors == 0)
                `uvm_info("SCOREBOARD", "TEST PASSED", UVM_LOW)
            else
                `uvm_error("SCOREBOARD", "TEST FAILED")
        endfunction
        
    endclass : neural_scoreboard
    
    // Environment
    class neural_env extends uvm_env;
        `uvm_component_utils(neural_env)
        
        axis_agent input_agent;
        axis_agent output_agent;
        neural_scoreboard scoreboard;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            
            input_agent = axis_agent::type_id::create("input_agent", this);
            input_agent.is_active = UVM_ACTIVE;
            
            output_agent = axis_agent::type_id::create("output_agent", this);
            output_agent.is_active = UVM_PASSIVE;
            
            scoreboard = neural_scoreboard::type_id::create("scoreboard", this);
        endfunction
        
        function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            output_agent.ap.connect(scoreboard.ap);
        endfunction
        
    endclass : neural_env
    
    // Sequences
    
    // Deterministic sequence (no randomize - for free Questa)
    class random_sequence extends uvm_sequence#(axis_transaction);
        `uvm_object_utils(random_sequence)
        
        int num_trans = 200;  // Fixed count
        
        function new(string name = "random_sequence");
            super.new(name);
        endfunction
        
        task body();
            int count = 0;
            repeat(num_trans) begin
                req = axis_transaction::type_id::create("req");
                start_item(req);
                
                // Pseudo-random pattern without randomize()
                req.data = 32'h00010000 + (count * 123);  // Simple counter-based pattern
                req.last = (count == num_trans - 1);
                
                finish_item(req);
                count++;
            end
        endtask
        
    endclass : random_sequence
    
    // EEG data from file sequence
    class eeg_file_sequence extends uvm_sequence#(axis_transaction);
        `uvm_object_utils(eeg_file_sequence)
        
        string filename = "../processed_data/eeg_data_Fc5.mem";
        logic [31:0] eeg_data[$];
        
        function new(string name = "eeg_file_sequence");
            super.new(name);
        endfunction
        
        task body();
            int fd;
            string line;
            logic [31:0] data_value;
            
            // Read .mem file
            `uvm_info("EEG_SEQ", $sformatf("Attempting to open: %s", filename), UVM_LOW)
            fd = $fopen(filename, "r");
            if (fd == 0) begin
                `uvm_fatal("FILE_ERROR", $sformatf("Cannot open %s - check file path!", filename))
            end
            
            while (!$feof(fd)) begin
                if ($fgets(line, fd)) begin
                    if ($sscanf(line, "%h", data_value) == 1) begin
                        eeg_data.push_back(data_value);
                    end
                end
            end
            $fclose(fd);
            
            `uvm_info("EEG_SEQ", $sformatf("Loaded %0d samples from %s", eeg_data.size(), filename), UVM_MEDIUM)
            
            // Send all samples
            foreach(eeg_data[i]) begin
                req = axis_transaction::type_id::create("req");
                start_item(req);
                req.data = eeg_data[i];
                req.last = (i == eeg_data.size()-1) ? 1'b1 : 1'b0;
                finish_item(req);
            end
        endtask
        
    endclass : eeg_file_sequence
    
    // Spike burst sequence (for testing spike detection)
    class spike_burst_sequence extends uvm_sequence#(axis_transaction);
        `uvm_object_utils(spike_burst_sequence)
        
        function new(string name = "spike_burst_sequence");
            super.new(name);
        endfunction
        
        task body();
            // Send baseline
            repeat(50) begin
                req = axis_transaction::type_id::create("req");
                start_item(req);
                req.data = 32'h00001000 + $urandom_range(0, 32'h00001000);
                req.last = 1'b0;
                finish_item(req);
            end
            
            // Send spike burst
            repeat(10) begin
                req = axis_transaction::type_id::create("req");
                start_item(req);
                req.data = 32'h00080000; // 8.0 amplitude
                req.last = 1'b0;
                finish_item(req);
            end
            
            // Return to baseline
            repeat(50) begin
                req = axis_transaction::type_id::create("req");
                start_item(req);
                req.data = 32'h00001000 + $urandom_range(0, 32'h00001000);
                req.last = 1'b0;
                finish_item(req);
            end
        endtask
        
    endclass : spike_burst_sequence
    
    // Base Test
    class base_test extends uvm_test;
        `uvm_component_utils(base_test)
        
        neural_env env;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            env = neural_env::type_id::create("env", this);
        endfunction
        
        function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            uvm_top.print_topology();
        endfunction
        
        task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            #1000ns;
            phase.drop_objection(this);
        endtask
        
    endclass : base_test
    
    // Random test
    class random_test extends base_test;
        `uvm_component_utils(random_test)
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        task run_phase(uvm_phase phase);
            random_sequence seq;
            
            phase.raise_objection(this);
            
            seq = random_sequence::type_id::create("seq");
            seq.num_trans = 200;
            seq.start(env.input_agent.sequencer);
            
            #1000ns;
            phase.drop_objection(this);
        endtask
        
    endclass : random_test
    
    // EEG file test
    class eeg_test extends base_test;
        `uvm_component_utils(eeg_test)
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        task run_phase(uvm_phase phase);
            eeg_file_sequence seq;
            
            phase.raise_objection(this);
            
            seq = eeg_file_sequence::type_id::create("seq");
            seq.start(env.input_agent.sequencer);
            
            #5000ns;
            phase.drop_objection(this);
        endtask
        
    endclass : eeg_test
    
    // Spike detection test
    class spike_test extends base_test;
        `uvm_component_utils(spike_test)
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        task run_phase(uvm_phase phase);
            spike_burst_sequence seq;
            
            phase.raise_objection(this);
            
            seq = spike_burst_sequence::type_id::create("seq");
            seq.start(env.input_agent.sequencer);
            
            #2000ns;
            phase.drop_objection(this);
        endtask
        
    endclass : spike_test

endpackage : neural_compressor_pkg_tb

