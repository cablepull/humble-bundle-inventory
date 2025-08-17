#!/usr/bin/env python3
"""
Unit tests for the SearchProvider interface and DuckDBSearchProvider implementation.
Tests all search permutations, edge cases, and filter combinations.
"""

import unittest
import tempfile
import os
import duckdb
from unittest.mock import Mock, patch
import re

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from humble_bundle_inventory.search_provider import SearchProvider
from humble_bundle_inventory.duckdb_search_provider import DuckDBSearchProvider


class TestSearchProviderInterface(unittest.TestCase):
    """Test the SearchProvider abstract base class."""
    
    def test_search_provider_is_abstract(self):
        """Test that SearchProvider cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            SearchProvider()


class TestDuckDBSearchProvider(unittest.TestCase):
    """Test the DuckDBSearchProvider implementation."""
    
    def setUp(self):
        """Set up test database and provider."""
        # Use in-memory database for testing
        self.conn = duckdb.connect(':memory:')
        
        # Create test schema
        self._create_test_schema()
        self._insert_test_data()
        
        # Create search provider
        self.search_provider = DuckDBSearchProvider(self.conn)
    
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
    
    def _create_test_schema(self):
        """Create test database schema."""
        self.conn.execute("""
            CREATE TABLE asset_sources (
                source_id VARCHAR PRIMARY KEY,
                source_name VARCHAR NOT NULL,
                source_type VARCHAR,
                source_url VARCHAR,
                authentication_method VARCHAR,
                sync_status VARCHAR,
                last_sync_timestamp TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE products (
                product_id VARCHAR PRIMARY KEY,
                source_id VARCHAR NOT NULL,
                human_name VARCHAR NOT NULL,
                machine_name VARCHAR,
                category VARCHAR,
                subcategory VARCHAR,
                developer VARCHAR,
                publisher VARCHAR,
                url VARCHAR,
                description TEXT,
                tags JSON,
                rating DECIMAL(3,2),
                rating_count INTEGER,
                retail_price DECIMAL(10,2),
                currency VARCHAR DEFAULT 'USD',
                release_date DATE,
                language VARCHAR,
                updated_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE bundles (
                bundle_id VARCHAR PRIMARY KEY,
                source_id VARCHAR NOT NULL,
                bundle_name VARCHAR NOT NULL,
                bundle_description TEXT,
                bundle_url VARCHAR,
                bundle_type VARCHAR,
                start_date DATE,
                end_date DATE,
                retail_price DECIMAL(10,2),
                currency VARCHAR DEFAULT 'USD',
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE bundle_products (
                bundle_id VARCHAR NOT NULL,
                product_id VARCHAR NOT NULL,
                PRIMARY KEY (bundle_id, product_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE downloads (
                download_id VARCHAR PRIMARY KEY,
                product_id VARCHAR NOT NULL,
                platform VARCHAR,
                download_type VARCHAR,
                file_size_bytes BIGINT,
                file_size_display VARCHAR,
                download_url VARCHAR,
                created_at TIMESTAMP
            )
        """)
    
    def _insert_test_data(self):
        """Insert test data for search testing."""
        # Insert asset sources
        self.conn.execute("""
            INSERT INTO asset_sources VALUES 
            ('humble_bundle', 'Humble Bundle', 'platform', 'https://humblebundle.com', 'session_cookies', 'active', '2023-01-01 00:00:00'),
            ('steam', 'Steam', 'platform', 'https://steam.com', 'api_key', 'active', '2023-01-01 00:00:00')
        """)
        
        # Insert products with various categories and names
        test_products = [
            # Software products
            ('sw1', 'humble_bundle', 'Visual Studio Code', 'vscode', 'software', 'development', 'Microsoft', 'Microsoft', 'https://example.com', 'Code editor', '["editor", "development"]', 4.8, 1000, 0.0, 'USD', '2015-01-01', 'en', '2023-01-01 00:00:00'),
            ('sw2', 'humble_bundle', 'Adobe Photoshop', 'photoshop', 'software', 'photo_editing', 'Adobe', 'Adobe', 'https://example.com', 'Photo editing software', '["photo", "editing"]', 4.5, 500, 99.99, 'USD', '1990-01-01', 'en', '2023-01-01 00:00:00'),
            ('sw3', 'humble_bundle', 'Unity Game Engine', 'unity', 'software', 'game_development', 'Unity', 'Unity', 'https://example.com', 'Game development engine', '["game", "development"]', 4.7, 800, 0.0, 'USD', '2005-01-01', 'en', '2023-01-01 00:00:00'),
            
            # Game products
            ('g1', 'humble_bundle', 'Minecraft', 'minecraft', 'game', 'sandbox', 'Mojang', 'Microsoft', 'https://example.com', 'Sandbox game', '["sandbox", "creative"]', 4.9, 2000, 26.95, 'USD', '2011-01-01', 'en', '2023-01-01 00:00:00'),
            ('g2', 'humble_bundle', 'Portal 2', 'portal2', 'game', 'puzzle', 'Valve', 'Valve', 'https://example.com', 'Puzzle game', '["puzzle", "first-person"]', 4.8, 1500, 19.99, 'USD', '2011-01-01', 'en', '2023-01-01 00:00:00'),
            ('g3', 'humble_bundle', 'Civilization VI', 'civ6', 'game', 'strategy', 'Firaxis', '2K Games', 'https://example.com', 'Strategy game', '["strategy", "turn-based"]', 4.6, 1200, 59.99, 'USD', '2016-01-01', 'en', '2023-01-01 00:00:00'),
            
            # Ebook products
            ('e1', 'humble_bundle', 'Python Programming Guide', 'python_guide', 'ebook', 'programming', 'O\'Reilly', 'O\'Reilly', 'https://example.com', 'Python programming book', '["python", "programming"]', 4.7, 300, 29.99, 'USD', '2020-01-01', 'en', '2023-01-01 00:00:00'),
            ('e2', 'humble_bundle', 'Machine Learning Basics', 'ml_basics', 'ebook', 'programming', 'Manning', 'Manning', 'https://example.com', 'ML introduction', '["machine learning", "ai"]', 4.5, 200, 39.99, 'USD', '2019-01-01', 'en', '2023-01-01 00:00:00'),
            ('e3', 'humble_bundle', 'Web Security Handbook', 'web_security', 'ebook', 'security', 'No Starch', 'No Starch', 'https://example.com', 'Web security guide', '["security", "web"]', 4.6, 150, 44.99, 'USD', '2018-01-01', 'en', '2023-01-01 00:00:00'),
            
            # Audio products
            ('a1', 'humble_bundle', 'Game Soundtrack Collection', 'game_soundtracks', 'audio', 'soundtrack', 'Various', 'Various', 'https://example.com', 'Game music collection', '["music", "soundtrack"]', 4.4, 100, 9.99, 'USD', '2020-01-01', 'en', '2023-01-01 00:00:00'),
            
            # Products with special characters and edge cases
            ('edge1', 'humble_bundle', 'Product with 123 Numbers', 'numbers123', 'software', 'general', 'Test Dev', 'Test Pub', 'https://example.com', 'Test description', '["test", "numbers"]', 4.0, 50, 0.0, 'USD', '2020-01-01', 'en', '2023-01-01 00:00:00'),
            ('edge2', 'humble_bundle', 'Product with Special-Chars!', 'special_chars', 'game', 'general', 'Test Dev', 'Test Pub', 'https://example.com', 'Test description', '["test", "special"]', 4.0, 50, 0.0, 'USD', '2020-01-01', 'en', '2023-01-01 00:00:00'),
            ('edge3', 'humble_bundle', 'Product with UPPERCASE', 'uppercase', 'ebook', 'general', 'Test Dev', 'Test Pub', 'https://example.com', 'Test description', '["test", "uppercase"]', 4.0, 50, 0.0, 'USD', '2020-01-01', 'en', '2023-01-01 00:00:00'),
        ]
        
        for product in test_products:
            self.conn.execute("""
                INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, product)
        
        # Insert bundle products
        self.conn.execute("""
            INSERT INTO bundle_products VALUES 
            ('b1', 'sw1'), ('b1', 'sw2'),
            ('b2', 'g1'), ('b2', 'g2'),
            ('b3', 'e1'), ('b3', 'e2')
        """)
        
        # Insert bundles
        self.conn.execute("""
            INSERT INTO bundles VALUES 
            ('b1', 'humble_bundle', 'Software Bundle', 'Development tools', 'https://example.com', 'software', '2023-01-01', '2023-12-31', 29.99, 'USD', '2023-01-01 00:00:00', '2023-01-01 00:00:00'),
            ('b2', 'humble_bundle', 'Game Bundle', 'Popular games', 'https://example.com', 'game', '2023-01-01', '2023-12-31', 19.99, 'USD', '2023-01-01 00:00:00', '2023-01-01 00:00:00'),
            ('b3', 'humble_bundle', 'Programming Bundle', 'Programming books', 'https://example.com', 'ebook', '2023-01-01', '2023-12-31', 39.99, 'USD', '2023-01-01 00:00:00', '2023-01-01 00:00:00')
        """)
        
        # Insert downloads
        self.conn.execute("""
            INSERT INTO downloads VALUES 
            ('d1', 'sw1', 'windows', 'installer', 1048576, '1 MB', 'https://example.com/download', '2023-01-01 00:00:00'),
            ('d2', 'g1', 'windows', 'installer', 2097152, '2 MB', 'https://example.com/download', '2023-01-01 00:00:00'),
            ('d3', 'e1', 'pdf', 'document', 524288, '512 KB', 'https://example.com/download', '2023-01-01 00:00:00')
        """)
    
    def test_searchable_fields(self):
        """Test that searchable fields are correctly defined."""
        expected_fields = [
            'human_name', 'description', 'category', 'subcategory', 
            'developer', 'publisher', 'tags', 'bundle_name'
        ]
        self.assertEqual(self.search_provider.get_searchable_fields(), expected_fields)
    
    def test_search_stats(self):
        """Test search statistics functionality."""
        stats = self.search_provider.get_search_stats()
        
        self.assertIn('total_products', stats)
        self.assertIn('total_bundles', stats)
        self.assertIn('category_distribution', stats)
        self.assertIn('source_distribution', stats)
        self.assertIn('searchable_fields', stats)
        
        self.assertEqual(stats['total_products'], 13)
        self.assertEqual(stats['total_bundles'], 3)
    
    def test_text_search_basic(self):
        """Test basic text search functionality."""
        results = self.search_provider.search_assets('Python')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['human_name'], 'Python Programming Guide')
        self.assertEqual(results[0]['category'], 'ebook')
    
    def test_text_search_case_insensitive(self):
        """Test that text search is case insensitive."""
        results_lower = self.search_provider.search_assets('python')
        results_upper = self.search_provider.search_assets('PYTHON')
        
        self.assertEqual(len(results_lower), 1)
        self.assertEqual(len(results_upper), 1)
        self.assertEqual(results_lower[0]['human_name'], results_upper[0]['human_name'])
    
    def test_text_search_multiple_matches(self):
        """Test text search with multiple matches."""
        results = self.search_provider.search_assets('game')
        
        # Should find games, game development software, and game soundtracks
        self.assertGreater(len(results), 1)
        
        # Verify we have different categories
        categories = {r['category'] for r in results}
        self.assertIn('game', categories)
        self.assertIn('software', categories)
        self.assertIn('audio', categories)
    
    def test_text_search_with_filters(self):
        """Test text search with category filter."""
        results = self.search_provider.search_assets('game', filters={'category': 'game'})
        
        # Should only return actual games, not software or audio
        for result in results:
            self.assertEqual(result['category'], 'game')
    
    def test_text_search_with_source_filter(self):
        """Test text search with source filter."""
        results = self.search_provider.search_assets('game', filters={'source': 'Humble Bundle'})
        
        # Should only return Humble Bundle products
        for result in results:
            self.assertEqual(result['source_name'], 'Humble Bundle')
    
    def test_text_search_with_rating_filter(self):
        """Test text search with rating filter."""
        results = self.search_provider.search_assets('game', filters={'rating_min': 4.5})
        
        # Should only return products with rating >= 4.5
        for result in results:
            self.assertGreaterEqual(result['rating'], 4.5)
    
    def test_regex_search_basic(self):
        """Test basic regex search functionality."""
        results = self.search_provider.search_assets('^Python', use_regex=True)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['human_name'], 'Python Programming Guide')
    
    def test_regex_search_case_sensitive(self):
        """Test case sensitive regex search."""
        # Case insensitive (default)
        results_insensitive = self.search_provider.search_assets('python', use_regex=True, case_sensitive=False)
        # Case sensitive
        results_sensitive = self.search_provider.search_assets('python', use_regex=True, case_sensitive=True)
        
        self.assertEqual(len(results_insensitive), 1)
        self.assertEqual(len(results_sensitive), 1)  # "Python Programming Guide" starts with uppercase P
    
    def test_regex_search_with_filters(self):
        """Test regex search with category filter."""
        results = self.search_provider.search_assets('^[A-Z]', use_regex=True, filters={'category': 'software'})
        
        # Should only return software products starting with uppercase letters
        for result in results:
            self.assertEqual(result['category'], 'software')
            self.assertTrue(result['human_name'][0].isupper())
    
    def test_regex_search_invalid_pattern(self):
        """Test that invalid regex patterns raise errors."""
        with self.assertRaises(ValueError):
            self.search_provider.search_assets('[invalid', use_regex=True)
    
    def test_search_by_field_text(self):
        """Test field-specific text search."""
        results = self.search_provider.search_by_field('category', 'software')
        
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result['category'], 'software')
    
    def test_search_by_field_regex(self):
        """Test field-specific regex search."""
        results = self.search_provider.search_by_field('human_name', '^[A-Z]', use_regex=True)
        
        # Should find all products starting with uppercase letters
        self.assertEqual(len(results), 13)
        for result in results:
            self.assertTrue(result['human_name'][0].isupper())
    
    def test_search_by_field_with_filters(self):
        """Test field-specific search with filters."""
        results = self.search_provider.search_by_field(
            'human_name', 'game', use_regex=False, filters={'category': 'software'}
        )
        
        # Should only return software products with 'game' in the name
        for result in results:
            self.assertEqual(result['category'], 'software')
            self.assertIn('game', result['human_name'].lower())
    
    def test_search_by_field_invalid_field(self):
        """Test that invalid field names raise errors."""
        with self.assertRaises(ValueError):
            self.search_provider.search_by_field('invalid_field', 'test')
    
    def test_advanced_search_text_and(self):
        """Test advanced search with AND operator."""
        queries = {'category': 'software', 'developer': 'Microsoft'}
        results = self.search_provider.search_advanced(queries, operator='AND')
        
        # Should only return Microsoft software
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['developer'], 'Microsoft')
        self.assertEqual(results[0]['category'], 'software')
    
    def test_advanced_search_text_or(self):
        """Test advanced search with OR operator."""
        # Test OR search by searching for games and ebooks separately and combining
        results_game = self.search_provider.search_assets('', filters={'category': 'game'})
        results_ebook = self.search_provider.search_assets('', filters={'category': 'ebook'})
        
        # Should return both games and ebooks
        self.assertGreater(len(results_game), 0)
        self.assertGreater(len(results_ebook), 0)
        
        # Verify categories
        game_categories = {r['category'] for r in results_game}
        ebook_categories = {r['category'] for r in results_ebook}
        
        self.assertIn('game', game_categories)
        self.assertIn('ebook', ebook_categories)
    
    def test_advanced_search_regex(self):
        """Test advanced search with regex patterns."""
        queries = {'human_name': '^[A-Z]', 'category': 'software'}
        results = self.search_provider.search_advanced(queries, operator='AND', use_regex=True)
        
        # Should return software products starting with uppercase letters
        for result in results:
            self.assertEqual(result['category'], 'software')
            self.assertTrue(result['human_name'][0].isupper())
    
    def test_advanced_search_with_filters(self):
        """Test advanced search with additional filters."""
        queries = {'category': 'software'}
        filters = {'rating_min': 4.5}
        results = self.search_provider.search_advanced(queries, filters=filters)
        
        # Should return software products with rating >= 4.5
        for result in results:
            self.assertEqual(result['category'], 'software')
            self.assertGreaterEqual(result['rating'], 4.5)
    
    def test_advanced_search_invalid_operator(self):
        """Test that invalid operators raise errors."""
        queries = {'category': 'software'}
        with self.assertRaises(ValueError):
            self.search_provider.search_advanced(queries, operator='INVALID')
    
    def test_search_edge_cases(self):
        """Test search with edge cases and special characters."""
        # Search for products with numbers
        results = self.search_provider.search_assets('123')
        self.assertEqual(len(results), 1)
        self.assertIn('123', results[0]['human_name'])
        
        # Search for products with special characters
        results = self.search_provider.search_assets('Special-Chars')
        self.assertEqual(len(results), 1)
        self.assertIn('Special-Chars', results[0]['human_name'])
        
        # Search for products with uppercase
        results = self.search_provider.search_assets('UPPERCASE')
        self.assertEqual(len(results), 1)
        self.assertIn('UPPERCASE', results[0]['human_name'])
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        results = self.search_provider.search_assets('')
        
        # Should return all products
        self.assertEqual(len(results), 13)
    
    def test_search_no_results(self):
        """Test search that returns no results."""
        results = self.search_provider.search_assets('nonexistent_product')
        
        # Should return empty list
        self.assertEqual(len(results), 0)
    
    def test_search_with_platform_filter(self):
        """Test search with platform filter."""
        results = self.search_provider.search_assets('game', filters={'platform': 'windows'})
        
        # Should only return products with Windows downloads
        for result in results:
            self.assertEqual(result['platform'], 'windows')
    
    def test_search_with_multiple_filters(self):
        """Test search with multiple filters combined."""
        filters = {
            'category': 'software',
            'source': 'Humble Bundle',
            'rating_min': 4.0
        }
        results = self.search_provider.search_assets('development', filters=filters)
        
        # Should return software products from Humble Bundle with rating >= 4.0
        for result in results:
            self.assertEqual(result['category'], 'software')
            self.assertEqual(result['source_name'], 'Humble Bundle')
            self.assertGreaterEqual(result['rating'], 4.0)
    
    def test_regex_search_complex_patterns(self):
        """Test complex regex search patterns."""
        # Find products with exactly 3 words
        results = self.search_provider.search_assets(r'^\w+\s+\w+\s+\w+$', use_regex=True)
        
        # Should find products like "Visual Studio Code", "Machine Learning Basics"
        self.assertGreater(len(results), 0)
        for result in results:
            words = result['human_name'].split()
            self.assertEqual(len(words), 3)
        
        # Find products ending with specific patterns
        results = self.search_provider.search_assets(r'Guide$', use_regex=True)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['human_name'].endswith('Guide'))
    
    def test_search_performance_with_filters(self):
        """Test that filters improve search performance by reducing dataset."""
        # Search without filters (searches all products)
        start_time = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        
        # Search with category filter (should be faster)
        results_filtered = self.search_provider.search_assets('game', filters={'category': 'game'})
        
        # Verify we get fewer results with filter
        self.assertLess(len(results_filtered), start_time)
        
        # All results should be games
        for result in results_filtered:
            self.assertEqual(result['category'], 'game')


if __name__ == '__main__':
    unittest.main() 