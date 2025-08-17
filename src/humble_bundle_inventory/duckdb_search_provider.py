#!/usr/bin/env python3
"""
DuckDB implementation of the SearchProvider interface.
Provides regex search capabilities for the DuckDB database.
"""

import duckdb
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .search_provider import SearchProvider

class DuckDBSearchProvider(SearchProvider):
    """
    DuckDB implementation of SearchProvider with regex search capabilities.
    """
    
    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        """
        Initialize the DuckDB search provider.
        
        Args:
            db_connection: Active DuckDB connection
        """
        self.conn = db_connection
        self.searchable_fields = [
            'human_name', 'description', 'category', 'subcategory', 
            'developer', 'publisher', 'tags', 'bundle_name'
        ]
    
    def search_assets(self, 
                     query: str, 
                     filters: Optional[Dict[str, Any]] = None,
                     use_regex: bool = False,
                     case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search assets using text or regex patterns.
        
        Args:
            query: Search query (text pattern or regex)
            filters: Optional filters to apply
            use_regex: Whether to treat query as regex pattern
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of matching assets with metadata
        """
        if use_regex:
            return self._search_with_regex(query, filters, case_sensitive)
        else:
            return self._search_with_text(query, filters)
    
    def search_by_field(self, 
                       field: str, 
                       query: str, 
                       use_regex: bool = False,
                       case_sensitive: bool = False,
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search assets by specific field using text or regex patterns.
        
        Args:
            field: Field name to search in
            query: Search query (text pattern or regex)
            use_regex: Whether to treat query as regex pattern
            case_sensitive: Whether search should be case sensitive
            filters: Optional filters to apply (category, source, platform, etc.)
            
        Returns:
            List of matching assets with metadata
        """
        if field not in self.searchable_fields:
            raise ValueError(f"Field '{field}' is not searchable. Available fields: {self.searchable_fields}")
        
        if use_regex:
            return self._search_field_with_regex(field, query, case_sensitive, filters)
        else:
            return self._search_field_with_text(field, query, filters)
    
    def search_advanced(self, 
                       queries: Dict[str, str], 
                       filters: Optional[Dict[str, Any]] = None,
                       use_regex: bool = False,
                       case_sensitive: bool = False,
                       operator: str = 'AND') -> List[Dict[str, Any]]:
        """
        Advanced search with multiple field queries.
        
        Args:
            queries: Dict of field_name -> query pairs
            filters: Optional filters to apply
            use_regex: Whether to treat queries as regex patterns
            case_sensitive: Whether search should be case sensitive
            operator: 'AND' or 'OR' to combine multiple queries
            
        Returns:
            List of matching assets with metadata
        """
        if operator not in ['AND', 'OR']:
            raise ValueError("Operator must be 'AND' or 'OR'")
        
        if use_regex:
            return self._advanced_search_with_regex(queries, filters, case_sensitive, operator)
        else:
            return self._advanced_search_with_text(queries, filters, operator)
    
    def get_searchable_fields(self) -> List[str]:
        """Get list of fields that can be searched."""
        return self.searchable_fields.copy()
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics and metadata."""
        try:
            # Get total counts
            total_products = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            total_bundles = self.conn.execute("SELECT COUNT(*) FROM bundles").fetchone()[0]
            
            # Get category distribution
            category_stats = self.conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM products 
                GROUP BY category 
                ORDER BY count DESC
            """).fetchall()
            
            # Get source distribution
            source_stats = self.conn.execute("""
                SELECT a.source_name, COUNT(p.product_id) as count
                FROM asset_sources a
                LEFT JOIN products p ON a.source_id = p.source_id
                GROUP BY a.source_name
                ORDER BY count DESC
            """).fetchall()
            
            return {
                'total_products': total_products,
                'total_bundles': total_bundles,
                'category_distribution': [{'category': row[0], 'count': row[1]} for row in category_stats],
                'source_distribution': [{'source': row[0], 'count': row[1]} for row in source_stats],
                'searchable_fields': self.searchable_fields,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'searchable_fields': self.searchable_fields,
                'last_updated': datetime.now().isoformat()
            }
    
    def _search_with_text(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using simple text patterns (ILIKE)."""
        sql = """
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        WHERE (p.human_name ILIKE ? OR p.description ILIKE ? OR p.tags ILIKE ?)
        """
        
        params = [f'%{query}%', f'%{query}%', f'%{query}%']
        
        # Add filters
        if filters:
            sql, params = self._add_filters_to_sql(sql, params, filters)
        
        sql += " ORDER BY p.human_name"
        
        results = self.conn.execute(sql, params).fetchall()
        return self._format_results(results)
    
    def _search_with_regex(self, query: str, filters: Optional[Dict[str, Any]] = None, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search using regex patterns."""
        # Validate regex pattern
        if not self.validate_regex(query):
            raise ValueError(f"Invalid regex pattern: {query}")
        
        # Get all products first (since DuckDB regex support varies)
        base_sql = """
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        """
        
        # Add filters
        if filters:
            base_sql, params = self._add_filters_to_sql(base_sql, [], filters)
        else:
            params = []
        
        base_sql += " ORDER BY p.human_name"
        
        # Get all results and filter with Python regex
        results = self.conn.execute(base_sql, params).fetchall()
        
        # Apply regex filtering
        pattern = re.compile(query, re.IGNORECASE if not case_sensitive else 0)
        filtered_results = []
        
        for row in results:
            # Check if any searchable field matches the regex
            if self._row_matches_regex(pattern, row):
                filtered_results.append(row)
        
        return self._format_results(filtered_results)
    
    def _search_field_with_text(self, field: str, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search specific field using text patterns."""
        sql = f"""
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        WHERE p.{field} ILIKE ?
        """
        
        params = [f'%{query}%']
        
        # Add filters
        if filters:
            sql, params = self._add_filters_to_sql(sql, params, filters)
        
        sql += " ORDER BY p.human_name"
        
        results = self.conn.execute(sql, params).fetchall()
        return self._format_results(results)
    
    def _search_field_with_regex(self, field: str, query: str, case_sensitive: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search specific field using regex patterns."""
        if not self.validate_regex(query):
            raise ValueError(f"Invalid regex pattern: {query}")
        
        # Build SQL with filters applied first
        sql = f"""
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        """
        
        params = []
        
        # Add filters first (this will reduce the dataset before regex processing)
        if filters:
            sql, params = self._add_filters_to_sql(sql, params, filters)
        
        sql += " ORDER BY p.human_name"
        
        # Get filtered results from database
        results = self.conn.execute(sql, params).fetchall()
        
        # Apply regex filtering to specific field on the already-filtered results
        pattern = re.compile(query, re.IGNORECASE if not case_sensitive else 0)
        filtered_results = []
        
        for row in results:
            field_value = self._get_field_value(row, field)
            if field_value and pattern.search(str(field_value)):
                filtered_results.append(row)
        
        return self._format_results(filtered_results)
    
    def _advanced_search_with_text(self, queries: Dict[str, str], filters: Optional[Dict[str, Any]] = None, operator: str = 'AND') -> List[Dict[str, Any]]:
        """Advanced search with multiple text queries."""
        sql = """
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        WHERE """
        
        conditions = []
        params = []
        
        for field, query in queries.items():
            if field in self.searchable_fields:
                conditions.append(f"p.{field} ILIKE ?")
                params.append(f'%{query}%')
        
        if not conditions:
            return []
        
        sql += f" {operator} ".join(conditions)
        
        # Add filters
        if filters:
            sql, params = self._add_filters_to_sql(sql, params, filters)
        
        sql += " ORDER BY p.human_name"
        
        results = self.conn.execute(sql, params).fetchall()
        return self._format_results(results)
    
    def _advanced_search_with_regex(self, queries: Dict[str, str], filters: Optional[Dict[str, Any]] = None, case_sensitive: bool = False, operator: str = 'AND') -> List[Dict[str, Any]]:
        """Advanced search with multiple regex queries."""
        # Validate all regex patterns
        for field, query in queries.items():
            if not self.validate_regex(query):
                raise ValueError(f"Invalid regex pattern for field '{field}': {query}")
        
        # Get base results
        base_sql = """
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        """
        
        # Add filters
        if filters:
            base_sql, params = self._add_filters_to_sql(base_sql, [], filters)
        else:
            params = []
        
        base_sql += " ORDER BY p.human_name"
        
        results = self.conn.execute(base_sql, params).fetchall()
        
        # Apply regex filtering with operator logic
        patterns = {field: re.compile(query, re.IGNORECASE if not case_sensitive else 0) 
                   for field, query in queries.items()}
        
        filtered_results = []
        
        for row in results:
            matches = []
            for field, pattern in patterns.items():
                field_value = self._get_field_value(row, field)
                if field_value and pattern.search(str(field_value)):
                    matches.append(True)
                else:
                    matches.append(False)
            
            # Apply operator logic
            if operator == 'AND' and all(matches):
                filtered_results.append(row)
            elif operator == 'OR' and any(matches):
                filtered_results.append(row)
        
        return self._format_results(filtered_results)
    
    def _add_filters_to_sql(self, sql: str, params: List[Any], filters: Dict[str, Any]) -> tuple:
        """Add filter conditions to SQL query."""
        if not filters:
            return sql, params
        
        filter_conditions = []
        
        if filters.get('category'):
            filter_conditions.append("p.category = ?")
            params.append(filters['category'])
        
        if filters.get('source'):
            filter_conditions.append("a.source_name = ?")
            params.append(filters['source'])
        
        if filters.get('platform'):
            filter_conditions.append("d.platform = ?")
            params.append(filters['platform'])
        
        if filters.get('rating_min'):
            filter_conditions.append("p.rating >= ?")
            params.append(filters['rating_min'])
        
        if filters.get('rating_max'):
            filter_conditions.append("p.rating <= ?")
            params.append(filters['rating_max'])
        
        if filter_conditions:
            # Check if we need to add WHERE or AND
            if "WHERE" in sql.upper():
                sql += " AND " + " AND ".join(filter_conditions)
            else:
                sql += " WHERE " + " AND ".join(filter_conditions)
        
        return sql, params
    
    def _row_matches_regex(self, pattern: re.Pattern, row: tuple) -> bool:
        """Check if a row matches the regex pattern in any searchable field."""
        for field in self.searchable_fields:
            field_value = self._get_field_value(row, field)
            if field_value and pattern.search(str(field_value)):
                return True
        return False
    
    def _get_field_value(self, row: tuple, field: str) -> Any:
        """Get field value from row tuple based on field name."""
        field_mapping = {
            'human_name': row[1],
            'description': None,  # Not in current select
            'category': row[2],
            'subcategory': row[3],
            'developer': row[4],
            'publisher': row[5],
            'tags': row[6],
            'bundle_name': row[10]
        }
        return field_mapping.get(field)
    
    def _format_results(self, results: List[tuple]) -> List[Dict[str, Any]]:
        """Format raw database results into dictionaries."""
        return [
            {
                'product_id': row[0],
                'human_name': row[1],
                'category': row[2],
                'subcategory': row[3],
                'developer': row[4],
                'publisher': row[5],
                'tags': row[6],
                'rating': row[7],
                'release_date': row[8],
                'source_name': row[9],
                'bundle_name': row[10],
                'platform': row[11],
                'download_type': row[12],
                'file_size_display': row[13]
            }
            for row in results
        ] 