#!/usr/bin/env python3
"""
Selenium-based authentication for Humble Bundle.
Handles JavaScript-based login and MFA challenges.
"""

import time
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from .config import settings
import os

class HumbleBundleAuthSelenium:
    """Handles authentication and session management for Humble Bundle using Selenium."""
    
    def __init__(self, headless: bool = True):
        """Initialize the authentication handler"""
        self.headless = headless
        self.driver = None
        self._session_dir = Path('.session_cache')
        
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome driver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            # Use truly headless mode for better stability and input handling
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            print(f"🔒 Setting up headless Chrome (headless={self.headless})")
        else:
            print(f"🖥️  Setting up visible Chrome (headless={self.headless})")
        
        # Additional options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Enable logging for network capture
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--v=1")
        
        # Disable images and CSS for faster loading
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-css")
        
        # Debug: print the options being set
        print(f"🔧 Chrome options: {chrome_options.arguments}")
        
        try:
            # Use webdriver-manager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # Set logging preferences
            chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"✅ Chrome driver created successfully")
            return driver
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            print("Falling back to system ChromeDriver...")
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            print(f"✅ Chrome driver created with fallback")
            return driver
    
    def _save_session(self):
        """Save current session for reuse"""
        try:
            # Ensure session cache directory exists
            session_dir = Path('.session_cache')
            session_dir.mkdir(exist_ok=True)
            
            # Save cookies
            cookies = self.driver.get_cookies()
            cookies_path = session_dir / 'cookies.pkl'
            with open(cookies_path, 'wb') as f:
                pickle.dump(cookies, f)
            
            # Save session metadata
            metadata = {
                'timestamp': time.time(),
                'url': self.driver.current_url,
                'title': self.driver.title
            }
            metadata_path = session_dir / 'session_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            print(f"💾 Session saved successfully to {session_dir}")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to save session: {e}")
            return False
    
    def _load_session(self) -> bool:
        """Load saved session if available and valid"""
        try:
            session_dir = Path('.session_cache')
            cookies_path = session_dir / 'cookies.pkl'
            metadata_path = session_dir / 'session_metadata.json'
            
            if not cookies_path.exists() or not metadata_path.exists():
                print("📋 No saved session found")
                return False
            
            # Load session metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check if session is still valid (less than 24 hours old)
            session_age = time.time() - metadata['timestamp']
            if session_age > 24 * 60 * 60:  # 24 hours
                print(f"📋 Session expired (age: {session_age/3600:.1f} hours)")
                return False
            
            # Navigate to the domain before loading cookies
            if metadata.get('url'):
                try:
                    # Extract domain from URL
                    from urllib.parse import urlparse
                    parsed_url = urlparse(metadata['url'])
                    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    print(f"🌐 Navigating to domain: {domain}")
                    self.driver.get(domain)
                    time.sleep(2)  # Wait for page to load
                except Exception as e:
                    print(f"⚠️  Failed to navigate to domain: {e}")
                    # Fallback to humblebundle.com
                    self.driver.get('https://www.humblebundle.com')
                    time.sleep(2)
            else:
                # Default to humblebundle.com
                self.driver.get('https://www.humblebundle.com')
                time.sleep(2)
            
            # Load cookies
            with open(cookies_path, 'rb') as f:
                cookies = pickle.load(f)
            
            # Apply cookies to current driver
            cookies_loaded = 0
            for cookie in cookies:
                try:
                    # Clean up cookie data to avoid domain issues
                    clean_cookie = {}
                    for key, value in cookie.items():
                        if key in ['name', 'value', 'domain', 'path']:
                            clean_cookie[key] = value
                    
                    self.driver.add_cookie(clean_cookie)
                    cookies_loaded += 1
                except Exception as e:
                    print(f"⚠️  Failed to add cookie: {e}")
                    continue
            
            print(f"📋 Session loaded successfully (age: {session_age/3600:.1f} hours, {cookies_loaded} cookies)")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to load session: {e}")
            return False
    
    def _verify_session(self) -> bool:
        """Verify if current session is still valid."""
        if not self.driver:
            return False
            
        try:
            # First load the cookies
            if not self._load_session():
                return False
            
            # Then navigate to library page
            self.driver.get('https://www.humblebundle.com/home/library')
            time.sleep(2)  # Wait for page to load
            
            # Check if we're redirected to login
            if 'login' in self.driver.current_url.lower():
                return False
                
            # Check if we can see library content
            try:
                # Look for library-specific elements
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='library'], [class*='bundle'], [class*='product']"))
                )
                return True
            except TimeoutException:
                return False
                
        except Exception as e:
            print(f"Session verification failed: {e}")
            return False
    
    def has_valid_session(self) -> bool:
        """Check if there's a valid session available."""
        try:
            # Check if session files exist and are not too old
            session_dir = Path('.session_cache')
            cookies_path = session_dir / 'cookies.pkl'
            metadata_path = session_dir / 'session_metadata.json'
            
            if not cookies_path.exists() or not metadata_path.exists():
                return False
            
            # Check session age
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            if time.time() - metadata['timestamp'] > 86400:  # 24 hours
                return False
            
            # Try to load and verify session
            if not self.driver:
                self.driver = self._setup_driver()
            
            return self._verify_session()
            
        except Exception as e:
            print(f"Session validation error: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        try:
            session_dir = Path('.session_cache')
            cookies_path = session_dir / 'cookies.pkl'
            metadata_path = session_dir / 'session_metadata.json'
            
            if not cookies_path.exists() or not metadata_path.exists():
                return {
                    'status': 'no_session',
                    'age_hours': 0,
                    'signature': None,
                    'cookie_count': 0,
                    'url': None,
                    'title': None
                }
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            age_hours = (time.time() - metadata['timestamp']) / 3600
            
            # Get additional info if driver is available
            url = metadata.get('url')
            title = metadata.get('title')
            cookie_count = 0
            
            if self.driver:
                try:
                    url = self.driver.current_url
                    title = self.driver.title
                except Exception:
                    pass
            
            return {
                'status': 'exists' if age_hours < 24 else 'expired',
                'age_hours': age_hours,
                'signature': f"session_{int(metadata['timestamp'])}",
                'cookie_count': cookie_count,
                'url': url,
                'title': title
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'age_hours': 0,
                'signature': None,
                'cookie_count': 0,
                'url': None,
                'title': None
            }
    
    def _wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """Wait for an element to be present and return it."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def _check_for_mfa(self) -> bool:
        """Check if MFA challenge is present on the page"""
        try:
            mfa_selectors = [
                "input[name*='code']",
                "input[name*='token']", 
                "input[name*='mfa']",
                "input[name*='2fa']",
                "[class*='mfa']",
                "[class*='2fa']",
                "[class*='verification']"
            ]
            
            for selector in mfa_selectors:
                try:
                    mfa_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if mfa_input and mfa_input.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception as e:
            print(f"⚠️  Error checking for MFA: {e}")
            return False

    def _handle_mfa_challenge(self):
        """Handle MFA challenge by prompting user for code"""
        print("🔐 MFA challenge detected!")
        print("Please provide your MFA code:")
        
        # CRITICAL: Remove ALL animations and ensure page is completely static
        print("🎬 Suspending all animations and ensuring page is static...")
        try:
            # Remove all CSS animations and transitions
            self.driver.execute_script("""
                // Disable all CSS animations and transitions
                var style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `
                    *, *::before, *::after {
                        animation: none !important;
                        transition: none !important;
                        transform: none !important;
                    }
                `;
                document.head.appendChild(style);
                
                // Also remove any JavaScript-based animations
                var animatedElements = document.querySelectorAll('[class*="animate"], [class*="fade"], [class*="slide"], [class*="bounce"]');
                animatedElements.forEach(function(el) {
                    el.style.animation = 'none';
                    el.style.transition = 'none';
                });
                
                // Remove any loading spinners or progress indicators
                var spinners = document.querySelectorAll('[class*="spinner"], [class*="loading"], [class*="progress"]');
                spinners.forEach(function(el) {
                    el.style.display = 'none';
                });
                
                // Force page to be completely static
                document.body.style.animation = 'none';
                document.body.style.transition = 'none';
                
                console.log('All animations suspended');
            """)
            print("✅ All animations suspended")
            
            # Wait for any remaining animations to finish
            time.sleep(3)
            
            # Final check - ensure no elements are moving
            self.driver.execute_script("""
                // Force all elements to be completely static
                var allElements = document.querySelectorAll('*');
                allElements.forEach(function(el) {
                    el.style.animation = 'none';
                    el.style.transition = 'none';
                    el.style.transform = 'none';
                });
            """)
            print("✅ Page is now completely static")
            
        except Exception as e:
            print(f"⚠️  Animation suspension failed: {e}")
        
        # Now prompt for MFA code
        print("🔢 Enter your MFA code:")
        try:
            mfa_code = input("MFA Code: ")
            return mfa_code
        except Exception as e:
            print(f"❌ MFA input failed: {e}")
            # Fallback to environment variable
            mfa_code = os.environ.get('HUMBLE_MFA_CODE')
            if mfa_code:
                print(f"📝 Using MFA code from environment variable")
                return mfa_code
            else:
                raise Exception("Could not get MFA code from user input or environment")
    
    def _handle_cookie_consent(self) -> bool:
        """Handle cookie consent banner if present."""
        print("🍪 Checking for cookie consent banner...")
        
        try:
            # Look for common cookie consent elements and dismiss them ALL
            cookie_selectors = [
                "button[id*='onetrust']",
                "button[class*='onetrust']",
                "button:contains('Accept')",
                "button:contains('Accept All')",
                "button:contains('I Accept')",
                "button:contains('OK')",
                "button:contains('Got it')",
                "button:contains('Close')",
                "button:contains('Dismiss')"
            ]
            
            # Also look for any OneTrust elements that might be blocking
            onetrust_selectors = [
                "[id*='onetrust']",
                "[class*='onetrust']",
                "[id*='cookie']",
                "[class*='cookie']"
            ]
            
            # First, try to find and click cookie acceptance buttons
            cookie_clicked = self._click_cookie_buttons(cookie_selectors)
            
            if cookie_clicked:
                print("🍪 Cookie buttons clicked, waiting for dismissal...")
                time.sleep(3)  # Wait for banner to disappear
                
                # Now try to remove any remaining OneTrust elements that might be blocking
                self._cleanup_remaining_cookie_elements(onetrust_selectors)
                
                # Wait a bit more for page to stabilize after cookie acceptance
                print("⏳ Waiting for page to stabilize...")
                time.sleep(3)
            else:
                print("🍪 No cookie consent banner found")
            
            # FINAL CHECK: Remove ALL OneTrust elements that could block interaction
            self._final_cookie_cleanup()
            
            return True
            
        except Exception as e:
            print(f"⚠️  Cookie handling encountered an issue: {e}")
            return False
    
    def _click_cookie_buttons(self, cookie_selectors: List[str]) -> bool:
        """Click cookie acceptance buttons."""
        cookie_clicked = False
        
        for selector in cookie_selectors:
            try:
                if ':contains(' in selector:
                    # Handle text-based button search
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        button_text = button.text.lower()
                        if any(word in button_text for word in ['accept', 'accept all', 'i accept', 'ok', 'got it', 'close', 'dismiss']):
                            print(f"🍪 Clicking cookie button: '{button.text}'")
                            button.click()
                            cookie_clicked = True
                            time.sleep(1)
                else:
                    cookie_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"🍪 Clicking cookie button: '{cookie_button.text}'")
                    cookie_button.click()
                    cookie_clicked = True
                    time.sleep(1)
            except NoSuchElementException:
                continue
        
        return cookie_clicked
    
    def _cleanup_remaining_cookie_elements(self, onetrust_selectors: List[str]) -> None:
        """Clean up remaining cookie-related elements."""
        print("🍪 Checking for remaining cookie elements...")
        
        for selector in onetrust_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        print(f"🍪 Found remaining element: {element.tag_name} with classes: {element.get_attribute('class')}")
                        # Try to hide it with JavaScript
                        try:
                            self.driver.execute_script("arguments[0].style.display = 'none';", element)
                            print(f"🍪 Hidden element with JavaScript")
                        except:
                            pass
            except Exception:
                continue
    
    def _final_cookie_cleanup(self) -> None:
        """Final cleanup of all cookie-related elements."""
        print("🍪 Final cleanup: Removing all OneTrust elements...")
        
        try:
            # Use JavaScript to remove all OneTrust elements completely
            self.driver.execute_script("""
                // Remove all OneTrust elements
                var elements = document.querySelectorAll('[id*="onetrust"], [class*="onetrust"]');
                elements.forEach(function(el) {
                    el.remove();
                });
                
                // Also remove any cookie-related elements
                var cookieElements = document.querySelectorAll('[id*="cookie"], [class*="cookie"]');
                cookieElements.forEach(function(el) {
                    el.remove();
                });
                
                // Remove any overlay elements that might be blocking
                var overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="popup"]');
                overlays.forEach(function(el) {
                    if (el.style.zIndex > 1000) {
                        el.remove();
                    }
                });
            """)
            print("🍪 Final cleanup completed")
        except Exception as e:
            print(f"⚠️  Final cleanup encountered an issue: {e}")
    
    def _find_login_elements(self) -> tuple:
        """Find email and password input elements."""
        print("🔍 Looking for login form...")
        
        # Look for email/username input
        email_input = self._wait_for_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username'], input[placeholder*='email'], input[placeholder*='Email']")
        
        if not email_input:
            # Try alternative selectors
            email_input = self._wait_for_element(By.CSS_SELECTOR, "input[type='text']")
        
        if not email_input:
            print("❌ Could not find email input field")
            return None, None
        
        # Look for password input
        password_input = self._wait_for_element(By.CSS_SELECTOR, "input[type='password']")
        
        if not password_input:
            print("❌ Could not find password input field")
            return None, None
        
        return email_input, password_input
    
    def _fill_credentials(self, email_input, password_input, email: str, password: str) -> None:
        """Fill in login credentials."""
        print("📝 Entering credentials...")
        email_input.clear()
        email_input.send_keys(email)
        
        password_input.clear()
        password_input.send_keys(password)
    
    def _submit_login_form(self) -> bool:
        """Submit the login form."""
        print("🚀 Submitting login form...")
        
        try:
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Login')",
                "button:contains('Sign In')",
                "button:contains('Log In')",
                "button:contains('Submit')"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if ':contains(' in selector:
                        # Handle text-based button search
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            button_text = button.text.lower()
                            if any(word in button_text for word in ['login', 'sign in', 'log in', 'submit']):
                                submit_button = button
                                break
                        if submit_button:
                            break
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                print(f"🔘 Found submit button: '{submit_button.text}'")
                submit_button.click()
                return True
            else:
                # Try pressing Enter on password field
                print("🔘 No submit button found, trying Enter key...")
                password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_input.send_keys(Keys.RETURN)
                return True
                
        except Exception as e:
            print(f"❌ Error submitting login form: {e}")
            return False
    
    def _handle_mfa_if_needed(self) -> bool:
        """Handle MFA if required."""
        print("🔐 Checking for MFA requirement...")
        
        try:
            # Wait a bit for potential MFA page to load
            time.sleep(3)
            
            # Check if we're on an MFA page
            mfa_indicators = [
                "input[placeholder*='code']",
                "input[placeholder*='Code']",
                "input[placeholder*='verification']",
                "input[placeholder*='Verification']",
                "input[name*='code']",
                "input[name*='verification']",
                "input[type='text'][maxlength='6']",
                "input[type='text'][maxlength='8']"
            ]
            
            mfa_input = None
            for selector in mfa_indicators:
                try:
                    mfa_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if mfa_input:
                        break
                except NoSuchElementException:
                    continue
            
            if mfa_input:
                print("🔐 MFA code input found, requesting code...")
                mfa_code = self._handle_mfa_challenge() # Use the existing _handle_mfa_challenge
                if mfa_code:
                    mfa_input.clear()
                    mfa_input.send_keys(mfa_code)
                    
                    # Look for submit button for MFA
                    mfa_submit_selectors = [
                        "button[type='submit']",
                        "button:contains('Verify')",
                        "button:contains('Submit')",
                        "button:contains('Continue')"
                    ]
                    
                    mfa_submitted = False
                    for selector in mfa_submit_selectors:
                        try:
                            if ':contains(' in selector:
                                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                                for button in buttons:
                                    button_text = button.text.lower()
                                    if any(word in button_text for word in ['verify', 'submit', 'continue']):
                                        button.click()
                                        mfa_submitted = True
                                        break
                                if mfa_submitted:
                                    break
                            else:
                                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                button.click()
                                mfa_submitted = True
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not mfa_submitted:
                        # Try Enter key
                        mfa_input.send_keys(Keys.RETURN)
                    
                    print("🔐 MFA code submitted, waiting for verification...")
                    time.sleep(5)  # Wait for MFA verification
                    return True
                else:
                    print("❌ Could not get MFA code")
                    return False
            else:
                print("✅ No MFA required")
                return True
                
        except Exception as e:
            print(f"⚠️  MFA handling encountered an issue: {e}")
            return False
    
    def _wait_for_login_success(self) -> bool:
        """Wait for login to complete successfully."""
        print("⏳ Waiting for login to complete...")
        
        try:
            # Wait for redirect to complete
            time.sleep(5)
            
            # Check if we're logged in by looking for user-specific elements
            success_indicators = [
                "[class*='user']",
                "[class*='profile']",
                "[class*='account']",
                "[id*='user']",
                "[id*='profile']",
                "[id*='account']",
                "a[href*='/account']",
                "a[href*='/profile']",
                "a[href*='/user']"
            ]
            
            for selector in success_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        print("✅ Login successful - user elements found")
                        return True
                except NoSuchElementException:
                    continue
            
            # Also check if we're on a page that indicates successful login
            current_url = self.driver.current_url
            if any(indicator in current_url for indicator in ['/account', '/profile', '/user', '/dashboard']):
                print("✅ Login successful - redirected to user page")
                return True
            
            # Check if we're still on login page (indicates failure)
            if '/login' in current_url:
                print("❌ Still on login page - login may have failed")
                return False
            
            print("⚠️  Login status unclear, assuming success")
            return True
            
        except Exception as e:
            print(f"⚠️  Error checking login status: {e}")
            return False
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Login to Humble Bundle using Selenium.
        
        Args:
            email: Humble Bundle email (uses config if not provided)
            password: Humble Bundle password (uses config if not provided)
            
        Returns:
            True if login successful, False otherwise
        """
        email = email or settings.humble_email
        password = password or settings.humble_password
        
        if not email or not password:
            raise ValueError("Email and password are required for login")
        
        try:
            # Setup driver
            self.driver = self._setup_driver()
            
            # Try to load existing session first
            if self._load_session():
                print("✅ Loaded existing session")
                return True
            
            print("🔄 Starting new login process...")
            
            # Navigate to login page
            self.driver.get('https://www.humblebundle.com/login')
            time.sleep(3)  # Wait for page to load
            
            # Find login elements
            email_input, password_input = self._find_login_elements()
            if not email_input or not password_input:
                return False
            
            # Fill in credentials
            self._fill_credentials(email_input, password_input, email, password)
            
            # Handle cookie consent
            self._handle_cookie_consent()
            
            # Submit login form
            if not self._submit_login_form():
                return False
            
            # Handle MFA if required
            if not self._handle_mfa_if_needed():
                return False
            
            # Wait for login to complete
            if not self._wait_for_login_success():
                return False
            
            # Save session
            self._save_session()
            print("✅ Login successful and session saved")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            if settings.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def get_authenticated_session(self) -> webdriver.Chrome:
        """Get authenticated Chrome driver for API calls."""
        if not self.driver or not self._verify_session():
            if not self.login():
                raise Exception("Failed to authenticate with Humble Bundle")
        
        return self.driver
    
    def logout(self) -> None:
        """Logout and clear session data."""
        try:
            if self.driver:
                self.driver.get('https://www.humblebundle.com/logout')
                time.sleep(2)
        except Exception:
            pass
        
        # Clear session files
        session_dir = Path('.session_cache')
        if session_dir.exists():
            import shutil
            shutil.rmtree(session_dir)
            print("🗑️  Session cache cleared")
        
        # Close driver
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.driver:
            self.driver.quit() 