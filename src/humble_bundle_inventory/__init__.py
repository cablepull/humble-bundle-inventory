"""
Humble Bundle Asset Inventory Manager

A comprehensive digital asset inventory management system for Humble Bundle and other sources.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "A comprehensive digital asset inventory management system for Humble Bundle and other sources"

# Import main components for easy access
from .database import AssetInventoryDatabase
from .search_provider import SearchProvider
from .duckdb_search_provider import DuckDBSearchProvider
from .enhanced_sync import EnhancedHumbleBundleSync
from .auth_selenium import HumbleBundleAuthSelenium

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "AssetInventoryDatabase",
    "SearchProvider", 
    "DuckDBSearchProvider",
    "EnhancedHumbleBundleSync",
    "HumbleBundleAuthSelenium",
] 