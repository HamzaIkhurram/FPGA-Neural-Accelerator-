# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Setup Environment

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Process EEG Data

```powershell
python scripts/process_eeg.py
```

This downloads PhysioNet EEGMMIDB data and generates `data/eeg_data_Fc5.mem` for simulation.

### 3. Run Simulation

```powershell
# Compile design
cd sim
vsim -c -do "do compile_simple.do; quit -f"

# Run automated regression
cd ..
python regression/run_regression.py --config regression/configs/regression_simple.json
```

## 📊 What You'll Get

- **RTL Design:** 5 SystemVerilog modules
- **UVM Testbench:** Complete verification environment
- **Python Reference:** Golden model for comparison
- **Regression Framework:** Automated testing with reporting
- **Real Data:** Processed EEG signals from PhysioNet

## 🎯 Next Steps

1. Explore the RTL design in `rtl/`
2. Review UVM testbench in `tb/`
3. Check regression results in `sim/reports/`
4. Read full documentation in `README.md`

**Ready to go!** 🎉

