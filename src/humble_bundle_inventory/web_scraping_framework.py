#!/usr/bin/env python3
"""
Abstract web scraping framework for digital asset inventory systems.
Provides common patterns for web automation, data extraction, and error handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class ExtractionStrategy(Enum):
    """Different strategies for data extraction."""
    DOM_PARSING = "dom_parsing"
    JAVASCRIPT_EXECUTION = "javascript_execution"
    API_INTERCEPTION = "api_interception"
    HYBRID = "hybrid"

@dataclass
class ExtractionRule:
    """Rule for extracting data from web elements."""
    name: str
    selector: str
    attribute: Optional[str] = None  # If None, gets text content
    regex_pattern: Optional[str] = None  # Post-process with regex
    required: bool = True
    multiple: bool = False  # Extract multiple elements

@dataclass
class PageConfig:
    """Configuration for a specific page."""
    url: str
    wait_selectors: List[str]  # Selectors to wait for before extraction
    extraction_rules: List[ExtractionRule]
    javascript_setup: Optional[str] = None  # JS to run before extraction
    scroll_to_load: bool = False  # Whether to scroll to trigger lazy loading
    wait_time: float = 3.0  # Additional wait time

class WebElementExtractor:
    """Utility class for extracting data from web elements."""
    
    @staticmethod
    def extract_text(element) -> str:
        """Extract text content from element."""
        return element.text.strip() if element else ""
    
    @staticmethod
    def extract_attribute(element, attribute: str) -> str:
        """Extract attribute value from element.""" 
        return element.get_attribute(attribute) if element else ""
    
    @staticmethod
    def extract_with_regex(text: str, pattern: str) -> str:
        """Extract text using regex pattern."""
        match = re.search(pattern, text)
        return match.group(1) if match else text
    
    @staticmethod
    def extract_multiple_texts(elements) -> List[str]:
        """Extract text from multiple elements."""
        return [elem.text.strip() for elem in elements if elem.text.strip()]

class BaseWebScraper(ABC):
    """
    Abstract base class for web scrapers.
    Provides common patterns for web automation and data extraction.
    """
    
    def __init__(self, driver: webdriver.Chrome, wait_timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_timeout)
        self.extractor = WebElementExtractor()
    
    def extract_from_page(self, config: PageConfig) -> Dict[str, Any]:
        """
        Extract data from a page using the provided configuration.
        Template method for page extraction.
        """
        try:
            # Step 1: Navigate to page
            self._navigate_to_page(config.url)
            
            # Step 2: Run JavaScript setup if needed
            if config.javascript_setup:
                self.driver.execute_script(config.javascript_setup)
            
            # Step 3: Wait for page to load
            self._wait_for_page_load(config)
            
            # Step 4: Handle dynamic content loading
            if config.scroll_to_load:
                self._trigger_dynamic_loading()
            
            # Step 5: Additional wait
            time.sleep(config.wait_time)
            
            # Step 6: Extract data using rules
            return self._extract_data_by_rules(config.extraction_rules)
            
        except Exception as e:
            print(f"Error extracting from page {config.url}: {e}")
            return {}
    
    def _navigate_to_page(self, url: str):
        """Navigate to the specified URL."""
        self.driver.get(url)
    
    def _wait_for_page_load(self, config: PageConfig):
        """Wait for page elements to load."""
        for selector in config.wait_selectors:
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            except TimeoutException:
                print(f"Warning: Selector {selector} not found within timeout")
    
    def _trigger_dynamic_loading(self):
        """Trigger dynamic content loading by scrolling."""
        # Scroll to bottom
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    
    def _extract_data_by_rules(self, rules: List[ExtractionRule]) -> Dict[str, Any]:
        """Extract data using extraction rules."""
        result = {}
        
        for rule in rules:
            try:
                if rule.multiple:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, rule.selector)
                    if rule.attribute:
                        values = [self.extractor.extract_attribute(elem, rule.attribute) for elem in elements]
                    else:
                        values = self.extractor.extract_multiple_texts(elements)
                    
                    # Apply regex if specified
                    if rule.regex_pattern:
                        values = [self.extractor.extract_with_regex(val, rule.regex_pattern) for val in values]
                    
                    result[rule.name] = values
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, rule.selector)
                    if rule.attribute:
                        value = self.extractor.extract_attribute(element, rule.attribute)
                    else:
                        value = self.extractor.extract_text(element)
                    
                    # Apply regex if specified
                    if rule.regex_pattern:
                        value = self.extractor.extract_with_regex(value, rule.regex_pattern)
                    
                    result[rule.name] = value
                    
            except NoSuchElementException:
                if rule.required:
                    print(f"Required element not found: {rule.selector}")
                result[rule.name] = [] if rule.multiple else ""
        
        return result
    
    def extract_with_javascript(self, script: str) -> Any:
        """Execute JavaScript and return result."""
        try:
            return self.driver.execute_script(script)
        except WebDriverException as e:
            print(f"JavaScript execution error: {e}")
            return None
    
    def find_elements_safe(self, selector: str) -> List:
        """Find elements safely, returning empty list if not found."""
        try:
            return self.driver.find_elements(By.CSS_SELECTOR, selector)
        except:
            return []
    
    def find_element_safe(self, selector: str):
        """Find element safely, returning None if not found."""
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except:
            return None
    
    # Abstract methods for specific implementations
    @abstractmethod
    def get_page_configs(self) -> Dict[str, PageConfig]:
        """Get page configurations for this scraper."""
        pass
    
    @abstractmethod  
    def process_extracted_data(self, page_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process extracted data into standardized format."""
        pass

class ProductPageScraper(BaseWebScraper):
    """Specialized scraper for product listing pages."""
    
    def extract_products(self, page_config: PageConfig) -> List[Dict[str, Any]]:
        """Extract multiple products from a listing page."""
        # Navigate and wait
        self._navigate_to_page(page_config.url)
        self._wait_for_page_load(page_config)
        
        if page_config.scroll_to_load:
            self._trigger_dynamic_loading()
        
        # Find product containers
        product_selector = self._get_product_container_selector()
        product_elements = self.find_elements_safe(product_selector)
        
        products = []
        for element in product_elements:
            try:
                product_data = self._extract_product_from_element(element)
                if product_data:
                    products.append(product_data)
            except Exception as e:
                print(f"Error extracting product: {e}")
                continue
        
        return products
    
    @abstractmethod
    def _get_product_container_selector(self) -> str:
        """Get CSS selector for product containers."""
        pass
    
    @abstractmethod
    def _extract_product_from_element(self, element) -> Optional[Dict[str, Any]]:
        """Extract product data from a single element."""
        pass

class ScrapingSession:
    """Manages a complete scraping session with multiple pages."""
    
    def __init__(self, scraper: BaseWebScraper):
        self.scraper = scraper
        self.session_data = {}
        self.errors = []
    
    def scrape_all_pages(self) -> Dict[str, Any]:
        """Scrape all configured pages."""
        page_configs = self.scraper.get_page_configs()
        
        for page_name, config in page_configs.items():
            try:
                print(f"Scraping page: {page_name}")
                raw_data = self.scraper.extract_from_page(config)
                processed_data = self.scraper.process_extracted_data(page_name, raw_data)
                self.session_data[page_name] = processed_data
            except Exception as e:
                error_msg = f"Error scraping {page_name}: {e}"
                print(error_msg)
                self.errors.append(error_msg)
        
        return {
            'data': self.session_data,
            'errors': self.errors,
            'pages_scraped': len(self.session_data),
            'total_pages': len(page_configs)
        }

# Utility functions for common scraping patterns
class ScrapingUtils:
    """Utility functions for common scraping operations."""
    
    @staticmethod
    def create_extraction_rule(name: str, selector: str, **kwargs) -> ExtractionRule:
        """Create an extraction rule with defaults."""
        return ExtractionRule(name=name, selector=selector, **kwargs)
    
    @staticmethod
    def create_product_page_config(url: str, product_selector: str, 
                                 wait_selectors: List[str] = None) -> PageConfig:
        """Create a page config for product listing pages."""
        if wait_selectors is None:
            wait_selectors = [product_selector]
        
        rules = [
            ExtractionRule("products", product_selector, multiple=True)
        ]
        
        return PageConfig(
            url=url,
            wait_selectors=wait_selectors,
            extraction_rules=rules,
            scroll_to_load=True
        )
    
    @staticmethod
    def extract_id_from_url(url: str, pattern: str) -> str:
        """Extract ID from URL using regex pattern."""
        match = re.search(pattern, url)
        return match.group(1) if match else ""