#!/usr/bin/env python3
"""
Digital Asset Inventory Manager - Main Entry Point
This file runs the main CLI interface from the src/ directory
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Change working directory to src for relative imports to work
os.chdir(src_path)

# Import and run the main CLI from the humble_bundle_inventory package
from humble_bundle_inventory.main import cli

if __name__ == "__main__":
    cli() 