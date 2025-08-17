# Technical Documentation

This document provides comprehensive technical details about the Humble Bundle Inventory Manager implementation, including architecture, database design, API interfaces, and development guidelines.

## 🏗️ System Architecture

### High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface<br/>main.py]
        CONFIG[Configuration<br/>config.py]
        AUTH_UI[Authentication UI]
    end
    
    subgraph "Core Abstraction Frameworks"
        SF[Sync Framework<br/>sync_framework.py]
        CE[Categorization Engine<br/>categorization_engine.py]
        WSF[Web Scraping Framework<br/>web_scraping_framework.py]
    end
    
    subgraph "Implementation Layer"
        AUTH[HumbleBundleAuthSelenium<br/>auth_selenium.py]
        SYNC[EnhancedHumbleBundleSync<br/>enhanced_sync.py]
        DB[AssetInventoryDatabase<br/>database.py]
        SEARCH[DuckDBSearchProvider<br/>duckdb_search_provider.py]
    end
    
    subgraph "External Systems"
        HB[Humble Bundle<br/>Library & API]
        SELENIUM[Selenium<br/>WebDriver]
        DUCKDB[DuckDB<br/>Database Engine]
    end
    
    subgraph "Data Storage"
        SCHEMA[Database Schema<br/>schema.sql]
        SESSIONS[Session Cache]
        LOGS[Log Files]
    end
    
    CLI --> SF
    CLI --> CE
    CLI --> WSF
    CLI --> CONFIG
    CLI --> AUTH_UI
    
    SF --> SYNC
    CE --> SYNC
    WSF --> SYNC
    
    SYNC --> AUTH
    SYNC --> DB
    SYNC --> HB
    
    AUTH --> SELENIUM
    AUTH --> SESSIONS
    DB --> DUCKDB
    DB --> SCHEMA
    SEARCH --> DUCKDB
    
    CLI --> SEARCH
    CLI --> DB
    
    style CLI fill:#e1f5fe
    style SF fill:#f3e5f5
    style CE fill:#e8f5e8
    style WSF fill:#fff3e0
    style AUTH fill:#ffebee
    style SYNC fill:#e3f2fd
    style DB fill:#f1f8e9
    style SEARCH fill:#fce4ec
```

### Component Interaction Architecture

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Interface
    participant SF as Sync Framework
    participant CE as Categorization Engine
    participant WSF as Web Scraping Framework
    participant AUTH as Authentication
    participant DB as Database
    participant HB as Humble Bundle
    
    User->>CLI: Execute command
    CLI->>CLI: Parse command and options
    
    alt Sync Command
        CLI->>SF: Initialize sync process
        SF->>AUTH: Check authentication status
        
        alt Session Valid
            AUTH->>SF: Return valid session
        else Session Invalid
            AUTH->>HB: Perform login
            HB->>AUTH: Return session
            AUTH->>SF: Return new session
        end
        
        SF->>WSF: Extract library data
        WSF->>HB: Navigate to library page
        HB->>WSF: Return page content
        WSF->>SF: Return extracted data
        
        SF->>CE: Categorize products
        CE->>SF: Return categorized data
        
        SF->>DB: Store processed data
        DB->>SF: Confirm storage
        
        SF->>CLI: Return sync results
        
    else Search Command
        CLI->>SEARCH: Execute search query
        SEARCH->>DB: Query database
        DB->>SEARCH: Return results
        SEARCH->>CLI: Return formatted results
    end
    
    CLI->>User: Display results
```

### Framework Responsibilities

The system is built on three core abstraction frameworks designed to reduce complexity and improve maintainability:

#### 1. Sync Framework (`sync_framework.py`)
**Architecture Pattern**: Template Method with Strategy Pattern
- **Base Class**: `BaseSyncEngine` with pluggable components
- **Components**: `SourceExtractor`, `ItemProcessor`, `DataSyncer` protocols
- **Factory**: `SyncEngineFactory` for creating configured engines

**Key Benefits**:
- Reduces complexity from 34.5 to ~8-10
- Enables easy addition of Steam, GOG, Epic Game Store
- Standardizes error handling and categorization

#### 2. Categorization Engine (`categorization_engine.py`)
**Architecture Pattern**: Strategy Pattern with Rule Engine
- **Core Class**: `CategorizationEngine` with multiple matchers
- **Rule System**: `CategoryRule` with pattern matching and weights
- **Confidence Scoring**: `CategoryResult` with confidence metrics

**Key Benefits**:
- Centralizes all categorization logic
- Supports extensible rules and ML integration
- Provides consistent confidence scoring across all sources

#### 3. Web Scraping Framework (`web_scraping_framework.py`)
**Architecture Pattern**: Template Method with Configuration-Driven Approach
- **Base Class**: `BaseWebScraper` with common automation patterns
- **Configuration**: `PageConfig` and `ExtractionRule` for declarative scraping
- **Session Management**: `ScrapingSession` for multi-page workflows

**Key Benefits**:
- Standardizes page extraction patterns
- Reduces error-prone DOM manipulation code
- Enables configuration-driven scraping

### Framework Class Relationships

```mermaid
classDiagram
    class BaseSyncEngine {
        <<abstract>>
        +extractor: SourceExtractor
        +processor: ItemProcessor
        +syncer: DataSyncer
        +sync_start_time: datetime
        +sync() SyncResult
        +_extract() List~ExtractedItem~
        +_process() List~ProcessedItem~
        +_sync() SyncResult
        +_handle_errors() None
    }
    
    class SourceExtractor {
        <<interface>>
        +authenticate() bool
        +extract_items() List~ExtractedItem~
        +get_source_info() Dict
    }
    
    class ItemProcessor {
        <<interface>>
        +process_item(item) Dict
        +categorize_item(item) CategoryConfidence
        +enhance_metadata(item) Dict
    }
    
    class DataSyncer {
        <<interface>>
        +sync_items(items) SyncResult
        +handle_conflicts(items) SyncResult
        +rollback_changes() bool
    }
    
    class EnhancedHumbleBundleSync {
        +sync_humble_bundle_enhanced() Dict
        -_extract_products_from_page() List
        -_process_page_products() Dict
        -_sync_enhanced_data() Dict
        -_handle_dynamic_content() None
    }
    
    class CategorizationEngine {
        +matchers: List~CategoryMatcher~
        +rules: List~CategoryRule~
        +categorize_item(item) CategoryResult
        +add_rule(rule) None
        +add_matcher(matcher) None
        +get_confidence_scores() Dict
    }
    
    class CategoryRule {
        +name: str
        +category: CategoryType
        +subcategory: str
        +patterns: List~str~
        +weight: float
        +field_weights: Dict
        +required_patterns: List~str~
        +exclusion_patterns: List~str~
    }
    
    class BaseWebScraper {
        <<abstract>>
        +driver: WebDriver
        +wait: WebDriverWait
        +extractor: WebElementExtractor
        +extract_from_page(config) Dict
        +_navigate_to_page(url) None
        +_wait_for_page_load(config) None
        +_handle_errors() None
    }
    
    class PageConfig {
        +url: str
        +wait_selectors: List~str~
        +extraction_rules: List~ExtractionRule~
        +javascript_setup: str
        +scroll_to_load: bool
        +wait_time: float
    }
    
    class ExtractionRule {
        +name: str
        +selector: str
        +attribute: str
        +regex_pattern: str
        +required: bool
        +multiple: bool
    }
    
    BaseSyncEngine --> SourceExtractor
    BaseSyncEngine --> ItemProcessor
    BaseSyncEngine --> DataSyncer
    EnhancedHumbleBundleSync --|> BaseSyncEngine
    CategorizationEngine --> CategoryRule
    BaseWebScraper --> PageConfig
    PageConfig --> ExtractionRule
```

## 🗄️ Database Design

### Database Schema Architecture

```mermaid
erDiagram
    asset_sources {
        varchar source_id PK
        varchar source_name
        varchar source_type
        varchar source_url
        varchar authentication_method
        timestamp last_sync_timestamp
        varchar sync_status
        timestamp created_at
        timestamp updated_at
    }
    
    bundles {
        varchar bundle_id PK
        varchar source_id FK
        varchar bundle_name
        varchar bundle_type
        timestamp purchase_date
        decimal amount_spent
        varchar currency
        varchar charity
        varchar bundle_url
        text description
        timestamp created_at
        timestamp updated_at
    }
    
    products {
        varchar product_id PK
        varchar source_id FK
        varchar human_name
        varchar machine_name
        varchar category
        varchar subcategory
        varchar developer
        varchar publisher
        varchar url
        text description
        varchar tags
        decimal rating
        integer rating_count
        decimal retail_price
        varchar currency
        date release_date
        varchar language
        timestamp created_at
        timestamp updated_at
    }
    
    bundle_products {
        varchar bundle_id FK
        varchar product_id FK
    }
    
    downloads {
        varchar download_id PK
        varchar product_id FK
        varchar source_id FK
        varchar platform
        varchar architecture
        varchar download_type
        varchar file_name
        bigint file_size
        varchar file_size_display
        varchar download_url
        varchar local_file_path
        varchar md5_hash
        varchar sha1_hash
        varchar download_status
        timestamp created_at
        timestamp updated_at
    }
    
    book_metadata {
        varchar product_id PK,FK
        varchar isbn
        varchar isbn13
        varchar asin
        date published_date
        integer page_count
        varchar language
        varchar authors
        varchar genres
        varchar series
        integer series_number
        varchar google_books_id
        varchar amazon_url
        varchar goodreads_url
        varchar audible_url
    }
    
    game_metadata {
        varchar product_id PK,FK
        varchar steam_app_id
        varchar gog_id
        varchar epic_id
        varchar uplay_id
        varchar origin_id
        integer metacritic_score
        decimal user_rating
        date release_date
        varchar genres
        varchar tags
        varchar supported_languages
        varchar minimum_requirements
        varchar recommended_requirements
        integer achievements_count
        boolean multiplayer
        boolean controller_support
        boolean vr_support
        boolean cloud_saves
    }
    
    software_metadata {
        varchar product_id PK,FK
        varchar version
        varchar license_type
        varchar license_key
        varchar system_requirements
        varchar supported_os
        varchar update_frequency
        timestamp last_update_check
    }
    
    personal_files {
        varchar file_id PK
        varchar source_id FK
        varchar file_path
        varchar file_name
        varchar file_type
        bigint file_size
        varchar file_size_display
        timestamp created_date
        timestamp modified_date
        varchar tags
        text description
        varchar category
        varchar subcategory
        timestamp created_at
        timestamp updated_at
    }
    
    sync_metadata {
        integer id PK
        varchar source_id FK
        timestamp last_sync_timestamp
        varchar sync_status
        integer products_synced
        integer products_failed
        integer bundles_synced
        integer bundles_failed
        text error_log
        bigint sync_duration_ms
        timestamp created_at
    }
    
    asset_sources ||--o{ bundles : "has"
    asset_sources ||--o{ products : "has"
    asset_sources ||--o{ downloads : "has"
    asset_sources ||--o{ personal_files : "has"
    asset_sources ||--o{ sync_metadata : "tracks"
    
    bundles ||--o{ bundle_products : "contains"
    products ||--o{ bundle_products : "belongs_to"
    products ||--o{ downloads : "has"
    products ||--o{ book_metadata : "has"
    products ||--o{ game_metadata : "has"
    products ||--o{ software_metadata : "has"
```

### Database Operations Flow

```mermaid
flowchart TD
    subgraph "Database Initialization"
        START[Start Application] --> CHECK_DB{Database<br/>Exists?}
        CHECK_DB -->|No| CREATE_SCHEMA[Load schema.sql]
        CHECK_DB -->|Yes| CONNECT[Connect to Database]
        CREATE_SCHEMA --> CREATE_TABLES[Create Tables]
        CREATE_TABLES --> CREATE_INDEXES[Create Indexes]
        CREATE_INDEXES --> INSERT_DATA[Insert Default Data]
        INSERT_DATA --> CREATE_VIEWS[Create Views]
        CREATE_VIEWS --> CONNECT
    end
    
    subgraph "Data Operations"
        CONNECT --> OPERATIONS{Operation Type}
        OPERATIONS -->|Sync| SYNC_OPS[Sync Operations]
        OPERATIONS -->|Search| SEARCH_OPS[Search Operations]
        OPERATIONS -->|Query| QUERY_OPS[Direct Queries]
        
        SYNC_OPS --> UPSERT[Upsert Products/Bundles]
        SEARCH_OPS --> SEARCH[Execute Search]
        QUERY_OPS --> EXECUTE[Execute SQL]
        
        UPSERT --> COMMIT[Commit Transaction]
        SEARCH --> FORMAT[Format Results]
        EXECUTE --> RETURN[Return Results]
    end
    
    subgraph "Error Handling"
        COMMIT --> SUCCESS{Success?}
        SUCCESS -->|No| ROLLBACK[Rollback Transaction]
        SUCCESS -->|Yes| LOG[Log Success]
        ROLLBACK --> LOG_ERROR[Log Error]
        LOG --> END[End Operation]
        LOG_ERROR --> END
    end
    
    style START fill:#e1f5fe
    style CREATE_SCHEMA fill:#f3e5f5
    style CONNECT fill:#e8f5e8
    style END fill:#fff3e0
```

### Key Design Principles

#### 1. Source Agnostic
- All tables reference `asset_sources` for platform identification
- Common schema supports Humble Bundle, Steam, GOG, and personal files
- Extensible for future platforms

#### 2. Normalized Structure
- Products and bundles are separate entities
- Many-to-many relationship between bundles and products
- Metadata stored in specialized tables for performance

#### 3. Search Optimization
- Strategic indexes on frequently queried fields
- Views for common query patterns
- JSON storage for flexible metadata (tags, genres, etc.)

### Database Operations

#### Connection Management
```python
class AssetInventoryDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self.conn = None
        self._ensure_database()
    
    def _ensure_database(self):
        """Initialize database connection and create tables if needed."""
        self.conn = duckdb.connect(self.db_path)
        self._create_tables()
```

#### Schema Creation
- Automatic table creation on first run
- SQL schema loaded from `schema.sql` file
- Statements executed in dependency order (tables → indexes → data → views)

## 🔐 Authentication System

### Authentication Flow Architecture

```mermaid
stateDiagram-v2
    [*] --> CheckSession
    CheckSession --> SessionValid: Session exists & valid
    CheckSession --> LoginRequired: No session or expired
    
    SessionValid --> [*]: Continue with valid session
    
    LoginRequired --> NavigateToLogin: Navigate to login page
    NavigateToLogin --> EnterCredentials: Enter email/password
    EnterCredentials --> SubmitLogin: Submit login form
    
    SubmitLogin --> CheckMFA: Check if MFA required
    CheckMFA --> MFARequired: MFA enabled
    CheckMFA --> LoginSuccess: No MFA required
    
    MFARequired --> EnterMFA: Enter MFA code
    EnterMFA --> SubmitMFA: Submit MFA code
    SubmitMFA --> ValidateMFA: Validate MFA
    
    ValidateMFA --> LoginSuccess: MFA valid
    ValidateMFA --> MFAError: MFA invalid
    MFAError --> EnterMFA: Retry MFA
    
    LoginSuccess --> SaveSession: Save session data
    SaveSession --> EncryptSession: Encrypt session
    EncryptSession --> StoreSession: Store encrypted session
    StoreSession --> [*]: Session ready
    
    LoginRequired --> LoginError: Login failed
    LoginError --> [*]: Exit with error
```

### Selenium-Based Authentication
The system uses Selenium WebDriver for Humble Bundle authentication:

```python
class HumbleBundleAuthSelenium:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.session_file = settings.session_cache_dir / "humble_session.pkl"
    
    def login(self) -> bool:
        """Authenticate with Humble Bundle."""
        # Implementation details...
    
    def has_valid_session(self) -> bool:
        """Check if existing session is still valid."""
        # Implementation details...
```

### Session Management
- **Encrypted Storage**: Sessions stored using Fernet encryption
- **Automatic Renewal**: Sessions auto-refresh when possible
- **MFA Support**: Full support for multi-factor authentication
- **Fallback Handling**: Graceful degradation when authentication fails

### Security Features
- **Credential Encryption**: Passwords encrypted before storage
- **Session Isolation**: Separate session files per user
- **HTTPS Enforcement**: All requests use secure connections
- **Rate Limiting**: Respectful API usage to avoid blocking

## 🔄 Synchronization Engine

### Sync Process Architecture

```mermaid
flowchart TD
    subgraph "Sync Initialization"
        START[Start Sync] --> CHECK_AUTH{Check<br/>Authentication}
        CHECK_AUTH -->|Valid| USE_SESSION[Use Existing Session]
        CHECK_AUTH -->|Invalid| LOGIN[Perform Login]
        LOGIN --> USE_SESSION
    end
    
    subgraph "Data Extraction"
        USE_SESSION --> NAVIGATE[Navigate to Library]
        NAVIGATE --> WAIT_CONTENT[Wait for Content]
        WAIT_CONTENT --> EXTRACT[Extract Product Data]
        EXTRACT --> PROCESS[Process Raw Data]
    end
    
    subgraph "Data Processing"
        PROCESS --> CATEGORIZE[Categorize Products]
        CATEGORIZE --> ENHANCE[Enhance Metadata]
        ENHANCE --> VALIDATE[Validate Data]
    end
    
    subgraph "Data Storage"
        VALIDATE --> PREPARE_DB[Prepare Database]
        PREPARE_DB --> STORE[Store Data]
        STORE --> UPDATE_METADATA[Update Sync Metadata]
        UPDATE_METADATA --> LOG_RESULTS[Log Results]
    end
    
    subgraph "Error Handling"
        LOG_RESULTS --> CHECK_ERRORS{Errors?}
        CHECK_ERRORS -->|Yes| HANDLE_ERRORS[Handle Errors]
        CHECK_ERRORS -->|No| SUCCESS[Sync Success]
        HANDLE_ERRORS --> PARTIAL[Partial Success]
    end
    
    style START fill:#e1f5fe
    style SUCCESS fill:#e8f5e8
    style PARTIAL fill:#fff3e0
    style HANDLE_ERRORS fill:#ffebee
```

### Enhanced Sync Implementation
The primary sync engine uses HAR analysis insights for enhanced metadata extraction:

```python
class EnhancedHumbleBundleSync:
    def __init__(self, auth: HumbleBundleAuthSelenium, db: AssetInventoryDatabase):
        self.auth = auth
        self.db = db
        self.driver = None
        self.user_data = None
        self.api_data = {}
    
    def sync_humble_bundle_enhanced(self) -> Dict[str, Any]:
        """Enhanced sync extracting products directly from the library page."""
        # Implementation details...
```

### Sync Process Flow
1. **Authentication**: Verify or establish Humble Bundle session
2. **Navigation**: Navigate to library page with dynamic content handling
3. **Extraction**: Extract product data using configured selectors
4. **Processing**: Categorize and enhance extracted data
5. **Storage**: Store processed data in DuckDB database
6. **Metadata**: Record sync statistics and error logs

### Error Handling and Recovery
- **Network Resilience**: Automatic retry with exponential backoff
- **Partial Success**: Continue processing on individual item failures
- **Error Logging**: Comprehensive error tracking and reporting
- **Graceful Degradation**: Fallback to alternative extraction methods

## 🔍 Search System

### Search Architecture Overview

```mermaid
graph TB
    subgraph "Search Interface"
        CLI[CLI Commands]
        BASIC[Basic Search]
        ADVANCED[Advanced Search]
        FIELD[Field-Specific]
    end
    
    subgraph "Search Provider Layer"
        SP[SearchProvider Interface]
        DUCKDB[DuckDBSearchProvider]
        QUERY_BUILDER[Query Builder]
    end
    
    subgraph "Database Layer"
        DB[DuckDB Engine]
        INDEXES[Search Indexes]
        VIEWS[Optimized Views]
    end
    
    subgraph "Data Sources"
        PRODUCTS[Products Table]
        METADATA[Metadata Tables]
        BUNDLES[Bundles Table]
    end
    
    CLI --> BASIC
    CLI --> ADVANCED
    CLI --> FIELD
    
    BASIC --> SP
    ADVANCED --> SP
    FIELD --> SP
    
    SP --> DUCKDB
    DUCKDB --> QUERY_BUILDER
    QUERY_BUILDER --> DB
    
    DB --> INDEXES
    DB --> VIEWS
    DB --> PRODUCTS
    DB --> METADATA
    DB --> BUNDLES
    
    style CLI fill:#e1f5fe
    style SP fill:#f3e5f5
    style DUCKDB fill:#e8f5e8
    style DB fill:#fff3e0
```

### Search Provider Interface
Abstract interface for search implementations:

```python
class SearchProvider(ABC):
    @abstractmethod
    def search_assets(self, query: str, filters: Optional[Dict[str, Any]] = None,
                     use_regex: bool = False, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search assets using text or regex patterns."""
        pass
    
    @abstractmethod
    def search_by_field(self, field: str, query: str, use_regex: bool = False,
                       case_sensitive: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search assets by specific field."""
        pass
```

### DuckDB Implementation
Concrete implementation using DuckDB's SQL capabilities:

```python
class DuckDBSearchProvider(SearchProvider):
    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        self.conn = db_connection
        self.searchable_fields = [
            'human_name', 'description', 'category', 'subcategory', 
            'developer', 'publisher', 'tags', 'bundle_name'
        ]
    
    def search_assets(self, query: str, filters: Optional[Dict[str, Any]] = None,
                     use_regex: bool = False, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search assets using text or regex patterns."""
        if use_regex:
            return self._search_with_regex(query, filters, case_sensitive)
        else:
            return self._search_with_text(query, filters)
```

### Search Features
- **Regex Support**: Full regex pattern matching with compilation
- **Field-Specific Search**: Search within specific database fields
- **Advanced Search**: Multi-field queries with AND/OR operators
- **Filtering**: Category, source, platform, and rating filters
- **Pagination**: Efficient handling of large result sets
- **Export Formats**: JSON, CSV, TSV, and table output

## 🎯 Categorization System

### Categorization Architecture

```mermaid
flowchart TD
    subgraph "Input Processing"
        INPUT[Product Data] --> EXTRACT[Extract Features]
        EXTRACT --> NORMALIZE[Normalize Text]
        NORMALIZE --> PREPARE[Prepare for Matching]
    end
    
    subgraph "Rule Matching"
        PREPARE --> APPLY_RULES[Apply Category Rules]
        APPLY_RULES --> PATTERN_MATCH[Pattern Matching]
        PATTERN_MATCH --> SCORE[Calculate Scores]
    end
    
    subgraph "Confidence Scoring"
        SCORE --> WEIGHT[Apply Weights]
        WEIGHT --> COMBINE[Combine Scores]
        COMBINE --> RANK[Rank Categories]
    end
    
    subgraph "Result Selection"
        RANK --> SELECT[Select Best Category]
        SELECT --> VALIDATE[Validate Result]
        VALIDATE --> OUTPUT[Output Category]
    end
    
    style INPUT fill:#e1f5fe
    style APPLY_RULES fill:#f3e5f5
    style SCORE fill:#e8f5e8
    style OUTPUT fill:#fff3e0
```

### Rule-Based Categorization
The categorization engine uses pattern matching with confidence scoring:

```python
@dataclass
class CategoryRule:
    name: str
    category: CategoryType
    subcategory: str
    patterns: List[str]
    weight: float
    field_weights: Dict[str, float]
    required_patterns: List[str] = None
    exclusion_patterns: List[str] = None

@dataclass
class CategoryResult:
    category: CategoryType
    subcategory: str
    confidence: float
    method: str
    matched_rules: List[str]
    scores: Dict[str, float]
```

### Categorization Process
1. **Pattern Compilation**: Pre-compile regex patterns for performance
2. **Rule Matching**: Apply rules with field-specific weights
3. **Confidence Scoring**: Calculate confidence based on pattern matches
4. **Result Selection**: Choose category with highest confidence
5. **Fallback Handling**: Default categorization for low-confidence results

### Extensibility
- **Custom Rules**: Add new categorization patterns
- **Weight Adjustment**: Fine-tune categorization accuracy
- **ML Integration**: Ready for machine learning-based categorization
- **Hierarchical Support**: Categories and subcategories

## 🌐 Web Scraping Framework

### Web Scraping Architecture

```mermaid
graph TB
    subgraph "Configuration Layer"
        PAGE_CONFIG[PageConfig]
        EXTRACTION_RULES[ExtractionRule]
        SCRAPING_CONFIG[Scraping Configuration]
    end
    
    subgraph "Web Scraping Engine"
        BASE_SCRAPER[BaseWebScraper]
        ELEMENT_EXTRACTOR[WebElementExtractor]
        SESSION_MANAGER[Session Manager]
    end
    
    subgraph "Browser Automation"
        WEBDRIVER[Selenium WebDriver]
        WAIT_STRATEGIES[Wait Strategies]
        ERROR_HANDLING[Error Handling]
    end
    
    subgraph "Data Processing"
        EXTRACTED_DATA[Extracted Data]
        VALIDATION[Data Validation]
        FORMATTING[Data Formatting]
    end
    
    PAGE_CONFIG --> BASE_SCRAPER
    EXTRACTION_RULES --> BASE_SCRAPER
    SCRAPING_CONFIG --> BASE_SCRAPER
    
    BASE_SCRAPER --> ELEMENT_EXTRACTOR
    BASE_SCRAPER --> SESSION_MANAGER
    
    ELEMENT_EXTRACTOR --> WEBDRIVER
    SESSION_MANAGER --> WEBDRIVER
    
    WEBDRIVER --> WAIT_STRATEGIES
    WEBDRIVER --> ERROR_HANDLING
    
    WEBDRIVER --> EXTRACTED_DATA
    EXTRACTED_DATA --> VALIDATION
    VALIDATION --> FORMATTING
    
    style PAGE_CONFIG fill:#e1f5fe
    style BASE_SCRAPER fill:#f3e5f5
    style WEBDRIVER fill:#e8f5e8
    style FORMATTING fill:#fff3e0
```

### Configuration-Driven Approach
The framework uses declarative configuration for web scraping:

```python
@dataclass
class PageConfig:
    url: str
    wait_selectors: List[str]
    extraction_rules: List[ExtractionRule]
    javascript_setup: Optional[str] = None
    scroll_to_load: bool = False
    wait_time: float = 3.0

@dataclass
class ExtractionRule:
    name: str
    selector: str
    attribute: Optional[str] = None
    regex_pattern: Optional[str] = None
    required: bool = True
    multiple: bool = False
```

### Automation Patterns
- **Dynamic Content**: Handle JavaScript-heavy pages
- **Lazy Loading**: Scroll to trigger content loading
- **Error Recovery**: Graceful handling of element failures
- **Session Management**: Persistent browser sessions

## ⚙️ Configuration Management

### Configuration Architecture

```mermaid
graph TB
    subgraph "Configuration Sources"
        ENV[Environment Variables]
        ENV_FILE[.env File]
        DEFAULTS[Default Values]
        CLI_ARGS[CLI Arguments]
    end
    
    subgraph "Configuration Processing"
        PYDANTIC[Pydantic Settings]
        VALIDATION[Configuration Validation]
        MERGE[Merge Sources]
    end
    
    subgraph "Configuration Storage"
        SETTINGS[Settings Object]
        CACHE[Configuration Cache]
        HOT_RELOAD[Hot Reload Support]
    end
    
    subgraph "Application Usage"
        APP_CONFIG[Application Config]
        FEATURE_FLAGS[Feature Flags]
        RUNTIME_CONFIG[Runtime Configuration]
    end
    
    ENV --> PYDANTIC
    ENV_FILE --> PYDANTIC
    DEFAULTS --> PYDANTIC
    CLI_ARGS --> PYDANTIC
    
    PYDANTIC --> VALIDATION
    VALIDATION --> MERGE
    MERGE --> SETTINGS
    
    SETTINGS --> CACHE
    SETTINGS --> HOT_RELOAD
    SETTINGS --> APP_CONFIG
    
    APP_CONFIG --> FEATURE_FLAGS
    APP_CONFIG --> RUNTIME_CONFIG
    
    style ENV fill:#e1f5fe
    style PYDANTIC fill:#f3e5f5
    style SETTINGS fill:#e8f5e8
    style APP_CONFIG fill:#fff3e0
```

### Pydantic Settings
Configuration managed using Pydantic with environment variable support:

```python
class Settings(BaseSettings):
    # Database configuration
    database_path: str = "~/.humble_bundle_inventory/humble_bundle.duckdb"
    
    # Authentication configuration
    humble_email: Optional[str] = None
    humble_password: Optional[str] = None
    
    # Sync configuration
    sync_interval_hours: int = 24
    requests_per_minute: int = 30
    
    # Logging configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Environment Variables
- **HUMBLE_EMAIL**: Humble Bundle account email
- **HUMBLE_PASSWORD**: Humble Bundle account password
- **DATABASE_PATH**: Custom database file location
- **LOG_LEVEL**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### File System Integration
The system integrates with the local file system:

```python
# Integration with file system
def ensure_user_directories():
    # Integrates with user home directory
    # Integrates with configuration directory
    # Integrates with database directory
    # Integrates with session cache directory
    # Integrates with log directory
```

**Integration Points**:
- **User Directories**: Integrates with user home directory
- **Configuration Storage**: Integrates with config file storage
- **Database Storage**: Integrates with database file storage
- **Session Cache**: Integrates with session file storage
- **Log Storage**: Integrates with log file storage

## 📊 Performance and Optimization

### Performance Architecture

```mermaid
graph TB
    subgraph "Database Optimization"
        INDEXES[Strategic Indexes]
        QUERY_OPT[Query Optimization]
        MEMORY_MGMT[Memory Management]
        BATCH_OPS[Batch Operations]
    end
    
    subgraph "Search Optimization"
        PATTERN_COMP[Pattern Compilation]
        RESULT_CACHE[Result Caching]
        FIELD_INDEX[Field Indexing]
        PAGINATION[Efficient Pagination]
    end
    
    subgraph "Sync Performance"
        INCREMENTAL[Incremental Updates]
        PARALLEL[Parallel Processing]
        RATE_LIMIT[Rate Limiting]
        ERROR_RECOVERY[Fast Recovery]
    end
    
    subgraph "Memory Management"
        DUCKDB_MEM[DuckDB Memory]
        SESSION_CACHE[Session Cache]
        RESULT_BUFFER[Result Buffer]
        GARBAGE_COLL[Garbage Collection]
    end
    
    style INDEXES fill:#e1f5fe
    style PATTERN_COMP fill:#f3e5f5
    style INCREMENTAL fill:#e8f5e8
    style DUCKDB_MEM fill:#fff3e0
```

### DuckDB Advantages
- **Analytical Queries**: Optimized for complex aggregations and joins
- **Columnar Storage**: Efficient for large datasets and analytical workloads
- **Indexing**: Strategic indexes for common query patterns
- **Memory Management**: Intelligent memory usage and caching

### Search Optimization
- **Field Indexing**: Primary fields indexed for fast retrieval
- **Regex Optimization**: Compiled patterns for efficient matching
- **Result Caching**: Cached results for repeated queries
- **Pagination**: Efficient handling of large result sets

### Sync Performance
- **Incremental Updates**: Only processes changed data
- **Batch Operations**: Efficient database operations
- **Rate Limiting**: Respects API limits and server resources
- **Error Recovery**: Graceful handling of network issues

## 🧪 Testing Strategy

### Testing Architecture

```mermaid
graph TB
    subgraph "Test Types"
        UNIT[Unit Tests]
        INTEGRATION[Integration Tests]
        E2E[End-to-End Tests]
        PERFORMANCE[Performance Tests]
    end
    
    subgraph "Test Framework"
        PYTEST[Pytest Framework]
        COVERAGE[Coverage Measurement]
        MOCKING[Mocking & Stubbing]
        FIXTURES[Test Fixtures]
    end
    
    subgraph "Test Execution"
        CI_CD[CI/CD Pipeline]
        PARALLEL[Parallel Execution]
        REPORTING[Test Reporting]
        FAILURE_ANALYSIS[Failure Analysis]
    end
    
    subgraph "Test Data"
        MOCK_DATA[Mock Data]
        TEST_DB[Test Database]
        SAMPLE_FILES[Sample Files]
        ENV_SETUP[Environment Setup]
    end
    
    UNIT --> PYTEST
    INTEGRATION --> PYTEST
    E2E --> PYTEST
    PERFORMANCE --> PYTEST
    
    PYTEST --> COVERAGE
    PYTEST --> MOCKING
    PYTEST --> FIXTURES
    
    PYTEST --> CI_CD
    PYTEST --> PARALLEL
    PYTEST --> REPORTING
    
    MOCKING --> MOCK_DATA
    FIXTURES --> TEST_DB
    INTEGRATION --> SAMPLE_FILES
    E2E --> ENV_SETUP
    
    style UNIT fill:#e1f5fe
    style PYTEST fill:#f3e5f5
    style CI_CD fill:#e8f5e8
    style MOCK_DATA fill:#fff3e0
```

### Test Coverage
Current test coverage: **64%** with comprehensive integration testing

### Test Types
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Authentication Tests**: Login and session management
- **Search Tests**: Search functionality validation
- **Sync Tests**: Synchronization process validation

### Test Framework
- **Pytest**: Primary testing framework
- **Coverage**: Test coverage measurement
- **Mocking**: External dependency isolation
- **Fixtures**: Reusable test data and setup

## 🚧 Technical Debt Status

### Technical Debt Overview

```mermaid
graph TB
    subgraph "Current Issues"
        HIGH_COMPLEXITY[92 High Complexity<br/>Functions]
        FRAMEWORK_MIGRATION[Framework Migration<br/>In Progress]
        TEST_COVERAGE[64% Test Coverage<br/>Target: 85%+]
        ERROR_HANDLING[Inconsistent Error<br/>Handling]
    end
    
    subgraph "Improvement Areas"
        COMPLEXITY_REDUCTION[Reduce Function<br/>Complexity]
        FRAMEWORK_INTEGRATION[Complete Framework<br/>Integration]
        TEST_ENHANCEMENT[Improve Test<br/>Coverage]
        PERFORMANCE_OPT[Performance<br/>Optimization]
    end
    
    subgraph "Success Metrics"
        COMPLEXITY_TARGET[<30 High Complexity<br/>Functions]
        FRAMEWORK_TARGET[100% Framework<br/>Adoption]
        COVERAGE_TARGET[85%+ Test<br/>Coverage]
        PERFORMANCE_TARGET[<10% Overhead<br/>from Frameworks]
    end
    
    HIGH_COMPLEXITY --> COMPLEXITY_REDUCTION
    FRAMEWORK_MIGRATION --> FRAMEWORK_INTEGRATION
    TEST_COVERAGE --> TEST_ENHANCEMENT
    ERROR_HANDLING --> PERFORMANCE_OPT
    
    COMPLEXITY_REDUCTION --> COMPLEXITY_TARGET
    FRAMEWORK_INTEGRATION --> FRAMEWORK_TARGET
    TEST_ENHANCEMENT --> COVERAGE_TARGET
    PERFORMANCE_OPT --> PERFORMANCE_TARGET
    
    style HIGH_COMPLEXITY fill:#ffebee
    style COMPLEXITY_TARGET fill:#e8f5e8
    style FRAMEWORK_TARGET fill:#e8f5e8
    style COVERAGE_TARGET fill:#e8f5e8
```

### Current Issues
- **High Complexity**: 92 high-complexity functions identified
- **Framework Migration**: In progress - reducing complexity from 34.5 to ~8-10
- **Test Coverage**: Target: 85%+ (currently 64%)

### Improvement Areas
1. **Framework Integration**: Complete migration to abstraction frameworks
2. **Complexity Reduction**: Refactor high-complexity functions
3. **Test Enhancement**: Improve test coverage and quality
4. **Performance Optimization**: Database and search optimization
5. **Error Handling**: Comprehensive error handling and recovery

### Success Metrics
- **Complexity Reduction**: 60%+ improvement in affected modules
- **Test Coverage**: Achieve 85%+ coverage
- **Performance**: <10% overhead from abstraction layers
- **Maintainability**: Reduced code duplication and complexity

## 🔮 Future Enhancements

### Planned Features
1. **Multi-Platform Support**: Steam, GOG, Epic Games Store integration
2. **Advanced Analytics**: Spending analysis and recommendation engine
3. **Machine Learning**: ML-based categorization and insights
4. **API Interface**: REST API for external integrations
5. **Web Dashboard**: Web-based user interface

### Architecture Evolution
1. **Microservices**: Potential migration to microservices architecture
2. **Cloud Integration**: Cloud-based storage and processing
3. **Real-time Sync**: WebSocket-based real-time updates
4. **Distributed Processing**: Multi-node processing for large libraries

## 📚 Development Guidelines

### Code Quality Standards
- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **MyPy**: Type checking
- **Pytest**: Testing framework

### Architecture Principles
1. **SOLID Principles**: Single responsibility, open/closed, etc.
2. **DRY Principle**: Don't repeat yourself
3. **Separation of Concerns**: Clear module boundaries
4. **Dependency Injection**: Loose coupling between components

### Documentation Standards
- **Docstrings**: Comprehensive function and class documentation
- **Type Hints**: Python type annotations
- **Examples**: Usage examples in documentation
- **Architecture Decision Records**: Documented design decisions

## 🔗 Related Documentation

- **[Main README](../README.md)** - Project overview and quick start
- **[Detailed Documentation](README.md)** - Comprehensive user guide
- **[Search Examples](search_examples.md)** - Search functionality guide
- **[Architectural Decision Records](adr/)** - Design decision rationale
- **[Complexity Analysis](CYCLOMATIC_COMPLEXITY_ANALYSIS.md)** - Code quality metrics
- **[Integration Summary](INTEGRATION_SUMMARY.md)** - System integration details 