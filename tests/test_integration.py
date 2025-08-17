#!/usr/bin/env python3
"""
Integration test script for the updated Humble Bundle synchronizer.
Tests the persistent session authentication and HAR-based data extraction.
"""

import time
from rich.console import Console
from rich.panel import Panel
from scripts.persistent_session_auth import PersistentSessionAuth
from scripts.har_based_client import HARBasedLibraryClient
from scripts.legacy.sync import HumbleBundleSync
from src.humble_bundle_inventory.database import HumbleBundleDatabase

console = Console()

def test_persistent_auth():
    """Test persistent session authentication."""
    console.print("🔐 Testing Persistent Session Authentication", style="bold blue")
    
    auth = PersistentSessionAuth(headless=True)
    
    try:
        # Check existing session
        session_info = auth.get_session_info()
        console.print(f"📋 Session status: {session_info['status']}")
        
        if session_info['status'] == 'exists':
            console.print(f"   Age: {session_info['age_hours']:.1f}h")
            console.print(f"   Signature: {session_info['signature']}")
        
        # Test authentication
        console.print("🔄 Testing authentication...")
        success = auth.login()
        
        if success:
            console.print("✅ Authentication successful!", style="green")
            
            # Test session verification
            console.print("🔍 Testing session verification...")
            if auth._verify_persistent_session():
                console.print("✅ Session verification successful!", style="green")
            else:
                console.print("❌ Session verification failed!", style="red")
                return False
        else:
            console.print("❌ Authentication failed!", style="red")
            return False
        
        return True
        
    except Exception as e:
        console.print(f"❌ Authentication test failed: {e}", style="red")
        return False
    finally:
        # Don't logout in test - preserve session
        pass

def test_har_client():
    """Test HAR-based client data extraction."""
    console.print("\n📊 Testing HAR-Based Data Extraction", style="bold blue")
    
    try:
        auth = PersistentSessionAuth(headless=True)
        
        if not auth.login():
            console.print("❌ Authentication failed for client test", style="red")
            return False
        
        client = HARBasedLibraryClient(auth)
        
        console.print("🔄 Extracting comprehensive library data...")
        start_time = time.time()
        
        library_data = client.get_comprehensive_library_data()
        
        extraction_time = time.time() - start_time
        
        # Analyze results
        products = library_data.get('products', [])
        bundles = library_data.get('bundles', [])
        downloads = library_data.get('downloads', [])
        user_data = library_data.get('user_data', {})
        
        console.print(f"✅ Data extraction completed in {extraction_time:.2f}s", style="green")
        console.print(f"   📦 Products: {len(products)}")
        console.print(f"   📚 Bundles: {len(bundles)}")
        console.print(f"   📥 Downloads: {len(downloads)}")
        
        # Show sample data
        if products:
            console.print("\n📦 Sample Products:")
            for i, product in enumerate(products[:3]):
                console.print(f"   {i+1}. {product.get('name', 'Unknown')} ({product.get('category', 'unknown')})")
        
        if user_data and user_data.get('extracted_fields'):
            fields = user_data['extracted_fields']
            console.print(f"\n👤 User: {fields.get('email', 'Unknown')}")
        
        return len(products) > 0 or len(bundles) > 0
        
    except Exception as e:
        console.print(f"❌ HAR client test failed: {e}", style="red")
        import traceback
        traceback.print_exc()
        return False

def test_sync_system():
    """Test the integrated sync system."""
    console.print("\n🔄 Testing Integrated Sync System", style="bold blue")
    
    try:
        syncer = HumbleBundleSync()
        
        console.print("🔄 Running sync test...")
        start_time = time.time()
        
        # Force sync to test the system
        result = syncer.sync(force=True)
        
        sync_time = time.time() - start_time
        
        console.print(f"✅ Sync completed in {sync_time:.2f}s", style="green")
        console.print(f"   Status: {result['status']}")
        console.print(f"   Products synced: {result.get('products_synced', 0)}")
        console.print(f"   Products failed: {result.get('products_failed', 0)}")
        
        if result.get('error_log'):
            console.print(f"   Errors: {result['error_log'][:200]}...", style="yellow")
        
        return result['status'] in ['success', 'partial']
        
    except Exception as e:
        console.print(f"❌ Sync test failed: {e}", style="red")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    """Test database operations."""
    console.print("\n🗄️ Testing Database Operations", style="bold blue")
    
    try:
        with HumbleBundleDatabase() as db:
            # Get library stats
            stats = db.get_library_stats()
            
            console.print("📊 Library Statistics:")
            console.print(f"   Total bundles: {stats.get('total_bundles', 0)}")
            console.print(f"   Total products: {stats.get('total_products', 0)}")
            console.print(f"   Total downloads: {stats.get('total_downloads', 0)}")
            console.print(f"   Total spent: ${stats.get('total_spent', 0):.2f}")
            
            # Test search
            search_results = db.search_products("test", limit=5)
            console.print(f"   Search test results: {len(search_results)} items")
            
            # Get last sync info
            last_sync = db.get_last_sync()
            if last_sync:
                console.print(f"   Last sync: {last_sync['last_sync_timestamp']}")
                console.print(f"   Last sync status: {last_sync['sync_status']}")
            
            return True
            
    except Exception as e:
        console.print(f"❌ Database test failed: {e}", style="red")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run integration tests."""
    console.print("🧪 Humble Bundle Integration Tests", style="bold magenta")
    console.print("=" * 50)
    
    test_results = {}
    
    # Run tests
    test_results['auth'] = test_persistent_auth()
    test_results['client'] = test_har_client()
    test_results['sync'] = test_sync_system()
    test_results['database'] = test_database()
    
    # Summary
    console.print("\n📋 Test Results Summary", style="bold blue")
    console.print("=" * 30)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        style = "green" if result else "red"
        console.print(f"   {test_name.title()}: {status}", style=style)
        if not result:
            all_passed = False
    
    console.print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}", 
                  style="green" if all_passed else "red")
    
    if all_passed:
        console.print("\n🚀 Integration successful! The system is ready to use.", style="bold green")
        console.print("\nNext steps:")
        console.print("   1. Run 'python main.py login' to authenticate")
        console.print("   2. Run 'python main.py sync' to synchronize your library")
        console.print("   3. Run 'python main.py status' to view library statistics")
    else:
        console.print("\n🔧 Some tests failed. Please check the error messages above.", style="bold red")

if __name__ == "__main__":
    main()