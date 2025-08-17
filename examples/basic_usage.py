#!/usr/bin/env python3
"""
Basic usage examples for the Humble Bundle Inventory Manager.
"""

from humble_bundle_inventory import HumbleBundleAuthSelenium, AssetInventoryDatabase, EnhancedHumbleBundleSync

def basic_sync_example():
    """Example of basic sync operation."""
    print("🚀 Basic Sync Example")
    
    # Initialize authentication
    with HumbleBundleAuthSelenium(headless=True) as auth:
        # Login (will use saved session if available)
        if auth.login():
            print("✅ Authentication successful")
            
            # Initialize database
            with AssetInventoryDatabase() as db:
                # Create sync engine
                sync = EnhancedHumbleBundleSync(auth, db)
                
                # Perform sync
                results = sync.sync_humble_bundle_enhanced()
                
                print(f"📊 Sync Results:")
                print(f"   Products synced: {results['products_synced']}")
                print(f"   Status: {results['status']}")
        else:
            print("❌ Authentication failed")

def basic_search_example():
    """Example of searching the database."""
    print("🔍 Basic Search Example")
    
    with AssetInventoryDatabase() as db:
        from humble_bundle_inventory import DuckDBSearchProvider
        
        # Create search provider
        search = DuckDBSearchProvider(db.conn)
        
        # Search for Python books
        results = search.search_assets("python", {"category": "ebook"})
        
        print(f"Found {len(results)} Python ebooks:")
        for result in results[:5]:  # Show first 5
            print(f"   - {result['human_name']}")

if __name__ == "__main__":
    basic_sync_example()
    basic_search_example()