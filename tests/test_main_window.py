#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Main Window Tests

This module contains tests for the main window.
"""

import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.main_window_hybrid import MainWindowHybrid

# Create QApplication instance for tests
app = QApplication.instance() or QApplication([])

class TestMainWindowHybrid:
    """Tests for the MainWindowHybrid class."""
    
    def setup_method(self):
        """Set up the test."""
        self.main_window = MainWindowHybrid()
    
    def teardown_method(self):
        """Tear down the test."""
        self.main_window.close()
    
    def test_init(self):
        """Test initialization."""
        assert self.main_window is not None
        assert self.main_window.windowTitle() == "RebelSCRIBE"
        assert self.main_window.tab_widget is not None
        assert self.main_window.tab_widget.count() == 2
        assert self.main_window.tab_widget.tabText(0) == "Novel Writing"
        assert self.main_window.tab_widget.tabText(1) == "Documentation"
    
    def test_menu_bar(self):
        """Test menu bar."""
        assert self.main_window.menu_bar is not None
        assert self.main_window.file_menu is not None
        assert self.main_window.edit_menu is not None
        assert self.main_window.view_menu is not None
        assert self.main_window.tools_menu is not None
        assert self.main_window.documentation_menu is not None
        assert self.main_window.help_menu is not None
    
    def test_tool_bar(self):
        """Test tool bar."""
        assert self.main_window.tool_bar is not None
    
    def test_novel_writing_tab(self):
        """Test novel writing tab."""
        assert self.main_window.novel_writing_tab is not None
    
    def test_documentation_tab(self):
        """Test documentation tab."""
        assert self.main_window.documentation_tab is not None
    
    def test_status_bar(self):
        """Test status bar."""
        assert self.main_window.status_bar is not None
