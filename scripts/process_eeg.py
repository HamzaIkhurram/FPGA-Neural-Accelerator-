
import mne
import numpy as np
import os

# --- Configuration ---
SUBJECT = 1
RUNS = [1, 2]  # Run 1: Baseline, open eyes; Run 2: Baseline, closed eyes
DATA_DIR = os.path.join(os.path.expanduser("~"), "mne_data", "MNE-eegbci-data", "files", "eegmmidb", "1.0.0")
OUTPUT_DIR = "processed_data"

def load_and_preprocess(subject, runs):
    Loads EDF files for a specific subject and runs using MNE.
    Returns raw data and events.
    """
# Format filenames based on PhysioNet structure: S001/S001R01.edf
    subject_str = f"S{subject:03d}"
    files = []
    for run in runs:
        run_str = f"R{run:02d}"
        file_path = os.path.join(DATA_DIR, subject_str, f"{subject_str}{run_str}.edf")
        if os.path.exists(file_path):
            files.append(file_path)
        else:
            print(f"Warning: File not found: {file_path}")

    if not files:
        raise FileNotFoundError("No EDF files found. Ensure dataset is downloaded.")

    # Load data
    raws = []
    for f in files:
        raw = mne.io.read_raw_edf(f, preload=True)
        raws.append(raw)
    
    # Concatenate runs if multiple
    raw = mne.concatenate_raws(raws)
    
    # Standardize channel names (strip '.')
    mne.rename_channels(raw.info, lambda x: x.strip('.'))
    
    return raw

def extract_data(raw):
    Extracts signal data as numpy array and annotations.
    """
    # Get data as (n_channels, n_times)
    data = raw.get_data()
    
    # Get events/annotations
    # For EEGMMIDB, annotations are usually stored in the raw object
    events, event_id = mne.events_from_annotations(raw)
    
    return data, events, event_id, raw.info['sfreq']

def to_fixed_point(data, integer_bits=16, fractional_bits=16):
    Converts floating point data to fixed point representation.
    Format: Q(integer_bits).(fractional_bits)
    """
    scale_factor = 1 << fractional_bits
    
    # Clamp values to avoid overflow
    max_val = (1 << (integer_bits + fractional_bits - 1)) - 1
    min_val = -(1 << (integer_bits + fractional_bits - 1))
    
    fixed_data = np.round(data * scale_factor).astype(np.int64)
    fixed_data = np.clip(fixed_data, min_val, max_val)
    
    return fixed_data

def write_mem_file(filename, data):
    Writes data to a .mem file (hex format) for Verilog/SystemVerilog $readmemh.
    """
    with open(filename, 'w') as f:
        for sample in data:
            # Convert to hex, handle negative numbers using two's complement masking
            hex_val = f"{(sample & 0xFFFFFFFF):08X}" 
            f.write(f"{hex_val}\n")
    print(f"Written {filename}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Loading data for Subject {SUBJECT}, Runs {RUNS}...")
    try:
        raw = load_and_preprocess(SUBJECT, RUNS)
    except Exception as e:
        print(f"Error loading data: {e}")
        # Fallback: Try to download if missing (simple check)
        print("Attempting to download missing data...")
        mne.datasets.eegbci.load_data(SUBJECT, RUNS, update_path=True)
        raw = load_and_preprocess(SUBJECT, RUNS)

    print("Preprocessing...")
    # Optional: Filter data (e.g., 1-40Hz bandpass)
    raw.filter(1., 40., fir_design='firwin', skip_by_annotation='edge')
    
    data, events, event_id, fs = extract_data(raw)
    print(f"Data shape: {data.shape}, Sampling Rate: {fs}Hz")
    print(f"Events: {event_id}")

    # Select a single channel for demo (e.g., Cz usually around index 9 or similar, let's pick Ch 0)
    # EEGMMIDB channels are typically 64.
    channel_idx = 0 
    channel_name = raw.ch_names[channel_idx]
    print(f"Extracting Channel {channel_name} for hardware simulation...")
    
    single_channel_data = data[channel_idx, :1000] # First 1000 samples
    
    print("Converting to Fixed-Point (Q16.16)...")
    fixed_point_data = to_fixed_point(single_channel_data)
    
    mem_filename = os.path.join(OUTPUT_DIR, f"eeg_data_{channel_name}.mem")
    write_mem_file(mem_filename, fixed_point_data)

    # Save raw numpy array for reference
    np.save(os.path.join(OUTPUT_DIR, "raw_eeg.npy"), data)
    print("Done.")

if __name__ == "__main__":
    main()


