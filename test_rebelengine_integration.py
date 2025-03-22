#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for RebelENGINE integration with RebelSCRIBE.

This script tests the RebelENGINE integration by extracting documentation from
RebelENGINE source code and generating documentation files.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.integrations.rebelengine_integration import RebelENGINEIntegration

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('rebelscribe.log')
        ]
    )

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test RebelENGINE integration with RebelSCRIBE")
    parser.add_argument("--rebelsuite-root", help="RebelSUITE root directory")
    parser.add_argument("--output-dir", help="Output directory for documentation")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    try:
        # Determine RebelSUITE root directory
        rebelsuite_root = args.rebelsuite_root
        if not rebelsuite_root:
            # Try to find the RebelSUITE root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if os.path.exists(os.path.join(parent_dir, "RebelCAD")) and \
               os.path.exists(os.path.join(parent_dir, "RebelENGINE")) and \
               os.path.exists(os.path.join(parent_dir, "RebelSUITE_Integration_Tracking.md")):
                rebelsuite_root = parent_dir
            else:
                print("Could not determine RebelSUITE root directory. Please specify with --rebelsuite-root.")
                return 1
        
        # Determine output directory
        output_dir = args.output_dir
        if not output_dir:
            output_dir = os.path.join(current_dir, "docs", "rebelengine")
        
        # Create integration
        print(f"Creating RebelENGINE integration with RebelSUITE root: {rebelsuite_root}")
        integration = RebelENGINEIntegration(rebelsuite_root)
        
        # Extract documentation
        print(f"Extracting documentation to: {output_dir}")
        docs = integration.extract_documentation(output_dir)
        
        # Print summary
        print(f"Extracted {len(docs)} documentation items from RebelENGINE")
        
        # Count by type
        type_counts = {}
        for doc in docs:
            if doc.type not in type_counts:
                type_counts[doc.type] = 0
            type_counts[doc.type] += 1
        
        print("\nDocumentation by type:")
        for doc_type, count in type_counts.items():
            print(f"  {doc_type}: {count}")
        
        # Count by language
        language_counts = {}
        for doc in docs:
            if doc.language not in language_counts:
                language_counts[doc.language] = 0
            language_counts[doc.language] += 1
        
        print("\nDocumentation by language:")
        for language, count in language_counts.items():
            print(f"  {language}: {count}")
        
        print("\nDocumentation extraction completed successfully")
        print(f"Documentation files generated in: {output_dir}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        logging.exception("An error occurred during documentation extraction")
        return 1

if __name__ == "__main__":
    sys.exit(main())
