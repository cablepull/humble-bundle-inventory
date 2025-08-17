#!/usr/bin/env python3
"""Test script for Selenium-based sync functionality."""

from src.humble_bundle_inventory.auth_selenium import HumbleBundleAuthSelenium
from src.humble_bundle_inventory.config import settings
from scripts.prototypes.humble_client import HumbleBundleClient

def test_sync():
    print("🚀 Testing Selenium-based sync functionality...")
    print(f"Email: {settings.humble_email}")
    print(f"Password: {'*' * len(settings.humble_password) if settings.humble_password else 'None'}")
    
    # Use headless mode for production testing
    print("\n🖥️  Starting browser in headless mode...")
    
    with HumbleBundleAuthSelenium(headless=True) as auth:
        try:
            print("\n🔄 Attempting login...")
            success = auth.login()
            
            if success:
                print("✅ Login successful!")
                
                # Test session verification
                print("🔍 Verifying session...")
                if auth._verify_session():
                    print("✅ Session verified successfully!")
                    
                    # Test client functionality
                    print("📚 Testing library access...")
                    client = HumbleBundleClient(auth)
                    
                    try:
                        library_data = client.get_library_data()
                        print("✅ Successfully retrieved library data!")
                        
                        # Get orders
                        orders = client.get_orders()
                        print(f"📦 Found {len(orders)} orders/bundles")
                        
                        if orders:
                            # Show first order as example
                            first_order = orders[0]
                            print(f"\n📋 First order: {first_order['bundle_name']}")
                            print(f"   Type: {first_order['bundle_type']}")
                            print(f"   Products: {len(first_order['products'])}")
                            
                            if first_order['products']:
                                first_product = first_order['products'][0]
                                print(f"   First product: {first_product['human_name']}")
                        
                    except Exception as e:
                        print(f"❌ Error accessing library: {e}")
                        
                else:
                    print("❌ Session verification failed!")
                    
            else:
                print("❌ Login failed!")
                
        except Exception as e:
            print(f"❌ Error during sync test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_sync() 