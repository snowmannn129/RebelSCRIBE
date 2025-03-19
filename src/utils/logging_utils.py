#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Utilities for RebelSCRIBE.

This module provides utilities for configuring and managing logging.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Optional, Union, List

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Default log file size (10 MB)
DEFAULT_MAX_BYTES = 10 * 1024 * 1024

# Default number of backup log files
DEFAULT_BACKUP_COUNT = 5


def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to the log file. If None, uses 'rebelscribe.log' in the current directory.
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_format: Format string for log messages.
        console_output: Whether to output logs to the console.
        file_output: Whether to output logs to a file.
        max_bytes: Maximum size of the log file before rotation.
        backup_count: Number of backup log files to keep.
        
    Returns:
        The configured root logger.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set the log level
    root_logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_output:
        if log_file is None:
            log_file = "rebelscribe.log"
        
        # Ensure the directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log the setup
    root_logger.info(f"Logging configured with level={logging.getLevelName(log_level)}")
    if file_output:
        root_logger.info(f"Log file: {log_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Name of the logger.
        
    Returns:
        The logger instance.
    """
    return logging.getLogger(name)


def set_log_level(level: Union[int, str], logger_name: Optional[str] = None) -> None:
    """
    Set the log level for a logger.
    
    Args:
        level: Log level (e.g., logging.DEBUG, 'DEBUG').
        logger_name: Name of the logger. If None, sets the level for the root logger.
    """
    # Convert string level to int if necessary
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Get the logger
    logger = logging.getLogger(logger_name)
    
    # Set the level
    logger.setLevel(level)
    logger.info(f"Log level set to {logging.getLevelName(level)}")


def add_file_handler(
    log_file: Union[str, Path],
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    logger_name: Optional[str] = None,
) -> logging.Handler:
    """
    Add a file handler to a logger.
    
    Args:
        log_file: Path to the log file.
        log_level: Logging level for the handler.
        log_format: Format string for log messages.
        max_bytes: Maximum size of the log file before rotation.
        backup_count: Number of backup log files to keep.
        logger_name: Name of the logger. If None, adds the handler to the root logger.
        
    Returns:
        The created handler.
    """
    # Ensure the directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Create handler
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    
    # Set level and formatter
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    
    # Add to logger
    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    
    logger.info(f"Added file handler for {log_file}")
    return handler


def add_console_handler(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    logger_name: Optional[str] = None,
) -> logging.Handler:
    """
    Add a console handler to a logger.
    
    Args:
        log_level: Logging level for the handler.
        log_format: Format string for log messages.
        logger_name: Name of the logger. If None, adds the handler to the root logger.
        
    Returns:
        The created handler.
    """
    # Create handler
    handler = logging.StreamHandler()
    
    # Set level and formatter
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    
    # Add to logger
    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    
    logger.info("Added console handler")
    return handler


def get_log_levels() -> Dict[str, int]:
    """
    Get a dictionary of available log levels.
    
    Returns:
        A dictionary mapping level names to level values.
    """
    return {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }


def get_all_loggers() -> List[str]:
    """
    Get a list of all logger names.
    
    Returns:
        A list of logger names.
    """
    return list(logging.root.manager.loggerDict.keys())


def disable_logging() -> None:
    """Disable all logging."""
    logging.disable(logging.CRITICAL)


def enable_logging() -> None:
    """Enable logging."""
    logging.disable(logging.NOTSET)
