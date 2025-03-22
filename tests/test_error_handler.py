#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Error Handler Tests

This module contains tests for the error handler.
"""

import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.error_handler_init import ErrorHandler

# Create QApplication instance for tests
app = QApplication.instance() or QApplication([])

class TestErrorHandler:
    """Tests for the ErrorHandler class."""
    
    def setup_method(self):
        """Set up the test."""
        self.error_handler = ErrorHandler()
    
    def test_init(self):
        """Test initialization."""
        assert self.error_handler is not None
        assert self.error_handler.main_window is None
    
    def test_set_main_window(self):
        """Test set_main_window method."""
        self.error_handler.set_main_window("main_window")
        assert self.error_handler.main_window == "main_window"
