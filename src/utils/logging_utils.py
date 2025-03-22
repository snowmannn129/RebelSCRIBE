#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Logging Utilities

This module provides logging utilities for RebelSCRIBE.
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Global logger dictionary
loggers = {}

def setup_logging(log_file="rebelscribe.log", console_output=True, file_output=True, level=logging.DEBUG):
    """
    Set up logging for the application.
    
    Args:
        log_file: The log file name.
        console_output: Whether to output logs to the console.
        file_output: Whether to output logs to a file.
        level: The logging level.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".rebelscribe" / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler
    if file_output:
        file_handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log setup complete
    root_logger.debug("Logging setup complete")

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: The logger name.
        
    Returns:
        The logger.
    """
    global loggers
    
    if name in loggers:
        return loggers[name]
    
    logger = logging.getLogger(name)
    loggers[name] = logger
    
    return logger
