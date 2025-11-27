Regression Orchestrator - Main Entry Point
Senior Staff Engineer: Complete workflow, error handling, statistics
"""
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from regression.core.config import RegressionConfig
from regression.core.sim_runner import SimulationRunner, SimulationResult
from regression.core.coverage import CoverageCollector, CoverageMetrics
from regression.core.reporter import RegressionReporter, RegressionSummary
from regression.core.notifications import EmailNotifier

logger = logging.getLogger(__name__)


class RegressionOrchestrator:
    Main regression orchestrator
    
    Responsibilities:
    - Load configuration
    - Run simulations (parallel or sequential)
    - Collect coverage
    - Generate reports
    - Send notifications
    - Track statistics
    """
    
    def __init__(self, config: RegressionConfig):
        Initialize orchestrator
        
        Args:
            config: Regression configuration
        """
        self.config = config
        self.work_dir = Path(config.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.sim_runner = SimulationRunner(config.simulation)
        self.coverage_collector = CoverageCollector(config.coverage, self.work_dir)
        self.reporter = RegressionReporter(config.report_dir or self.work_dir / 'reports')
        
        # Email notifier (optional)
        self.email_notifier = None
        if config.email_enabled and config.email_recipients:
            # Note: Email credentials should come from environment or secure config
            logger.warning("Email notifications enabled but notifier not configured")
        
        logger.info(f"Initialized RegressionOrchestrator: {config.name}")
    
    def run(self) -> RegressionSummary:
        Run complete regression
        
        Returns:
            RegressionSummary object
        """
        logger.info(f"Starting regression: {self.config.name}")
        start_time = time.time()
        
        # Step 0: Ensure compilation (check if work library exists)
        if not (self.work_dir / "work").exists():
            logger.warning("Work library not found. Attempting to compile...")
            self._compile_design()
        
        # Step 1: Get test list
        test_list = self._get_test_list()
        logger.info(f"Found {len(test_list)} test(s) to run")
        
        # Step 2: Run simulations
        results = self._run_simulations(test_list)
        
        # Step 3: Collect coverage
        coverage = None
        if self.config.coverage.enabled:
            coverage = self._collect_coverage()
        
        # Step 4: Generate summary
        duration = time.time() - start_time
        summary = RegressionSummary(
            name=self.config.name,
            timestamp=datetime.now(),
            total_tests=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if r.failed),
            skipped=sum(1 for r in results if r.status.value == 'SKIPPED'),
            duration=duration,
            results=results,
            coverage=coverage
        )
        
        # Step 5: Generate reports
        self._generate_reports(summary)
        
        # Step 6: Send notifications
        if self.config.email_enabled:
            self._send_notifications(summary)
        
        logger.info(f"Regression complete: {summary.passed}/{summary.total_tests} passed "
                   f"({summary.pass_rate:.1f}%) in {duration:.2f}s")
        
        return summary
    
    def _get_test_list(self) -> List[str]:
"""Get list of tests to run"""
        if self.config.tests:
            # Use explicitly configured tests
            test_list = [
                test.name for test in self.config.tests
                if test.enabled
            ]
        elif self.config.test_patterns:
            # Find tests matching patterns
            test_list = []
            for pattern in self.config.test_patterns:
                # Search for test files matching pattern
                test_files = list(self.work_dir.rglob(pattern))
                for test_file in test_files:
                    # Extract test names from files
                    # This is simplified - real implementation would parse test files
                    test_list.append(test_file.stem)
        else:
            # Default test list
            test_list = ['random_test', 'eeg_test', 'spike_test']
        
        return test_list
    
    def _run_simulations(self, test_list: List[str]) -> List[SimulationResult]:
        # For simple testbench, it runs all tests in one simulation
        if "simple" in self.config.simulation.top_module.lower():
            logger.info("Running simple testbench (single simulation)")
            # Simple testbench doesn't use test names - run once
            result = self.sim_runner.run_test("simple_test")
            return [result]
        
        # UVM testbench - run each test separately
        if self.config.parallel and len(test_list) > 1:
            logger.info("Running simulations in parallel")
            results = self.sim_runner.run_tests_parallel(
                test_list,
                max_workers=self.config.max_workers
            )
        else:
            logger.info("Running simulations sequentially")
            results = []
            for test_name in test_list:
                result = self.sim_runner.run_test(test_name)
                results.append(result)
                
                # Stop on error if configured
                if self.config.stop_on_error and result.failed:
                    logger.warning(f"Stopping on error: {test_name}")
                    break
        
        return results
    
    def _collect_coverage(self) -> Optional[CoverageMetrics]:
        """Collect and merge coverage"""
        try:
            # Find coverage files
            coverage_files = self.coverage_collector.find_coverage_files()
            
            if not coverage_files:
                logger.warning("No coverage files found")
                return None
            
            # Merge if configured
            if self.config.coverage.merge and len(coverage_files) > 1:
                merged_file = self.coverage_collector.merge_coverage(
                    coverage_files,
                    self.config.coverage.output_file
                )
                coverage_file = merged_file
            else:
                coverage_file = coverage_files[0]
            
            # Parse coverage
            metrics = self.coverage_collector.parse_coverage(coverage_file)
            
            # Check thresholds
            passed, failures = self.coverage_collector.check_thresholds(
                metrics,
                self.config.coverage.thresholds
            )
            
            if not passed:
                logger.warning(f"Coverage thresholds not met: {', '.join(failures)}")
            else:
                logger.info("Coverage thresholds met")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting coverage: {e}", exc_info=True)
            return None
    
    def _generate_reports(self, summary: RegressionSummary):
        logger.info("Generating reports")
        
        reports = self.reporter.generate_report(
            summary,
            formats=self.config.report_format
        )
        
        for fmt, report_path in reports.items():
            logger.info(f"Generated {fmt.upper()} report: {report_path}")
    
    def _send_notifications(self, summary: RegressionSummary):
        """Send email notifications"""
        if not self.email_notifier:
            logger.warning("Email notifier not configured, skipping notifications")
            return
        
        logger.info(f"Sending email notifications to {len(self.config.email_recipients)} recipient(s)")
        
        success = self.email_notifier.send_regression_report(
            summary,
            self.config.email_recipients,
            self.reporter
        )
        
        if success:
            logger.info("Email notifications sent successfully")
        else:
            logger.error("Failed to send email notifications")
    
    def _compile_design(self):
        logger.info("Compiling design...")
        compile_script = self.work_dir / "compile_simple.do"
        
        if compile_script.exists():
            import subprocess
            tool_path = self.config.simulation.tool_path or "vsim"
            
            # Run vlog to compile (this is simplified - real implementation would parse .do file)
            logger.info("Running compilation...")
            # For now, just warn - user should compile manually first
            logger.warning("Compilation should be done manually. Run: cd sim && do compile_simple.do")
        else:
            logger.warning(f"Compile script not found: {compile_script}")
    
    @classmethod
    def from_config_file(cls, config_path: Path) -> 'RegressionOrchestrator':
        """
        Create orchestrator from configuration file
        
        Args:
            config_path: Path to configuration file (JSON/YAML)
            
        Returns:
            RegressionOrchestrator instance
        config = RegressionConfig.from_file(config_path)
        return cls(config)

