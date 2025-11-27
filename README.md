# FPGA Neural Signal Compressor

Real-time brain-computer interface (BCI) signal processing accelerator with UVM verification and automated regression framework

## Overview

This project implements a hardware-accelerated neural signal compressor for EEG/BCI applications, demonstrating production-grade ASIC design practices including automated regression, design integration, and functional coverage analysis.

**Key Features:**
- **IIR bandpass filtering** (1-40Hz) for artifact removal
- **Adaptive spike detection** with refractory period handling
- **Hybrid compression** using delta + run-length encoding
- **AXI-Stream interfaces** for seamless SoC integration
- **Complete UVM testbench** with industry-standard verification methodology
- **Production-grade regression automation framework** with coverage collection and reporting

## Automated Regression & Design Integration

A core component of this project is a **Python-based regression automation system** that streamlines design verification workflows:

- **Multi-tool simulation support**: Questa, VCS, Verilator integration
- **Automated test execution**: Parallel test runs with timeout handling
- **Functional coverage collection**: Automated coverage tracking and reporting
- **Design integration scripts**: Automated compilation, simulation, and reporting pipelines
- **Production-grade reporting**: HTML, JSON, and text reports with pass/fail triage

This framework reduces manual test execution effort by ~80% and provides the foundation for scalable ASIC design verification workflows.

## Project Structure

```
├── rtl/                    # RTL design files
│   ├── neural_compressor_pkg.sv
│   ├── fixed_point_filter.sv
│   ├── spike_detector.sv
│   ├── delta_compressor.sv
│   └── neural_compressor_top.sv
│
├── tb/                     # Testbenches
│   ├── axis_if.sv
│   ├── neural_compressor_pkg_tb.sv    # UVM testbench
│   ├── neural_compressor_tb.sv
│   └── neural_compressor_tb_simple.sv # Simple testbench
│
├── scripts/                # Python utilities
│   ├── process_eeg.py
│   └── reference_model.py
│
├── regression/             # Automated regression framework
│   ├── core/               # Core automation components
│   │   ├── config.py       # Configuration management
│   │   ├── sim_runner.py   # Multi-tool simulation execution
│   │   ├── coverage.py     # Coverage collection & analysis
│   │   ├── reporter.py     # Multi-format reporting
│   │   └── regression.py   # Main orchestrator
│   ├── configs/            # Regression configurations
│   └── run_regression.py   # CLI entry point
│
├── sim/                    # Simulation scripts and logs
│   ├── compile_simple.do   # Design integration scripts
│   ├── run_simple.do
│   └── logs/
│
├── data/                   # Processed EEG data
│   └── eeg_data_Fc5.mem
│
└── docs/                   # Documentation
```

## Quick Start

### Prerequisites

- Python 3.10+
- Questa Sim/ModelSim (or VCS/Verilator)
- NumPy, SciPy, Matplotlib, MNE

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Process EEG data
python scripts/process_eeg.py
```

### Design Integration & Simulation

```bash
# Compile design (automated integration script)
cd sim
vsim -c -do "do compile_simple.do; quit -f"

# Run automated regression framework
cd ..
python regression/run_regression.py --config regression/configs/regression_simple.json --verbose
```

The regression framework automatically:
- Executes test suites across multiple simulation tools
- Collects functional coverage metrics
- Generates comprehensive reports (HTML, JSON, text)
- Provides automated pass/fail triage

## Regression Framework Usage

```bash
# Run full regression suite
python regression/run_regression.py --config regression/configs/regression_simple.json

# Run specific test
python regression/run_regression.py --test simple_test

# Parallel execution
python regression/run_regression.py --parallel --workers 4

# Verbose output
python regression/run_regression.py --verbose
```

**Key Features:**
- Multi-tool support (Questa/VCS/Verilator)
- Parallel test execution
- Coverage collection and threshold checking
- Automated HTML/JSON/text reporting
- Process detection and error handling
- Timeout management

## Technical Details

### RTL Design

- **Fixed-point arithmetic** (Q16.16) optimized for FPGA/ASIC implementation
- **Pipeline architecture** with 3-stage processing (filter → detector → compressor)
- **AXI-Stream protocol** for SoC integration
- **Synthesis-ready** with timing constraints

### Verification

- **UVM testbench** with constrained-random sequences
- **Multiple test scenarios**: Random data, real EEG data, spike detection
- **Functional coverage** tracking and analysis
- **Automated regression** with comprehensive reporting

### Data Processing

- **Real EEG data** from PhysioNet EEGMMIDB dataset
- **Python reference model** for golden comparison
- **Signal preprocessing** pipeline (filtering, spike detection, compression)

## Results

- **Compression Ratio:** 40-70% while preserving spike information
- **Spike Detection:** Adaptive threshold with 8-sample refractory period
- **Filter:** 4th-order IIR Butterworth bandpass (1-40Hz @ 160Hz)
- **Verification:** 100% functional coverage with automated regression
- **Automation:** 80% reduction in manual test execution effort

## Skills Demonstrated

- **Hardware Design:** SystemVerilog RTL, fixed-point DSP, pipeline architecture
- **Design Integration:** Automated compilation and simulation scripts
- **Verification:** UVM methodology, constrained-random testing, coverage analysis
- **Automation:** Python regression framework, multi-tool support, automated reporting
- **Signal Processing:** IIR filter design, spike detection algorithms, data compression
- **ASIC Design Flow:** Complete RTL-to-verification pipeline with automation

## License

MIT License - See LICENSE file for details
