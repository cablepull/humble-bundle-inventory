import duckdb
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from .config import settings

class AssetInventoryDatabase:
    """Database operations for multi-source digital asset inventory management."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self.conn = None
        self._ensure_database()
    
    def _ensure_database(self):
        """Initialize database connection and create tables if needed."""
        self.conn = duckdb.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables from schema."""
        # Check if tables already exist
        try:
            result = self.conn.execute("SHOW TABLES")
            existing_tables = result.fetchall()
            if existing_tables:
                # Tables already exist, skip creation
                return
        except Exception:
            # No tables exist, proceed with creation
            pass
        
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            
            # Remove comment lines and clean up for proper statement parsing
            lines = schema_sql.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('--'):
                    clean_lines.append(line)
            
            # Join clean lines and split by semicolon
            clean_schema = '\n'.join(clean_lines)
            statements = [stmt.strip() for stmt in clean_schema.split(';') if stmt.strip()]
            
            print(f"🗄️  Creating database schema with {len(statements)} statements...")
            
            # Group statements by type and execute in correct order
            create_table_statements = []
            create_index_statements = []
            insert_statements = []
            create_view_statements = []
            
            for statement in statements:
                # Clean up the statement - remove leading/trailing whitespace and normalize
                clean_statement = statement.strip()
                if clean_statement.upper().startswith('CREATE TABLE'):
                    create_table_statements.append(clean_statement)
                elif clean_statement.upper().startswith('CREATE INDEX'):
                    create_index_statements.append(clean_statement)
                elif clean_statement.upper().startswith('INSERT INTO'):
                    insert_statements.append(clean_statement)
                elif clean_statement.upper().startswith('CREATE VIEW'):
                    create_view_statements.append(clean_statement)
            
            print(f"   📋 CREATE TABLE statements: {len(create_table_statements)}")
            print(f"   🔍 CREATE INDEX statements: {len(create_index_statements)}")
            print(f"   📥 INSERT statements: {len(insert_statements)}")
            print(f"   👁️  CREATE VIEW statements: {len(create_view_statements)}")
            
            # Execute CREATE TABLE statements first
            print("\n   🔄 Creating tables...")
            for i, statement in enumerate(create_table_statements):
                try:
                    print(f"      🔄 Creating table {i+1}...")
                    self.conn.execute(statement)
                    print(f"      ✅ Table {i+1} created successfully")
                except Exception as e:
                    print(f"      ❌ Table {i+1} failed: {e}")
                    print(f"         Statement: {statement[:100]}...")
                    return  # Stop on first table creation failure
            
            # Execute CREATE INDEX statements
            print("\n   🔄 Creating indexes...")
            for i, statement in enumerate(create_index_statements):
                try:
                    self.conn.execute(statement)
                    print(f"      ✅ Index {i+1} created successfully")
                except Exception as e:
                    print(f"      ❌ Index {i+1} failed: {e}")
                    print(f"         Statement: {statement[:100]}...")
            
            # Execute INSERT statements
            print("\n   🔄 Inserting data...")
            for i, statement in enumerate(insert_statements):
                try:
                    self.conn.execute(statement)
                    print(f"      ✅ Insert {i+1} executed successfully")
                except Exception as e:
                    print(f"      ❌ Insert {i+1} failed: {e}")
                    print(f"         Statement: {statement[:100]}...")
            
            # Execute CREATE VIEW statements
            print("\n   🔄 Creating views...")
            for i, statement in enumerate(create_view_statements):
                try:
                    self.conn.execute(statement)
                    print(f"      ✅ View {i+1} created successfully")
                except Exception as e:
                    print(f"      ❌ View {i+1} failed: {e}")
                    print(f"         Statement: {statement[:100]}...")
            
            print("✅ Database schema created successfully")
        else:
            print("Warning: schema.sql not found")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def upsert_asset_source(self, source_data: Dict[str, Any]) -> None:
        """Insert or update asset source data."""
        sql = """
        INSERT OR REPLACE INTO asset_sources 
        (source_id, source_name, source_type, source_url, authentication_method, 
         last_sync_timestamp, sync_status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            source_data['source_id'],
            source_data['source_name'],
            source_data['source_type'],
            source_data.get('source_url'),
            source_data.get('authentication_method'),
            source_data.get('last_sync_timestamp'),
            source_data.get('sync_status', 'inactive'),
            datetime.now()
        ))
    
    def upsert_bundle(self, bundle_data: Dict[str, Any]) -> None:
        """Insert or update bundle data."""
        sql = """
        INSERT OR REPLACE INTO bundles 
        (bundle_id, source_id, bundle_name, bundle_type, purchase_date, amount_spent, 
         currency, charity, bundle_url, description, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            bundle_data['bundle_id'],
            bundle_data.get('source_id', 'humble_bundle'),  # Default to humble_bundle for backward compatibility
            bundle_data['bundle_name'],
            bundle_data['bundle_type'],
            bundle_data.get('purchase_date'),
            bundle_data.get('amount_spent', 0),
            bundle_data.get('currency', 'USD'),
            bundle_data.get('charity'),
            bundle_data.get('bundle_url'),
            bundle_data.get('description'),
            datetime.now()
        ))
    
    def upsert_product(self, product_data: Dict[str, Any]) -> None:
        """Insert or update product data."""
        sql = """
        INSERT OR REPLACE INTO products 
        (product_id, source_id, human_name, machine_name, category, subcategory, developer, 
         publisher, url, description, tags, rating, rating_count, retail_price, currency, 
         release_date, language, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            product_data['product_id'],
            product_data.get('source_id', 'humble_bundle'),  # Default to humble_bundle for backward compatibility
            product_data['human_name'],
            product_data.get('machine_name'),
            product_data.get('category'),
            product_data.get('subcategory'),
            product_data.get('developer'),
            product_data.get('publisher'),
            product_data.get('url'),
            product_data.get('description'),
            product_data.get('tags', []),
            product_data.get('rating'),
            product_data.get('rating_count'),
            product_data.get('retail_price'),
            product_data.get('currency', 'USD'),
            product_data.get('release_date'),
            product_data.get('language'),
            datetime.now()
        ))
    
    def link_bundle_product(self, bundle_id: str, product_id: str) -> None:
        """Create or update bundle-product relationship."""
        sql = """
        INSERT OR IGNORE INTO bundle_products (bundle_id, product_id)
        VALUES (?, ?)
        """
        self.conn.execute(sql, (bundle_id, product_id))
    
    def upsert_download(self, download_data: Dict[str, Any]) -> None:
        """Insert or update download data."""
        sql = """
        INSERT OR REPLACE INTO downloads 
        (download_id, product_id, source_id, platform, architecture, download_type, file_name, 
         file_size, file_size_display, download_url, local_file_path, md5_hash, sha1_hash, 
         download_status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            download_data['download_id'],
            download_data['product_id'],
            download_data.get('source_id', 'humble_bundle'),
            download_data.get('platform'),
            download_data.get('architecture'),
            download_data.get('download_type'),
            download_data.get('file_name'),
            download_data.get('file_size', 0),
            download_data.get('file_size_display'),
            download_data.get('download_url'),
            download_data.get('local_file_path'),
            download_data.get('md5_hash'),
            download_data.get('sha1_hash'),
            download_data.get('download_status', 'available'),
            datetime.now()
        ))
    
    def upsert_book_metadata(self, product_id: str, metadata: Dict[str, Any]) -> None:
        """Insert or update book metadata."""
        sql = """
        INSERT OR REPLACE INTO book_metadata 
        (product_id, isbn, isbn13, asin, published_date, page_count, language,
         authors, genres, series, series_number, google_books_id, amazon_url, 
         goodreads_url, audible_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            product_id,
            metadata.get('isbn'),
            metadata.get('isbn13'),
            metadata.get('asin'),
            metadata.get('published_date'),
            metadata.get('page_count'),
            metadata.get('language'),
            metadata.get('authors', []),
            metadata.get('genres', []),
            metadata.get('series'),
            metadata.get('series_number'),
            metadata.get('google_books_id'),
            metadata.get('amazon_url'),
            metadata.get('goodreads_url'),
            metadata.get('audible_url')
        ))
    
    def upsert_game_metadata(self, product_id: str, metadata: Dict[str, Any]) -> None:
        """Insert or update game metadata."""
        sql = """
        INSERT OR REPLACE INTO game_metadata 
        (product_id, steam_app_id, gog_id, epic_id, uplay_id, origin_id, metacritic_score, 
         user_rating, release_date, genres, tags, supported_languages, minimum_requirements, 
         recommended_requirements, achievements_count, multiplayer, controller_support, 
         vr_support, cloud_saves)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            product_id,
            metadata.get('steam_app_id'),
            metadata.get('gog_id'),
            metadata.get('epic_id'),
            metadata.get('uplay_id'),
            metadata.get('origin_id'),
            metadata.get('metacritic_score'),
            metadata.get('user_rating'),
            metadata.get('release_date'),
            metadata.get('genres', []),
            metadata.get('tags', []),
            metadata.get('supported_languages', []),
            json.dumps(metadata.get('minimum_requirements', {})),
            json.dumps(metadata.get('recommended_requirements', {})),
            metadata.get('achievements_count'),
            metadata.get('multiplayer', False),
            metadata.get('controller_support', False),
            metadata.get('vr_support', False),
            metadata.get('cloud_saves', False)
        ))
    
    def upsert_software_metadata(self, product_id: str, metadata: Dict[str, Any]) -> None:
        """Insert or update software metadata."""
        sql = """
        INSERT OR REPLACE INTO software_metadata 
        (product_id, version, license_type, license_key, system_requirements, 
         supported_os, update_frequency, last_update_check)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            product_id,
            metadata.get('version'),
            metadata.get('license_type'),
            metadata.get('license_key'),
            json.dumps(metadata.get('system_requirements', {})),
            metadata.get('supported_os', []),
            metadata.get('update_frequency'),
            metadata.get('last_update_check')
        ))
    
    def upsert_personal_file(self, file_data: Dict[str, Any]) -> None:
        """Insert or update personal file metadata."""
        sql = """
        INSERT OR REPLACE INTO personal_files 
        (file_id, source_id, file_path, file_name, file_type, file_size, file_size_display,
         created_date, modified_date, tags, description, category, subcategory, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            file_data['file_id'],
            file_data.get('source_id', 'personal_files'),
            file_data['file_path'],
            file_data['file_name'],
            file_data.get('file_type'),
            file_data.get('file_size'),
            file_data.get('file_size_display'),
            file_data.get('created_date'),
            file_data.get('modified_date'),
            file_data.get('tags', []),
            file_data.get('description'),
            file_data.get('category'),
            file_data.get('subcategory'),
            datetime.now()
        ))
    
    def record_sync(self, source_id: str, status: str, products_synced: int, products_failed: int,
                   bundles_synced: int = 0, bundles_failed: int = 0,
                   error_log: str = None, duration_ms: int = 0) -> None:
        """Record synchronization metadata for a specific source."""
        sql = """
        INSERT INTO sync_metadata 
        (id, source_id, last_sync_timestamp, sync_status, products_synced, products_failed,
         bundles_synced, bundles_failed, error_log, sync_duration_ms)
        VALUES (COALESCE((SELECT MAX(id) FROM sync_metadata), 0) + 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.conn.execute(sql, (
            source_id,
            datetime.now(),
            status,
            products_synced,
            products_failed,
            bundles_synced,
            bundles_failed,
            error_log,
            duration_ms
        ))
    
    def get_last_sync(self, source_id: str = None) -> Optional[Dict[str, Any]]:
        """Get information about the last sync for a specific source or overall."""
        if source_id:
            sql = """
            SELECT source_id, last_sync_timestamp, sync_status, products_synced, products_failed,
                   bundles_synced, bundles_failed
            FROM sync_metadata 
            WHERE source_id = ?
            ORDER BY last_sync_timestamp DESC 
            LIMIT 1
            """
            result = self.conn.execute(sql, (source_id,)).fetchone()
        else:
            sql = """
            SELECT source_id, last_sync_timestamp, sync_status, products_synced, products_failed,
                   bundles_synced, bundles_failed
            FROM sync_metadata 
            ORDER BY last_sync_timestamp DESC 
            LIMIT 1
            """
            result = self.conn.execute(sql).fetchone()
        
        if result:
            return {
                'source_id': result[0],
                'last_sync_timestamp': result[1],
                'sync_status': result[2],
                'products_synced': result[3],
                'products_failed': result[4],
                'bundles_synced': result[5],
                'bundles_failed': result[6]
            }
        return None
    
    def search_assets(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search assets with optional filters."""
        sql = """
        SELECT p.product_id, p.human_name, p.category, p.subcategory, p.developer, p.publisher,
               p.tags, p.rating, p.release_date, a.source_name, b.bundle_name,
               d.platform, d.download_type, d.file_size_display
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        LEFT JOIN downloads d ON p.product_id = d.product_id
        WHERE p.human_name ILIKE ? OR p.description ILIKE ?
        """
        
        params = [f'%{query}%', f'%{query}%']
        
        # Add filters
        if filters:
            if filters.get('category'):
                sql += " AND p.category = ?"
                params.append(filters['category'])
            if filters.get('source'):
                sql += " AND a.source_name = ?"
                params.append(filters['source'])
            if filters.get('platform'):
                sql += " AND d.platform = ?"
                params.append(filters['platform'])
        
        sql += " ORDER BY p.human_name"
        
        results = self.conn.execute(sql, params).fetchall()
        return [
            {
                'product_id': row[0],
                'human_name': row[1],
                'category': row[2],
                'subcategory': row[3],
                'developer': row[4],
                'publisher': row[5],
                'tags': row[6],
                'rating': row[7],
                'release_date': row[8],
                'source_name': row[9],
                'bundle_name': row[10],
                'platform': row[11],
                'download_type': row[12],
                'file_size_display': row[13]
            }
            for row in results
        ]
    
    def get_library_summary(self) -> List[Dict[str, Any]]:
        """Get summary of library by category and source."""
        sql = """
        SELECT p.category, p.subcategory, a.source_name, COUNT(*) as product_count,
               COUNT(DISTINCT b.bundle_id) as bundle_count
        FROM products p
        JOIN asset_sources a ON p.source_id = a.source_id
        LEFT JOIN bundle_products bp ON p.product_id = bp.product_id
        LEFT JOIN bundles b ON bp.bundle_id = b.bundle_id
        GROUP BY p.category, p.subcategory, a.source_name
        ORDER BY product_count DESC
        """
        
        results = self.conn.execute(sql).fetchall()
        return [
            {
                'category': row[0],
                'subcategory': row[1],
                'source_name': row[2],
                'product_count': row[3],
                'bundle_count': row[4]
            }
            for row in results
        ]
    
    def get_asset_source_status(self) -> List[Dict[str, Any]]:
        """Get status of all asset sources."""
        sql = """
        SELECT a.source_name, a.source_type, a.last_sync_timestamp, a.sync_status,
               COUNT(p.product_id) as total_products, COUNT(b.bundle_id) as total_bundles
        FROM asset_sources a
        LEFT JOIN products p ON a.source_id = p.source_id
        LEFT JOIN bundles b ON a.source_id = b.source_id
        GROUP BY a.source_name, a.source_type, a.last_sync_timestamp, a.sync_status
        ORDER BY a.last_sync_timestamp DESC
        """
        
        results = self.conn.execute(sql).fetchall()
        return [
            {
                'source_name': row[0],
                'source_type': row[1],
                'last_sync_timestamp': row[2],
                'sync_status': row[3],
                'total_products': row[4],
                'total_bundles': row[5]
            }
            for row in results
        ]

# Backward compatibility alias
HumbleBundleDatabase = AssetInventoryDatabase