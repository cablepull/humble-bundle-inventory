# Regex Search Architecture

## Overview

The Digital Asset Inventory Manager now features a **pluggable search architecture** that allows regex search capabilities to be applied to any data connector. This design makes the system extensible for future data sources while maintaining a clean separation of concerns.

## Architecture Components

### 1. SearchProvider Abstract Base Class (`src/search_provider.py`)

The `SearchProvider` abstract base class defines the interface for regex search across different data sources:

```python
class SearchProvider(ABC):
    @abstractmethod
    def search_assets(self, query: str, filters: Optional[Dict[str, Any]] = None,
                     use_regex: bool = False, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search assets using text or regex patterns."""
        pass
    
    @abstractmethod
    def search_by_field(self, field: str, query: str, use_regex: bool = False,
                       case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search assets by specific field using text or regex patterns."""
        pass
    
    @abstractmethod
    def search_advanced(self, queries: Dict[str, str], filters: Optional[Dict[str, Any]] = None,
                       use_regex: bool = False, case_sensitive: bool = False,
                       operator: str = 'AND') -> List[Dict[str, Any]]:
        """Advanced search with multiple field queries."""
        pass
```

**Key Features:**
- **Regex Validation**: Built-in regex pattern validation
- **Pattern Building**: Helper methods for building and compiling regex patterns
- **Case Sensitivity**: Support for case-sensitive and case-insensitive searches
- **Utility Methods**: Methods for escaping special characters and pattern matching

### 2. DuckDBSearchProvider Implementation (`src/duckdb_search_provider.py`)

The `DuckDBSearchProvider` implements the `SearchProvider` interface specifically for DuckDB:

```python
class DuckDBSearchProvider(SearchProvider):
    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        self.conn = db_connection
        self.searchable_fields = [
            'human_name', 'description', 'category', 'subcategory', 
            'developer', 'publisher', 'tags', 'bundle_name'
        ]
```

**Implementation Details:**
- **Hybrid Approach**: Uses SQL for text searches, Python regex for complex patterns
- **Field Mapping**: Maps database columns to searchable fields
- **Filter Support**: Comprehensive filtering by category, source, platform, rating ranges
- **Performance Optimization**: Efficient SQL queries with Python regex post-processing

## Search Capabilities

### 1. Basic Text Search
```bash
# Simple text search
python main.py search 'python'

# Case-insensitive search
python main.py search 'Python'
```

### 2. Regex Search
```bash
# Find products starting with numbers (discount percentages)
python main.py search '^\d+%' --regex

# Find products starting with capital letters
python main.py search '^[A-Z]' --regex

# Case-sensitive regex search
python main.py search '^[A-Z][a-z]+' --regex --case-sensitive
```

### 3. Field-Specific Search
```bash
# Search in specific field only
python main.py search 'game' --field category

# Regex search in specific field
python main.py search 'subscription' --field category --regex
```

### 4. Advanced Multi-Field Search
```bash
# AND operator (all conditions must match)
python main.py advanced-search --queries "category:game,developer:valve" --operator AND

# OR operator (any condition can match)
python main.py advanced-search --queries "category:ebook,category:software" --operator OR

# With regex patterns
python main.py advanced-search --queries "category:subscription,source:Humble Bundle" --operator AND --regex
```

### 5. Advanced Filtering
```bash
# Filter by category and source
python main.py search 'book' --category ebook --source humble_bundle

# Filter by rating range
python main.py search 'game' --rating-min 4.0 --rating-max 5.0

# Filter by platform
python main.py search 'software' --platform windows
```

## CLI Commands

### Search Commands
- **`search`**: Basic search with regex support
- **`advanced-search`**: Multi-field search with AND/OR operators
- **`search-info`**: Show search capabilities and statistics

### Search Options
- **`--regex`**: Treat query as regex pattern
- **`--case-sensitive`**: Case-sensitive search (with regex)
- **`--field`**: Search in specific field only
- **`--operator`**: AND/OR operator for advanced search
- **`--rating-min/--rating-max`**: Rating range filters
- **`--dump`**: Export all results
- **`--format`**: Export format (table, json, csv, tsv)

## Extensibility

### Adding New Data Sources

To add support for a new data source (e.g., Steam, GOG), simply implement the `SearchProvider` interface:

```python
class SteamSearchProvider(SearchProvider):
    def __init__(self, steam_api_client):
        self.client = steam_api_client
        self.searchable_fields = ['name', 'genre', 'developer', 'tags']
    
    def search_assets(self, query: str, filters: Optional[Dict[str, Any]] = None,
                     use_regex: bool = False, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        # Implement Steam-specific search logic
        pass
    
    # Implement other abstract methods...
```

### Integration with Main CLI

```python
# In main.py, add new search provider
if source == 'steam':
    search_provider = SteamSearchProvider(steam_client)
elif source == 'gog':
    search_provider = GOGSearchProvider(gog_client)
else:
    search_provider = DuckDBSearchProvider(db.conn)
```

## Performance Considerations

### DuckDB Implementation
- **Text Search**: Uses native DuckDB `ILIKE` for simple patterns
- **Regex Search**: Fetches results and applies Python regex for complex patterns
- **Indexing**: Leverages existing database indexes for filtering
- **Pagination**: Efficient result pagination for large datasets

### Optimization Strategies
- **Field-Specific Search**: Reduces data transfer by searching only relevant fields
- **Filter Pushdown**: Applies database filters before regex processing
- **Result Limiting**: Configurable page sizes for memory management

## Usage Examples

### Finding Discounted Games
```bash
# Find all products with discount percentages
python main.py search '^\d+% Off' --regex

# Find specific game series with discounts
python main.py search '^\d+% Off - STORY OF SEASONS' --regex
```

### Category-Based Search
```bash
# Find all ebooks
python main.py search 'ebook' --field category

# Find games with regex pattern
python main.py search '^[A-Z][a-z]+' --field category --regex
```

### Complex Multi-Criteria Search
```bash
# Find high-rated games from specific developer
python main.py advanced-search --queries "category:game,developer:valve,rating:4.5" --operator AND

# Find products matching multiple patterns
python main.py advanced-search --queries "name:^[A-Z],category:game" --operator AND --regex
```

### Export and Analysis
```bash
# Export regex search results to JSON
python main.py search '^\d+%' --regex --dump --format json

# Export to CSV for spreadsheet analysis
python main.py search 'STORY OF SEASONS' --regex --dump --format csv

# Export to TSV for command-line processing
python main.py search 'game' --field category --dump --format tsv
```

## Future Enhancements

### Planned Features
1. **Saved Searches**: Store and reuse complex search queries
2. **Search Templates**: Predefined search patterns for common use cases
3. **Search Analytics**: Track popular searches and improve results
4. **Fuzzy Search**: Support for approximate string matching
5. **Full-Text Search**: Advanced text indexing and search capabilities

### Integration Opportunities
1. **Elasticsearch**: Add full-text search capabilities
2. **Vector Search**: Semantic search using embeddings
3. **Machine Learning**: Intelligent search result ranking
4. **API Endpoints**: REST API for external search integration

## Conclusion

The new regex search architecture provides:

- **Extensibility**: Easy to add new data sources
- **Flexibility**: Support for both simple and complex search patterns
- **Performance**: Efficient search with DuckDB integration
- **Usability**: Intuitive CLI interface with comprehensive options
- **Export**: Multiple output formats for further analysis

This architecture makes the Digital Asset Inventory Manager a powerful tool for searching and analyzing digital assets across multiple platforms while maintaining clean separation of concerns and extensibility for future enhancements. 