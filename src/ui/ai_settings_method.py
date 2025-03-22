#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - AI Settings Method

This module provides the AI settings method for the hybrid version of RebelSCRIBE.
"""

import os
import sys
from pathlib import Path

from src.utils.logging_utils import get_logger
from src.ui.ai_settings_dialog import AISettingsDialog

logger = get_logger(__name__)

def on_ai_settings(self):
    """Handle AI settings action."""
    logger.debug("AI settings action triggered")
    
    # Create AI settings dialog
    dialog = AISettingsDialog(self)
    
    # Show dialog
    if dialog.exec():
        # Update status bar
        self.status_bar.showMessage("AI settings updated", 3000)
