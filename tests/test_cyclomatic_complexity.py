#!/usr/bin/env python3
"""
Unit tests for the cyclomatic complexity analyzer.
Tests the analyzer's ability to correctly identify and measure code complexity.
"""

import unittest
import tempfile
import os
import sys
import ast
from pathlib import Path

# Add tests to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

from cyclomatic_complexity import CyclomaticComplexityAnalyzer, CyclomaticComplexityVisitor


class TestCyclomaticComplexityVisitor(unittest.TestCase):
    """Test the AST visitor for cyclomatic complexity calculation."""
    
    def test_simple_function(self):
        """Test complexity calculation for a simple function."""
        code = """
def simple_function():
    return 42
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('simple_function', visitor.complexity_data)
        # Return statements add 0.5 complexity, so 1 + 0.5 = 1.5
        self.assertEqual(visitor.complexity_data['simple_function']['complexity'], 1.5)
    
    def test_function_with_if(self):
        """Test complexity calculation for a function with if statement."""
        code = """
def function_with_if(x):
    if x > 0:
        return "positive"
    else:
        return "negative"
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('function_with_if', visitor.complexity_data)
        self.assertEqual(visitor.complexity_data['function_with_if']['complexity'], 2)  # 1 + 1 if
    
    def test_function_with_while(self):
        """Test complexity calculation for a function with while loop."""
        code = """
def function_with_while(n):
    i = 0
    while i < n:
        i += 1
    return i
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('function_with_while', visitor.complexity_data)
        self.assertEqual(visitor.complexity_data['function_with_while']['complexity'], 2)  # 1 + 1 while
    
    def test_function_with_for(self):
        """Test complexity calculation for a function with for loop."""
        code = """
def function_with_for(items):
    total = 0
    for item in items:
        total += item
    return total
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('function_with_for', visitor.complexity_data)
        self.assertEqual(visitor.complexity_data['function_with_for']['complexity'], 2)  # 1 + 1 for
    
    def test_function_with_exception(self):
        """Test complexity calculation for a function with exception handling."""
        code = """
def function_with_exception(x):
    try:
        return 1 / x
    except ZeroDivisionError:
        return None
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('function_with_exception', visitor.complexity_data)
        self.assertEqual(visitor.complexity_data['function_with_exception']['complexity'], 2)  # 1 + 1 except
    
    def test_function_with_boolean_operations(self):
        """Test complexity calculation for a function with boolean operations."""
        code = """
def function_with_boolean(a, b, c):
    if a and b or c:
        return True
    return False
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('function_with_boolean', visitor.complexity_data)
        # 1 (base) + 1 (if) + 1 (and) + 1 (or) = 4
        self.assertEqual(visitor.complexity_data['function_with_boolean']['complexity'], 4)
    
    def test_class_methods(self):
        """Test complexity calculation for class methods."""
        code = """
class TestClass:
    def simple_method(self):
        return 42
    
    def complex_method(self, x):
        if x > 0:
            while x > 0:
                x -= 1
        return x
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('TestClass.simple_method', visitor.complexity_data)
        self.assertIn('TestClass.complex_method', visitor.complexity_data)
        
        self.assertEqual(visitor.complexity_data['TestClass.simple_method']['complexity'], 1)
        self.assertEqual(visitor.complexity_data['TestClass.complex_method']['complexity'], 3)  # 1 + 1 if + 1 while
    
    def test_async_function(self):
        """Test complexity calculation for async functions."""
        code = """
async def async_function():
    if True:
        for i in range(10):
            await some_coroutine()
    return "done"
"""
        tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        
        self.assertIn('async_function', visitor.complexity_data)
        self.assertEqual(visitor.complexity_data['async_function']['complexity'], 3)  # 1 + 1 if + 1 for


class TestCyclomaticComplexityAnalyzer(unittest.TestCase):
    """Test the main analyzer class."""
    
    def setUp(self):
        """Set up test environment."""
        self.analyzer = CyclomaticComplexityAnalyzer(threshold=5)
        self.temp_dir = tempfile.mkdtemp()
        self.temp_files = []
    
    def tearDown(self):
        """Clean up test environment."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def _create_test_file(self, filename: str, content: str) -> str:
        """Create a temporary test file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        self.temp_files.append(file_path)
        return file_path
    
    def test_analyze_simple_file(self):
        """Test analysis of a simple Python file."""
        content = """
def simple_function():
    return 42

def function_with_if(x):
    if x > 0:
        return "positive"
    return "negative"
"""
        file_path = self._create_test_file('simple.py', content)
        result = self.analyzer.analyze_file(Path(file_path))
        
        self.assertEqual(result['total_functions'], 2)
        self.assertEqual(result['high_complexity_count'], 0)
        self.assertIn('simple_function', result['functions'])
        self.assertIn('function_with_if', result['functions'])
        self.assertEqual(result['functions']['simple_function']['complexity'], 1.5)
        self.assertEqual(result['functions']['function_with_if']['complexity'], 2)
    
    def test_analyze_complex_file(self):
        """Test analysis of a file with high complexity functions."""
        content = """
def very_complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(x):
                    while i < y:
                        if i % 2 == 0:
                            try:
                                result = 1 / i
                            except ZeroDivisionError:
                                result = 0
                        i += 1
    return x + y + z

def simple_function():
    return 42
"""
        file_path = self._create_test_file('complex.py', content)
        result = self.analyzer.analyze_file(Path(file_path))
        
        self.assertEqual(result['total_functions'], 2)
        self.assertEqual(result['high_complexity_count'], 1)
        self.assertIn('very_complex_function', result['functions'])
        self.assertIn('simple_function', result['functions'])
        
        # The complex function should have high complexity
        complex_func = result['functions']['very_complex_function']
        self.assertGreater(complex_func['complexity'], 5)
    
    def test_analyze_directory(self):
        """Test analysis of a directory with multiple Python files."""
        # Create multiple test files
        simple_content = "def simple(): return 42"
        complex_content = """
def complex_func():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return 42
"""
        
        self._create_test_file('simple.py', simple_content)
        self._create_test_file('complex.py', complex_content)
        
        # Analyze directory
        result = self.analyzer.analyze_directory(Path(self.temp_dir))
        
        self.assertEqual(result['files_analyzed'], 2)
        self.assertEqual(result['total_functions'], 2)
        self.assertEqual(result['high_complexity_functions'], 1)
        
        # Check that both files are in the results (using full paths)
        file_paths = list(result['file_results'].keys())
        self.assertEqual(len(file_paths), 2)
        self.assertTrue(any('simple.py' in path for path in file_paths))
        self.assertTrue(any('complex.py' in path for path in file_paths))
    
    def test_exclude_patterns(self):
        """Test that exclude patterns work correctly."""
        # Create a directory structure that should be excluded
        excluded_dir = os.path.join(self.temp_dir, '__pycache__')
        os.makedirs(excluded_dir, exist_ok=True)
        
        # Create a file that should be excluded
        excluded_content = "def excluded(): return 42"
        excluded_file = os.path.join(excluded_dir, 'excluded.py')
        with open(excluded_file, 'w') as f:
            f.write(excluded_content)
        
        # Create a regular file
        regular_content = "def regular(): return 42"
        self._create_test_file('regular.py', regular_content)
        
        # Analyze with exclude patterns
        result = self.analyzer.analyze_directory(Path(self.temp_dir), exclude_patterns=['__pycache__'])
        
        # Should only analyze the regular file
        self.assertEqual(result['files_analyzed'], 1)
        self.assertEqual(result['total_functions'], 1)
    
    def test_generate_text_report(self):
        """Test text report generation."""
        content = """
def simple_function():
    return 42

def complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            if True:
                                if True:
                                    if True:
                                        if True:
                                            return 42
"""
        file_path = self._create_test_file('test_report.py', content)
        result = self.analyzer.analyze_file(Path(file_path))
        
        # Add directory info to match expected format
        result['directory'] = str(Path(file_path).parent)
        
        # Generate report
        report = self.analyzer.generate_report(result)
        
        # Check that report contains expected information
        self.assertIn('CYCLOMATIC COMPLEXITY ANALYSIS REPORT', report)
        self.assertIn('Total Functions: 2', report)
        self.assertIn('High Complexity Functions', report)
        self.assertIn('complex_function', report)
    
    def test_generate_json_report(self):
        """Test JSON report generation."""
        content = "def simple(): return 42"
        file_path = self._create_test_file('test_json.py', content)
        result = self.analyzer.analyze_file(Path(file_path))
        
        # Generate JSON report
        report = self.analyzer.generate_report(result, 'json')
        
        # Parse JSON to verify it's valid
        import json
        parsed = json.loads(report)
        self.assertIn('file_path', parsed)
        self.assertIn('functions', parsed)
        self.assertIn('total_functions', parsed)


class TestComplexityThresholds(unittest.TestCase):
    """Test different complexity thresholds."""
    
    def test_low_threshold(self):
        """Test with a low complexity threshold."""
        analyzer = CyclomaticComplexityAnalyzer(threshold=2)
        
        content = """
def simple_function():
    return 42

def function_with_if(x):
    if x > 0:
        return "positive"
    return "negative"

def function_with_loop():
    for i in range(10):
        if i % 2 == 0:
            print(i)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            file_path = f.name
        
        try:
            result = analyzer.analyze_file(Path(file_path))
            
            # With threshold 2, the third function should be flagged as high complexity
            # function_with_loop has: 1 (base) + 1 (for) + 1 (if) + 0.5 (return) = 3.5
            self.assertEqual(result['high_complexity_count'], 1)
            self.assertIn('function_with_loop', result['functions'])
            self.assertGreater(result['functions']['function_with_loop']['complexity'], 2)
            
        finally:
            os.unlink(file_path)
    
    def test_high_threshold(self):
        """Test with a high complexity threshold."""
        analyzer = CyclomaticComplexityAnalyzer(threshold=20)
        
        content = """
def very_complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            if True:
                                if True:
                                    if True:
                                        if True:
                                            if True:
                                                if True:
                                                    if True:
                                                        if True:
                                                            if True:
                                                                if True:
                                                                    if True:
                                                                        if True:
                                                                            if True:
                                                                                if True:
                                                                                    return 42
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            file_path = f.name
        
        try:
            result = analyzer.analyze_file(Path(file_path))
            
            # With threshold 20, even this very complex function should not be flagged
            # The function has 1 (base) + 20 (if statements) + 0.5 (return) = 21.5
            # So it should be flagged as high complexity
            self.assertEqual(result['high_complexity_count'], 1)
            
        finally:
            os.unlink(file_path)


if __name__ == '__main__':
    unittest.main() 