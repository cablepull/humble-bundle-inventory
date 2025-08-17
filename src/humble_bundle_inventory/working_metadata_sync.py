#!/usr/bin/env python3
"""
Working metadata synchronization for Humble Bundle.
Extracts product metadata and syncs to the database.
"""

from .auth_selenium import HumbleBundleAuthSelenium
from .database import AssetInventoryDatabase
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .config import settings

class WorkingMetadataSync:
    """Working sync system that extracts metadata from Humble Bundle."""
    
    def __init__(self, auth: HumbleBundleAuthSelenium, db: AssetInventoryDatabase):
        self.auth = auth
        self.db = db
        self.driver = None
    
    def sync_humble_bundle_metadata(self) -> Dict[str, Any]:
        """Sync Humble Bundle metadata to the database."""
        if not self.driver:
            self.driver = self.auth.get_authenticated_session()
        
        print("📚 Starting Humble Bundle metadata sync...")
        
        # Ensure Humble Bundle source exists
        self.db.upsert_asset_source({
            'source_id': 'humble_bundle',
            'source_name': 'Humble Bundle',
            'source_type': 'platform',
            'source_url': 'https://www.humblebundle.com',
            'authentication_method': 'session_cookies',
            'sync_status': 'active'
        })
        
        # Navigate to library page
        print("   🌐 Navigating to library page...")
        self.driver.get('https://www.humblebundle.com/home/library')
        
        # Wait for initial page load
        print("   ⏳ Waiting for initial page load...")
        time.sleep(5)
        
        # Wait for content to load
        print("   ⏳ Waiting for content to load (30 seconds)...")
        time.sleep(30)
        
        # Extract products and metadata
        print("   🔍 Extracting products and metadata...")
        products_data = self._extract_products_metadata()
        
        # Extract bundles
        print("   🔍 Extracting bundles...")
        bundles_data = self._extract_bundles_data()
        
        # Sync to database
        print("   💾 Syncing to database...")
        sync_results = self._sync_to_database(products_data, bundles_data)
        
        # Record sync metadata
        self.db.record_sync(
            source_id='humble_bundle',
            status=sync_results['status'],
            products_synced=sync_results['products_synced'],
            products_failed=sync_results['products_failed'],
            bundles_synced=sync_results['bundles_synced'],
            bundles_failed=sync_results['bundles_failed'],
            error_log=sync_results.get('error_log'),
            duration_ms=sync_results['duration_ms']
        )
        
        print(f"   📊 Sync complete:")
        print(f"      Products synced: {sync_results['products_synced']}")
        print(f"      Products failed: {sync_results['products_failed']}")
        print(f"      Bundles synced: {sync_results['bundles_synced']}")
        print(f"      Bundles failed: {sync_results['bundles_failed']}")
        print(f"      Duration: {sync_results['duration_ms']}ms")
        
        return sync_results
    
    def _extract_products_metadata(self) -> List[Dict[str, Any]]:
        """Extract products and their metadata from the library page."""
        products = []
        
        try:
            # Look for the download list container we discovered
            download_list = self.driver.find_element(By.CSS_SELECTOR, ".hb-download-list.download-list")
            
            if not download_list:
                print("         ⚠️  Download list not found")
                return products
            
            print(f"         ✅ Found download list container")
            
            # Look for product headings within the download list
            product_headings = download_list.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            
            print(f"         📦 Found {len(product_headings)} product headings in download list")
            
            # For each product heading, extract metadata
            for i, heading in enumerate(product_headings):
                try:
                    product_name = heading.text.strip()
                    
                    # Skip non-product headings
                    if (len(product_name) < 10 or
                        product_name.startswith('Humble') or
                        product_name.startswith('Library') or
                        product_name.startswith('Welcome')):
                        continue
                    
                    if i % 100 == 0:
                        print(f"         🔍 Processing product {i+1}: {product_name[:50]}...")
                    
                    # Extract product metadata
                    product_data = self._extract_product_metadata(heading, product_name)
                    if product_data:
                        products.append(product_data)
                        
                except Exception as e:
                    print(f"            ❌ Error processing product: {e}")
                    continue
            
        except Exception as e:
            print(f"         ❌ Error extracting products: {e}")
        
        return products
    
    def _extract_product_metadata(self, heading, product_name: str) -> Optional[Dict[str, Any]]:
        """Extract metadata for a specific product."""
        try:
            # Generate product ID from name
            product_id = hashlib.md5(product_name.encode()).hexdigest()
            
            # Determine product category and subcategory
            category, subcategory = self._categorize_product(product_name)
            
            # Extract additional metadata from the heading context
            parent = heading.find_element(By.XPATH, "..")
            additional_info = self._extract_additional_metadata(parent)
            
            product_data = {
                'product_id': product_id,
                'source_id': 'humble_bundle',
                'human_name': product_name,
                'machine_name': product_name.lower().replace(' ', '_').replace('-', '_'),
                'category': category,
                'subcategory': subcategory,
                'developer': additional_info.get('developer'),
                'publisher': additional_info.get('publisher'),
                'url': additional_info.get('url'),
                'description': additional_info.get('description'),
                'tags': additional_info.get('tags', []),
                'rating': additional_info.get('rating'),
                'rating_count': additional_info.get('rating_count'),
                'retail_price': additional_info.get('retail_price'),
                'currency': 'USD',
                'release_date': additional_info.get('release_date'),
                'language': additional_info.get('language', 'en')
            }
            
            return product_data
            
        except Exception as e:
            print(f"            ⚠️  Error extracting product metadata: {e}")
            return None
    
    def _categorize_product(self, product_name: str) -> tuple:
        """Categorize a product based on its name."""
        name_lower = product_name.lower()
        
        # Game categories
        if any(word in name_lower for word in ['game', 'simulator', 'adventure', 'strategy', 'war', 'total war', 'collection', 'edition', 'steam', 'origin', 'uplay']):
            category = 'game'
            if 'rpg' in name_lower or 'role' in name_lower:
                subcategory = 'rpg'
            elif 'strategy' in name_lower or 'war' in name_lower:
                subcategory = 'strategy'
            elif 'simulator' in name_lower or 'sim' in name_lower:
                subcategory = 'simulation'
            elif 'adventure' in name_lower:
                subcategory = 'adventure'
            elif 'shooter' in name_lower or 'fps' in name_lower:
                subcategory = 'shooter'
            else:
                subcategory = 'general'
        
        # Book categories
        elif any(word in name_lower for word in ['guide', 'manual', 'tutorial', 'book', 'tips', 'secrets', 'cookbook', 'handbook', 'cooking', 'gardening', 'survival']):
            category = 'ebook'
            if 'cooking' in name_lower or 'recipe' in name_lower:
                subcategory = 'cooking'
            elif 'gardening' in name_lower or 'garden' in name_lower:
                subcategory = 'gardening'
            elif 'survival' in name_lower or 'prepper' in name_lower:
                subcategory = 'survival'
            elif 'programming' in name_lower or 'coding' in name_lower:
                subcategory = 'programming'
            elif 'business' in name_lower or 'finance' in name_lower:
                subcategory = 'business'
            else:
                subcategory = 'general'
        
        # Software categories
        elif any(word in name_lower for word in ['software', 'tool', 'utility', 'app', 'studio', 'pro', 'suite', 'editor']):
            category = 'software'
            if 'photo' in name_lower or 'image' in name_lower:
                subcategory = 'photo_editing'
            elif 'video' in name_lower or 'movie' in name_lower:
                subcategory = 'video_editing'
            elif 'audio' in name_lower or 'music' in name_lower:
                subcategory = 'audio_editing'
            elif '3d' in name_lower or 'modeling' in name_lower:
                subcategory = '3d_modeling'
            else:
                subcategory = 'general'
        
        # Comic categories
        elif any(word in name_lower for word in ['comic', 'manga', 'graphic novel', 'volume']):
            category = 'comic'
            subcategory = 'general'
        
        # Audio categories
        elif any(word in name_lower for word in ['audio', 'music', 'podcast', 'soundtrack', 'ost']):
            category = 'audio'
            subcategory = 'general'
        
        # Bundle categories
        elif any(word in name_lower for word in ['bundle', 'pack', 'collection', 'edition']):
            category = 'bundle'
            subcategory = 'mixed'
        
        else:
            category = 'unknown'
            subcategory = 'general'
        
        return category, subcategory
    
    def _extract_additional_metadata(self, parent_element) -> Dict[str, Any]:
        """Extract additional metadata from the parent element."""
        metadata = {}
        
        try:
            # Look for developer/publisher information
            text_content = parent_element.text
            
            # Look for common patterns
            if 'by ' in text_content:
                developer_match = text_content.split('by ')[1].split('\n')[0].strip()
                if developer_match and len(developer_match) < 100:
                    metadata['developer'] = developer_match
            
            # Look for price information
            if '$' in text_content:
                import re
                price_match = re.search(r'\$(\d+(?:\.\d{2})?)', text_content)
                if price_match:
                    metadata['retail_price'] = float(price_match.group(1))
            
            # Look for rating information
            if '★' in text_content or 'rating' in text_content.lower():
                import re
                rating_match = re.search(r'(\d+(?:\.\d{1,2})?)\s*(?:★|stars?|rating)', text_content, re.IGNORECASE)
                if rating_match:
                    metadata['rating'] = float(rating_match.group(1))
            
            # Extract tags from text content
            tags = []
            common_tags = ['indie', 'rpg', 'strategy', 'adventure', 'simulation', 'shooter', 'puzzle', 'platformer', 'racing', 'sports']
            for tag in common_tags:
                if tag in text_content.lower():
                    tags.append(tag)
            
            if tags:
                metadata['tags'] = tags
            
        except Exception as e:
            pass
        
        return metadata
    
    def _extract_bundles_data(self) -> List[Dict[str, Any]]:
        """Extract bundle information."""
        bundles = []
        
        try:
            # For now, create a default bundle since we're focusing on individual products
            # In the future, we can extract actual bundle information
            default_bundle = {
                'bundle_id': 'humble_bundle_default',
                'source_id': 'humble_bundle',
                'bundle_name': 'Humble Bundle Library',
                'bundle_type': 'mixed',
                'purchase_date': None,
                'amount_spent': 0,
                'currency': 'USD',
                'charity': None,
                'bundle_url': 'https://www.humblebundle.com/home/library',
                'description': 'Default bundle for Humble Bundle library products'
            }
            bundles.append(default_bundle)
            
        except Exception as e:
            print(f"         ⚠️  Error extracting bundles: {e}")
        
        return bundles
    
    def _sync_to_database(self, products_data: List[Dict[str, Any]], bundles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync extracted data to the database."""
        start_time = time.time()
        products_synced = 0
        products_failed = 0
        bundles_synced = 0
        bundles_failed = 0
        errors = []
        
        try:
            # Sync bundles
            for bundle in bundles_data:
                try:
                    self.db.upsert_bundle(bundle)
                    bundles_synced += 1
                except Exception as e:
                    bundles_failed += 1
                    errors.append(f"Bundle sync error: {e}")
            
            # Sync products
            for product in products_data:
                try:
                    self.db.upsert_product(product)
                    
                    # Link to default bundle
                    self.db.link_bundle_product('humble_bundle_default', product['product_id'])
                    
                    products_synced += 1
                except Exception as e:
                    products_failed += 1
                    errors.append(f"Product sync error: {e}")
            
            # Determine sync status
            if products_failed == 0 and bundles_failed == 0:
                status = 'success'
            elif products_synced > 0:
                status = 'partial'
            else:
                status = 'failed'
            
        except Exception as e:
            status = 'failed'
            errors.append(f"General sync error: {e}")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return {
            'status': status,
            'products_synced': products_synced,
            'products_failed': products_failed,
            'bundles_synced': bundles_synced,
            'bundles_failed': bundles_failed,
            'error_log': '\n'.join(errors) if errors else None,
            'duration_ms': duration_ms
        }

def test_working_metadata_sync():
    """Test the working metadata sync system."""
    print("🧪 Testing Working Metadata Sync...")
    
    with HumbleBundleAuthSelenium(headless=True) as auth:
        try:
            print("🔄 Authenticating...")
            if not auth.login():
                print("❌ Authentication failed")
                return
            
            print("✅ Authentication successful!")
            
            # Initialize database
            with AssetInventoryDatabase() as db:
                # Test working metadata sync
                sync = WorkingMetadataSync(auth, db)
                
                print("📚 Starting metadata sync...")
                results = sync.sync_humble_bundle_metadata()
                
                print(f"\n📊 Metadata Sync Results:")
                print(f"   Status: {results['status']}")
                print(f"   Products synced: {results['products_synced']}")
                print(f"   Products failed: {results['products_failed']}")
                print(f"   Bundles synced: {results['bundles_synced']}")
                print(f"   Bundles failed: {results['bundles_failed']}")
                print(f"   Duration: {results['duration_ms']}ms")
                
                if results.get('error_log'):
                    print(f"\n⚠️  Errors encountered:")
                    print(results['error_log'])
                
                # Test search functionality
                print(f"\n🔍 Testing search functionality...")
                search_results = db.search_assets("python", filters={'category': 'ebook'})
                print(f"   Found {len(search_results)} Python-related ebooks")
                
                # Get library summary
                print(f"\n📊 Library Summary:")
                summary = db.get_library_summary()
                for item in summary[:5]:  # Show first 5
                    print(f"   {item['category']} ({item['subcategory']}): {item['product_count']} products from {item['source_name']}")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_working_metadata_sync() 