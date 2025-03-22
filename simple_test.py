#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for RebelSCRIBE documentation functionality.
"""

import os
import sys
from pathlib import Path

# Add src directory to path to allow imports
src_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(src_dir))

try:
    print("Importing Documentation class...")
    from src.backend.models.documentation import Documentation
    print("Successfully imported Documentation class")
    
    print("\nCreating Documentation object...")
    doc = Documentation(
        title="Test Documentation",
        type=Documentation.TYPE_API,
        content="This is a test documentation.",
        component=Documentation.COMPONENT_SCRIBE,
        api_version="1.0.0"
    )
    print(f"Created Documentation object: {doc}")
    
    print("\nGenerating Markdown...")
    markdown = doc.generate_markdown()
    print("Generated Markdown:")
    print(markdown)
    
    print("\nTest completed successfully!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
