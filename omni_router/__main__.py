#!/usr/bin/env python3
"""Cross-platform entry point: python -m omni_router"""
import os
import sys

# Ensure the package dir is importable regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omni_router import main

if __name__ == "__main__":
    main()
