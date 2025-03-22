#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Logging Utils Tests

This module contains tests for the logging utilities.
"""

import os
import sys
import pytest
import logging
from pathlib import Path

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.logging_utils import setup_logging, get_logger

class TestLoggingUtils:
    """Tests for the logging utilities."""
    
    def test_setup_logging(self):
        """Test setup_logging function."""
        # Test with default parameters
        setup_logging()
        
        # Test with custom parameters
        setup_logging(
            log_file="test.log",
            console_output=False,
            file_output=False,
            level=logging.INFO
        )
    
    def test_get_logger(self):
        """Test get_logger function."""
        # Test with new logger
        logger1 = get_logger("test_logger1")
        assert logger1 is not None
        assert logger1.name == "test_logger1"
        
        # Test with existing logger
        logger2 = get_logger("test_logger1")
        assert logger2 is not None
        assert logger2.name == "test_logger1"
        assert logger1 is logger2
