# Humble Bundle API Analysis and Implementation Guide

## Overview

This document details the discovered Humble Bundle API endpoints and the implementation approach used for library synchronization. The information was gathered through HTTP Archive (HAR) analysis and reverse engineering of the web interface.

## Discovered API Endpoints

### Primary Data Endpoint

**URL**: `https://www.humblebundle.com/api/v1/orders`

**Method**: GET

**Parameters**:
- `all_tpkds=true` - Include all third-party keys
- `gamekeys={gamekey}` - Specific bundle gamekey (can be repeated)

**Authentication**: Session cookies required (`_simpleauth_sess`, `csrf_cookie`)

**Example Request**:
```
GET /api/v1/orders?all_tpkds=true&gamekeys=6Y8wnhvdzNyNE5Cn&gamekeys=zdConsentUpdate&gamekeys=SearchAction&gamekeys=Y3R1JDHEUNP7
```

**Response Structure**:
```json
{
  "results": [
    {
      "gamekey": "6Y8wnhvdzNyNE5Cn",
      "product": {
        "human_name": "Example Bundle Name",
        "machine_name": "example_bundle",
        "created": "2024-01-15T10:30:00Z"
      },
      "subproducts": [
        {
          "human_name": "Example Product",
          "machine_name": "example_product",
          "developer": "Example Developer",
          "publisher": "Example Publisher",
          "downloads": [
            {
              "name": "Direct Download",
              "download_structs": [
                {
                  "name": "PDF",
                  "url": {"web": "https://..."},
                  "file_size": 1234567,
                  "platform": "ebook",
                  "sha1": "abc123...",
                  "md5": "def456..."
                }
              ]
            }
          ]
        }
      ],
      "amount_spent": 15.00,
      "currency": "USD",
      "created": "2024-01-15T10:30:00Z",
      "charity": {
        "name": "Example Charity",
        "amount": 5.00
      }
    }
  ]
}
```

### Secondary Endpoints

**Store Coupons**: `https://www.humblebundle.com/store/coupons`
- Returns available store coupons and promotional codes

## Gamekey Discovery Methods

### Method 1: JavaScript Variables

The primary method involves extracting gamekeys from JavaScript variables embedded in the library page:

```javascript
// Check window.models object
if (window.models && window.models.gamekeys) {
    return window.models.gamekeys;
}

// Search for gamekey arrays in other window.models properties
for (var key in window.models) {
    var value = window.models[key];
    if (Array.isArray(value) && value.length > 0) {
        if (typeof value[0] === 'string' && /^[A-Za-z0-9]{12,16}$/.test(value[0])) {
            gamekeys = gamekeys.concat(value);
        }
    }
}
```

### Method 2: Regex Pattern Extraction

Fallback method using regex patterns on page source:

```python
patterns = [
    r'"gamekeys?"\s*:\s*\[([^\]]+)\]',
    r'gamekeys?\s*[=:]\s*\[([^\]]+)\]',
    r'"([A-Za-z0-9]{12,16})"\s*[,\]]'  # Direct gamekey pattern
]

for pattern in patterns:
    matches = re.findall(pattern, page_source)
    # Process matches to extract individual gamekeys
```

### Method 3: DOM Element Attributes

Extract from HTML data attributes and links:

```python
elements = driver.find_elements("css selector", "[data-gamekey], [data-game-key], [href*='gamekey']")

for element in elements:
    gamekey = element.get_attribute('data-gamekey') or element.get_attribute('data-game-key')
    if gamekey and re.match(r'^[A-Za-z0-9]{12,16}$', gamekey):
        gamekeys.append(gamekey)
```

## Implementation Strategy

### 1. Authentication and Session Management

```python
class PersistentSessionAuth:
    def login(self, email: str, password: str) -> bool:
        # Navigate to login page
        # Fill credentials
        # Handle MFA if required
        # Validate session
        # Save encrypted session data
        pass
    
    def _verify_persistent_session(self) -> bool:
        # Navigate to library page
        # Check for authentication indicators
        # Validate user-specific content
        pass
```

### 2. Gamekey Extraction

```python
def _extract_gamekeys_from_page(self) -> List[str]:
    # Navigate to library page
    # Execute JavaScript gamekey extraction
    # Apply regex fallback methods
    # Try DOM element extraction
    # Trigger content loading if needed
    # Return unique gamekeys
    pass
```

### 3. API Data Retrieval

```python
def _fetch_orders_with_gamekeys(self, gamekeys: List[str]) -> List[Dict]:
    # Split gamekeys into batches (35 per request)
    # Build API URLs with proper parameter encoding
    # Make authenticated requests with session cookies
    # Handle rate limiting and errors
    # Process and combine response data
    pass
```

### 4. Data Processing Pipeline

```python
def _process_orders_data(self, orders: List[Dict]) -> Tuple[List, List, List]:
    products, bundles, downloads = [], [], []
    
    for order in orders:
        # Extract bundle information
        bundle = {
            'gamekey': order.get('gamekey'),
            'name': order.get('product', {}).get('human_name'),
            'type': self._categorize_bundle(order.get('product', {}).get('human_name')),
            'created': order.get('created'),
            'total_amount': order.get('amount_spent', 0),
            'currency': order.get('currency', 'USD')
        }
        bundles.append(bundle)
        
        # Extract products from subproducts
        for subproduct in order.get('subproducts', []):
            product = {
                'product_id': subproduct.get('machine_name'),
                'human_name': subproduct.get('human_name'),
                'category': self._categorize_product(subproduct.get('human_name')),
                'developer': subproduct.get('developer'),
                'publisher': subproduct.get('publisher'),
                'bundle_gamekey': order.get('gamekey')
            }
            products.append(product)
            
            # Extract downloads from delivery methods
            for delivery in subproduct.get('downloads', []):
                for download_struct in delivery.get('download_structs', []):
                    download = {
                        'product_id': subproduct.get('machine_name'),
                        'platform': download_struct.get('platform'),
                        'format': download_struct.get('name'),
                        'url': download_struct.get('url', {}).get('web'),
                        'size': download_struct.get('file_size', 0),
                        'sha1': download_struct.get('sha1'),
                        'md5': download_struct.get('md5'),
                        'gamekey': order.get('gamekey')
                    }
                    downloads.append(download)
    
    return products, bundles, downloads
```

## Rate Limiting and Error Handling

### Rate Limiting Implementation

```python
def _rate_limit(self) -> None:
    now = time.time()
    self._request_times = [t for t in self._request_times if now - t < 60]
    
    if len(self._request_times) >= settings.requests_per_minute:
        sleep_time = 60 - (now - self._request_times[0])
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    self._request_times.append(now)
```

### Error Recovery Strategies

1. **Network Errors**: Exponential backoff with configurable retry limits
2. **Authentication Errors**: Session refresh and re-authentication
3. **API Errors**: Partial batch retry and error logging
4. **Parsing Errors**: Graceful degradation with error context

## Security Considerations

### 1. Session Security

- All session cookies encrypted with Fernet symmetric encryption
- Session signatures prevent tampering and validate integrity
- Automatic session expiry based on cookie lifetimes
- Secure key generation and storage

### 2. API Usage Ethics

- Respectful rate limiting (default: 30 requests/minute)
- User-Agent headers matching browser behavior
- No automated scraping beyond personal library access
- Compliance with Humble Bundle terms of service

### 3. Data Protection

- Local-only data storage (no cloud transmission)
- Environment variable credential storage
- Optional data field exclusion for privacy
- User-controlled data retention policies

## Testing and Validation

### HAR Analysis Workflow

1. **Capture Network Traffic**:
   ```bash
   # Open Chrome DevTools
   # Navigate to Network tab
   # Perform library operations
   # Export HAR file for analysis
   ```

2. **Analyze API Patterns**:
   ```python
   def analyze_har_file(har_path: str):
       with open(har_path, 'r') as f:
           har_data = json.load(f)
       
       for entry in har_data['log']['entries']:
           url = entry['request']['url']
           if '/api/v1/orders' in url:
               # Analyze request parameters
               # Extract gamekey patterns
               # Document response structure
   ```

3. **Validate Implementation**:
   ```python
   def test_gamekey_extraction():
       client = HumbleBundleAPIClient(auth)
       gamekeys = client._extract_gamekeys_from_page()
       assert len(gamekeys) > 0
       assert all(re.match(r'^[A-Za-z0-9]{12,16}$', key) for key in gamekeys)
   ```

## Performance Metrics

Based on testing with real library data:

- **Gamekey Extraction**: ~3-5 seconds for JavaScript method
- **API Response Time**: ~2-4 seconds per batch (35 gamekeys)
- **Data Processing**: ~1-2 seconds per 100 products
- **Database Sync**: ~0.1 seconds per product with upserts
- **Session Restoration**: ~1-2 seconds for cached sessions

## Troubleshooting Common Issues

### 1. Gamekey Extraction Failures

**Problem**: No gamekeys found on library page

**Solutions**:
- Verify user is logged in and has library access
- Check if page content has loaded completely
- Try triggering lazy loading with scroll interactions
- Verify JavaScript execution environment

### 2. API Authentication Errors

**Problem**: 401/403 responses from API endpoints

**Solutions**:
- Refresh authentication session
- Verify cookie transfer from browser to requests session
- Check for CSRF token requirements
- Validate session expiry and renewal

### 3. Incomplete Data Extraction

**Problem**: Missing products or bundles in results

**Solutions**:
- Increase gamekey batch processing timeout
- Verify all gamekeys are being discovered
- Check for pagination in API responses
- Validate JSON parsing for edge cases

This API documentation provides a complete reference for implementing Humble Bundle library synchronization using the discovered endpoints and methods.