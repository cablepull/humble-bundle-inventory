#!/usr/bin/env python3
"""
Basic test to check imports and basic functionality without authentication.
"""

from rich.console import Console

console = Console()

def test_imports():
    """Test that all modules can be imported."""
    console.print("📦 Testing module imports...", style="blue")
    
    try:
        from persistent_session_auth import PersistentSessionAuth
        console.print("   ✅ persistent_session_auth imported", style="green")
    except Exception as e:
        console.print(f"   ❌ persistent_session_auth failed: {e}", style="red")
        return False
    
    try:
        from har_based_client import HARBasedLibraryClient
        console.print("   ✅ har_based_client imported", style="green")
    except Exception as e:
        console.print(f"   ❌ har_based_client failed: {e}", style="red")
        return False
    
    try:
        from sync import HumbleBundleSync
        console.print("   ✅ sync imported", style="green")
    except Exception as e:
        console.print(f"   ❌ sync failed: {e}", style="red")
        return False
    
    try:
        from database import HumbleBundleDatabase
        console.print("   ✅ database imported", style="green")
    except Exception as e:
        console.print(f"   ❌ database failed: {e}", style="red")
        return False
    
    return True

def test_database_basic():
    """Test basic database operations."""
    console.print("\n🗄️ Testing basic database operations...", style="blue")
    
    try:
        from database import HumbleBundleDatabase
        
        with HumbleBundleDatabase() as db:
            # Test getting stats (should work even with empty DB)
            stats = db.get_library_stats()
            console.print(f"   ✅ Database stats: {stats}", style="green")
            
            # Test search (should return empty results)
            results = db.search_products("test", limit=1)
            console.print(f"   ✅ Search results: {len(results)} items", style="green")
            
        return True
        
    except Exception as e:
        console.print(f"   ❌ Database test failed: {e}", style="red")
        return False

def test_session_info():
    """Test session info without authentication."""
    console.print("\n🔐 Testing session info...", style="blue")
    
    try:
        from persistent_session_auth import PersistentSessionAuth
        
        auth = PersistentSessionAuth()
        session_info = auth.get_session_info()
        console.print(f"   ✅ Session info: {session_info['status']}", style="green")
        
        return True
        
    except Exception as e:
        console.print(f"   ❌ Session info test failed: {e}", style="red")
        return False

def main():
    """Run basic tests."""
    console.print("🧪 Basic Integration Tests", style="bold magenta")
    console.print("=" * 30)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Basic", test_database_basic),
        ("Session Info", test_session_info)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    console.print(f"\n📊 Results: {passed}/{len(tests)} tests passed", 
                  style="green" if passed == len(tests) else "yellow")
    
    if passed == len(tests):
        console.print("✅ All basic tests passed! System ready for authentication testing.", style="bold green")
    else:
        console.print("⚠️  Some basic tests failed. Check the errors above.", style="bold yellow")

if __name__ == "__main__":
    main()