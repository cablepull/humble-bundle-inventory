#!/usr/bin/env python3
"""Test script for Selenium-based Humble Bundle authentication."""

from src.humble_bundle_inventory.auth_selenium import HumbleBundleAuthSelenium
from src.humble_bundle_inventory.config import settings

def test_selenium_auth():
    print("🔐 Testing Selenium-based Humble Bundle authentication...")
    print(f"Email: {settings.humble_email}")
    print(f"Password: {'*' * len(settings.humble_password) if settings.humble_password else 'None'}")
    
    # Test with non-headless mode first so you can see what's happening
    print("\n🖥️  Starting browser in visible mode for testing...")
    
    with HumbleBundleAuthSelenium(headless=False) as auth:
        try:
            print("\n🔄 Attempting login...")
            success = auth.login()
            
            if success:
                print("✅ Login successful!")
                
                # Test session verification
                print("🔍 Verifying session...")
                if auth._verify_session():
                    print("✅ Session verified successfully!")
                    
                    # Test accessing library
                    print("📚 Testing library access...")
                    driver = auth.get_authenticated_session()
                    print(f"Current URL: {driver.current_url}")
                    
                    if 'library' in driver.current_url.lower():
                        print("✅ Successfully accessed library!")
                    else:
                        print("⚠️  Not on library page")
                        
                else:
                    print("❌ Session verification failed!")
                    
            else:
                print("❌ Login failed!")
                
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_selenium_auth() 