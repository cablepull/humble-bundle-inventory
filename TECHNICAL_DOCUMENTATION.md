# Humble Bundle Library Synchronization - Technical Documentation

## Overview

This application is a complete library synchronization system for Humble Bundle that extracts user library data and synchronizes it to a local DuckDB database. The system uses HAR (HTTP Archive) analysis-based API discovery, persistent session management, and robust web automation to provide comprehensive library metadata extraction.

## Architecture

### Core Components

1. **Persistent Session Authentication** (`scripts/persistent_session_auth.py`)
   - Encrypted session storage with Fernet encryption
   - Session validation and automatic refresh
   - MFA (Multi-Factor Authentication) support with email verification
   - Session metadata tracking with signature validation
   - Chrome WebDriver automation with optimized settings

2. **API Client** (`scripts/api_client.py`)
   - HAR-analysis based gamekey extraction from library page
   - Direct API calls to `/api/v1/orders` endpoint with gamekey batching
   - Multiple gamekey discovery strategies (JavaScript variables, regex patterns, element attributes)
   - Rate limiting and respectful API usage
   - Comprehensive error handling and retry logic

3. **Database Management** (`database.py`)
   - DuckDB schema with tables for bundles, products, downloads, and metadata
   - Atomic operations with proper transaction handling
   - Support for book and game metadata enrichment
   - Comprehensive sync metadata tracking
   - Library statistics and search functionality

4. **Synchronization Engine** (`scripts/sync.py`)
   - API-based data processing pipeline
   - Rich progress tracking with real-time updates
   - Product categorization and metadata extraction
   - Bundle and download relationship management
   - Comprehensive error logging and recovery

5. **Configuration Management** (`src/config.py`)
   - Pydantic-based settings with environment variable support
   - Encrypted credential storage
   - Configurable sync intervals and rate limiting
   - Flexible database and session management

## Implementation Details

### Authentication Flow

1. **Session Loading**:
   - Check for existing encrypted session files
   - Validate session metadata (age, signature, expiry)
   - Attempt to restore Chrome driver with saved cookies

2. **Session Validation**:
   - Navigate to `/home/library` to verify authentication
   - Check for user-specific elements and content
   - Validate against multiple authentication indicators

3. **New Login Process**:
   - Navigate to login page with optimized Chrome options
   - Fill email/password fields using multiple selector strategies
   - Handle MFA challenges with email verification codes
   - Support for alphanumeric codes (4-12 characters)
   - Multiple submission methods (button click, Enter key)

4. **Session Persistence**:
   - Encrypt session data with Fernet (cookies, URL, metadata)
   - Create session signature for validation
   - Store metadata separately for quick access
   - Automatic session refresh on successful operations

### Data Extraction Pipeline

1. **Gamekey Discovery**:
   ```javascript
   // Multiple JavaScript variable checks
   if (window.models && window.models.gamekeys) {
       return window.models.gamekeys;
   }
   
   // Search for gamekey arrays in window.models
   for (var key in window.models) {
       var value = window.models[key];
       if (Array.isArray(value) && /^[A-Za-z0-9]{12,16}$/.test(value[0])) {
           gamekeys = gamekeys.concat(value);
       }
   }
   ```

2. **API Data Retrieval**:
   ```python
   # Batched API calls to /api/v1/orders
   base_url = f"{self.base_url}/api/v1/orders"
   param_parts = ['all_tpkds=true']
   for gamekey in gamekeys:
       param_parts.append(f'gamekeys={gamekey}')
   url = f"{base_url}?{'&'.join(param_parts)}"
   ```

3. **Data Processing**:
   - Extract bundle information (gamekey, name, type, creation date)
   - Process subproducts into individual product records
   - Extract download information from delivery methods
   - Apply categorization logic based on product names
   - Generate database-compatible data structures

### Database Schema

The application uses a comprehensive DuckDB schema:

```sql
-- Core tables
bundles (bundle_id, bundle_name, bundle_type, purchase_date, amount_spent, charity)
products (product_id, human_name, machine_name, category, developer, publisher, url, description)
downloads (download_id, product_id, platform, architecture, download_type, file_name, file_size, download_url)

-- Relationship tables
bundle_products (bundle_id, product_id)

-- Metadata tables
book_metadata (product_id, isbn, isbn13, authors, genres, rating, page_count)
game_metadata (product_id, steam_app_id, metacritic_score, genres, tags, achievements_count)
sync_metadata (id, last_sync_timestamp, sync_status, products_synced, products_failed, sync_duration_ms)
```

### Error Handling and Recovery

1. **Authentication Errors**:
   - Automatic retry with exponential backoff
   - Session invalidation and cleanup on persistent failures
   - MFA retry mechanism with user guidance
   - Fallback to new login on session restoration failure

2. **API Errors**:
   - Rate limiting with request queuing
   - Gamekey batch retry on partial failures
   - Network timeout handling with configurable limits
   - JSON parsing error recovery

3. **Database Errors**:
   - Transaction rollback on operation failures
   - Schema validation and automatic repair
   - Duplicate handling with upsert operations
   - Comprehensive error logging with context

## Configuration

### Environment Variables

```env
# Database
DATABASE_PATH=humble_bundle.duckdb

# Humble Bundle credentials
HUMBLE_EMAIL=your_email@example.com
HUMBLE_PASSWORD=your_password

# Session management
SESSION_CACHE_PATH=.session_cache

# Sync settings
SYNC_INTERVAL_HOURS=24
MAX_RETRIES=3
REQUEST_TIMEOUT=30
REQUESTS_PER_MINUTE=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=humble_sync.log
```

### Session Security

- All session data encrypted with Fernet symmetric encryption
- Session signatures prevent tampering
- Automatic key generation and secure storage
- Session expiry validation with cookie lifetime tracking
- Clean session invalidation on logout

## Performance Optimizations

1. **Batch Processing**:
   - Gamekey batching (35 keys per API request)
   - Parallel processing for independent operations
   - Progress tracking with rich console output

2. **Caching Strategy**:
   - Persistent session caching with signature validation
   - Metadata caching to avoid redundant API calls
   - Database connection pooling with context managers

3. **Rate Limiting**:
   - Configurable requests per minute (default: 30)
   - Automatic throttling with sleep intervals
   - Request queue management during high load

## Testing and Debugging

### Debug Scripts

- `debug_library.py`: Page structure analysis and HAR capture
- `debug_*_structure.py`: HTML element discovery and content analysis
- `capture_*.py`: Network traffic capture and API discovery
- `test_*.py`: Authentication flow and integration testing

### Logging

- Comprehensive logging with multiple levels (DEBUG, INFO, WARNING, ERROR)
- Separate log files for different components
- Performance metrics and timing information
- Error context with stack traces and request details

## Known Limitations and Future Improvements

1. **Current Limitations**:
   - Requires Chrome WebDriver for authentication
   - Limited to Humble Bundle as data source
   - No automated gamekey discovery beyond JavaScript variables
   - Session persistence dependent on cookie lifetime

2. **Planned Improvements**:
   - Support for additional bundle platforms (Steam, GOG)
   - Enhanced metadata enrichment from external sources
   - Web-based dashboard for library management
   - Automated download management and organization
   - API endpoint discovery automation

## Usage Examples

### Basic Synchronization

```python
from scripts.sync import HumbleBundleSync

sync = HumbleBundleSync()
result = sync.sync(force=True)

print(f"Status: {result['status']}")
print(f"Products synced: {result['products_synced']}")
print(f"Products failed: {result['products_failed']}")
```

### Session Management

```python
from scripts.persistent_session_auth import PersistentSessionAuth

auth = PersistentSessionAuth()
success = auth.login(email="user@example.com", password="password")

if success:
    driver = auth.get_authenticated_session()
    # Use authenticated driver for operations
```

### Database Operations

```python
from database import HumbleBundleDatabase

with HumbleBundleDatabase() as db:
    stats = db.get_library_stats()
    products = db.search_products("python", category="ebook", limit=10)
    last_sync = db.get_last_sync()
```

## Security Considerations

1. **Credential Protection**:
   - Environment variable storage for sensitive data
   - No hardcoded credentials in source code
   - Encrypted session storage with secure key management

2. **Network Security**:
   - HTTPS-only communication with Humble Bundle
   - Certificate validation for all requests
   - Rate limiting to prevent abuse detection

3. **Data Privacy**:
   - Local database storage (no cloud transmission)
   - User-controlled data retention policies
   - Option to exclude sensitive metadata fields

This application represents a complete, production-ready solution for Humble Bundle library synchronization with robust error handling, security features, and comprehensive metadata extraction capabilities.