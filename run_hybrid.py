#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE Hybrid Launcher

This script launches the hybrid version of RebelSCRIBE, which combines
documentation management and novel writing functionality.
"""

import sys
import os
from pathlib import Path

# Add src directory to path to allow imports
src_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(src_dir))

# Import the hybrid main module
from src.main_hybrid import main

if __name__ == "__main__":
    sys.exit(main())
