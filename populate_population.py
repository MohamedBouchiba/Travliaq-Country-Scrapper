#!/usr/bin/env python3
"""
Convenience wrapper for population enrichment script.

Usage:
    python populate_population.py
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run
from migration.populate_city_population import main

if __name__ == "__main__":
    main()
