# HAR-Based Metadata Analysis Guide

This guide explains how to use the enhanced HAR (HTTP Archive) based metadata analysis tools to understand and improve metadata extraction from Humble Bundle's API responses.

## Overview

The HAR-based metadata analysis system consists of three main components:

1. **HAR Metadata Analyzer** - Captures comprehensive network interactions and JavaScript data
2. **API Response Analyzer** - Analyzes actual API responses to understand metadata structure  
3. **Enhanced Metadata Extractor** - Applies insights to improve extraction quality

## Quick Start

### 1. Capture HAR Data and Network Interactions

```bash
# Run comprehensive HAR capture
python scripts/har_metadata_analyzer.py
```

This will:
- Enable Chrome DevTools Protocol network monitoring
- Execute comprehensive JavaScript data extraction
- Trigger API interactions by interacting with the page
- Capture performance timeline and network requests
- Generate enhanced metadata extractor code

**Output Files:**
- `har_analysis/comprehensive_analysis_TIMESTAMP.json` - Main analysis data
- `har_analysis/js_extraction_TIMESTAMP.json` - JavaScript data extraction
- `har_analysis/api_interactions_TIMESTAMP.json` - API interaction results
- `har_analysis/enhanced_metadata_extractor_TIMESTAMP.py` - Generated extractor

### 2. Analyze API Responses

```bash
# Run comprehensive API response analysis
python scripts/api_response_analyzer.py
```

This will:
- Test multiple gamekey extraction methods
- Capture actual API responses with gamekey batching
- Analyze response structure and metadata patterns
- Generate improved categorization rules
- Identify metadata enrichment opportunities

**Output Files:**
- `api_analysis/api_analysis_TIMESTAMP.json` - Complete API analysis
- `api_analysis/gamekeys_analysis_TIMESTAMP.json` - Gamekey extraction analysis
- `api_analysis/metadata_structure_TIMESTAMP.json` - Response structure analysis
- `api_analysis/enhanced_categorization_TIMESTAMP.json` - Categorization improvements

### 3. Apply Enhanced Metadata Extraction

```bash
# Run enhanced metadata extraction
python scripts/enhanced_metadata_extractor.py
```

This will:
- Apply enhanced categorization rules based on HAR analysis
- Extract comprehensive metadata with confidence scoring
- Perform cross-product enhancements (developer analysis, etc.)
- Generate detailed extraction quality report

**Output Files:**
- `enhanced_extraction_TIMESTAMP.json` - Enhanced extraction results with quality metrics

## Understanding the Analysis Results

### HAR Analysis Output

The HAR analysis provides insights into:

**JavaScript Data Sources:**
```json
{
  "javascript_data": {
    "gamekeys": ["6Y8wnhvdzNyNE5Cn", "SearchAction", ...],
    "metadataPatterns": {
      "gamekeys": {"type": "array", "size": 4, "hasGamekeys": true},
      "user_data": {"type": "object", "size": 12}
    },
    "domData": {
      ".product": [{"data-gamekey": "...", "data-human-name": "..."}]
    }
  }
}
```

**Network Request Patterns:**
```json
{
  "network_analysis": {
    "api_requests": 3,
    "api_endpoints": ["/api/v1/orders"],
    "request_patterns": {
      "api_patterns": ["/api/v1/orders"]
    }
  }
}
```

### API Response Analysis

**Gamekey Extraction Comparison:**
```json
{
  "gamekeys_analysis": {
    "methods": {
      "javascript": {"gamekeys": [...], "count": 4},
      "api_client": {"gamekeys": [...], "count": 4}, 
      "dom": {"gamekeys": [...], "count": 2}
    },
    "recommended_method": {
      "primary_method": "api_client",
      "reasoning": "Highest gamekey count (4) with no errors"
    }
  }
}
```

**Metadata Structure Analysis:**
```json
{
  "metadata_structure": {
    "response_analysis": {
      "order_structure": {
        "top_level_fields": ["gamekey", "product", "subproducts", "amount_spent"],
        "key_identifiers": {"gamekey": "6Y8wnhvdzNyNE5Cn"}
      },
      "subproduct_structure": {
        "common_fields": ["human_name", "machine_name", "developer", "downloads"],
        "field_analysis": {
          "human_name": {"coverage": 1.0, "present_in": 5},
          "developer": {"coverage": 0.8, "present_in": 4}
        }
      }
    }
  }
}
```

### Enhanced Extraction Results

**Categorization Improvements:**
```json
{
  "categorization_analysis": {
    "category_distribution": {
      "ebook": 12,
      "game": 8, 
      "software": 3,
      "unknown": 1
    },
    "average_confidence": 0.85,
    "high_confidence_products": 20,
    "low_confidence_products": 4
  }
}
```

**Quality Metrics:**
```json
{
  "quality_metrics": {
    "extraction_completeness": 98.5,
    "average_categorization_confidence": 85.2,
    "metadata_richness_score": 78.3
  }
}
```

## Advanced Usage

### Custom Analysis Workflows

**1. Focused Gamekey Analysis:**
```python
from scripts.api_response_analyzer import APIResponseAnalyzer

analyzer = APIResponseAnalyzer()
gamekey_analysis = analyzer._analyze_gamekey_extraction()
print(f"Best method: {gamekey_analysis['recommended_method']['primary_method']}")
print(f"Total gamekeys: {gamekey_analysis['total_unique_gamekeys']}")
```

**2. Custom Categorization Rules:**
```python
from scripts.enhanced_metadata_extractor import EnhancedMetadataExtractor

# Create custom extractor with modified rules
extractor = EnhancedMetadataExtractor()

# Add custom category
extractor.enhanced_categorization_rules['name_patterns']['tutorial'] = {
    'keywords': ['tutorial', 'course', 'lesson', 'training', 'workshop'],
    'confidence_boost': ['learn', 'teach', 'guide', 'step-by-step']
}

# Apply custom extraction
result = extractor.extract_enhanced_library_data()
```

**3. Metadata Enrichment Analysis:**
```python
# Analyze specific metadata patterns
from pathlib import Path
import json

# Load recent analysis
analysis_files = list(Path("api_analysis").glob("api_analysis_*.json"))
latest_analysis = max(analysis_files, key=lambda f: f.stat().st_mtime)

with open(latest_analysis, 'r') as f:
    data = json.load(f)

# Extract categorization improvements
categorization = data.get('enhanced_categorization', {})
print("Suggested improvements:")
for rule in categorization.get('improved_rules', []):
    print(f"  - {rule}")
```

### Performance Optimization

**1. Batch Processing:**
```python
# Process gamekeys in smaller batches for better performance
analyzer = APIResponseAnalyzer()
analyzer.client.batch_size = 5  # Reduce batch size
analysis = analyzer.analyze_api_responses()
```

**2. Selective Analysis:**
```python
# Only analyze specific components
analyzer = HARMetadataAnalyzer()

# Skip expensive network analysis
analysis = analyzer.capture_comprehensive_har()
analysis.pop('network_analysis', None)  # Remove network analysis

analyzer._save_comprehensive_data(analysis)
```

## Troubleshooting

### Common Issues

**1. No Gamekeys Found:**
```bash
# Check if you're logged in
python -c "
from scripts.persistent_session_auth import PersistentSessionAuth
auth = PersistentSessionAuth()
if not auth.login():
    print('Authentication failed - login first')
else:
    print('Authentication successful')
"

# Verify library page access
python -c "
from scripts.persistent_session_auth import PersistentSessionAuth
auth = PersistentSessionAuth()
driver = auth.get_authenticated_session()
driver.get('https://www.humblebundle.com/home/library')
print('Page title:', driver.title)
print('Library in URL:', 'library' in driver.current_url)
"
```

**2. API Response Errors:**
```bash
# Check session cookies
python -c "
from scripts.api_client import HumbleBundleAPIClient
from scripts.persistent_session_auth import PersistentSessionAuth
auth = PersistentSessionAuth()
client = HumbleBundleAPIClient(auth)
try:
    client._update_session_cookies()
    print('Session cookies updated successfully')
except Exception as e:
    print(f'Cookie update failed: {e}')
"
```

**3. Low Categorization Confidence:**
```bash
# Analyze categorization patterns
python -c "
import json
from pathlib import Path

# Find products with low confidence
analysis_files = list(Path('.').glob('enhanced_extraction_*.json'))
if analysis_files:
    latest = max(analysis_files, key=lambda f: f.stat().st_mtime)
    with open(latest, 'r') as f:
        data = json.load(f)
    
    low_confidence = [
        p for p in data.get('enhanced_data', {}).get('products', [])
        if p.get('category_confidence', 0) < 0.5
    ]
    
    print(f'Low confidence products: {len(low_confidence)}')
    for product in low_confidence[:5]:
        print(f'  - {product[\"human_name\"]}: {product[\"category\"]} ({product[\"category_confidence\"]:.2f})')
"
```

### Debug Mode

Enable debug output for detailed analysis:

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug information
analyzer = HARMetadataAnalyzer()
analysis = analyzer.capture_comprehensive_har()

# Check debug output in analysis
debug_info = analysis.get('debug_info', {})
print("Debug information:", debug_info)
```

## Integration with Existing Sync

To integrate enhanced metadata extraction with the existing sync system:

```python
# In sync.py, replace the basic categorization with enhanced version
from scripts.enhanced_metadata_extractor import EnhancedMetadataExtractor

class HumbleBundleSync:
    def __init__(self):
        # ... existing initialization ...
        self.enhanced_extractor = EnhancedMetadataExtractor()
    
    def sync(self, force: bool = False) -> Dict[str, Any]:
        # Use enhanced extraction instead of basic API client
        enhanced_result = self.enhanced_extractor.extract_enhanced_library_data()
        enhanced_data = enhanced_result['enhanced_data']
        
        # Process enhanced data
        products = enhanced_data['products']
        bundles = enhanced_data['bundles']
        downloads = enhanced_data['downloads']
        
        # Continue with existing sync logic...
        result = self._sync_api_data(products, bundles, downloads, {})
        
        return result
```

## Output File Structure

All analysis tools create timestamped output files in dedicated directories:

```
humblebundle/
├── har_analysis/
│   ├── comprehensive_analysis_20240115_143022.json
│   ├── js_extraction_20240115_143022.json
│   ├── api_interactions_20240115_143022.json
│   ├── performance_analysis_20240115_143022.json
│   ├── network_requests_20240115_143022.json
│   ├── metadata_patterns_20240115_143022.json
│   ├── summary_20240115_143022.json
│   └── enhanced_metadata_extractor_20240115_143022.py
│
├── api_analysis/
│   ├── api_analysis_20240115_143530.json
│   ├── gamekeys_analysis_20240115_143530.json
│   ├── api_responses_20240115_143530.json
│   ├── metadata_structure_20240115_143530.json
│   ├── extraction_patterns_20240115_143530.json
│   ├── enhanced_categorization_20240115_143530.json
│   └── analysis_summary_20240115_143530.json
│
└── enhanced_extraction_20240115_144015.json
```

This comprehensive analysis system provides deep insights into Humble Bundle's API structure and enables significant improvements in metadata extraction quality and accuracy.