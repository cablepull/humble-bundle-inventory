#!/usr/bin/env python3
"""
Abstract search provider interface for digital asset inventory.
Allows regex search to be applied to any data connector.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import re

class SearchProvider(ABC):
    """
    Abstract base class for search providers.
    Defines the interface for regex search across different data sources.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def search_by_field(self, 
                       field: str, 
                       query: str, 
                       use_regex: bool = False,
                       case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search assets by specific field using text or regex patterns.
        
        Args:
            field: Field name to search in (e.g., 'name', 'category', 'tags')
            query: Search query (text pattern or regex)
            use_regex: Whether to treat query as regex pattern
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of matching assets with metadata
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_searchable_fields(self) -> List[str]:
        """
        Get list of fields that can be searched.
        
        Returns:
            List of searchable field names
        """
        pass
    
    @abstractmethod
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search statistics and metadata.
        
        Returns:
            Dict containing search statistics
        """
        pass
    
    def validate_regex(self, pattern: str) -> bool:
        """
        Validate if a regex pattern is valid.
        
        Args:
            pattern: Regex pattern to validate
            
        Returns:
            True if pattern is valid, False otherwise
        """
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    def escape_regex_special_chars(self, text: str) -> str:
        """
        Escape special regex characters in text for literal matching.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for regex literal matching
        """
        return re.escape(text)
    
    def build_regex_pattern(self, query: str, case_sensitive: bool = False) -> str:
        """
        Build a regex pattern from query string.
        
        Args:
            query: Query string
            case_sensitive: Whether pattern should be case sensitive
            
        Returns:
            Compiled regex pattern
        """
        if not case_sensitive:
            return re.compile(query, re.IGNORECASE)
        return re.compile(query)
    
    def match_regex(self, pattern: re.Pattern, text: str) -> bool:
        """
        Check if text matches regex pattern.
        
        Args:
            pattern: Compiled regex pattern
            text: Text to match against
            
        Returns:
            True if text matches pattern, False otherwise
        """
        if text is None:
            return False
        return bool(pattern.search(str(text))) 