Wave Dump Analyzer - Production Quality
Senior Staff Engineer: Automated signal analysis, pattern detection
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class SignalTransition:
"""Signal transition event"""
    time: float
    signal: str
    from_value: str
    to_value: str
    transition_type: str  # 'rising', 'falling', 'change'


@dataclass
class WaveAnalysis:
    signal_count: int
    transitions: List[SignalTransition]
    max_sim_time: float
    signals_analyzed: List[str]
    errors_found: List[str]
    warnings_found: List[str]


class WaveAnalyzer:
    """
    Analyze wave dump files for automated verification
    
    Features:
    - Parse VCD/WLF/FST files
    - Detect signal transitions
    - Find timing violations
    - Extract key events
    - Generate analysis reports
    
    def __init__(self, work_dir: Path):
        """
        Initialize wave analyzer
        
        Args:
            work_dir: Working directory containing wave files
        self.work_dir = Path(work_dir)
        logger.info(f"Initialized WaveAnalyzer: work_dir={self.work_dir}")
    
    def find_wave_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
        """
        Find wave dump files
        
        Args:
            patterns: File patterns to search
            
        Returns:
            List of wave file paths
        if patterns is None:
            patterns = ['*.vcd', '*.wlf', '*.fst', '*.fsdb']
        
        wave_files = []
        for pattern in patterns:
            wave_files.extend(self.work_dir.rglob(pattern))
        
        logger.info(f"Found {len(wave_files)} wave file(s)")
        return wave_files
    
    def analyze_vcd(self, vcd_file: Path) -> WaveAnalysis:
        """
        Analyze VCD (Value Change Dump) file
        
        Args:
            vcd_file: Path to VCD file
            
        Returns:
            WaveAnalysis object
        logger.info(f"Analyzing VCD file: {vcd_file}")
        
        signals = {}
        transitions = []
        max_time = 0.0
        errors = []
        warnings = []
        
        try:
            with open(vcd_file, 'r') as f:
                current_time = 0.0
                
                for line in f:
                    line = line.strip()
                    
                    # Parse time stamp
                    if line.startswith('#'):
                        current_time = float(line[1:])
                        max_time = max(max_time, current_time)
                    
                    # Parse value changes
                    elif line and line[0] in '01xXzZ':
                        # Format: 0signal_id or 1signal_id
                        match = re.match(r'([01xXzZ])(\w+)', line)
                        if match:
                            value = match.group(1)
                            signal_id = match.group(2)
                            
                            if signal_id in signals:
                                prev_value = signals[signal_id]
                                if value != prev_value:
                                    transitions.append(SignalTransition(
                                        time=current_time,
                                        signal=signal_id,
                                        from_value=prev_value,
                                        to_value=value,
                                        transition_type='change'
                                    ))
                            signals[signal_id] = value
                    
                    # Look for errors/warnings in comments
                    if 'error' in line.lower() or 'fatal' in line.lower():
                        errors.append(f"{current_time}: {line}")
                    elif 'warning' in line.lower():
                        warnings.append(f"{current_time}: {line}")
        
        except Exception as e:
            logger.error(f"Error analyzing VCD file: {e}", exc_info=True)
            errors.append(f"Analysis error: {str(e)}")
        
        return WaveAnalysis(
            signal_count=len(signals),
            transitions=transitions,
            max_sim_time=max_time,
            signals_analyzed=list(signals.keys()),
            errors_found=errors,
            warnings_found=warnings
        )
    
    def analyze_transcript_for_errors(self, transcript_file: Path) -> Dict[str, List[str]]:
        """
        Analyze simulation transcript for errors/warnings
        
        Args:
            transcript_file: Path to transcript/log file
            
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        errors = []
        warnings = []
        
        try:
            with open(transcript_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line_lower = line.lower()
                    
                    # Look for error patterns
                    if any(keyword in line_lower for keyword in ['error', 'fatal', 'failed']):
                        errors.append(f"Line {line_num}: {line.strip()}")
                    
                    # Look for warning patterns
                    elif 'warning' in line_lower:
                        warnings.append(f"Line {line_num}: {line.strip()}")
        
        except Exception as e:
            logger.error(f"Error reading transcript: {e}", exc_info=True)
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def check_signal_stability(self, analysis: WaveAnalysis, 
                              signal_name: str,
                              stable_time: float) -> bool:
        """
        Check if signal is stable for specified time
        
        Args:
            analysis: WaveAnalysis object
            signal_name: Signal to check
            stable_time: Required stable time
            
        Returns:
            True if signal is stable
        # Filter transitions for this signal
        signal_transitions = [
            t for t in analysis.transitions
            if signal_name in t.signal
        ]
        
        if len(signal_transitions) < 2:
            return True  # Signal didn't change
        
        # Check time between transitions
        for i in range(len(signal_transitions) - 1):
            time_diff = signal_transitions[i+1].time - signal_transitions[i].time
            if time_diff < stable_time:
                return False
        
        return True
    
    def detect_setup_hold_violations(self, analysis: WaveAnalysis,
                                     clock_signal: str,
                                     data_signal: str,
                                     setup_time: float,
                                     hold_time: float) -> List[Dict]:
        """
        Detect setup/hold time violations
        
        Args:
            analysis: WaveAnalysis object
            clock_signal: Clock signal name
            data_signal: Data signal name
            setup_time: Required setup time
            hold_time: Required hold time
            
        Returns:
            List of violations found
        violations = []
        
        # Find clock edges
        clock_edges = [
            t for t in analysis.transitions
            if clock_signal in t.signal and t.to_value == '1'
        ]
        
        # Find data changes
        data_changes = [
            t for t in analysis.transitions
            if data_signal in t.signal
        ]
        
        # Check setup/hold around each clock edge
        for edge in clock_edges:
            # Check setup time
            data_changes_before = [
                d for d in data_changes
                if edge.time - setup_time <= d.time < edge.time
            ]
            
            if data_changes_before:
                violations.append({
                    'type': 'setup',
                    'clock_time': edge.time,
                    'data_time': data_changes_before[0].time,
                    'violation': edge.time - data_changes_before[0].time
                })
            
            # Check hold time
            data_changes_after = [
                d for d in data_changes
                if edge.time < d.time <= edge.time + hold_time
            ]
            
            if data_changes_after:
                violations.append({
                    'type': 'hold',
                    'clock_time': edge.time,
                    'data_time': data_changes_after[0].time,
                    'violation': data_changes_after[0].time - edge.time
                })
        
        return violations
    
    def generate_analysis_report(self, analysis: WaveAnalysis, 
                                output_file: Optional[Path] = None) -> Path:
        """
        Generate wave analysis report
        
        Args:
            analysis: WaveAnalysis object
            output_file: Optional output file path
            
        Returns:
            Path to generated report
        if output_file is None:
            output_file = self.work_dir / 'wave_analysis.txt'
        else:
            output_file = Path(output_file)
        
        with open(output_file, 'w') as f:
            f.write(f"""
{'='*70}
Wave Dump Analysis Report
{'='*70}
Signals Analyzed:     {analysis.signal_count}
Transitions Detected: {len(analysis.transitions)}
Max Simulation Time:  {analysis.max_sim_time:.2f} ps

Signals:
{chr(10).join(f'  - {sig}' for sig in analysis.signals_analyzed[:20])}
  ... ({len(analysis.signals_analyzed)} total)

{'='*70}
Errors Found: {len(analysis.errors_found)}
{'='*70}
            for error in analysis.errors_found:
                f.write(f"{error}\n")
            
            f.write(f"""
{'='*70}
Warnings Found: {len(analysis.warnings_found)}
{'='*70}
            for warning in analysis.warnings_found[:10]:  # Limit warnings
                f.write(f"{warning}\n")
        
        logger.info(f"Generated wave analysis report: {output_file}")
        return output_file

