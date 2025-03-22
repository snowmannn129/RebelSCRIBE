#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Theme Manager Tests

This module contains tests for the theme manager.
"""

import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSettings

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.theme_manager import ThemeManager

# Create QApplication instance for tests
app = QApplication.instance() or QApplication([])

class TestThemeManager:
    """Tests for the ThemeManager class."""
    
    def setup_method(self):
        """Set up the test."""
        self.theme_manager = ThemeManager()
    
    def test_init(self):
        """Test initialization."""
        assert self.theme_manager is not None
        assert self.theme_manager.settings is not None
    
    def test_apply_theme(self):
        """Test apply_theme method."""
        # Test with light theme
        settings = QSettings()
        settings.setValue("theme", "Light")
        self.theme_manager.apply_theme(app)
        
        # Test with dark theme
        settings.setValue("theme", "Dark")
        self.theme_manager.apply_theme(app)
        
        # Test with system theme
        settings.setValue("theme", "System")
        self.theme_manager.apply_theme(app)
        
        # Test with custom theme
        settings.setValue("theme", "Custom")
        settings.setValue("ui/accentColor", "#007bff")
        settings.setValue("ui/backgroundColor", "#ffffff")
        settings.setValue("ui/textColor", "#000000")
        self.theme_manager.apply_theme(app)
        
        # Test with unknown theme
        settings.setValue("theme", "Unknown")
        self.theme_manager.apply_theme(app)
