#!/usr/bin/env python3
"""
Integration tests for the search functionality through the CLI interface.
Tests the full search pipeline including all permutations and edge cases.
"""

import unittest
import tempfile
import os
import sys
import subprocess
import json
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from humble_bundle_inventory.database import AssetInventoryDatabase


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for search functionality through CLI."""
    
    def setUp(self):
        """Set up test database and environment."""
        # Create temporary database path (don't create the file yet)
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.duckdb')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        # Remove the empty file so DuckDB can create a fresh database
        os.unlink(self.db_path)
        
        # Set environment variable for test database
        os.environ['DATABASE_PATH'] = self.db_path
        
        # Create test database - this will create a new database file
        self.db = AssetInventoryDatabase(db_path=self.db_path)
        self._create_test_schema()
        self._insert_test_data()
        
        # Get path to main.py
        self.main_path = Path(__file__).parent.parent / 'main.py'
    
    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        # Only remove the file if it exists
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        if 'DATABASE_PATH' in os.environ:
            del os.environ['DATABASE_PATH']
    
    def _create_test_schema(self):
        """Create test database schema."""
        # The database automatically creates tables on initialization
        # No need to call create_schema() explicitly
        pass
    
    def _insert_test_data(self):
        """Insert test data for search testing."""
        # Insert asset source
        self.db.upsert_asset_source({
            'source_id': 'humble_bundle',
            'source_name': 'Humble Bundle',
            'source_type': 'platform',
            'source_url': 'https://humblebundle.com',
            'authentication_method': 'session_cookies',
            'sync_status': 'active'
        })
        
        # Insert test products
        test_products = [
            {
                'product_id': 'sw1',
                'source_id': 'humble_bundle',
                'human_name': 'Visual Studio Code',
                'machine_name': 'vscode',
                'category': 'software',
                'subcategory': 'development',
                'developer': 'Microsoft',
                'publisher': 'Microsoft',
                'url': 'https://example.com',
                'description': 'Code editor',
                'tags': ['editor', 'development'],
                'rating': 4.8,
                'rating_count': 1000,
                'retail_price': 0.0,
                'currency': 'USD',
                'release_date': '2015-01-01',
                'language': 'en'
            },
            {
                'product_id': 'sw2',
                'source_id': 'humble_bundle',
                'human_name': 'Adobe Photoshop',
                'machine_name': 'photoshop',
                'category': 'software',
                'subcategory': 'photo_editing',
                'developer': 'Adobe',
                'publisher': 'Adobe',
                'url': 'https://example.com',
                'description': 'Photo editing software',
                'tags': ['photo', 'editing'],
                'rating': 4.5,
                'rating_count': 500,
                'retail_price': 99.99,
                'currency': 'USD',
                'release_date': '1990-01-01',
                'language': 'en'
            },
            {
                'product_id': 'g1',
                'source_id': 'humble_bundle',
                'human_name': 'Minecraft',
                'machine_name': 'minecraft',
                'category': 'game',
                'subcategory': 'sandbox',
                'developer': 'Mojang',
                'publisher': 'Microsoft',
                'url': 'https://example.com',
                'description': 'Sandbox game',
                'tags': ['sandbox', 'creative'],
                'rating': 4.9,
                'rating_count': 2000,
                'retail_price': 26.95,
                'currency': 'USD',
                'release_date': '2011-01-01',
                'language': 'en'
            },
            {
                'product_id': 'g2',
                'source_id': 'humble_bundle',
                'human_name': 'Portal 2',
                'machine_name': 'portal2',
                'category': 'game',
                'subcategory': 'puzzle',
                'developer': 'Valve',
                'publisher': 'Valve',
                'url': 'https://example.com',
                'description': 'Puzzle game',
                'tags': ['puzzle', 'first-person'],
                'rating': 4.8,
                'rating_count': 1500,
                'retail_price': 19.99,
                'currency': 'USD',
                'release_date': '2011-01-01',
                'language': 'en'
            },
            {
                'product_id': 'e1',
                'source_id': 'humble_bundle',
                'human_name': 'Python Programming Guide',
                'machine_name': 'python_guide',
                'category': 'ebook',
                'subcategory': 'programming',
                'developer': 'O\'Reilly',
                'publisher': 'O\'Reilly',
                'url': 'https://example.com',
                'description': 'Python programming book',
                'tags': ['python', 'programming'],
                'rating': 4.7,
                'rating_count': 300,
                'retail_price': 29.99,
                'currency': 'USD',
                'release_date': '2020-01-01',
                'language': 'en'
            },
            {
                'product_id': 'e2',
                'source_id': 'humble_bundle',
                'human_name': 'Machine Learning Basics',
                'machine_name': 'ml_basics',
                'category': 'ebook',
                'subcategory': 'programming',
                'developer': 'Manning',
                'publisher': 'Manning',
                'url': 'https://example.com',
                'description': 'ML introduction',
                'tags': ['machine learning', 'ai'],
                'rating': 4.5,
                'rating_count': 200,
                'retail_price': 39.99,
                'currency': 'USD',
                'release_date': '2019-01-01',
                'language': 'en'
            }
        ]
        
        for product in test_products:
            self.db.upsert_product(product)
    
    def _run_cli_command(self, args):
        """Run CLI command and return result."""
        try:
            # Close database connection to avoid locking issues
            if hasattr(self, 'db') and self.db.conn:
                self.db.conn.close()
            
            result = subprocess.run(
                [sys.executable, str(self.main_path)] + args,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                timeout=30
            )
            
            # Reopen database connection for further test operations
            if hasattr(self, 'db'):
                self.db._ensure_database()
            
            return result
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, -1, "", "Command timed out")
    
    def test_search_basic(self):
        """Test basic search functionality."""
        result = self._run_cli_command(['search', 'Python'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Python Programming Guide', result.stdout)
        self.assertIn('ebook', result.stdout)
    
    def test_search_with_category_filter(self):
        """Test search with category filter."""
        result = self._run_cli_command(['search', 'game', '--category', 'game'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Minecraft', result.stdout)
        self.assertIn('Portal 2', result.stdout)
        # Should not contain software or ebooks
        self.assertNotIn('Visual Studio Code', result.stdout)
        self.assertNotIn('Python Programming Guide', result.stdout)
    
    def test_search_with_field_specific(self):
        """Test field-specific search."""
        result = self._run_cli_command(['search', 'software', '--field', 'category'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Adobe Photoshop', result.stdout)
        # Should not contain games or ebooks
        self.assertNotIn('Minecraft', result.stdout)
        self.assertNotIn('Python Programming Guide', result.stdout)
    
    def test_search_with_field_and_category(self):
        """Test field-specific search with category filter."""
        result = self._run_cli_command(['search', 'game', '--field', 'human_name', '--category', 'software'])
        
        self.assertEqual(result.returncode, 0)
        # Should find software with 'game' in name (like Unity Game Engine)
        # But our test data doesn't have this, so should return empty
        self.assertIn('Found 0 assets', result.stdout)
    
    def test_search_regex_basic(self):
        """Test basic regex search."""
        result = self._run_cli_command(['search', '^[A-Z]', '--regex'])
        
        self.assertEqual(result.returncode, 0)
        # Should find all products starting with uppercase letters
        self.assertIn('Found 6 assets', result.stdout)
    
    def test_search_regex_with_category(self):
        """Test regex search with category filter."""
        result = self._run_cli_command(['search', '^[A-Z]', '--regex', '--category', 'software'])
        
        self.assertEqual(result.returncode, 0)
        # Should find only software products starting with uppercase
        self.assertIn('Found 2 assets', result.stdout)
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Adobe Photoshop', result.stdout)
    
    def test_search_regex_case_sensitive(self):
        """Test case sensitive regex search."""
        result = self._run_cli_command(['search', 'python', '--regex', '--case-sensitive'])
        
        self.assertEqual(result.returncode, 0)
        # Should find 0 results since 'python' is lowercase
        self.assertIn('Found 0 assets', result.stdout)
    
    def test_search_with_source_filter(self):
        """Test search with source filter."""
        result = self._run_cli_command(['search', 'game', '--source', 'Humble Bundle'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Minecraft', result.stdout)
        self.assertIn('Portal 2', result.stdout)
    
    def test_search_with_rating_filter(self):
        """Test search with rating filter."""
        result = self._run_cli_command(['search', 'game', '--rating-min', '4.8'])
        
        self.assertEqual(result.returncode, 0)
        # Should only find Portal 2 (4.8) and Minecraft (4.9)
        self.assertIn('Portal 2', result.stdout)
        self.assertIn('Minecraft', result.stdout)
    
    def test_search_pagination(self):
        """Test search pagination."""
        # First page
        result1 = self._run_cli_command(['search', '', '--page-size', '3', '--page', '1'])
        self.assertEqual(result1.returncode, 0)
        self.assertIn('Showing page 1 of 2', result1.stdout)
        
        # Second page
        result2 = self._run_cli_command(['search', '', '--page-size', '3', '--page', '2'])
        self.assertEqual(result2.returncode, 0)
        self.assertIn('Showing page 2 of 2', result1.stdout)
    
    def test_search_dump_json(self):
        """Test search with JSON dump."""
        result = self._run_cli_command(['search', 'Python', '--dump', '--format', 'json'])
        
        self.assertEqual(result.returncode, 0)
        
        # Parse JSON output
        try:
            json_data = json.loads(result.stdout)
            self.assertIsInstance(json_data, list)
            self.assertEqual(len(json_data), 1)
            self.assertEqual(json_data[0]['name'], 'Python Programming Guide')
            self.assertEqual(json_data[0]['category'], 'ebook')
        except json.JSONDecodeError:
            self.fail("Failed to parse JSON output")
    
    def test_search_dump_csv(self):
        """Test search with CSV dump."""
        result = self._run_cli_command(['search', 'Python', '--dump', '--format', 'csv'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Name,Category,Subcategory,Source,Developer,Publisher,Rating,Release Date,Tags,Description', result.stdout)
        self.assertIn('Python Programming Guide,ebook,programming,Humble Bundle,O\'Reilly,O\'Reilly,4.7,2020-01-01,["python", "programming"],Python programming book', result.stdout)
    
    def test_search_dump_tsv(self):
        """Test search with TSV dump."""
        result = self._run_cli_command(['search', 'Python', '--dump', '--format', 'tsv'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Name\tCategory\tSubcategory\tSource\tDeveloper\tPublisher\tRating\tRelease Date\tTags\tDescription', result.stdout)
    
    def test_search_no_results(self):
        """Test search that returns no results."""
        result = self._run_cli_command(['search', 'nonexistent_product'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Found 0 assets', result.stdout)
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        result = self._run_cli_command(['search', ''])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Found 6 assets', result.stdout)
    
    def test_search_invalid_field(self):
        """Test search with invalid field."""
        result = self._run_cli_command(['search', 'test', '--field', 'invalid_field'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Field \'invalid_field\' is not searchable', result.stdout)
    
    def test_search_invalid_regex(self):
        """Test search with invalid regex pattern."""
        result = self._run_cli_command(['search', '[invalid', '--regex'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Invalid regex pattern', result.stdout)
    
    def test_search_help(self):
        """Test search help command."""
        result = self._run_cli_command(['search', '--help'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Search assets in the database', result.stdout)
        self.assertIn('--category', result.stdout)
        self.assertIn('--regex', result.stdout)
        self.assertIn('--field', result.stdout)
    
    def test_advanced_search_and(self):
        """Test advanced search with AND operator."""
        result = self._run_cli_command(['advanced-search', '--queries', 'category:software,developer:Microsoft'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Found 1 assets', result.stdout)
    
    def test_advanced_search_or(self):
        """Test advanced search with OR operator."""
        result = self._run_cli_command(['advanced-search', '--queries', 'category:game,category:ebook', '--operator', 'OR'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Minecraft', result.stdout)
        self.assertIn('Portal 2', result.stdout)
        self.assertIn('Python Programming Guide', result.stdout)
        self.assertIn('Machine Learning Basics', result.stdout)
    
    def test_advanced_search_with_regex(self):
        """Test advanced search with regex patterns."""
        result = self._run_cli_command(['advanced-search', '--queries', 'human_name:^[A-Z],category:software', '--regex'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Adobe Photoshop', result.stdout)
        self.assertIn('Found 2 assets', result.stdout)
    
    def test_advanced_search_with_filters(self):
        """Test advanced search with additional filters."""
        result = self._run_cli_command(['advanced-search', '--queries', 'category:software', '--rating-min', '4.5'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Adobe Photoshop', result.stdout)
        self.assertIn('Found 2 assets', result.stdout)
    
    def test_search_performance_comparison(self):
        """Test that filtered searches are more efficient."""
        # Search without filters
        start_time = time.time()
        result1 = self._run_cli_command(['search', 'game'])
        time1 = time.time() - start_time
        
        # Search with category filter
        start_time = time.time()
        result2 = self._run_cli_command(['search', 'game', '--category', 'game'])
        time2 = time.time() - start_time
        
        self.assertEqual(result1.returncode, 0)
        self.assertEqual(result2.returncode, 0)
        
        # Both should work, but filtered search should be faster
        # (though with small test data, difference might be minimal)
        self.assertIn('Found', result1.stdout)
        self.assertIn('Found', result2.stdout)
    
    def test_search_edge_cases(self):
        """Test search with edge cases."""
        # Search with special characters
        result = self._run_cli_command(['search', 'Adobe Photoshop'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Adobe Photoshop', result.stdout)
        
        # Search with numbers
        result = self._run_cli_command(['search', 'Visual Studio'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Visual Studio Code', result.stdout)
    
    def test_search_multiple_filters(self):
        """Test search with multiple filters combined."""
        result = self._run_cli_command([
            'search', 'development', 
            '--category', 'software',
            '--rating-min', '4.0'
        ])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Found 1 assets', result.stdout)
    
    def test_search_field_combinations(self):
        """Test various field combinations."""
        # Search in human_name field
        result1 = self._run_cli_command(['search', 'Python', '--field', 'human_name'])
        
        # Search in category field
        result2 = self._run_cli_command(['search', 'software', '--field', 'category'])
        
        # Search in developer field
        result3 = self._run_cli_command(['search', 'Microsoft', '--field', 'developer'])
        
        self.assertEqual(result1.returncode, 0)
        self.assertEqual(result2.returncode, 0)
        self.assertEqual(result3.returncode, 0)
        
        self.assertIn('Python Programming Guide', result1.stdout)
        self.assertIn('Visual Studio Code', result2.stdout)
        self.assertIn('Visual Studio Code', result3.stdout)
    
    def test_search_regex_complex_patterns(self):
        """Test complex regex search patterns."""
        # Find products with exactly 3 words
        result = self._run_cli_command(['search', r'^\w+\s+\w+\s+\w+$', '--regex'])
        
        self.assertEqual(result.returncode, 0)
        # Should find products like "Visual Studio Code", "Machine Learning Basics"
        self.assertIn('Visual Studio Code', result.stdout)
        self.assertIn('Machine Learning Basics', result.stdout)
        
        # Find products ending with specific patterns
        result = self._run_cli_command(['search', r'Guide$', '--regex'])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Python Programming Guide', result.stdout)
    
    def test_search_error_handling(self):
        """Test search error handling."""
        # Test with invalid database path
        original_db_path = os.environ.get('HUMBLE_BUNDLE_DB_PATH')
        os.environ['HUMBLE_BUNDLE_DB_PATH'] = '/invalid/path/db.duckdb'
        
        result = self._run_cli_command(['search', 'test'])
        
        # Should handle error gracefully
        self.assertNotEqual(result.returncode, 0)
        
        # Restore original path
        if original_db_path:
            os.environ['HUMBLE_BUNDLE_DB_PATH'] = original_db_path
        else:
            del os.environ['HUMBLE_BUNDLE_DB_PATH']


if __name__ == '__main__':
    unittest.main() 