# Search Quick Reference Card

## Most Useful Searches

### 📚 Books
```bash
# All Python books
python main.py search "python" --category books --dump

# All programming books
python main.py search "programming" --category books --dump

# All ebooks
python main.py search "" --category ebooks --dump

# Machine learning books
python main.py search "machine learning" --category books
```

### 🎮 Games
```bash
# All games
python main.py search "" --category games --dump

# Space games
python main.py search "space" --category games

# RPG games
python main.py search "RPG" --category games

# Strategy games
python main.py search "strategy" --category games
```

### 💻 Software
```bash
# All software
python main.py search "" --category software --dump

# Development tools
python main.py search "development" --category software

# Cloud platform tools
python main.py search "cloud" --category software
```

### 🔍 Advanced Filters
```bash
# Filter by source
python main.py search "" --source humble_bundle --dump

# Filter by platform
python main.py search "" --platform windows --dump

# Combine filters
python main.py search "python" --category books --source humble_bundle
```

### 📊 Export Options
```bash
# Export to CSV
python main.py search "python" --dump --format csv > python_assets.csv

# Export to JSON
python main.py search "machine learning" --dump --format json > ml_assets.json

# Export to TSV
python main.py search "game" --dump --format tsv > games.tsv
```

## Quick Commands

```bash
# Check what you have
python main.py status

# Update your inventory
python main.py sync

# Check session status
python main.py session

# Get help
python main.py --help
python main.py search --help
```

## Pro Tips

1. **Use `--dump`** to see all results without pagination
2. **Start broad** then narrow down with filters
3. **Export results** for external analysis
4. **Use quotes** for multi-word searches: `"machine learning"`
5. **Check categories** with empty search: `python main.py search "" --dump` 