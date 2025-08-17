#!/usr/bin/env python3
"""
Test runner for the Digital Asset Inventory Manager.
Runs unit tests, integration tests, or specific test categories.
"""

import sys
import os
import argparse
import unittest
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_cyclomatic_complexity_analysis(project_path: str, threshold: int = 10, 
                                     include_tests: bool = False, output_file: str = None):
    """Run cyclomatic complexity analysis on the project."""
    try:
        from cyclomatic_complexity import analyze_project
        
        print("🔍 Running Cyclomatic Complexity Analysis...")
        
        # Set up exclude patterns
        exclude_patterns = ['__pycache__', '.git', '.venv', 'venv', 'node_modules', '*.pyc']
        if not include_tests:
            exclude_patterns.append('tests')
        
        # Run analysis
        results = analyze_project(
            project_path=project_path,
            threshold=threshold,
            exclude_patterns=exclude_patterns,
            output_format='text',
            output_file=output_file
        )
        
        if results:
            # Print summary
            print(f"\n📊 Complexity Analysis Summary:")
            print(f"   Files analyzed: {results['files_analyzed']}")
            print(f"   Total functions: {results['total_functions']}")
            print(f"   High complexity functions (>{threshold}): {results['high_complexity_functions']}")
            
            # Return results for further processing
            return results
        else:
            print("❌ Analysis failed or no results returned")
            return None
            
    except ImportError:
        print("❌ Cyclomatic complexity analyzer not available")
        print("   Make sure tests/cyclomatic_complexity.py exists")
        return None
    except Exception as e:
        print(f"💥 Error during complexity analysis: {e}")
        return None


def run_unit_tests(verbosity=2, pattern=None):
    """Run unit tests."""
    print("🧪 Running Unit Tests...")
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    if pattern:
        loader.testNamePatterns = [pattern]
    
    # Find test files
    test_dir = Path(__file__).parent
    unit_tests = loader.discover(
        str(test_dir), 
        pattern='test_*.py',
        top_level_dir=str(test_dir.parent)
    )
    
    # Filter to only unit tests (exclude integration tests)
    unit_suite = unittest.TestSuite()
    for suite in unit_tests:
        for test in suite:
            if 'integration' not in str(test).lower():
                unit_suite.addTest(test)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(unit_suite)
    
    return result


def run_integration_tests(verbosity=2, pattern=None):
    """Run integration tests."""
    print("🔗 Running Integration Tests...")
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    if pattern:
        loader.testNamePatterns = [pattern]
    
    # Find test files
    test_dir = Path(__file__).parent
    integration_tests = loader.discover(
        str(test_dir), 
        pattern='test_*integration*.py',
        top_level_dir=str(test_dir.parent)
    )
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(integration_tests)
    
    return result


def run_search_tests(verbosity=2, pattern=None):
    """Run search-related tests specifically."""
    print("🔍 Running Search Tests...")
    
    # Run search provider tests
    print("  📚 Testing SearchProvider interface...")
    search_provider_result = run_unit_tests(verbosity, pattern)
    
    # Run search integration tests
    print("  🔗 Testing search CLI integration...")
    search_integration_result = run_integration_tests(verbosity, pattern)
    
    # Combine results
    combined_result = unittest.TestResult()
    combined_result.failures.extend(search_provider_result.failures)
    combined_result.errors.extend(search_provider_result.errors)
    combined_result.skipped.extend(search_provider_result.skipped)
    combined_result.failures.extend(search_integration_result.failures)
    combined_result.errors.extend(search_integration_result.errors)
    combined_result.skipped.extend(search_integration_result.skipped)
    
    return combined_result


def run_all_tests(verbosity=2, pattern=None):
    """Run all tests."""
    print("🚀 Running All Tests...")
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    if pattern:
        loader.testNamePatterns = [pattern]
    
    # Find all test files
    test_dir = Path(__file__).parent
    all_tests = loader.discover(
        str(test_dir), 
        pattern='test_*.py',
        top_level_dir=str(test_dir.parent)
    )
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(all_tests)
    
    return result


def run_specific_test_file(test_file, verbosity=2):
    """Run a specific test file."""
    print(f"🎯 Running specific test file: {test_file}")
    
    if not test_file.endswith('.py'):
        test_file += '.py'
    
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return None
    
    # Import and run the specific test file
    loader = unittest.TestLoader()
    suite = loader.discover(
        str(test_path.parent),
        pattern=test_path.name,
        top_level_dir=str(test_path.parent.parent)
    )
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


def print_test_summary(result, test_type):
    """Print a summary of test results."""
    print(f"\n{'='*60}")
    print(f"📊 {test_type} Test Summary")
    print(f"{'='*60}")
    
    if hasattr(result, 'testsRun'):
        print(f"Tests run: {result.testsRun}")
    
    if hasattr(result, 'failures') and result.failures:
        print(f"❌ Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if hasattr(result, 'errors') and result.errors:
        print(f"💥 Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if hasattr(result, 'skipped') and result.skipped:
        print(f"⏭️  Skipped: {len(result.skipped)}")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    if hasattr(result, 'wasSuccessful'):
        success = result.wasSuccessful()
        print(f"🎯 Overall Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    print(f"{'='*60}\n")


def print_complexity_summary(complexity_results):
    """Print a summary of complexity analysis results."""
    if not complexity_results:
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 Cyclomatic Complexity Summary")
    print(f"{'='*60}")
    
    print(f"Files analyzed: {complexity_results['files_analyzed']}")
    print(f"Total functions: {complexity_results['total_functions']}")
    print(f"High complexity functions: {complexity_results['high_complexity_functions']}")
    
    if complexity_results['high_complexity_functions'] > 0:
        print(f"⚠️  Found {complexity_results['high_complexity_functions']} functions with high complexity")
        print("   Consider refactoring these functions to improve maintainability")
    else:
        print("✅ All functions have acceptable complexity levels")
    
    print(f"{'='*60}\n")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run tests for Digital Asset Inventory Manager')
    parser.add_argument(
        '--type', 
        choices=['unit', 'integration', 'search', 'all'], 
        default='all',
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '--file',
        help='Run a specific test file'
    )
    parser.add_argument(
        '--pattern',
        help='Test name pattern to match (e.g., "*search*")'
    )
    parser.add_argument(
        '--verbosity', 
        type=int, 
        choices=[0, 1, 2], 
        default=2,
        help='Test output verbosity (default: 2)'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage reporting'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Skip slow tests (integration tests)'
    )
    parser.add_argument(
        '--complexity',
        action='store_true',
        help='Run cyclomatic complexity analysis'
    )
    parser.add_argument(
        '--complexity-threshold',
        type=int,
        default=10,
        help='Complexity threshold for analysis (default: 10)'
    )
    parser.add_argument(
        '--complexity-output',
        help='Output file for complexity analysis report'
    )
    parser.add_argument(
        '--include-tests-in-complexity',
        action='store_true',
        help='Include test files in complexity analysis'
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path(__file__).parent.exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    start_time = time.time()
    
    try:
        # Run complexity analysis if requested
        complexity_results = None
        if args.complexity:
            project_path = Path(__file__).parent.parent
            complexity_results = run_cyclomatic_complexity_analysis(
                project_path=str(project_path),
                threshold=args.complexity_threshold,
                include_tests=args.include_tests_in_complexity,
                output_file=args.complexity_output
            )
        
        # Run tests if not only complexity analysis
        if not args.complexity or args.type != 'none':
            if args.file:
                # Run specific test file
                result = run_specific_test_file(args.file, args.verbosity)
                if result:
                    print_test_summary(result, f"File: {args.file}")
            elif args.type == 'unit':
                # Run unit tests only
                result = run_unit_tests(args.verbosity, args.pattern)
                print_test_summary(result, "Unit Tests")
            elif args.type == 'integration':
                # Run integration tests only
                if args.fast:
                    print("⚠️  Skipping integration tests due to --fast flag")
                    return
                result = run_integration_tests(args.verbosity, args.pattern)
                print_test_summary(result, "Integration Tests")
            elif args.type == 'search':
                # Run search tests only
                result = run_search_tests(args.verbosity, args.pattern)
                print_test_summary(result, "Search Tests")
            else:
                # Run all tests
                if args.fast:
                    print("⚠️  Running only unit tests due to --fast flag")
                    result = run_unit_tests(args.verbosity, args.pattern)
                    print_test_summary(result, "Unit Tests (Fast Mode)")
                else:
                    result = run_all_tests(args.verbosity, args.pattern)
                    print_test_summary(result, "All Tests")
        else:
            result = None
        
        # Print complexity summary if analysis was run
        if complexity_results:
            print_complexity_summary(complexity_results)
        
        # Print timing information
        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️  Total execution duration: {duration:.2f} seconds")
        
        # Exit with appropriate code
        exit_code = 0
        
        # Check test results
        if result and hasattr(result, 'wasSuccessful'):
            if not result.wasSuccessful():
                exit_code = 1
        
        # Check complexity results
        if complexity_results and complexity_results['high_complexity_functions'] > 0:
            print("⚠️  High complexity functions detected - consider refactoring")
            # Don't fail the build for complexity, just warn
            # exit_code = 2  # Uncomment to make complexity issues fail the build
        
        sys.exit(exit_code)
            
    except KeyboardInterrupt:
        print("\n⚠️  Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Error during execution: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 