Configuration Management - Senior Staff Engineer Patterns
Advanced Python: dataclasses, type hints, validation
"""
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Literal
import json
from enum import Enum
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


class SimulationTool(str, Enum):
"""Supported simulation tools"""
    QUESTA = "questa"
    VCS = "vcs"
    VERILATOR = "verilator"
    XCELIUM = "xcelium"


@dataclass
class SimulationConfig:
    tool: SimulationTool
    work_dir: Path
    top_module: str
    timeout: int = 300
    max_workers: int = 4
    tool_path: Optional[Path] = None
    tool_args: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Type conversion after initialization"""
        if isinstance(self.work_dir, str):
            self.work_dir = Path(self.work_dir)
        if isinstance(self.tool, str):
            self.tool = SimulationTool(self.tool)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['work_dir'] = str(self.work_dir)
        d['tool'] = self.tool.value
        if d['tool_path']:
            d['tool_path'] = str(d['tool_path'])
        return d


@dataclass
class CoverageConfig:
    """Coverage collection configuration"""
    enabled: bool = True
    tool: Literal['questa', 'vcs'] = 'questa'
    merge: bool = True
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        'line_coverage': 80.0,
        'toggle_coverage': 90.0,
        'fsm_coverage': 75.0,
        'expression_coverage': 85.0
    })
    output_file: Optional[Path] = None
    
    def __post_init__(self):
        if self.output_file and isinstance(self.output_file, str):
            self.output_file = Path(self.output_file)


@dataclass
class TestConfig:
    """Individual test configuration"""
    name: str
    test_file: Optional[Path] = None
    test_class: Optional[str] = None
    timeout: Optional[int] = None
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.test_file and isinstance(self.test_file, str):
            self.test_file = Path(self.test_file)


@dataclass
class RegressionConfig:
    """Complete regression configuration"""
    name: str
    work_dir: Path
    simulation: SimulationConfig
    coverage: CoverageConfig = field(default_factory=CoverageConfig)
    tests: List[TestConfig] = field(default_factory=list)
    test_patterns: List[str] = field(default_factory=list)
    parallel: bool = True
    max_workers: int = 4
    stop_on_error: bool = False
    
    # Reporting
    report_format: List[str] = field(default_factory=lambda: ['html', 'json'])
    report_dir: Optional[Path] = None
    
    # Notifications
    email_enabled: bool = False
    email_recipients: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.work_dir, str):
            self.work_dir = Path(self.work_dir)
        if self.report_dir and isinstance(self.report_dir, str):
            self.report_dir = Path(self.report_dir)
        if not self.report_dir:
            self.report_dir = self.work_dir / 'reports'
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'RegressionConfig':
        """Load configuration from JSON/YAML file"""
        config_path = Path(config_path).resolve()
        config_dir = config_path.parent
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                if not HAS_YAML:
                    raise ImportError("YAML support requires 'pyyaml' package. Install with: pip install pyyaml")
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Resolve relative paths relative to current working directory (project root)
        # This is standard behavior - config paths are relative to where script runs from
        config = cls.from_dict(data)
        cwd = Path.cwd()
        
        # Resolve work_dir relative to current working directory if it's relative
        if not config.work_dir.is_absolute():
            config.work_dir = (cwd / config.work_dir).resolve()
        if not config.simulation.work_dir.is_absolute():
            config.simulation.work_dir = (cwd / config.simulation.work_dir).resolve()
        
        return config
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RegressionConfig':
        # Convert nested dicts to config objects
        sim_config = SimulationConfig(**data['simulation'])
        cov_config = CoverageConfig(**data.get('coverage', {}))
        
        tests = [
            TestConfig(**test_data) 
            for test_data in data.get('tests', [])
        ]
        
        config = cls(
            name=data['name'],
            work_dir=Path(data['work_dir']),
            simulation=sim_config,
            coverage=cov_config,
            tests=tests,
            test_patterns=data.get('test_patterns', []),
            parallel=data.get('parallel', True),
            max_workers=data.get('max_workers', 4),
            stop_on_error=data.get('stop_on_error', False),
            report_format=data.get('report_format', ['html', 'json']),
            email_enabled=data.get('email_enabled', False),
            email_recipients=data.get('email_recipients', [])
        )
        
        return config
    
    def to_file(self, config_path: Path):
        """Save configuration to file"""
        config_path = Path(config_path)
        data = self.to_dict()
        
        with open(config_path, 'w') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'work_dir': str(self.work_dir),
            'simulation': self.simulation.to_dict(),
            'coverage': asdict(self.coverage),
            'tests': [asdict(test) for test in self.tests],
            'test_patterns': self.test_patterns,
            'parallel': self.parallel,
            'max_workers': self.max_workers,
            'stop_on_error': self.stop_on_error,
            'report_format': self.report_format,
            'report_dir': str(self.report_dir) if self.report_dir else None,
            'email_enabled': self.email_enabled,
            'email_recipients': self.email_recipients
        }

