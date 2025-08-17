-- DuckDB Schema for Digital Asset Inventory Management System
-- Supports multiple sources: Humble Bundle, Steam, GOG, personal files, etc.
-- Optimized for analytical queries and efficient storage

-- ============================================================================
-- CREATE TABLES (must be first)
-- ============================================================================

-- Asset sources table (Humble Bundle, Steam, GOG, personal files, etc.)
CREATE TABLE asset_sources (
    source_id VARCHAR PRIMARY KEY,
    source_name VARCHAR NOT NULL, -- 'Humble Bundle', 'Steam', 'GOG', 'Personal Files', etc.
    source_type VARCHAR NOT NULL, -- 'platform', 'personal', 'subscription', 'purchase'
    source_url VARCHAR,
    authentication_method VARCHAR, -- 'oauth', 'api_key', 'session_cookies', 'none'
    last_sync_timestamp TIMESTAMP,
    sync_status VARCHAR, -- 'active', 'inactive', 'error'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main bundles table (now source-agnostic)
CREATE TABLE bundles (
    bundle_id VARCHAR PRIMARY KEY,
    source_id VARCHAR REFERENCES asset_sources(source_id),
    bundle_name VARCHAR NOT NULL,
    bundle_type VARCHAR NOT NULL, -- 'games', 'books', 'software', 'comics', 'mixed'
    purchase_date TIMESTAMP,
    amount_spent DECIMAL(10,2),
    currency VARCHAR DEFAULT 'USD',
    charity VARCHAR,
    bundle_url VARCHAR,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table (now source-agnostic)
CREATE TABLE products (
    product_id VARCHAR PRIMARY KEY,
    source_id VARCHAR REFERENCES asset_sources(source_id),
    human_name VARCHAR NOT NULL,
    machine_name VARCHAR,
    category VARCHAR, -- 'game', 'ebook', 'audiobook', 'software', 'comic', 'video', 'audio', 'document'
    subcategory VARCHAR, -- 'rpg', 'strategy', 'programming', 'cooking', 'fiction', 'non-fiction'
    developer VARCHAR,
    publisher VARCHAR,
    url VARCHAR,
    description TEXT,
    tags VARCHAR, -- Store as JSON string for DuckDB compatibility
    rating DECIMAL(3,2), -- e.g., 4.25
    rating_count INTEGER,
    retail_price DECIMAL(10,2),
    currency VARCHAR DEFAULT 'USD',
    release_date DATE,
    language VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship between bundles and products
CREATE TABLE bundle_products (
    bundle_id VARCHAR REFERENCES bundles(bundle_id),
    product_id VARCHAR REFERENCES products(product_id),
    PRIMARY KEY (bundle_id, product_id)
);

-- Downloads table for files associated with products
CREATE TABLE downloads (
    download_id VARCHAR PRIMARY KEY,
    product_id VARCHAR REFERENCES products(product_id),
    source_id VARCHAR REFERENCES asset_sources(source_id),
    platform VARCHAR, -- 'windows', 'mac', 'linux', 'android', 'ios', 'ebook', 'audio', 'universal'
    architecture VARCHAR, -- '32-bit', '64-bit', 'universal', 'arm', 'x86'
    download_type VARCHAR, -- '.deb', '.exe', '.dmg', '.pdf', '.epub', '.mobi', '.mp3', '.mp4'
    file_name VARCHAR,
    file_size BIGINT, -- in bytes for efficient sorting/filtering
    file_size_display VARCHAR, -- human readable like "101.3 MB"
    download_url VARCHAR,
    local_file_path VARCHAR, -- for locally stored files
    md5_hash VARCHAR,
    sha1_hash VARCHAR,
    download_status VARCHAR, -- 'available', 'downloaded', 'failed', 'expired'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Book-specific metadata (for ebooks and audiobooks)
CREATE TABLE book_metadata (
    product_id VARCHAR PRIMARY KEY REFERENCES products(product_id),
    isbn VARCHAR,
    isbn13 VARCHAR,
    asin VARCHAR,
    published_date DATE,
    page_count INTEGER,
    language VARCHAR,
    authors VARCHAR, -- Store as JSON string for DuckDB compatibility
    genres VARCHAR, -- Store as JSON string for DuckDB compatibility
    series VARCHAR,
    series_number INTEGER,
    google_books_id VARCHAR,
    amazon_url VARCHAR,
    goodreads_url VARCHAR,
    audible_url VARCHAR
);

-- Game-specific metadata
CREATE TABLE game_metadata (
    product_id VARCHAR PRIMARY KEY REFERENCES products(product_id),
    steam_app_id VARCHAR,
    gog_id VARCHAR,
    epic_id VARCHAR,
    uplay_id VARCHAR,
    origin_id VARCHAR,
    metacritic_score INTEGER,
    user_rating DECIMAL(3,2),
    release_date DATE,
    genres VARCHAR, -- Store as JSON string for DuckDB compatibility
    tags VARCHAR, -- Store as JSON string for DuckDB compatibility
    supported_languages VARCHAR, -- Store as JSON string for DuckDB compatibility
    minimum_requirements VARCHAR, -- Store as JSON string
    recommended_requirements VARCHAR, -- Store as JSON string
    achievements_count INTEGER,
    multiplayer BOOLEAN DEFAULT FALSE,
    controller_support BOOLEAN DEFAULT FALSE,
    vr_support BOOLEAN DEFAULT FALSE,
    cloud_saves BOOLEAN DEFAULT FALSE
);

-- Software-specific metadata
CREATE TABLE software_metadata (
    product_id VARCHAR PRIMARY KEY REFERENCES products(product_id),
    version VARCHAR,
    license_type VARCHAR, -- 'free', 'paid', 'subscription', 'open_source'
    license_key VARCHAR,
    system_requirements VARCHAR, -- Store as JSON string
    supported_os VARCHAR, -- Store as JSON string for DuckDB compatibility
    update_frequency VARCHAR, -- 'daily', 'weekly', 'monthly', 'manual'
    last_update_check TIMESTAMP
);

-- Personal file metadata (for locally stored assets)
CREATE TABLE personal_files (
    file_id VARCHAR PRIMARY KEY,
    source_id VARCHAR REFERENCES asset_sources(source_id),
    file_path VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    file_type VARCHAR,
    file_size BIGINT,
    file_size_display VARCHAR,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    tags VARCHAR, -- Store as JSON string for DuckDB compatibility
    description TEXT,
    category VARCHAR,
    subcategory VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync metadata table for tracking synchronization state per source
CREATE TABLE sync_metadata (
    id INTEGER PRIMARY KEY,
    source_id VARCHAR REFERENCES asset_sources(source_id),
    last_sync_timestamp TIMESTAMP,
    sync_status VARCHAR, -- 'success', 'partial', 'failed'
    products_synced INTEGER,
    products_failed INTEGER,
    bundles_synced INTEGER,
    bundles_failed INTEGER,
    error_log TEXT,
    sync_duration_ms BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asset search and discovery table
CREATE TABLE asset_search (
    search_id VARCHAR PRIMARY KEY,
    search_query VARCHAR NOT NULL,
    search_filters VARCHAR, -- Store search filters as JSON string
    results_count INTEGER,
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR -- for future user management
);

-- ============================================================================
-- CREATE INDEXES (after tables are created)
-- ============================================================================

-- Indexes for performance (DuckDB compatible)
CREATE INDEX idx_asset_sources_name ON asset_sources(source_name);
CREATE INDEX idx_asset_sources_type ON asset_sources(source_type);
CREATE INDEX idx_bundles_source ON bundles(source_id);
CREATE INDEX idx_bundles_type ON bundles(bundle_type);
CREATE INDEX idx_bundles_purchase_date ON bundles(purchase_date);
CREATE INDEX idx_products_source ON products(source_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_name ON products(human_name);
CREATE INDEX idx_products_subcategory ON products(subcategory);
CREATE INDEX idx_downloads_source ON downloads(source_id);
CREATE INDEX idx_downloads_platform ON downloads(platform);
CREATE INDEX idx_downloads_product_id ON downloads(product_id);
CREATE INDEX idx_book_metadata_isbn ON book_metadata(isbn);
CREATE INDEX idx_game_metadata_genres ON game_metadata(genres);
CREATE INDEX idx_game_metadata_release_date ON game_metadata(release_date);
CREATE INDEX idx_personal_files_path ON personal_files(file_path);
CREATE INDEX idx_personal_files_type ON personal_files(file_type);
CREATE INDEX idx_sync_metadata_source ON sync_metadata(source_id);

-- ============================================================================
-- INSERT DEFAULT DATA (after tables and indexes are created)
-- ============================================================================

-- Insert default asset sources
INSERT INTO asset_sources (source_id, source_name, source_type, authentication_method, sync_status) VALUES
('humble_bundle', 'Humble Bundle', 'platform', 'session_cookies', 'active'),
('steam', 'Steam', 'platform', 'api_key', 'inactive'),
('gog', 'GOG.com', 'platform', 'api_key', 'inactive'),
('personal_files', 'Personal Files', 'personal', 'none', 'inactive'),
('epic_games', 'Epic Games Store', 'platform', 'oauth', 'inactive'),
('origin', 'Origin/EA App', 'platform', 'oauth', 'inactive'),
('uplay', 'Ubisoft Connect', 'platform', 'oauth', 'inactive');

-- ============================================================================
-- CREATE VIEWS (after all data is inserted)
-- ============================================================================

-- Views for common queries
CREATE VIEW library_summary AS
SELECT 
    p.category,
    p.subcategory,
    a.source_name,
    COUNT(*) as product_count,
    COUNT(DISTINCT b.bundle_id) as bundle_count
FROM products p
JOIN asset_sources a ON p.source_id = a.source_id
LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
LEFT JOIN bundles b ON bp.bundle_id = bp.bundle_id
GROUP BY p.category, p.subcategory, a.source_name
ORDER BY product_count DESC;

CREATE VIEW recent_purchases AS
SELECT 
    a.source_name,
    b.bundle_name,
    b.bundle_type,
    b.purchase_date,
    b.amount_spent,
    b.currency,
    COUNT(bp.product_id) as product_count
FROM bundles b
JOIN asset_sources a ON b.source_id = a.source_id
JOIN bundle_products bp ON b.bundle_id = bp.bundle_id
WHERE b.purchase_date > CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.source_name, b.bundle_id, b.bundle_name, b.bundle_type, b.purchase_date, b.amount_spent, b.currency
ORDER BY b.purchase_date DESC;

CREATE VIEW asset_source_status AS
SELECT 
    a.source_name,
    a.source_type,
    a.last_sync_timestamp,
    a.sync_status,
    COUNT(p.product_id) as total_products,
    COUNT(b.bundle_id) as total_bundles
FROM asset_sources a
LEFT JOIN products p ON a.source_id = p.source_id
LEFT JOIN bundles b ON a.source_id = b.source_id
GROUP BY a.source_name, a.source_type, a.last_sync_timestamp, a.sync_status
ORDER BY a.last_sync_timestamp DESC;

CREATE VIEW searchable_assets AS
SELECT 
    p.product_id,
    p.human_name,
    p.category,
    p.subcategory,
    p.developer,
    p.publisher,
    p.tags,
    p.rating,
    p.release_date,
    a.source_name,
    b.bundle_name,
    d.platform,
    d.download_type,
    d.file_size_display
FROM products p
JOIN asset_sources a ON p.source_id = a.source_id
LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
LEFT JOIN downloads d ON p.product_id = d.product_id
WHERE p.human_name IS NOT NULL;