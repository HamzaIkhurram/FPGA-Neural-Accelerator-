Regression Reporter - Production Quality
Senior Staff Engineer: Multi-format reports, HTML generation, statistics
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from html import escape as html_escape

from regression.core.sim_runner import SimulationResult
from regression.core.coverage import CoverageMetrics

logger = logging.getLogger(__name__)


@dataclass
class RegressionSummary:
"""Summary of regression run"""
    name: str
    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    results: List[SimulationResult]
    coverage: Optional[CoverageMetrics] = None
    
    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100.0


class RegressionReporter:
    """
    Generate comprehensive regression reports
    
    Supports:
    - HTML (interactive, beautiful)
    - JSON (machine-readable)
    - Text (console-friendly)
    - Email summaries
    
    def __init__(self, output_dir: Path):
        """
        Initialize reporter
        
        Args:
            output_dir: Directory for report output
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized RegressionReporter: output_dir={self.output_dir}")
    
    def generate_report(self, summary: RegressionSummary, 
                       formats: List[str] = None) -> Dict[str, Path]:
        """
        Generate reports in specified formats
        
        Args:
            summary: Regression summary
            formats: List of formats ('html', 'json', 'text')
            
        Returns:
            Dictionary mapping format to report file path
        formats = formats or ['html', 'json', 'text']
        
        reports = {}
        
        for fmt in formats:
            if fmt == 'html':
                reports['html'] = self._generate_html(summary)
            elif fmt == 'json':
                reports['json'] = self._generate_json(summary)
            elif fmt == 'text':
                reports['text'] = self._generate_text(summary)
            else:
                logger.warning(f"Unknown report format: {fmt}")
        
        logger.info(f"Generated {len(reports)} report(s)")
        return reports
    
    def _generate_html(self, summary: RegressionSummary) -> Path:
        """Generate HTML report"""
        report_file = self.output_dir / f"regression_{summary.timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = self._build_html(summary)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {report_file}")
        return report_file
    
    def _build_html(self, summary: RegressionSummary) -> str:
        pass_rate = summary.pass_rate
        status_color = "green" if summary.failed == 0 else "red"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regression Report - {summary.name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
        }}
        .stat-card.failed {{
            border-left-color: #f44336;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .pass-rate {{
            font-size: 3em;
            font-weight: bold;
            color: {status_color};
            text-align: center;
            margin: 30px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status-passed {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .status-failed {{
            color: #f44336;
            font-weight: bold;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Neural Compressor Regression Report</h1>
        <p class="timestamp">Generated: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="pass-rate">{pass_rate:.1f}%</div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{summary.total_tests}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #4CAF50;">{summary.passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-value" style="color: #f44336;">{summary.failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.duration:.1f}s</div>
                <div class="stat-label">Duration</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Exit Code</th>
                    <th>Warnings</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
        
        for result in summary.results:
                status_class = "status-passed" if result.passed else "status-failed"
                status_text = result.status.value
                html += f"""
                <tr>
                    <td>{html_escape(result.test_name)}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{result.duration:.2f}</td>
                    <td>{result.exit_code}</td>
                    <td>{result.warnings}</td>
                    <td>{result.errors}</td>
                </tr>
        
        html += """
            </tbody>
        </table>
        
        if summary.coverage:
            html += f"""
        <h2>Coverage Summary</h2>
        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{summary.coverage.line_coverage:.1f}%</div>
                <div class="stat-label">Line Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.coverage.toggle_coverage:.1f}%</div>
                <div class="stat-label">Toggle Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.coverage.fsm_coverage:.1f}%</div>
                <div class="stat-label">FSM Coverage</div>
            </div>
        </div>
        
        html += """
    </div>
</body>
</html>
        return html
    
    def _generate_json(self, summary: RegressionSummary) -> Path:
        """Generate JSON report"""
        report_file = self.output_dir / f"regression_{summary.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to dictionary
        report_dict = {
            'name': summary.name,
            'timestamp': summary.timestamp.isoformat(),
            'total_tests': summary.total_tests,
            'passed': summary.passed,
            'failed': summary.failed,
            'skipped': summary.skipped,
            'duration': summary.duration,
            'pass_rate': summary.pass_rate,
            'results': [
                {
                    'test_name': r.test_name,
                    'status': r.status.value,
                    'exit_code': r.exit_code,
                    'duration': r.duration,
                    'warnings': r.warnings,
                    'errors': r.errors,
                    'sim_time': r.sim_time,
                    'error_message': r.error_message
                }
                for r in summary.results
            ]
        }
        
        if summary.coverage:
            report_dict['coverage'] = asdict(summary.coverage)
        
        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        logger.info(f"Generated JSON report: {report_file}")
        return report_file
    
    def _generate_text(self, summary: RegressionSummary) -> Path:
        report_file = self.output_dir / f"regression_{summary.timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"""
{'='*70}
  Neural Compressor Regression Report
{'='*70}
Name:       {summary.name}
Timestamp:  {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Duration:   {summary.duration:.2f}s

Summary:
  Total Tests:  {summary.total_tests}
  Passed:       {summary.passed}
  Failed:       {summary.failed}
  Skipped:      {summary.skipped}
  Pass Rate:    {summary.pass_rate:.1f}%

{'='*70}
Test Results:
{'='*70}
            for result in summary.results:
                status_icon = "[PASS]" if result.passed else "[FAIL]"
                f.write(f"{status_icon} {result.test_name:30s} {result.status.value:10s} "
                       f"{result.duration:6.2f}s  "
                       f"W:{result.warnings:3d} E:{result.errors:3d}\n")
                
                if result.error_message:
                    f.write(f"    Error: {result.error_message}\n")
        
        logger.info(f"Generated text report: {report_file}")
        return report_file
    
    def generate_email_summary(self, summary: RegressionSummary) -> str:
        """
        Generate email-friendly summary
        
        Args:
            summary: Regression summary
            
        Returns:
            HTML email content
        status = "PASSED" if summary.failed == 0 else "FAILED"
        status_emoji = "✅" if summary.failed == 0 else "❌"
        
        email_html = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>{status_emoji} Regression {status}: {summary.name}</h2>
    <p><strong>Timestamp:</strong> {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Pass Rate:</strong> {summary.pass_rate:.1f}% ({summary.passed}/{summary.total_tests} passed)</p>
    <p><strong>Duration:</strong> {summary.duration:.2f}s</p>
    
    <h3>Failed Tests:</h3>
    <ul>
        for result in summary.results:
            if result.failed:
                email_html += f"<li>{result.test_name}: {result.error_message or result.status.value}</li>"
        
        email_html += """
    </ul>
</body>
</html>
        return email_html

