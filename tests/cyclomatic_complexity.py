#!/usr/bin/env python3
"""
Cyclomatic Complexity Analyzer for Python Code.
Measures the complexity of functions and methods to identify code that might need refactoring.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse
import json


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """AST visitor that calculates cyclomatic complexity for functions and methods."""
    
    def __init__(self):
        self.complexity_data = {}
        self.current_function = None
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions and calculate complexity."""
        # Calculate base complexity (1 for the function entry)
        complexity = 1
        
        # Add complexity for each decision point
        complexity += self._count_decision_points(node)
        
        # Store complexity data
        function_name = node.name
        if self.current_class:
            function_name = f"{self.current_class}.{function_name}"
        
        self.complexity_data[function_name] = {
            'complexity': complexity,
            'line_number': node.lineno,
            'type': 'method' if self.current_class else 'function',
            'class': self.current_class,
            'name': node.name
        }
        
        # Visit child nodes
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        # Treat async functions the same as regular functions
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions."""
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class
    
    def _count_decision_points(self, node: ast.AST) -> int:
        """Count decision points in an AST node."""
        complexity = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.Return):
                # Multiple return statements can increase complexity
                complexity += 0.5
            elif isinstance(child, ast.BoolOp):
                # Boolean operations with 'and'/'or' can increase complexity
                if isinstance(child.op, (ast.And, ast.Or)):
                    complexity += len(child.values) - 1
        
        return complexity


class CyclomaticComplexityAnalyzer:
    """Main analyzer class for cyclomatic complexity."""
    
    def __init__(self, threshold: int = 10):
        self.threshold = threshold
        self.visitor = CyclomaticComplexityVisitor()
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file for cyclomatic complexity."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Reset visitor and analyze
            self.visitor.complexity_data.clear()
            self.visitor.current_class = None
            self.visitor.visit(tree)
            
            return {
                'file_path': str(file_path),
                'functions': self.visitor.complexity_data.copy(),
                'total_functions': len(self.visitor.complexity_data),
                'high_complexity_count': sum(1 for data in self.visitor.complexity_data.values() 
                                           if data['complexity'] > self.threshold)
            }
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': str(e),
                'functions': {},
                'total_functions': 0,
                'high_complexity_count': 0
            }
    
    def analyze_directory(self, directory_path: Path, exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """Analyze all Python files in a directory recursively."""
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '.git', '.venv', 'venv', 'node_modules', '*.pyc']
        
        results = {
            'directory': str(directory_path),
            'files_analyzed': 0,
            'total_functions': 0,
            'high_complexity_functions': 0,
            'complexity_distribution': {},
            'file_results': {},
            'high_complexity_details': []
        }
        
        # Find all Python files
        python_files = list(directory_path.rglob('*.py'))
        
        for file_path in python_files:
            # Skip excluded patterns
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue
            
            # Analyze the file
            file_result = self.analyze_file(file_path)
            results['file_results'][str(file_path)] = file_result
            
            if 'error' not in file_result:
                results['files_analyzed'] += 1
                results['total_functions'] += file_result['total_functions']
                results['high_complexity_functions'] += file_result['high_complexity_count']
                
                # Update complexity distribution
                for func_data in file_result['functions'].values():
                    complexity = func_data['complexity']
                    results['complexity_distribution'][complexity] = results['complexity_distribution'].get(complexity, 0) + 1
                    
                    # Track high complexity functions
                    if complexity > self.threshold:
                        results['high_complexity_details'].append({
                            'file': str(file_path),
                            'function': func_data['name'],
                            'class': func_data['class'],
                            'complexity': complexity,
                            'line': func_data['line_number']
                        })
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_format: str = 'text') -> str:
        """Generate a report from analysis results."""
        if output_format == 'json':
            return json.dumps(results, indent=2)
        
        # Text format
        report = []
        report.append("=" * 80)
        report.append("CYCLOMATIC COMPLEXITY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Directory: {results['directory']}")
        report.append(f"Files Analyzed: {results['files_analyzed']}")
        report.append(f"Total Functions: {results['total_functions']}")
        report.append(f"High Complexity Functions (>={self.threshold}): {results['high_complexity_functions']}")
        report.append("")
        
        # Complexity distribution
        if results['complexity_distribution']:
            report.append("Complexity Distribution:")
            for complexity in sorted(results['complexity_distribution'].keys()):
                count = results['complexity_distribution'][complexity]
                report.append(f"  Complexity {complexity}: {count} functions")
            report.append("")
        
        # High complexity details
        if results['high_complexity_details']:
            report.append("High Complexity Functions (Consider Refactoring):")
            report.append("-" * 60)
            
            # Sort by complexity (highest first)
            high_complexity_sorted = sorted(results['high_complexity_details'], 
                                          key=lambda x: x['complexity'], reverse=True)
            
            for func in high_complexity_sorted:
                class_info = f"{func['class']}." if func['class'] else ""
                report.append(f"  {class_info}{func['function']} (line {func['line']})")
                report.append(f"    File: {func['file']}")
                report.append(f"    Complexity: {func['complexity']}")
                report.append("")
        
        # File-level summary
        report.append("File-Level Summary:")
        report.append("-" * 40)
        for file_path, file_result in results['file_results'].items():
            if 'error' not in file_result:
                report.append(f"  {file_path}: {file_result['total_functions']} functions, "
                           f"{file_result['high_complexity_count']} high complexity")
        
        return "\n".join(report)


def analyze_project(project_path: str, threshold: int = 10, exclude_patterns: List[str] = None, 
                   output_format: str = 'text', output_file: str = None) -> None:
    """Analyze a project for cyclomatic complexity."""
    project_path = Path(project_path)
    
    if not project_path.exists():
        print(f"Error: Project path '{project_path}' does not exist.")
        return
    
    # Default exclude patterns
    if exclude_patterns is None:
        exclude_patterns = ['__pycache__', '.git', '.venv', 'venv', 'node_modules', '*.pyc', 'tests']
    
    # Create analyzer
    analyzer = CyclomaticComplexityAnalyzer(threshold=threshold)
    
    # Analyze the project
    print(f"Analyzing project: {project_path}")
    results = analyzer.analyze_directory(project_path, exclude_patterns=exclude_patterns)
    
    # Generate report
    report = analyzer.generate_report(results, output_format)
    
    # Output report
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")
    else:
        print(report)
    
    # Return results for programmatic use
    return results


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description='Analyze Python code for cyclomatic complexity')
    parser.add_argument('path', help='Path to Python file or directory to analyze')
    parser.add_argument('--threshold', '-t', type=int, default=10, 
                       help='Complexity threshold (default: 10)')
    parser.add_argument('--exclude', '-e', nargs='*', 
                       help='Patterns to exclude from analysis')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--include-tests', action='store_true',
                       help='Include test files in analysis')
    
    args = parser.parse_args()
    
    # Set up exclude patterns
    exclude_patterns = args.exclude or ['__pycache__', '.git', '.venv', 'venv', 'node_modules', '*.pyc']
    
    if not args.include_tests:
        exclude_patterns.append('tests')
    
    # Analyze the project
    try:
        results = analyze_project(
            project_path=args.path,
            threshold=args.threshold,
            exclude_patterns=exclude_patterns,
            output_format=args.format,
            output_file=args.output
        )
        
        # Exit with error code if high complexity functions found
        if results and results['high_complexity_functions'] > 0:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 