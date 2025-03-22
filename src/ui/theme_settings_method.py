#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Theme Settings Method

This module provides the theme settings method for the hybrid version of RebelSCRIBE.
"""

import os
import sys
from pathlib import Path

from src.utils.logging_utils import get_logger
from src.ui.theme_settings_dialog import ThemeSettingsDialog

logger = get_logger(__name__)

def on_theme_settings(self):
    """Handle theme settings action."""
    logger.debug("Theme settings action triggered")
    
    # Create theme settings dialog
    dialog = ThemeSettingsDialog(self, self.theme_manager)
    
    # Show dialog
    if dialog.exec():
        # Apply theme
        self.theme_manager.apply_theme(self.app)
        
        # Update status bar
        self.status_bar.showMessage("Theme settings updated", 3000)
