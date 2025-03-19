#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - AI-powered novel writing program inspired by Scrivener.

This is the main entry point for the RebelSCRIBE application.
"""

import sys
import os
from pathlib import Path

def setup_environment():
    """Set up the application environment."""
    # Add src directory to path to allow imports
    src_dir = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(src_dir))
    
    # Create necessary directories if they don't exist
    os.makedirs(Path.home() / ".rebelscribe", exist_ok=True)
    
    print("Environment setup complete")  # Use print since logger isn't set up yet

# Set up environment before imports
setup_environment()

# Now import our logging utilities
from src.utils.logging_utils import setup_logging, get_logger

# Set up logging
setup_logging(
    log_file="rebelscribe.log",
    console_output=True,
    file_output=True
)

logger = get_logger(__name__)
logger.info("Environment setup complete")

def main():
    """Main entry point for the application."""
    logger.info("Starting RebelSCRIBE")
    
    try:
        # Import UI components here to avoid circular imports
        from src.ui.main_window import MainWindow
        from src.ui.error_handler_init import initialize_error_handler
        
        # Initialize enhanced error handler
        logger.info("Initializing enhanced error handler")
        initialize_error_handler()
        
        # Start the application
        app = MainWindow()
        app.run()
        
    except Exception as e:
        logger.error(f"Error starting RebelSCRIBE: {e}", exc_info=True)
        return 1
    
    logger.info("RebelSCRIBE closed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
