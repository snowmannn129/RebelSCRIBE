#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run RebelDESK Integration for RebelSCRIBE.

This script runs the RebelDESK integration for RebelSCRIBE, which extracts documentation
from RebelDESK source code and generates documentation files.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.integrations.rebeldesk_integration import RebelDESKIntegration
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def main():
    """Run the RebelDESK integration."""
    try:
        # Initialize the integration
        integration = RebelDESKIntegration()
        
        # Extract documentation from RebelDESK source code
        docs = integration.extract_documentation()
        
        # Integrate with RebelDESK
        success = integration.integrate_with_rebeldesk()
        
        if success:
            logger.info("RebelDESK integration completed successfully")
            print("RebelDESK integration completed successfully")
            print(f"Extracted {len(docs)} documentation items from RebelDESK")
        else:
            logger.error("RebelDESK integration failed")
            print("RebelDESK integration failed")
            return 1
        
        return 0
    except Exception as e:
        logger.error(f"Error running RebelDESK integration: {e}", exc_info=True)
        print(f"Error running RebelDESK integration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
