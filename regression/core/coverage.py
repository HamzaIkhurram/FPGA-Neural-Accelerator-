Coverage Collector - Production Quality
Senior Staff Engineer: Hierarchical analysis, threshold checking, merging
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess

from regression.core.config import CoverageConfig

logger = logging.getLogger(__name__)


@dataclass
class CoverageMetrics:
"""Coverage metrics for a module or entire design"""
    line_coverage: float = 0.0
    toggle_coverage: float = 0.0
    fsm_coverage: float = 0.0
    expression_coverage: float = 0.0
    branch_coverage: float = 0.0
    condition_coverage: float = 0.0
    
    def meets_thresholds(self, thresholds: Dict[str, float]) -> Tuple[bool, List[str]]:
        Check if metrics meet thresholds
        
        Returns:
            (passed, list of failing metrics)
        """
        failed = []
        
        for metric_name, threshold in thresholds.items():
            metric_value = getattr(self, metric_name, 0.0)
            if metric_value < threshold:
                failed.append(f"{metric_name}: {metric_value:.2f}% < {threshold:.2f}%")
        
        return (len(failed) == 0, failed)


@dataclass
class ModuleCoverage:
    module_name: str
    metrics: CoverageMetrics
    lines_covered: int = 0
    lines_total: int = 0


class CoverageCollector:
    """
    Collect and analyze functional coverage
    
    Supports:
    - Questa (.ucdb files)
    - VCS (.acdb files)
    - Merging multiple coverage databases
    - Hierarchical module breakdown
    - Threshold checking
    
    def __init__(self, config: CoverageConfig, work_dir: Path):
        """
        Initialize coverage collector
        
        Args:
            config: Coverage configuration
            work_dir: Working directory for coverage files
        self.config = config
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.tool = config.tool
        
        logger.info(f"Initialized CoverageCollector: tool={self.tool}, "
                   f"work_dir={self.work_dir}")
    
    def find_coverage_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
        """
        Find coverage database files
        
        Args:
            patterns: Optional file patterns to search
            
        Returns:
            List of coverage file paths
        if patterns is None:
            patterns = ['*.ucdb', '*.acdb', '*.vdb']
        
        coverage_files = []
        for pattern in patterns:
            coverage_files.extend(self.work_dir.rglob(pattern))
        
        logger.info(f"Found {len(coverage_files)} coverage files")
        return coverage_files
    
    def parse_coverage(self, coverage_file: Path) -> CoverageMetrics:
        """
        Parse coverage database file
        
        Args:
            coverage_file: Path to coverage database
            
        Returns:
            CoverageMetrics object
        logger.info(f"Parsing coverage file: {coverage_file}")
        
        if self.tool == 'questa':
            return self._parse_questa_coverage(coverage_file)
        elif self.tool == 'vcs':
            return self._parse_vcs_coverage(coverage_file)
        else:
            raise ValueError(f"Unsupported coverage tool: {self.tool}")
    
    def _parse_questa_coverage(self, coverage_file: Path) -> CoverageMetrics:
        """Parse Questa coverage database"""
        metrics = CoverageMetrics()
        
        # Use Questa coverage commands to extract metrics
        try:
            # Run vcover command to get coverage report
            cmd = [
                'vcover', 'report',
                '-code', 'all',
                '-file', str(coverage_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                metrics = self._parse_questa_report(result.stdout)
            else:
                logger.warning(f"Failed to parse Questa coverage: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Coverage parsing timed out")
        except Exception as e:
            logger.error(f"Error parsing Questa coverage: {e}", exc_info=True)
        
        return metrics
    
    def _parse_questa_report(self, report_text: str) -> CoverageMetrics:
        metrics = CoverageMetrics()
        
        # Parse coverage percentages from report
        # Questa format: "Coverage: XX.XX%"
        line_match = re.search(r'Line Coverage:\s*(\d+\.?\d*)%', report_text)
        if line_match:
            metrics.line_coverage = float(line_match.group(1))
        
        toggle_match = re.search(r'Toggle Coverage:\s*(\d+\.?\d*)%', report_text)
        if toggle_match:
            metrics.toggle_coverage = float(toggle_match.group(1))
        
        fsm_match = re.search(r'FSM Coverage:\s*(\d+\.?\d*)%', report_text)
        if fsm_match:
            metrics.fsm_coverage = float(fsm_match.group(1))
        
        return metrics
    
    def _parse_vcs_coverage(self, coverage_file: Path) -> CoverageMetrics:
        """Parse VCS coverage database"""
        # VCS coverage parsing implementation
        metrics = CoverageMetrics()
        # TODO: Implement VCS coverage parsing
        return metrics
    
    def merge_coverage(self, coverage_files: List[Path], 
                      output_file: Optional[Path] = None) -> Path:
        Merge multiple coverage databases
        
        Args:
            coverage_files: List of coverage files to merge
            output_file: Optional output file path
            
        Returns:
            Path to merged coverage file
        """
        if not coverage_files:
            raise ValueError("No coverage files provided for merging")
        
        if output_file is None:
            output_file = self.work_dir / "merged_coverage.ucdb"
        else:
            output_file = Path(output_file)
        
        logger.info(f"Merging {len(coverage_files)} coverage files -> {output_file}")
        
        if self.tool == 'questa':
            self._merge_questa_coverage(coverage_files, output_file)
        elif self.tool == 'vcs':
            self._merge_vcs_coverage(coverage_files, output_file)
        else:
            raise ValueError(f"Unsupported tool for merging: {self.tool}")
        
        return output_file
    
    def _merge_questa_coverage(self, coverage_files: List[Path], output_file: Path):
        try:
            # vcover merge command
            cmd = ['vcover', 'merge', '-stats', str(output_file)]
            cmd.extend([str(f) for f in coverage_files])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Coverage merge failed: {result.stderr}")
                raise RuntimeError(f"Failed to merge coverage: {result.stderr}")
            
            logger.info(f"Successfully merged coverage to {output_file}")
            
        except subprocess.TimeoutExpired:
            logger.error("Coverage merge timed out")
            raise
        except Exception as e:
            logger.error(f"Error merging coverage: {e}", exc_info=True)
            raise
    
    def _merge_vcs_coverage(self, coverage_files: List[Path], output_file: Path):
        """Merge VCS coverage databases"""
        # TODO: Implement VCS coverage merging
        logger.warning("VCS coverage merging not yet implemented")
    
    def get_module_breakdown(self, coverage_file: Path) -> Dict[str, ModuleCoverage]:
        Get coverage breakdown by module
        
        Args:
            coverage_file: Path to coverage database
            
        Returns:
            Dictionary mapping module names to coverage metrics
        """
        logger.info(f"Extracting module breakdown from {coverage_file}")
        
        breakdown = {}
        
        if self.tool == 'questa':
            breakdown = self._get_questa_module_breakdown(coverage_file)
        
        return breakdown
    
    def _get_questa_module_breakdown(self, coverage_file: Path) -> Dict[str, ModuleCoverage]:
        breakdown = {}
        
        try:
            # Use vcover report with hierarchical options
            cmd = [
                'vcover', 'report',
                '-code', 'all',
                '-hierarchical',
                '-file', str(coverage_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Parse hierarchical report
                current_module = None
                for line in result.stdout.split('\n'):
                    # Parse module lines
                    module_match = re.match(r'(\w+)\s+.*?(\d+\.?\d*)%', line)
                    if module_match:
                        module_name = module_match.group(1)
                        coverage_pct = float(module_match.group(2))
                        
                        metrics = CoverageMetrics(line_coverage=coverage_pct)
                        breakdown[module_name] = ModuleCoverage(
                            module_name=module_name,
                            metrics=metrics
                        )
        except Exception as e:
            logger.error(f"Error extracting module breakdown: {e}", exc_info=True)
        
        return breakdown
    
    def check_thresholds(self, metrics: CoverageMetrics, 
                        thresholds: Optional[Dict[str, float]] = None) -> Tuple[bool, List[str]]:
        """
        Check coverage metrics against thresholds
        
        Args:
            metrics: Coverage metrics to check
            thresholds: Optional thresholds (uses config default if None)
            
        Returns:
            (passed, list of failure messages)
        thresholds = thresholds or self.config.thresholds
        
        passed, failures = metrics.meets_thresholds(thresholds)
        
        if passed:
            logger.info("Coverage thresholds met")
        else:
            logger.warning(f"Coverage thresholds not met: {', '.join(failures)}")
        
        return (passed, failures)

