#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run the RebelENGINE integration for RebelSCRIBE.

This script extracts documentation from RebelENGINE source code and generates
documentation using RebelSCRIBE.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(parent_dir))

from src.integrations.rebelengine_integration import RebelENGINEIntegration

def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run RebelENGINE integration for RebelSCRIBE")
    parser.add_argument("--rebelsuite-root", help="RebelSUITE root directory")
    parser.add_argument("--output-dir", help="Output directory for documentation")
    args = parser.parse_args()
    
    try:
        # Get RebelSUITE root directory
        rebelsuite_root = args.rebelsuite_root
        if not rebelsuite_root:
            # Try to detect RebelSUITE root directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            rebelsuite_root = os.path.dirname(script_dir)
        
        # Get output directory
        output_dir = args.output_dir
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "rebelengine")
        
        print(f"RebelSUITE root directory: {rebelsuite_root}")
        print(f"Output directory: {output_dir}")
        
        # Create integration
        integration = RebelENGINEIntegration(rebelsuite_root)
        
        # Extract documentation
        docs = integration.extract_documentation(output_dir)
        
        print(f"Successfully extracted documentation from {len(docs)} files")
        print(f"Documentation generated in: {output_dir}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
