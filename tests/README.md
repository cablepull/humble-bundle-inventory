# Test Suite Documentation

## Overview

The Digital Asset Inventory Manager includes a comprehensive test suite that covers all search permutations, edge cases, and integration scenarios. The tests are designed to ensure the search functionality works correctly across all use cases and combinations.

## Test Structure

```
tests/
├── README.md                 # This documentation
├── run_tests.py             # Test runner script
├── test_search_provider.py  # Unit tests for search providers
└── test_search_integration.py # Integration tests for CLI search
```

## Test Categories

### 1. Unit Tests (`test_search_provider.py`)

**Purpose**: Test individual components in isolation with mocked dependencies.

**Coverage**:
- ✅ **SearchProvider Interface**: Abstract base class validation
- ✅ **DuckDBSearchProvider Implementation**: Core search functionality
- ✅ **Text Search**: Basic and filtered text searches
- ✅ **Regex Search**: Pattern matching with case sensitivity
- ✅ **Field-Specific Search**: Searching in specific fields
- ✅ **Advanced Search**: Multi-field queries with AND/OR operators
- ✅ **Filter Combinations**: Category, source, platform, rating filters
- ✅ **Edge Cases**: Special characters, numbers, empty queries
- ✅ **Error Handling**: Invalid fields, regex patterns, operators
- ✅ **Performance**: Filter efficiency and dataset reduction

**Key Test Scenarios**:
```python
# Basic text search
test_text_search_basic()
test_text_search_case_insensitive()
test_text_search_multiple_matches()

# Filtered searches
test_text_search_with_filters()
test_text_search_with_source_filter()
test_text_search_with_rating_filter()

# Regex searches
test_regex_search_basic()
test_regex_search_case_sensitive()
test_regex_search_with_filters()

# Field-specific searches
test_search_by_field_text()
test_search_by_field_regex()
test_search_by_field_with_filters()

# Advanced searches
test_advanced_search_text_and()
test_advanced_search_text_or()
test_advanced_search_regex()

# Edge cases
test_search_edge_cases()
test_search_empty_query()
test_search_no_results()
```

### 2. Integration Tests (`test_search_integration.py`)

**Purpose**: Test the full search pipeline through the CLI interface.

**Coverage**:
- ✅ **CLI Commands**: All search command variations
- ✅ **Output Formats**: Table, JSON, CSV, TSV
- ✅ **Pagination**: Page navigation and sizing
- ✅ **Filter Combinations**: Multiple filters applied together
- ✅ **Error Handling**: Invalid inputs and graceful failures
- ✅ **Performance**: Timing comparisons between filtered/unfiltered searches

**Key Test Scenarios**:
```python
# CLI search variations
test_search_basic()
test_search_with_category_filter()
test_search_with_field_specific()
test_search_with_field_and_category()

# Regex CLI searches
test_search_regex_basic()
test_search_regex_with_category()
test_search_regex_case_sensitive()

# Output formats
test_search_dump_json()
test_search_dump_csv()
test_search_dump_tsv()

# Advanced CLI features
test_advanced_search_and()
test_advanced_search_or()
test_advanced_search_with_regex()

# Edge cases and error handling
test_search_invalid_field()
test_search_invalid_regex()
test_search_error_handling()
```

## Search Permutations Tested

### 1. Basic Search Combinations

| Query Type | Field Filter | Category Filter | Source Filter | Rating Filter | Tested |
|------------|--------------|-----------------|---------------|---------------|---------|
| Text | ❌ | ❌ | ❌ | ❌ | ✅ |
| Text | ✅ | ❌ | ❌ | ❌ | ✅ |
| Text | ❌ | ✅ | ❌ | ❌ | ✅ |
| Text | ❌ | ❌ | ✅ | ❌ | ✅ |
| Text | ❌ | ❌ | ❌ | ✅ | ✅ |
| Text | ✅ | ✅ | ❌ | ❌ | ✅ |
| Text | ✅ | ❌ | ✅ | ❌ | ✅ |
| Text | ✅ | ❌ | ❌ | ✅ | ✅ |
| Text | ❌ | ✅ | ✅ | ❌ | ✅ |
| Text | ❌ | ✅ | ❌ | ✅ | ✅ |
| Text | ❌ | ❌ | ✅ | ✅ | ✅ |
| Text | ✅ | ✅ | ✅ | ❌ | ✅ |
| Text | ✅ | ✅ | ❌ | ✅ | ✅ |
| Text | ✅ | ❌ | ✅ | ✅ | ✅ |
| Text | ❌ | ✅ | ✅ | ✅ | ✅ |
| Text | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2. Regex Search Combinations

| Query Type | Field Filter | Category Filter | Case Sensitive | Tested |
|------------|--------------|-----------------|-----------------|---------|
| Regex | ❌ | ❌ | ❌ | ✅ |
| Regex | ✅ | ❌ | ❌ | ✅ |
| Regex | ❌ | ✅ | ❌ | ✅ |
| Regex | ✅ | ✅ | ❌ | ✅ |
| Regex | ❌ | ❌ | ✅ | ✅ |
| Regex | ✅ | ❌ | ✅ | ✅ |
| Regex | ❌ | ✅ | ✅ | ✅ |
| Regex | ✅ | ✅ | ✅ | ✅ |

### 3. Field-Specific Search Combinations

| Field | Query Type | Filters | Tested |
|-------|------------|---------|---------|
| human_name | Text | ❌ | ✅ |
| human_name | Text | Category | ✅ |
| human_name | Text | Source | ✅ |
| human_name | Text | Rating | ✅ |
| human_name | Text | Multiple | ✅ |
| human_name | Regex | ❌ | ✅ |
| human_name | Regex | Category | ✅ |
| human_name | Regex | Multiple | ✅ |
| category | Text | ❌ | ✅ |
| category | Text | Source | ✅ |
| developer | Text | ❌ | ✅ |
| developer | Text | Category | ✅ |
| publisher | Text | ❌ | ✅ |
| tags | Text | ❌ | ✅ |

### 4. Advanced Search Combinations

| Operator | Query Count | Regex | Filters | Tested |
|----------|-------------|-------|---------|---------|
| AND | 2 | ❌ | ❌ | ✅ |
| AND | 2 | ❌ | Category | ✅ |
| AND | 2 | ❌ | Rating | ✅ |
| AND | 2 | ❌ | Multiple | ✅ |
| AND | 2 | ✅ | ❌ | ✅ |
| AND | 2 | ✅ | Category | ✅ |
| OR | 2 | ❌ | ❌ | ✅ |
| OR | 2 | ❌ | Category | ✅ |
| OR | 2 | ✅ | ❌ | ✅ |
| OR | 2 | ✅ | Category | ✅ |

## Running Tests

### 1. Test Runner Script

The `run_tests.py` script provides a comprehensive way to run tests:

```bash
# Run all tests
python tests/run_tests.py

# Run only unit tests
python tests/run_tests.py --type unit

# Run only integration tests
python tests/run_tests.py --type integration

# Run only search-related tests
python tests/run_tests.py --type search

# Run tests with specific pattern
python tests/run_tests.py --pattern "*search*"

# Run specific test file
python tests/run_tests.py --file test_search_provider

# Fast mode (skip integration tests)
python tests/run_tests.py --fast

# Verbose output
python tests/run_tests.py --verbosity 2
```

### 2. Direct Python Execution

```bash
# Run unit tests directly
python -m unittest tests.test_search_provider -v

# Run integration tests directly
python -m unittest tests.test_search_integration -v

# Run specific test class
python -m unittest tests.test_search_provider.TestDuckDBSearchProvider -v

# Run specific test method
python -m unittest tests.test_search_provider.TestDuckDBSearchProvider.test_text_search_basic -v
```

### 3. Coverage Testing

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run tests/run_tests.py --type unit
coverage report
coverage html  # Generate HTML report
```

## Test Data

The tests use a comprehensive test dataset that includes:

### Products
- **Software**: Visual Studio Code, Adobe Photoshop, Unity Game Engine
- **Games**: Minecraft, Portal 2, Civilization VI
- **Ebooks**: Python Programming Guide, Machine Learning Basics, Web Security Handbook
- **Audio**: Game Soundtrack Collection
- **Edge Cases**: Products with numbers, special characters, uppercase names

### Categories & Subcategories
- software: development, photo_editing, game_development
- game: sandbox, puzzle, strategy
- ebook: programming, security
- audio: soundtrack

### Metadata
- Ratings: 4.0 to 4.9
- Developers: Microsoft, Adobe, Unity, Mojang, Valve, O'Reilly, Manning
- Publishers: Various publishers
- Tags: JSON arrays with relevant keywords
- Release dates: Various dates from 1990-2020

## Performance Testing

The test suite includes performance validation:

### 1. Filter Efficiency
- Tests that category filters reduce dataset size
- Verifies SQL-level filtering vs Python post-processing
- Measures performance improvement with filters

### 2. Search Scalability
- Tests with various dataset sizes
- Validates search performance with complex queries
- Ensures regex performance on filtered datasets

## Error Handling Testing

### 1. Invalid Inputs
- Invalid field names
- Malformed regex patterns
- Invalid filter values
- Missing required parameters

### 2. Edge Cases
- Empty queries
- No results
- Database connection failures
- Invalid database paths

### 3. Graceful Degradation
- Error messages for invalid inputs
- Fallback behavior for missing data
- Timeout handling for long-running queries

## Continuous Integration

The test suite is designed for CI/CD pipelines:

### 1. Fast Feedback
- Unit tests run quickly (< 5 seconds)
- Integration tests can be skipped in fast mode
- Parallel test execution support

### 2. Deterministic Results
- No external dependencies
- Temporary database creation/cleanup
- Isolated test environments

### 3. Exit Codes
- Proper exit codes for CI systems
- Detailed failure reporting
- Test result summaries

## Adding New Tests

### 1. Unit Tests
```python
def test_new_feature(self):
    """Test description."""
    # Arrange
    expected = "expected_value"
    
    # Act
    result = self.search_provider.new_feature()
    
    # Assert
    self.assertEqual(result, expected)
```

### 2. Integration Tests
```python
def test_new_cli_feature(self):
    """Test new CLI feature."""
    result = self._run_cli_command(['new-command', '--option', 'value'])
    
    self.assertEqual(result.returncode, 0)
    self.assertIn('expected_output', result.stdout)
```

### 3. Test Data
- Add test data to `_insert_test_data()` method
- Ensure data covers edge cases
- Include various categories and metadata combinations

## Best Practices

### 1. Test Naming
- Use descriptive test names
- Follow pattern: `test_<feature>_<scenario>`
- Include edge case descriptions

### 2. Test Structure
- Arrange: Set up test data and conditions
- Act: Execute the functionality being tested
- Assert: Verify expected outcomes

### 3. Test Isolation
- Each test should be independent
- Use `setUp()` and `tearDown()` for common setup
- Clean up resources after each test

### 4. Coverage
- Test both success and failure paths
- Include edge cases and boundary conditions
- Test error handling and validation

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Database Errors**: Check temporary file permissions
3. **Timeout Errors**: Increase timeout for slow systems
4. **Path Issues**: Run from project root directory

### Debug Mode

```bash
# Run with maximum verbosity
python tests/run_tests.py --verbosity 2

# Run specific failing test
python -m unittest tests.test_search_provider.TestDuckDBSearchProvider.test_specific_method -v

# Use Python debugger
python -m pdb tests/run_tests.py --type unit
```

## Performance Benchmarks

The test suite includes performance benchmarks:

- **Unit Tests**: < 5 seconds for full suite
- **Integration Tests**: < 10 seconds for full suite
- **Search Performance**: < 100ms for filtered searches
- **Memory Usage**: < 50MB for test execution

## Future Enhancements

### Planned Test Additions
- [ ] Load testing with large datasets
- [ ] Concurrent search testing
- [ ] Memory leak detection
- [ ] Performance regression testing
- [ ] Cross-platform compatibility testing

### Test Infrastructure
- [ ] Parallel test execution
- [ ] Test result caching
- [ ] Automated performance regression detection
- [ ] Integration with monitoring systems 