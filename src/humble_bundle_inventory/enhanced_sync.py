#!/usr/bin/env python3
"""
Enhanced metadata synchronization for Humble Bundle.
Based on HAR analysis insights, handles gamekey structure and enhanced metadata extraction.
"""

import sys
import time
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

from .auth_selenium import HumbleBundleAuthSelenium
from .database import AssetInventoryDatabase
from .config import settings

class EnhancedHumbleBundleSync:
    """
    Enhanced sync system based on HAR analysis insights.
    Handles gamekey-based API structure and enhanced metadata extraction.
    """
    
    def __init__(self, auth: HumbleBundleAuthSelenium, db: AssetInventoryDatabase):
        self.auth = auth
        self.db = db
        self.driver = None
        self.user_data = None
        self.api_data = {}
        
    def sync_humble_bundle_enhanced(self) -> Dict[str, Any]:
        """Enhanced sync extracting products directly from the library page."""
        if not self.driver:
            self.driver = self.auth.get_authenticated_session()
        
        print("🚀 Starting Enhanced Humble Bundle sync...")
        
        # Update Humble Bundle source
        self.db.upsert_asset_source({
            'source_id': 'humble_bundle',
            'source_name': 'Humble Bundle',
            'source_type': 'platform', 
            'source_url': 'https://www.humblebundle.com',
            'authentication_method': 'session_cookies',
            'sync_status': 'active',
            'last_sync_timestamp': datetime.now()
        })
        
        # Navigate to library and extract comprehensive data
        print("   🌐 Navigating to library page...")
        self.driver.get('https://www.humblebundle.com/home/library')
        time.sleep(5)
        
        # Wait for page to fully load and trigger any dynamic content
        print("   ⏳ Waiting for dynamic content to load...")
        self._wait_for_library_content()
        
        # Extract real products from the library page
        print("   🔍 Extracting products from library page...")
        page_products = self._extract_products_from_page()
        
        if page_products:
            print(f"      📦 Found {len(page_products)} products from page")
        else:
            print("      ⚠️  No products found on page")
            return {
                'status': 'failed',
                'products_synced': 0,
                'products_failed': 0,
                'bundles_synced': 0,
                'bundles_failed': 0,
                'subscription_items': 0,
                'downloadable_products': 0,
                'duration_ms': 0,
                'error_log': 'No products found on page'
            }
        
        # Process the page products directly
        print("   🔄 Processing page products...")
        processed_data = self._process_page_products(page_products)
        
        # Skip enhanced categorization for now - products are already categorized
        print("   🎯 Products already categorized during extraction...")
        enhanced_data = processed_data
        
        # Sync to database
        print("   💾 Syncing to database...")
        sync_results = self._sync_enhanced_data(enhanced_data)
        
        # Record detailed sync metadata
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
        
        print(f"✅ Enhanced sync complete:")
        print(f"   Products synced: {sync_results['products_synced']}")
        print(f"   Bundles synced: {sync_results['bundles_synced']}")
        print(f"   Subscription content: {sync_results.get('subscription_items', 0)}")
        print(f"   Downloadable products: {sync_results.get('downloadable_products', 0)}")
        print(f"   Duration: {sync_results['duration_ms']}ms")
        
        return sync_results
    
    def _wait_for_library_content(self):
        """Wait for library content to load and trigger dynamic loading."""
        try:
            # Wait for initial elements to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            
            # Try to click elements that might trigger API calls
            try:
                # Look for library navigation or load more buttons
                load_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button[data-action], .load-more, .show-more, [data-toggle]")
                for button in load_buttons[:3]:  # Limit to first 3
                    try:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(2)
                    except:
                        continue
            except:
                pass
                
        except Exception as e:
            print(f"      ⚠️  Warning during content loading: {e}")
    
    def _trigger_api_calls_and_extract(self) -> Dict[str, Any]:
        """Attempt to trigger API calls and extract data."""
        try:
            # Force refresh with longer wait
            print("      🔄 Refreshing page to trigger API calls...")
            self.driver.refresh()
            time.sleep(10)
            
            # Try to trigger network activity
            trigger_script = """
            // Try to trigger data loading
            if (typeof fetchLibraryData === 'function') {
                fetchLibraryData();
            }
            
            // Try to access any data loading functions
            if (window.models && window.models.triggerLoad) {
                window.models.triggerLoad();
            }
            
            // Dispatch events that might trigger data loading
            window.dispatchEvent(new Event('load'));
            window.dispatchEvent(new Event('DOMContentLoaded'));
            
            return 'triggered';
            """
            
            self.driver.execute_script(trigger_script)
            time.sleep(5)
            
            # Re-extract data
            return self._extract_api_data()
            
        except Exception as e:
            print(f"      ⚠️  Error triggering API calls: {e}")
            return {'orders': {}, 'gamekeys': []}
    
    def _load_har_analysis_data(self) -> Dict[str, Any]:
        """Load data from our HAR analysis for demonstration."""
        try:
            # Load the enhanced extraction data we captured
            har_file = Path('/Users/tenguns/dev/humblebundle/enhanced_extraction_20250815_104032.json')
            if har_file.exists():
                with open(har_file) as f:
                    har_data = json.load(f)
                
                # Extract the raw orders data
                raw_orders = har_data.get('raw_data', {}).get('orders', [])
                if raw_orders and len(raw_orders) > 0:
                    # Convert to our expected format
                    orders = {}
                    gamekeys = []
                    
                    for order_item in raw_orders:
                        # Each order item is a dict with gamekey as key
                        for gamekey, order_data in order_item.items():
                            if gamekey not in ['zdConsentUpdate', 'SearchAction'] and order_data is not None:
                                orders[gamekey] = order_data
                                gamekeys.append(gamekey)
                    
                    print(f"      📊 Loaded {len(orders)} orders from HAR analysis")
                    return {
                        'orders': orders,
                        'gamekeys': gamekeys,
                        'source': 'har_analysis'
                    }
            
            print("      ⚠️  HAR analysis file not found, creating mock data...")
            return self._create_mock_data()
            
        except Exception as e:
            print(f"      ⚠️  Error loading HAR data: {e}")
            return self._create_mock_data()
    
    def _extract_products_from_page(self) -> List[Dict[str, Any]]:
        """Extract products directly from the library page."""
        products = []
        
        try:
            # Wait for content to load
            time.sleep(5)
            
            print("         🔍 Analyzing page structure for products...")
            
            # First, try to find the main content area
            main_content = None
            content_selectors = [
                "main", 
                ".main-content", 
                ".content", 
                ".library-content",
                ".download-list",
                ".hb-download-list",
                "[class*='library']",
                "[class*='download']",
                "body"
            ]
            
            for selector in content_selectors:
                try:
                    main_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"         ✅ Found main content with selector: {selector}")
                    break
                except:
                    continue
            
            if not main_content:
                print("         ❌ No main content found")
                return products
            
            # Get page source for analysis
            page_source = self.driver.page_source
            print(f"         📄 Page source length: {len(page_source)} characters")
            
            # Look for product patterns in multiple ways
            product_names = set()  # Use set to avoid duplicates
            
            # Method 1: Look for product titles in HTML
            html_products = self._extract_products_from_html(page_source)
            product_names.update(html_products)
            
            # Method 2: Look for text patterns
            text_products = self._extract_products_from_text(main_content.text)
            product_names.update(text_products)
            
            # Method 3: Look for specific Humble Bundle patterns
            bundle_products = self._extract_bundle_products(page_source)
            product_names.update(bundle_products)
            
            print(f"         📦 Found {len(product_names)} unique potential products")
            
            # Process each product name
            for i, product_name in enumerate(product_names):
                try:
                    if i % 50 == 0:
                        print(f"         🔍 Processing product {i+1}: {product_name[:50]}...")
                    
                    # Create product data directly from name
                    product_data = self._create_product_from_name(product_name)
                    if product_data:
                        products.append(product_data)
                        
                except Exception as e:
                    print(f"            ⚠️  Error processing product {i+1}: {e}")
                    continue
            
            print(f"         ✅ Successfully processed {len(products)} products")
            
        except Exception as e:
            print(f"         ❌ Error extracting products from page: {e}")
            import traceback
            traceback.print_exc()
        
        return products
    
    def _extract_products_from_html(self, page_source: str) -> List[str]:
        """Extract product names from HTML source."""
        products = []
        
        try:
            import re
            
            # Look for various HTML patterns that might contain product names
            patterns = [
                # Headings that look like product names
                r'<h[1-6][^>]*>([^<]{10,200})</h[1-6]>',
                # Divs with title-like classes
                r'<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]{10,200})</div>',
                # Links that might be product links
                r'<a[^>]*href="[^"]*download[^"]*"[^>]*>([^<]{10,200})</a>',
                # Spans with name-like classes
                r'<span[^>]*class="[^"]*name[^"]*"[^>]*>([^<]{10,200})</span>',
                # Any text that looks like a product name
                r'<[^>]*>([A-Z][^<]{15,150})</[^>]*>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    match = match.strip()
                    if self._is_valid_product_name(match):
                        products.append(match)
            
        except Exception as e:
            print(f"            ⚠️  Error extracting from HTML: {e}")
        
        return products
    
    def _extract_products_from_text(self, page_text: str) -> List[str]:
        """Extract product names from page text."""
        products = []
        
        try:
            # Split text into lines and look for product-like patterns
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and navigation text
                if not line or len(line) < 10:
                    continue
                
                # Skip common navigation and header text
                if any(skip in line.lower() for skip in [
                    'humble bundle', 'library', 'welcome', 'home', 'account', 'settings',
                    'logout', 'login', 'search', 'filter', 'sort', 'page', 'of',
                    'previous', 'next', 'first', 'last', 'loading', 'please wait',
                    'copyright', 'privacy', 'terms', 'help', 'support'
                ]):
                    continue
                
                # Look for product-like patterns
                if any(pattern in line for pattern in [
                    '% Off', 'Discount', 'Bundle', 'Collection', 'Edition',
                    'Game', 'Software', 'Book', 'Comic', 'Audio', 'Music',
                    'Download', 'Install', 'Play', 'Read', 'Listen'
                ]):
                    if self._is_valid_product_name(line):
                        products.append(line)
                # Also include lines that look like product names
                elif (len(line) >= 15 and len(line) <= 200 and 
                      not line.isupper() and 
                      line[0].isalnum() and
                      self._is_valid_product_name(line)):
                    products.append(line)
            
        except Exception as e:
            print(f"            ⚠️  Error extracting from text: {e}")
        
        return products
    
    def _extract_bundle_products(self, page_source: str) -> List[str]:
        """Extract products specific to Humble Bundle patterns."""
        products = []
        
        try:
            import re
            
            # Look for Humble Bundle specific patterns
            patterns = [
                # Bundle names
                r'<[^>]*>([A-Z][a-z\s]+Bundle[^<]{0,50})</[^>]*>',
                # Choice items
                r'<[^>]*>([A-Z][^<]*Choice[^<]{0,50})</[^>]*>',
                # Discount patterns
                r'<[^>]*>(\d+%\s*Off[^<]{0,100})</[^>]*>',
                # Game names (common in Humble Bundle)
                r'<[^>]*>([A-Z][a-z\s]+(?:Game|Simulator|Adventure|Strategy)[^<]{0,50})</[^>]*>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    match = match.strip()
                    if self._is_valid_product_name(match):
                        products.append(match)
            
        except Exception as e:
            print(f"            ⚠️  Error extracting bundle products: {e}")
        
        return products
    
    def _is_valid_product_name(self, name: str) -> bool:
        """Check if a string looks like a valid product name."""
        if not name or len(name) < 10 or len(name) > 200:
            return False
        
        # Skip if it's mostly special characters or numbers
        if len([c for c in name if c.isalnum() or c.isspace()]) < len(name) * 0.7:
            return False
        
        # Skip if it's all caps (likely navigation)
        if name.isupper():
            return False
        
        # Skip if it contains common navigation text
        skip_words = [
            'humble', 'bundle', 'library', 'welcome', 'home', 'account', 
            'settings', 'logout', 'login', 'search', 'filter', 'sort',
            'page', 'of', 'previous', 'next', 'first', 'last', 'loading',
            'please wait', 'copyright', 'privacy', 'terms', 'help', 'support',
            'menu', 'navigation', 'breadcrumb', 'footer', 'header'
        ]
        
        name_lower = name.lower()
        if any(word in name_lower for word in skip_words):
            return False
        
        # Must start with alphanumeric
        if not name[0].isalnum():
            return False
        
        return True
    
    # This method is now replaced by _extract_products_from_text
    
    def _create_product_from_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Create product data directly from product name."""
        try:
            # Generate product ID from name
            product_id = hashlib.md5(product_name.encode()).hexdigest()
            
            # Determine product category and subcategory
            category, subcategory = self._categorize_product_enhanced(product_name)
            
            product_data = {
                'product_id': product_id,
                'source_id': 'humble_bundle',
                'human_name': product_name,
                'machine_name': product_name.lower().replace(' ', '_').replace('-', '_'),
                'category': category,
                'subcategory': subcategory,
                'developer': None,
                'publisher': None,
                'url': None,
                'description': None,
                'tags': [],
                'rating': None,
                'rating_count': None,
                'retail_price': None,
                'currency': 'USD',
                'release_date': None,
                'language': 'en',
                'extraction_method': 'text_analysis'
            }
            
            return product_data
            
        except Exception as e:
            print(f"            ⚠️  Error creating product from name: {e}")
            return None
    
    # This method is now replaced by the new extraction methods
    
    def _extract_product_metadata_from_page(self, heading, product_name: str) -> Optional[Dict[str, Any]]:
        """Extract metadata for a specific product from the page."""
        try:
            # Generate product ID from name
            product_id = hashlib.md5(product_name.encode()).hexdigest()
            
            # Determine product category and subcategory
            category, subcategory = self._categorize_product_enhanced(product_name)
            
            # Extract additional metadata from the heading context
            parent = heading.find_element(By.XPATH, "..")
            additional_info = self._extract_additional_metadata_from_page(parent)
            
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
                'language': additional_info.get('language', 'en'),
                'extraction_method': 'page_analysis'
            }
            
            return product_data
            
        except Exception as e:
            print(f"            ⚠️  Error extracting product metadata: {e}")
            return None
    
    def _find_additional_products(self) -> List[Dict[str, Any]]:
        """Find additional products that might be in different containers."""
        additional_products = []
        
        try:
            # Look for other product containers
            product_selectors = [
                "[class*='product']",
                "[class*='item']", 
                "[class*='game']",
                "[class*='bundle']",
                ".product-item",
                ".game-item",
                ".bundle-item"
            ]
            
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:20]:  # Limit to first 20
                        try:
                            # Try to extract product name
                            name_elem = element.find_element(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, .title, .name")
                            if name_elem:
                                product_name = name_elem.text.strip()
                                if product_name and len(product_name) > 5:
                                    product_data = self._extract_product_metadata_from_page(name_elem, product_name)
                                    if product_data:
                                        additional_products.append(product_data)
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            print(f"         ⚠️  Error finding additional products: {e}")
        
        return additional_products
    
    def _extract_additional_metadata_from_page(self, parent_element) -> Dict[str, Any]:
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
                    metadata['rating'] = float(price_match.group(1))
            
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
    
    def _get_categorization_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get categorization rules configuration."""
        return {
            'game': {
                'keywords': [
                    'game', 'simulator', 'adventure', 'strategy', 'war', 'total war', 'rpg', 'role',
                    'shooter', 'fps', 'platformer', 'puzzle', 'racing', 'sports', 'fighting', 'stealth',
                    'survival horror', 'visual novel', 'point and click', 'tower defense', 'real-time',
                    'turn-based', 'roguelike', 'roguelite', 'metroidvania', 'souls-like', 'open world',
                    'sandbox', 'mmo', 'multiplayer', 'co-op', 'competitive', 'esports', 'arcade',
                    'retro', 'classic', 'remastered', 'definitive edition', 'gold edition', 'ultimate',
                    'complete', 'collection', 'bundle', 'pack', 'dlc', 'expansion', 'season pass',
                    # Additional game patterns
                    'cowboy', 'humans', 'snowman', 'tale', 'storm', 'spirits', 'worms', 'armageddon',
                    'brigade', 'express', 'df-9', 'hack', 'slash', 'bard', 'midnight', 'fight',
                    'demystified', 'jobseekers', 'jakarta', 'knits', 'cosplay', 'costuming',
                    # More game patterns
                    'amnesia', 'alien', 'anna', 'antichamber', 'aralon', 'resident evil', 'saints row',
                    'sid meier', 'civilization', 'railroads', 'star wars', 'force unleashed', 'jedi',
                    'sakura', 'agent', 'angels', 'beach', 'fantasy', 'spirit', 'samorost', 'savant',
                    'scourgebringer', 'shadow', 'blade', 'grounds', 'siegecraft', 'defender',
                    'rollerdrome', 'road redemption', 'relic rush', 'redemption', 'reliable'
                ],
                'exclude_keywords': [
                    'guide', 'manual', 'tutorial', 'book', 'bible', 'fundamentals', 'learning',
                    'introduction', 'primer', 'basics', 'essential', 'practical', 'hands-on',
                    'mastering', 'understanding', 'analysis', 'engineering', 'development'
                ],
                'subcategories': {
                    'rpg': ['rpg', 'role'],
                    'strategy': ['strategy', 'war', 'tower defense'],
                    'simulation': ['simulator', 'sim'],
                    'adventure': ['adventure', 'point and click'],
                    'shooter': ['shooter', 'fps'],
                    'platformer': ['platformer', 'metroidvania'],
                    'puzzle': ['puzzle'],
                    'racing': ['racing'],
                    'sports': ['sports'],
                    'fighting': ['fighting'],
                    'stealth': ['stealth'],
                    'survival_horror': ['survival horror'],
                    'visual_novel': ['visual novel']
                }
            },
            'ebook': {
                'keywords': [
                    'guide', 'manual', 'tutorial', 'book', 'tips', 'secrets', 'cookbook', 'handbook', 
                    'cooking', 'gardening', 'survival', 'bible', 'fundamentals', 'programming', 'coding',
                    'edition', '2nd', '3rd', '4th', '5th', 'definitive', 'complete', 'comprehensive',
                    'learning', 'learn', 'introduction', 'intro', 'primer', 'basics', 'essential',
                    'practical', 'hands-on', 'mastering', 'understanding', 'analysis', 'engineering',
                    'development', 'design', 'architecture', 'testing', 'security', 'penetration',
                    'automation', 'infrastructure', 'networking', 'linux', 'python', 'haskell', 'elixir',
                    'matlab', 'azure', 'kubernetes', 'ansible', 'cryptocurrency', 'multifactor',
                    'authentication', 'machine learning', 'deep learning', 'data science', 'statistics',
                    'mathematics', 'physics', 'chemistry', 'biology', 'psychology', 'sociology',
                    'economics', 'finance', 'marketing', 'management', 'leadership', 'communication',
                    'writing', 'journalism', 'photography', 'art', 'music', 'film', 'television',
                    'history', 'philosophy', 'religion', 'politics', 'law', 'medicine', 'health',
                    'fitness', 'nutrition', 'travel', 'geography', 'astronomy', 'geology', 'ecology',
                    # Additional patterns
                    'things every', 'ways to', 'minute', 'chaplain', 'practitioner',
                    'business intelligence', 'analytics', 'advancing', 'adversary', 'emulation',
                    'mitre', 'att&ck', 'att&amp;ck', 'content', 'tier', 'mastery',
                    # More ebook patterns
                    'anomaly detection', 'apache spark', 'arduino', 'scala', 'cookbook', 'edition',
                    'sewing', 'machine', 'magic', 'seven elements', 'seven languages', 'seven weeks',
                    'self-tracking', 'sentiment analysis', 'opinion mining', 'serious cryptography',
                    'reversible digital watermarking', 'theory and practice', 'field guide',
                    'passive reconnaissance', 'networked world', 'hybrid cloud', 'computer architects',
                    'dependable distributed systems', 'microservice architecture', 'online social networks',
                    'trust', 'seeking sre', 'devops', 'site reliability engineering'
                ],
                'subcategories': {
                    'cooking': ['cooking', 'recipe', 'food', 'culinary'],
                    'gardening': ['gardening', 'garden', 'plants', 'horticulture'],
                    'survival': ['survival', 'prepper', 'outdoor', 'wilderness'],
                    'programming': ['programming', 'coding', 'software', 'development', 'python', 'haskell', 'elixir', 'matlab', 'linux', 'azure', 'kubernetes', 'ansible'],
                    'business': ['business', 'finance', 'management', 'marketing', 'economics'],
                    'security': ['security', 'penetration', 'hacking', 'cybersecurity', 'authentication'],
                    'science': ['mathematics', 'statistics', 'physics', 'chemistry', 'biology'],
                    'social_sciences': ['psychology', 'sociology', 'philosophy', 'religion'],
                    'arts': ['art', 'music', 'film', 'photography', 'design'],
                    'humanities': ['history', 'geography', 'politics', 'law']
                }
            },
            'software': {
                'keywords': ['software', 'tool', 'utility', 'app', 'studio', 'pro', 'suite', 'editor'],
                'subcategories': {
                    'photo_editing': ['photo', 'image'],
                    'video_editing': ['video', 'movie'],
                    'audio_editing': ['audio', 'music'],
                    '3d_modeling': ['3d', 'modeling']
                }
            },
            'comic': {
                'keywords': ['comic', 'manga', 'graphic novel', 'volume'],
                'subcategories': {}
            },
            'audio': {
                'keywords': ['audio', 'music', 'podcast', 'soundtrack', 'ost'],
                'subcategories': {}
            },
            'bundle': {
                'keywords': ['bundle', 'pack', 'collection', 'edition'],
                'subcategories': {}
            },
            'subscription_content': {
                'keywords': ['% off', 'discount', 'coupon', 'choice', 'subscription'],
                'subcategories': {}
            }
        }
    
    def _determine_category(self, name_lower: str, rules: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Determine the main category based on rules."""
        for category, rule in rules.items():
            if category == 'subscription_content':
                # Special handling for subscription content
                if any(keyword in name_lower for keyword in rule['keywords']):
                    return category
            
            # Check if any keyword matches
            if any(keyword in name_lower for keyword in rule['keywords']):
                # Check exclusion keywords for certain categories
                if 'exclude_keywords' in rule:
                    if any(exclude in name_lower for exclude in rule['exclude_keywords']):
                        continue
                return category
        
        return None
    
    def _determine_subcategory(self, name_lower: str, category: str, rules: Dict[str, Dict[str, Any]]) -> str:
        """Determine the subcategory based on category rules."""
        if category not in rules:
            return 'general'
        
        rule = rules[category]
        if 'subcategories' not in rule or not rule['subcategories']:
            return 'general'
        
        for subcategory, keywords in rule['subcategories'].items():
            if any(keyword in name_lower for keyword in keywords):
                return subcategory
        
        return 'general'
    
    def _categorize_product_enhanced(self, product_name: str) -> tuple:
        """Enhanced categorization with confidence scoring using configuration-driven rules."""
        name_lower = product_name.lower()
        rules = self._get_categorization_rules()
        
        # Determine main category
        category = self._determine_category(name_lower, rules)
        
        if category is None:
            category = 'unknown'
        
        # Determine subcategory
        subcategory = self._determine_subcategory(name_lower, category, rules)
        
        return category, subcategory
    
    def _create_mock_data(self) -> Dict[str, Any]:
        """Create mock data for testing the sync system."""
        mock_gamekey = "6Y8wnhvdzNyNE5Cn"
        mock_orders = {
            mock_gamekey: {
                "amount_spent": 0.0,
                "product": {
                    "category": "subscriptioncontent",
                    "machine_name": "july_2025_choice",
                    "human_name": "July 2025 Humble Choice",
                    "is_subs_v3_product": True
                },
                "gamekey": mock_gamekey,
                "created": "2025-07-30T02:36:36.233634",
                "subproducts": [
                    {
                        "machine_name": "example_game_discount_coupon",
                        "url": "https://www.humblebundle.com/home/coupons", 
                        "downloads": [],
                        "payee": {
                            "human_name": "Humble Bundle",
                            "machine_name": "humblebundle"
                        },
                        "human_name": "75% Off - Example Game",
                        "custom_download_page_box_html": "<p>Your discount coupon is ready!</p>",
                        "icon": "https://example.com/icon.png"
                    }
                ],
                "currency": "USD",
                "total": 14.99
            }
        }
        
        print(f"      🎭 Created mock data with 1 order for testing")
        return {
            'orders': mock_orders,
            'gamekeys': [mock_gamekey],
            'source': 'mock_data'
        }
    
    def _extract_user_data(self) -> Dict[str, Any]:
        """Extract user data from window.models using HAR insights."""
        user_extraction_script = """
        var userData = {};
        
        // Extract from discovered user_json structure
        if (window.models && window.models.user_json) {
            userData = window.models.user_json;
        }
        
        // Extract subscription state
        if (window.models && window.models.userSubscriptionState) {
            userData.subscription_state = window.models.userSubscriptionState;
        }
        
        // Extract request data for additional context
        if (window.models && window.models.request) {
            userData.request_context = window.models.request;
        }
        
        return userData;
        """
        
        try:
            user_data = self.driver.execute_script(user_extraction_script)
            self.user_data = user_data
            print(f"      📱 Extracted user data with {len(user_data)} fields")
            return user_data
        except Exception as e:
            print(f"      ⚠️  Error extracting user data: {e}")
            return {}
    
    def _extract_api_data(self) -> Dict[str, Any]:
        """Extract API data using discovered endpoints and structure."""
        api_extraction_script = """
        var apiData = {
            orders: {},
            gamekeys: [],
            all_models: {},
            debug_info: {}
        };
        
        // Debug: capture all window.models data for analysis
        if (window.models) {
            apiData.all_models = window.models;
            apiData.debug_info.models_keys = Object.keys(window.models);
            apiData.debug_info.models_count = Object.keys(window.models).length;
            
            // Check for gamekeys array
            if (window.models.gamekeys) {
                apiData.gamekeys = window.models.gamekeys;
            }
            
            // Check for orders data
            if (window.models.orders) {
                apiData.orders = window.models.orders;
            }
            
            // Look for order data in other keys (HAR showed gamekeys as top-level keys)
            Object.keys(window.models).forEach(function(key) {
                var value = window.models[key];
                
                // Pattern: gamekey is 12-16 character alphanumeric string
                if (/^[A-Za-z0-9]{12,16}$/.test(key) && typeof value === 'object' && value !== null) {
                    apiData.orders[key] = value;
                    if (apiData.gamekeys.indexOf(key) === -1) {
                        apiData.gamekeys.push(key);
                    }
                }
                
                // Also check for objects that might contain order data
                if (typeof value === 'object' && value !== null) {
                    // Check if this object has gamekey-like structure
                    if (value.gamekey || value.subproducts || value.product) {
                        apiData.orders[key] = value;
                        if (value.gamekey && apiData.gamekeys.indexOf(value.gamekey) === -1) {
                            apiData.gamekeys.push(value.gamekey);
                        }
                    }
                }
            });
            
            // Additional extraction from known HAR patterns
            if (window.models.user_json) {
                apiData.user_data = window.models.user_json;
            }
        }
        
        return apiData;
        """
        
        try:
            api_data = self.driver.execute_script(api_extraction_script)
            print(f"      🔑 Found {len(api_data.get('gamekeys', []))} gamekeys")
            print(f"      📦 Found {len(api_data.get('orders', {}))} orders")
            print(f"      🔍 Total models keys: {api_data.get('debug_info', {}).get('models_count', 0)}")
            
            # Debug: Show some model keys for troubleshooting
            models_keys = api_data.get('debug_info', {}).get('models_keys', [])
            if models_keys:
                print(f"      📋 Sample model keys: {models_keys[:10]}")
            
            return api_data
        except Exception as e:
            print(f"      ⚠️  Error extracting API data: {e}")
            return {'orders': {}, 'gamekeys': []}
    
    def _process_page_products(self, page_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process page products directly into the expected format."""
        processed = {
            'bundles': [],
            'products': page_products,  # Use page products directly
            'downloads': [],
            'subscription_content': [],
            'downloadable_products': []
        }
        
        # Categorize products based on their category field
        for product in page_products:
            category = product.get('category', 'unknown')
            if category == 'subscription_content':
                processed['subscription_content'].append(product)
            else:
                processed['downloadable_products'].append(product)
        
        print(f"      📊 Processed {len(processed['products'])} products from page")
        print(f"      🎫 Subscription content: {len(processed['subscription_content'])}")
        print(f"      📥 Downloadable products: {len(processed['downloadable_products'])}")
        
        return processed
    
    def _process_api_orders(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process orders using discovered API structure."""
        processed = {
            'bundles': [],
            'products': [],
            'downloads': [],
            'subscription_content': [],
            'downloadable_products': []
        }
        
        # Process API orders first
        orders = api_data.get('orders', {})
        
        for gamekey, order_data in orders.items():
            if not isinstance(order_data, dict):
                continue
                
            try:
                # Process bundle/order information
                bundle_data = self._process_order_to_bundle(gamekey, order_data)
                if bundle_data:
                    processed['bundles'].append(bundle_data)
                
                # Process subproducts
                subproducts = order_data.get('subproducts', [])
                for subproduct in subproducts:
                    product_data = self._process_subproduct(gamekey, subproduct, order_data)
                    if product_data:
                        # Categorize as subscription content or downloadable product
                        if self._is_subscription_content(subproduct):
                            processed['subscription_content'].append(product_data)
                        else:
                            processed['downloadable_products'].append(product_data)
                            
                        processed['products'].append(product_data)
                        
                        # Process downloads
                        downloads = self._process_subproduct_downloads(product_data, subproduct)
                        processed['downloads'].extend(downloads)
                        
            except Exception as e:
                print(f"         ⚠️  Error processing order {gamekey}: {e}")
                continue
        
        # Process page products (extracted directly from library page)
        page_products = api_data.get('page_products', [])
        print(f"      📄 Found {len(page_products)} page products to process")
        if page_products:
            print(f"      📄 Processing {len(page_products)} products from page analysis...")
            
            for product_data in page_products:
                try:
                    # Add to products list
                    processed['products'].append(product_data)
                    
                    # Categorize based on extraction method
                    if product_data.get('extraction_method') == 'page_analysis':
                        if product_data.get('category') == 'subscription_content':
                            processed['subscription_content'].append(product_data)
                        else:
                            processed['downloadable_products'].append(product_data)
                    
                except Exception as e:
                    print(f"         ⚠️  Error processing page product: {e}")
                    continue
        
        print(f"      📊 Processed {len(processed['bundles'])} bundles, {len(processed['products'])} products")
        print(f"      🎫 Subscription content: {len(processed['subscription_content'])}")
        print(f"      📥 Downloadable products: {len(processed['downloadable_products'])}")
        
        return processed
    
    def _process_order_to_bundle(self, gamekey: str, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert order data to bundle format."""
        try:
            product_info = order_data.get('product', {})
            
            bundle_data = {
                'bundle_id': gamekey,
                'source_id': 'humble_bundle',
                'bundle_name': product_info.get('human_name', f'Order {gamekey}'),
                'bundle_type': self._determine_bundle_type(product_info),
                'purchase_date': self._parse_date(order_data.get('created')),
                'amount_spent': float(order_data.get('amount_spent', 0)),
                'currency': order_data.get('currency', 'USD'),
                'charity': order_data.get('charity'),
                'bundle_url': f"https://www.humblebundle.com/downloads?key={gamekey}",
                'description': product_info.get('post_purchase_text', '')
            }
            
            return bundle_data
        except Exception as e:
            print(f"            ⚠️  Error creating bundle from order: {e}")
            return None
    
    def _process_subproduct(self, gamekey: str, subproduct: Dict[str, Any], order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process subproduct into product format."""
        try:
            machine_name = subproduct.get('machine_name', '')
            human_name = subproduct.get('human_name', '')

            if not human_name:
                return None

            product_id = hashlib.md5(f"{gamekey}_{machine_name}".encode()).hexdigest()
            
            category = self._categorize_subproduct(subproduct)

            product_data = {
                'product_id': product_id,
                'source_id': 'humble_bundle',
                'gamekey': gamekey,
                'human_name': human_name,
                'machine_name': machine_name,
                'category': category,
                'subcategory': self._determine_subcategory(human_name.lower(), category, self._get_categorization_rules()),
                'developer': subproduct.get('payee', {}).get('human_name'),
                'publisher': subproduct.get('payee', {}).get('human_name'),
                'url': subproduct.get('url'),
                'description': subproduct.get('custom_download_page_box_html', ''),
                'tags': self._extract_tags_from_subproduct(subproduct),
                'rating': None,
                'rating_count': None,
                'retail_price': None,
                'currency': order_data.get('currency', 'USD'),
                'release_date': None,
                'language': 'en',
                'icon_url': subproduct.get('icon'),
                'library_family_name': subproduct.get('library_family_name', ''),
                'is_subscription_content': self._is_subscription_content(subproduct)
            }

            return product_data

        except Exception as e:
            print(f"            ⚠️  Error processing subproduct: {e}")
            return None
    
    def _process_subproduct_downloads(self, product_data: Dict[str, Any], subproduct: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process downloads from subproduct."""
        downloads = []
        
        for download in subproduct.get('downloads', []):
            try:
                download_id = hashlib.md5(f"{product_data['product_id']}_{download.get('machine_name', '')}".encode()).hexdigest()
                
                download_data = {
                    'download_id': download_id,
                    'product_id': product_data['product_id'],
                    'source_id': 'humble_bundle',
                    'platform': download.get('platform', 'universal'),
                    'architecture': download.get('architecture'),
                    'download_type': download.get('download_type'),
                    'file_name': download.get('file_name'),
                    'file_size': download.get('file_size', 0),
                    'file_size_display': download.get('file_size_display'),
                    'download_url': download.get('download_url'),
                    'local_file_path': None,
                    'md5_hash': download.get('md5'),
                    'sha1_hash': download.get('sha1'),
                    'download_status': 'available'
                }
                
                downloads.append(download_data)
            except Exception as e:
                print(f"               ⚠️  Error processing download: {e}")
                continue
        
        return downloads
    
    def _apply_enhanced_categorization(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply enhanced categorization with confidence scoring."""
        enhanced = processed_data.copy()
        
        for product in enhanced['products']:
            try:
                # Apply enhanced categorization with confidence scoring
                category_result = self._categorize_with_confidence(product)
                
                product.update({
                    'category': category_result['category'],
                    'subcategory': category_result['subcategory'],
                    'categorization_confidence': category_result['confidence'],
                    'categorization_method': category_result['method'],
                    'enhancement_notes': category_result.get('notes', [])
                })
                
                # Apply metadata enrichment
                enriched_metadata = self._enrich_metadata(product)
                product.update(enriched_metadata)
                
            except Exception as e:
                print(f"            ⚠️  Error in enhanced categorization: {e}")
                continue
        
        return enhanced
    
    def _categorize_with_confidence(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced categorization with confidence scoring."""
        name = product.get('human_name', '').lower()
        machine_name = product.get('machine_name', '').lower()
        description = product.get('description', '').lower()
        
        # Initialize category scores
        category_scores = {
            'ebook': 0.0,
            'game': 0.0,
            'software': 0.0,
            'comic': 0.0,
            'audio': 0.0,
            'video': 0.0,
            'unknown': 0.0
        }
        
        # Score based on name patterns
        if any(word in name for word in ['game', 'simulator', 'adventure', 'rpg', 'strategy']):
            category_scores['game'] += 2.0
        if any(word in name for word in ['book', 'guide', 'manual', 'tutorial', 'reference']):
            category_scores['ebook'] += 2.0
        if any(word in name for word in ['software', 'tool', 'application', 'editor']):
            category_scores['software'] += 2.0
        if any(word in name for word in ['comic', 'graphic novel', 'manga']):
            category_scores['comic'] += 2.0
        if any(word in name for word in ['audio', 'music', 'soundtrack', 'podcast']):
            category_scores['audio'] += 2.0
        if any(word in name for word in ['video', 'movie', 'film', 'tutorial']):
            category_scores['video'] += 2.0
        
        # Score based on machine name patterns
        if any(word in machine_name for word in ['game', 'sim', 'rpg', 'strategy']):
            category_scores['game'] += 1.5
        if any(word in machine_name for word in ['book', 'guide', 'manual']):
            category_scores['ebook'] += 1.5
        if any(word in machine_name for word in ['software', 'tool', 'app']):
            category_scores['software'] += 1.5
        
        # Score based on description patterns
        if any(word in description for word in ['game', 'play', 'level', 'quest']):
            category_scores['game'] += 1.0
        if any(word in description for word in ['book', 'read', 'learn', 'study']):
            category_scores['ebook'] += 1.0
        if any(word in description for word in ['software', 'tool', 'use', 'create']):
            category_scores['software'] += 1.0
        
        # Determine best category
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category] / 4.0  # Normalize to 0-1 scale
        
        # Determine subcategory
        subcategory = self._determine_subcategory(name, best_category, self._get_categorization_rules())
        
        # Determine categorization method
        method = 'enhanced_pattern_matching'
        if confidence < 0.5:
            method = 'fallback_categorization'
        
        return {
            'category': best_category,
            'subcategory': subcategory,
            'confidence': confidence,
            'method': method,
            'scores': category_scores
        }
    
    def _enrich_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich product metadata with additional information."""
        enriched = {}
        
        # Extract developer patterns
        developer = product.get('developer', '')
        if developer and developer != 'Humble Bundle':
            enriched['verified_developer'] = developer
        
        # Extract discount information from description
        description = product.get('description', '')
        discount_match = re.search(r'(\d+)%\s*[Oo]ff', description)
        if discount_match:
            enriched['discount_percentage'] = int(discount_match.group(1))
        
        # Extract URL domain for additional context
        url = product.get('url', '')
        if url:
            enriched['url_domain'] = url.split('/')[2] if '/' in url else url
        
        return enriched
    
    def _sync_enhanced_data(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync enhanced data to database."""
        start_time = time.time()
        results = {
            'products_synced': 0,
            'products_failed': 0,
            'bundles_synced': 0,
            'bundles_failed': 0,
            'subscription_items': 0,
            'downloadable_products': 0,
            'errors': []
        }
        
        try:
            # Sync bundles
            for bundle in enhanced_data.get('bundles', []):
                try:
                    self.db.upsert_bundle(bundle)
                    results['bundles_synced'] += 1
                except Exception as e:
                    results['bundles_failed'] += 1
                    results['errors'].append(f"Bundle sync error: {e}")
            
            # Sync products
            for product in enhanced_data.get('products', []):
                try:
                    self.db.upsert_product(product)
                    
                    # Link to bundle if gamekey exists
                    gamekey = product.get('gamekey')
                    if gamekey:
                        self.db.link_bundle_product(gamekey, product['product_id'])
                    
                    # Count subscription vs downloadable based on category
                    category = product.get('category', '')
                    if category == 'subscription_content':
                        results['subscription_items'] += 1
                    else:
                        results['downloadable_products'] += 1
                    
                    results['products_synced'] += 1
                except Exception as e:
                    results['products_failed'] += 1
                    results['errors'].append(f"Product sync error: {e}")
            
            # Sync downloads
            for download in enhanced_data.get('downloads', []):
                try:
                    self.db.upsert_download(download)
                except Exception as e:
                    results['errors'].append(f"Download sync error: {e}")
            
            # Determine overall status
            if results['products_failed'] == 0 and results['bundles_failed'] == 0:
                status = 'success'
            elif results['products_synced'] > 0:
                status = 'partial'
            else:
                status = 'failed'
            
            results['status'] = status
            
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"General sync error: {e}")
        
        results['duration_ms'] = int((time.time() - start_time) * 1000)
        results['error_log'] = '\n'.join(results['errors']) if results['errors'] else None
        
        return results
    
    # Helper methods
    def _determine_bundle_type(self, product_info: Dict[str, Any]) -> str:
        """Determine bundle type from product info."""
        category = product_info.get('category', '').lower()
        
        if 'subscription' in category:
            return 'subscription'
        elif 'game' in category:
            return 'games'
        elif 'book' in category:
            return 'books'
        elif 'software' in category:
            return 'software'
        else:
            return 'mixed'
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _categorize_subproduct(self, subproduct: Dict[str, Any]) -> str:
        """Enhanced subproduct categorization."""
        machine_name = subproduct.get('machine_name', '').lower()
        human_name = subproduct.get('human_name', '').lower()
        
        if 'coupon' in machine_name or 'choice' in machine_name:
            return 'subscription_content'
        elif any(word in human_name for word in ['game', 'simulator', 'adventure']):
            return 'game'
        elif any(word in human_name for word in ['guide', 'manual', 'book']):
            return 'ebook'
        else:
            return 'unknown'
    
    def _extract_tags_from_subproduct(self, subproduct: Dict[str, Any]) -> List[str]:
        """Extract tags from subproduct."""
        tags = []
        machine_name = subproduct.get('machine_name', '').lower()
        
        if 'coupon' in machine_name:
            tags.append('coupon')
        if 'choice' in machine_name:
            tags.append('humble_choice')
        if 'dlc' in machine_name:
            tags.append('dlc')
        
        return tags
    
    def _is_subscription_content(self, subproduct: Dict[str, Any]) -> bool:
        """Check if subproduct is subscription content (coupon, etc)."""
        machine_name = subproduct.get('machine_name', '').lower()
        human_name = subproduct.get('human_name', '').lower()
        url = subproduct.get('url', '').lower()
        
        return (
            'coupon' in machine_name or
            'choice' in machine_name or
            'coupons' in url or
            '% off' in human_name
        )

def test_enhanced_sync():
    """Test the enhanced sync system."""
    print("🧪 Testing Enhanced Humble Bundle Sync...")
    
    with HumbleBundleAuthSelenium(headless=True) as auth:
        try:
            print("🔄 Authenticating...")
            if not auth.login():
                print("❌ Authentication failed")
                return
            
            print("✅ Authentication successful!")
            
            # Initialize database
            with AssetInventoryDatabase() as db:
                # Test enhanced sync
                sync = EnhancedHumbleBundleSync(auth, db)
                
                print("🚀 Starting enhanced sync...")
                results = sync.sync_humble_bundle_enhanced()
                
                print(f"\n📊 Enhanced Sync Results:")
                print(f"   Status: {results['status']}")
                print(f"   Products synced: {results['products_synced']}")
                print(f"   Products failed: {results['products_failed']}")
                print(f"   Bundles synced: {results['bundles_synced']}")
                print(f"   Bundles failed: {results['bundles_failed']}")
                print(f"   Subscription items: {results.get('subscription_items', 0)}")
                print(f"   Downloadable products: {results.get('downloadable_products', 0)}")
                print(f"   Duration: {results['duration_ms']}ms")
                
                if results.get('error_log'):
                    print(f"\n⚠️  Errors encountered:")
                    print(results['error_log'])
                
                # Show database summary
                print(f"\n📊 Database Summary:")
                summary = db.get_library_summary()
                for item in summary[:10]:
                    print(f"   {item['category']} ({item['subcategory']}): {item['product_count']} products")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_sync()