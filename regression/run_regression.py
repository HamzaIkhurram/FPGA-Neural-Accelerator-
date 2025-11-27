#!/usr/bin/env python3
Main Regression Runner - Command Line Interface

Usage:
    python run_regression.py [--config CONFIG_FILE] [--test TEST_NAME] [--parallel] [--email]

Advanced Python: argparse, logging, context managers
"""
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from regression.core.regression import RegressionOrchestrator
from regression.core.config import RegressionConfig


def setup_logging(verbose: bool = False):
"""Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    parser = argparse.ArgumentParser(
        description='Neural Compressor Regression Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full regression with default config
  python run_regression.py

  # Run specific test
  python run_regression.py --test random_test

  # Run with custom config
  python run_regression.py --config regression/configs/regression.json

  # Run sequentially (no parallel)
  python run_regression.py --no-parallel

  # Enable email notifications
  python run_regression.py --email
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=Path(__file__).parent / 'configs' / 'regression.json',
        help='Regression configuration file (default: regression/configs/regression.json)'
    )
    
    parser.add_argument(
        '--test',
        action='append',
        dest='tests',
        help='Run specific test(s) (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=None,
        help='Run tests in parallel (overrides config)'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_false',
        dest='parallel',
        help='Run tests sequentially'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        help='Number of parallel workers (overrides config)'
    )
    
    parser.add_argument(
        '--email',
        action='store_true',
        help='Enable email notifications'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop regression on first failure'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        if not args.config.exists():
            logger.error(f"Configuration file not found: {args.config}")
            sys.exit(1)
        
        logger.info(f"Loading configuration from: {args.config}")
        config = RegressionConfig.from_file(args.config)
        
        # Override config with command line args
        if args.parallel is not None:
            config.parallel = args.parallel
        
        if args.workers:
            config.max_workers = args.workers
            config.simulation.max_workers = args.workers
        
        if args.email:
            config.email_enabled = True
        
        if args.stop_on_error:
            config.stop_on_error = True
        
        if args.tests:
            # Override test list
            from regression.core.config import TestConfig
            config.tests = [
                TestConfig(name=test_name, enabled=True)
                for test_name in args.tests
            ]
        
        # Create orchestrator
        orchestrator = RegressionOrchestrator(config)
        
        # Run regression
        summary = orchestrator.run()
        
        # Exit with appropriate code
        if summary.failed > 0:
            logger.error(f"Regression FAILED: {summary.failed} test(s) failed")
            sys.exit(1)
        else:
            logger.info(f"Regression PASSED: {summary.passed}/{summary.total_tests} passed")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.warning("Regression interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Regression failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

