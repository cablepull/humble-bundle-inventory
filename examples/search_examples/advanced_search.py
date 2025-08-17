#!/usr/bin/env python3
"""
Advanced search examples showing regex, filters, and field-specific searches.
"""

from humble_bundle_inventory import AssetInventoryDatabase, DuckDBSearchProvider

def regex_search_examples():
    """Examples of regex-based searching."""
    print("🔍 Regex Search Examples")
    
    with AssetInventoryDatabase() as db:
        search = DuckDBSearchProvider(db.conn)
        
        # Case-insensitive regex for machine learning books
        results = search.search_assets(
            r".*machine.*learning.*",
            use_regex=True,
            filters={"category": "ebook"}
        )
        print(f"Machine Learning books: {len(results)}")
        
        # Find games with numbers in the title
        results = search.search_assets(
            r".*\d+.*",
            use_regex=True,
            filters={"category": "game"}
        )
        print(f"Games with numbers: {len(results)}")

def field_specific_search():
    """Examples of field-specific searching."""
    print("🎯 Field-Specific Search Examples")
    
    with AssetInventoryDatabase() as db:
        search = DuckDBSearchProvider(db.conn)
        
        # Search only in developer field
        results = search.search_by_field("developer", "O'Reilly")
        print(f"O'Reilly publications: {len(results)}")
        
        # Search in category field
        results = search.search_by_field("category", "software")
        print(f"Software items: {len(results)}")

def complex_filter_examples():
    """Examples of complex filtering."""
    print("🔧 Complex Filter Examples")
    
    with AssetInventoryDatabase() as db:
        search = DuckDBSearchProvider(db.conn)
        
        # Multiple filters
        results = search.search_assets(
            "programming",
            filters={
                "category": "ebook",
                "source": "Humble Bundle"
            }
        )
        print(f"Programming ebooks from Humble Bundle: {len(results)}")

if __name__ == "__main__":
    regex_search_examples()
    field_specific_search()
    complex_filter_examples()