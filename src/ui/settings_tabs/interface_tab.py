#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Interface Settings Tab

This module implements the interface settings tab for the settings dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
    QPushButton, QLabel, QCheckBox, QComboBox
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class InterfaceTab(QWidget):
    """Interface settings tab for the settings dialog."""
    
    def __init__(self, parent=None):
        """
        Initialize the interface tab.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Interface tab initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addRow("Application Theme:", self.theme_combo)
        
        self.accent_color_button = QPushButton("Accent Color...")
        self.accent_color_preview = QLabel()
        self.accent_color_preview.setFixedSize(24, 24)
        self.accent_color_preview.setStyleSheet("background-color: #0078D7; border: 1px solid #CCCCCC;")
        theme_layout.addRow(self.accent_color_button, self.accent_color_preview)
        
        layout.addWidget(theme_group)
        
        # Layout group
        layout_group = QGroupBox("Layout")
        layout_layout = QFormLayout(layout_group)
        
        self.show_toolbar_checkbox = QCheckBox("Show Toolbar")
        layout_layout.addRow(self.show_toolbar_checkbox)
        
        self.show_statusbar_checkbox = QCheckBox("Show Status Bar")
        layout_layout.addRow(self.show_statusbar_checkbox)
        
        self.show_line_numbers_checkbox = QCheckBox("Show Line Numbers")
        layout_layout.addRow(self.show_line_numbers_checkbox)
        
        layout.addWidget(layout_group)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        
        self.restore_session_checkbox = QCheckBox("Restore Previous Session")
        startup_layout.addRow(self.restore_session_checkbox)
        
        self.show_welcome_checkbox = QCheckBox("Show Welcome Screen")
        startup_layout.addRow(self.show_welcome_checkbox)
        
        layout.addWidget(startup_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def load_settings(self, settings):
        """
        Load settings into the tab.
        
        Args:
            settings: The settings dictionary.
        """
        interface_settings = settings.get("interface", {})
        
        # Theme settings
        theme = interface_settings.get("theme", "Light")
        self.theme_combo.setCurrentText(theme)
        
        accent_color = interface_settings.get("accent_color", "#0078D7")
        self.accent_color_preview.setStyleSheet(f"background-color: {accent_color}; border: 1px solid #CCCCCC;")
        
        # Layout settings
        show_toolbar = interface_settings.get("show_toolbar", True)
        self.show_toolbar_checkbox.setChecked(show_toolbar)
        
        show_statusbar = interface_settings.get("show_statusbar", True)
        self.show_statusbar_checkbox.setChecked(show_statusbar)
        
        show_line_numbers = interface_settings.get("show_line_numbers", True)
        self.show_line_numbers_checkbox.setChecked(show_line_numbers)
        
        # Startup settings
        restore_session = interface_settings.get("restore_session", True)
        self.restore_session_checkbox.setChecked(restore_session)
        
        show_welcome = interface_settings.get("show_welcome", True)
        self.show_welcome_checkbox.setChecked(show_welcome)
    
    def get_settings(self):
        """
        Get the current settings from the tab.
        
        Returns:
            A dictionary containing the current settings.
        """
        settings = {}
        
        # Theme settings
        settings["theme"] = self.theme_combo.currentText()
        
        accent_color = self.accent_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        settings["accent_color"] = accent_color
        
        # Layout settings
        settings["show_toolbar"] = self.show_toolbar_checkbox.isChecked()
        settings["show_statusbar"] = self.show_statusbar_checkbox.isChecked()
        settings["show_line_numbers"] = self.show_line_numbers_checkbox.isChecked()
        
        # Startup settings
        settings["restore_session"] = self.restore_session_checkbox.isChecked()
        settings["show_welcome"] = self.show_welcome_checkbox.isChecked()
        
        return settings
    
    def connect_signals(self, dialog):
        """
        Connect signals to the dialog.
        
        Args:
            dialog: The parent dialog.
        """
        self.theme_combo.currentTextChanged.connect(dialog._on_theme_changed)
        self.accent_color_button.clicked.connect(dialog._on_select_accent_color)
