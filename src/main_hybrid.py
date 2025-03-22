#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Hybrid Documentation and Novel Writing Program.

This is the main entry point for the RebelSCRIBE application, which combines
documentation management and novel writing functionality.
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

# Import documentation methods
from src.ui.documentation_methods import on_extract_documentation, on_generate_static_site, on_integrate_with_component

# Import event bus signals
from src.ui.event_bus_signals import (
    connect_event_bus_signals,
    on_document_selected,
    on_document_content_changed,
    on_document_saved,
    on_document_deleted,
    on_project_closed,
    on_error
)

# Import theme settings method
from src.ui.theme_settings_method import on_theme_settings

# Import about method
from src.ui.about_method import on_about

# Import AI settings method
from src.ui.ai_settings_method import on_ai_settings

# Import benchmarking methods
from src.ui.benchmarking_methods import on_model_benchmarking, on_batch_benchmarking, on_model_finetuning

# Add methods to MainWindowHybrid class
def add_methods_to_main_window_hybrid():
    """Add methods to MainWindowHybrid class."""
    from src.ui.main_window_hybrid import MainWindowHybrid
    
    # Add documentation methods
    MainWindowHybrid._on_extract_documentation = on_extract_documentation
    MainWindowHybrid._on_generate_static_site = on_generate_static_site
    MainWindowHybrid._on_integrate_with_component = on_integrate_with_component
    
    # Add event bus signal methods
    MainWindowHybrid._connect_event_bus_signals = connect_event_bus_signals
    MainWindowHybrid._on_document_selected = on_document_selected
    MainWindowHybrid._on_document_content_changed = on_document_content_changed
    MainWindowHybrid._on_document_saved = on_document_saved
    MainWindowHybrid._on_document_deleted = on_document_deleted
    MainWindowHybrid._on_project_closed = on_project_closed
    MainWindowHybrid._on_error = on_error
    
    # Add theme settings method
    MainWindowHybrid._on_theme_settings = on_theme_settings
    
    # Add about method
    MainWindowHybrid._on_about = on_about
    
    # Add AI settings method
    MainWindowHybrid._on_ai_settings = on_ai_settings
    
    # Add benchmarking methods
    MainWindowHybrid._on_model_benchmarking = on_model_benchmarking
    MainWindowHybrid._on_batch_benchmarking = on_batch_benchmarking
    MainWindowHybrid._on_model_finetuning = on_model_finetuning
    
    logger.info("Added methods to MainWindowHybrid class")

def main():
    """Main entry point for the application."""
    logger.info("Starting RebelSCRIBE")
    
    try:
        # Import UI components here to avoid circular imports
        from src.ui.main_window_hybrid import MainWindowHybrid
        from src.ui.error_handler_init import initialize_error_handler
        
        # Add methods to MainWindowHybrid class
        add_methods_to_main_window_hybrid()
        
        # Initialize enhanced error handler
        logger.info("Initializing enhanced error handler")
        initialize_error_handler()
        
        # Start the application
        app = MainWindowHybrid()
        app.run()
        
    except Exception as e:
        logger.error(f"Error starting RebelSCRIBE: {e}", exc_info=True)
        return 1
    
    logger.info("RebelSCRIBE closed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
