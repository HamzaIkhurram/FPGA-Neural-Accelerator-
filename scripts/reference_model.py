"""Python reference model for neural compressor verification implementing filtering, spike detection, and compression algorithms"""

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import os

class FixedPointQ16_16:
"""Fixed-point Q16.16 representation"""
    @staticmethod
    def to_fixed(value):
        return int(np.round(value * (1 << 16)))
    
    @staticmethod
    def to_float(value):
        """Convert Q16.16 fixed-point to float"""
        # Handle signed 32-bit integers
        if value & 0x80000000:
            value = value - 0x100000000
        return value / (1 << 16)
    
    @staticmethod
    def mult(a, b):
        # Sign extend for proper signed multiplication
        a = np.int64(a)
        b = np.int64(b)
        prod = (a * b) >> 16
        # Clamp to 32-bit
        return np.int32(prod & 0xFFFFFFFF)


class NeuralCompressorReference:
    """Reference model for the neural compressor"""
    
    def __init__(self):
        # Filter coefficients (Q16.16 fixed-point)
        # 4th order Butterworth bandpass 1-40Hz @ 160Hz
        self.b_coeff = [
            0x00000D6B,  # 0.003435
            0x00000000,  # 0
            -0x0000A5A6,  # -0.006870 (negative of 0xFFFF5A5A as two's complement)
            0x00000000,  # 0
            0x00000D6B   # 0.003435
        ]
        
        self.a_coeff = [
            0x00010000,  # 1.0
            -0x000270A4,  # -2.609375 (negative of 0xFFFD8F5C)
            0x0002B852,  # 2.696289
            -0x0001B333,  # -1.658203 (negative of 0xFFFE4CCD)
            0x00003D71   # 0.239258
        ]
        
        # Convert to float for scipy comparison
        self.b_float = [FixedPointQ16_16.to_float(x) for x in self.b_coeff]
        self.a_float = [FixedPointQ16_16.to_float(x) for x in self.a_coeff]
        
        # Spike detection parameters
        self.spike_threshold = FixedPointQ16_16.to_float(0x00050000)  # 5.0
        self.window_size = 32
        self.refractory_period = 8
        
        # Compression parameters
        self.rle_threshold = FixedPointQ16_16.to_float(0x00001999)  # 0.1
        self.max_run_length = 255
        
    def filter_signal(self, data):
        # Use scipy for floating-point reference
        filtered = signal.lfilter(self.b_float, self.a_float, data)
        return filtered
    
    def detect_spikes(self, data):
        """Detect spikes using threshold and windowing"""
        spikes = np.zeros(len(data), dtype=bool)
        refractory_counter = 0
        
        # Wait for window to fill
        for i in range(self.window_size, len(data)):
            if refractory_counter > 0:
                refractory_counter -= 1
                continue
            
            # Check threshold
            if abs(data[i]) > self.spike_threshold:
                spikes[i] = True
                refractory_counter = self.refractory_period
        
        return spikes
    
    def compress_signal(self, data, spikes):
        compressed = []
        packet_types = []  # 0=delta, 1=RLE, 2=spike, 3=literal
        
        prev_value = 0
        run_count = 0
        run_value = 0
        in_run = False
        
        for i, value in enumerate(data):
            if spikes[i]:
                # Emit pending run first
                if in_run and run_count > 0:
                    compressed.append((run_count, run_value))
                    packet_types.append(1)  # RLE
                    in_run = False
                    run_count = 0
                
                # Emit spike
                compressed.append(value)
                packet_types.append(2)  # Spike
                prev_value = value
                
            else:
                delta = value - prev_value
                
                if abs(delta) < self.rle_threshold:
                    # Continue or start run
                    if not in_run:
                        run_value = value
                        run_count = 1
                        in_run = True
                    else:
                        run_count += 1
                    
                    # Force emit if max length
                    if run_count >= self.max_run_length:
                        compressed.append((run_count, run_value))
                        packet_types.append(1)  # RLE
                        prev_value = run_value
                        in_run = False
                        run_count = 0
                else:
                    # Emit pending run
                    if in_run and run_count > 0:
                        compressed.append((run_count, run_value))
                        packet_types.append(1)  # RLE
                        prev_value = run_value
                        in_run = False
                        run_count = 0
                    
                    # Emit delta
                    compressed.append(delta)
                    packet_types.append(0)  # Delta
                    prev_value = value
        
        # Emit final run if any
        if in_run and run_count > 0:
            compressed.append((run_count, run_value))
            packet_types.append(1)  # RLE
        
        return compressed, packet_types
    
    def process(self, input_data):
        """Full processing pipeline"""
        # Filter
        filtered = self.filter_signal(input_data)
        
        # Detect spikes
        spikes = self.detect_spikes(filtered)
        
        # Compress
        compressed, packet_types = self.compress_signal(filtered, spikes)
        
        # Calculate statistics
        stats = {
            'input_samples': len(input_data),
            'output_packets': len(compressed),
            'compression_ratio': (len(compressed) / len(input_data)) * 100 if len(input_data) > 0 else 0,
            'spike_count': np.sum(spikes)
        }
        
        return {
            'filtered': filtered,
            'spikes': spikes,
            'compressed': compressed,
            'packet_types': packet_types,
            'stats': stats
        }


def load_eeg_mem_file(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                # Parse hex value
                value = int(line, 16)
                # Convert to signed if needed
                if value & 0x80000000:
                    value = value - 0x100000000
                data.append(value)
    
    # Convert from Q16.16 to float
    data_float = [FixedPointQ16_16.to_float(x) for x in data]
    return np.array(data_float)


def visualize_results(input_data, results, output_file='analysis.png'):
    """Create visualization of processing pipeline"""
    fig, axes = plt.subplots(4, 1, figsize=(12, 10))
    
    time = np.arange(len(input_data))
    
    # Original signal
    axes[0].plot(time, input_data, 'b-', linewidth=0.5)
    axes[0].set_title('Original EEG Signal')
    axes[0].set_ylabel('Amplitude')
    axes[0].grid(True, alpha=0.3)
    
    # Filtered signal
    axes[1].plot(time, results['filtered'], 'g-', linewidth=0.5)
    axes[1].set_title('Filtered Signal (1-40Hz)')
    axes[1].set_ylabel('Amplitude')
    axes[1].grid(True, alpha=0.3)
    
    # Spike detection
    axes[2].plot(time, results['filtered'], 'g-', linewidth=0.5, alpha=0.5)
    spike_times = np.where(results['spikes'])[0]
    if len(spike_times) > 0:
        axes[2].scatter(spike_times, results['filtered'][spike_times], 
                       color='r', marker='o', s=50, label='Spikes')
    axes[2].set_title(f"Spike Detection ({results['stats']['spike_count']} spikes)")
    axes[2].set_ylabel('Amplitude')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    # Compression info
    stats_text = (
        f"Input Samples: {results['stats']['input_samples']}\n"
        f"Output Packets: {results['stats']['output_packets']}\n"
        f"Compression Ratio: {results['stats']['compression_ratio']:.2f}%\n"
        f"Spike Count: {results['stats']['spike_count']}"
    )
    
    # Packet type distribution
    packet_type_names = ['Delta', 'RLE', 'Spike', 'Literal']
    packet_counts = [results['packet_types'].count(i) for i in range(4)]
    
    axes[3].bar(packet_type_names, packet_counts, color=['blue', 'green', 'red', 'orange'])
    axes[3].set_title('Compression Packet Distribution')
    axes[3].set_ylabel('Count')
    axes[3].text(0.02, 0.95, stats_text, transform=axes[3].transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    axes[3].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"Visualization saved to {output_file}")
    plt.close()


def main():
    print("=" * 70)
    print("Neural Compressor Reference Model")
    print("=" * 70)
    
    # Load EEG data
    eeg_file = "processed_data/eeg_data_Fc5.mem"
    if not os.path.exists(eeg_file):
        print(f"Error: {eeg_file} not found!")
        print("Run process_eeg.py first to generate the dataset.")
        return
    
    print(f"\nLoading EEG data from {eeg_file}...")
    input_data = load_eeg_mem_file(eeg_file)
    print(f"Loaded {len(input_data)} samples")
    
    # Create reference model
    model = NeuralCompressorReference()
    
    # Process data
    print("\nProcessing...")
    results = model.process(input_data)
    
    # Print statistics
    print("\n" + "=" * 70)
    print("Processing Results")
    print("=" * 70)
    print(f"Input samples:        {results['stats']['input_samples']}")
    print(f"Output packets:       {results['stats']['output_packets']}")
    print(f"Compression ratio:    {results['stats']['compression_ratio']:.2f}%")
    print(f"Spikes detected:      {results['stats']['spike_count']}")
    print("=" * 70)
    
    # Packet type breakdown
    packet_types = results['packet_types']
    print("\nPacket Type Distribution:")
    print(f"  Delta:    {packet_types.count(0)} packets")
    print(f"  RLE:      {packet_types.count(1)} packets")
    print(f"  Spike:    {packet_types.count(2)} packets")
    print(f"  Literal:  {packet_types.count(3)} packets")
    
    # Generate visualization
    print("\nGenerating visualization...")
    visualize_results(input_data, results, 'processed_data/analysis.png')
    
    # Save compressed output for verification
    np.save('processed_data/reference_filtered.npy', results['filtered'])
    np.save('processed_data/reference_spikes.npy', results['spikes'])
    print("\nReference outputs saved for verification.")
    
    print("\n[OK] Reference model complete!")


if __name__ == "__main__":
    main()

