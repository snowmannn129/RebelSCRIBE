#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - About Method

This module provides the about method for the hybrid version of RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def on_about(self):
    """Handle about action."""
    logger.debug("About action triggered")
    
    # Create about message
    about_message = """
    <h1>RebelSCRIBE</h1>
    <p>Version 1.0.0</p>
    <p>RebelSCRIBE is a hybrid documentation and novel writing program.</p>
    <p>It combines the functionality of a documentation management system with a novel writing program.</p>
    <p>RebelSCRIBE is part of the RebelSUITE ecosystem.</p>
    <p>&copy; 2025 RebelSUITE</p>
    """
    
    # Show about message
    QMessageBox.about(self, "About RebelSCRIBE", about_message)
