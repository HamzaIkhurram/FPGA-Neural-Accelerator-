# Data Processing Documentation

## EEG Dataset Processing

This project uses real EEG data from the PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB) for hardware verification.

### Dataset Source
- **Database**: PhysioNet EEGMMIDB
- **Subject**: 1
- **Runs**: Baseline open eyes (R01), Baseline closed eyes (R02)
- **Channels**: 64 EEG channels
- **Sampling Rate**: 160 Hz

### Processing Pipeline

1. **Data Download**
   - Automatic download via MNE-Python library
   - Stores in `~/mne_data/MNE-eegbci-data/`

2. **Preprocessing**
   - 1-40 Hz bandpass filter (FIR design)
   - Artifact removal
   - Channel standardization

3. **Extraction**
   - Single channel selection (Fc5)
   - 1000 sample window extraction
   - Fixed-point conversion (Q16.16 format)

4. **Fixed-Point Conversion**
   - Format: Q16.16 (16 integer bits, 16 fractional bits)
   - Scale factor: 2^16 = 65536
   - Range: -32768.0 to +32767.9999
   - Output: Hex-encoded .mem file for Verilog simulation

### Output Files

- `data/eeg_data_Fc5.mem`: Fixed-point hex format for RTL simulation
- Contains 1000 samples in 32-bit hex format (one per line)

### Usage

```python
python scripts/process_eeg.py
```

This generates the `.mem` file used by the testbench for real-world signal processing verification.

