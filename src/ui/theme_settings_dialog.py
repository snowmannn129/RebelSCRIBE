#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Theme Settings Dialog

This module implements the theme settings dialog for RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QColorDialog, QFormLayout, QGroupBox,
    QCheckBox, QSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ThemeSettingsDialog(QDialog):
    """
    Theme settings dialog for RebelSCRIBE.
    
    This dialog allows the user to customize the theme settings for RebelSCRIBE.
    """
    
    def __init__(self, parent=None, theme_manager=None):
        """
        Initialize the theme settings dialog.
        
        Args:
            parent: The parent widget.
            theme_manager: The theme manager.
        """
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        
        # Set up dialog properties
        self.setWindowTitle("Theme Settings")
        self.setMinimumWidth(400)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create theme selection group
        self.create_theme_selection_group()
        
        # Create editor settings group
        self.create_editor_settings_group()
        
        # Create UI settings group
        self.create_ui_settings_group()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Add button box to layout
        self.layout.addWidget(self.button_box)
        
        # Load settings
        self.load_settings()
        
        logger.debug("Theme settings dialog initialized")
    
    def create_theme_selection_group(self):
        """Create theme selection group."""
        group_box = QGroupBox("Theme")
        layout = QFormLayout(group_box)
        
        # Theme combo box
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System", "Custom"])
        layout.addRow("Theme:", self.theme_combo)
        
        # Add group box to layout
        self.layout.addWidget(group_box)
    
    def create_editor_settings_group(self):
        """Create editor settings group."""
        group_box = QGroupBox("Editor")
        layout = QFormLayout(group_box)
        
        # Font combo box
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Consolas", "Courier New", "Monospace", "Source Code Pro"])
        layout.addRow("Font:", self.font_combo)
        
        # Font size spin box
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        layout.addRow("Font Size:", self.font_size_spin)
        
        # Line numbers checkbox
        self.line_numbers_check = QCheckBox()
        layout.addRow("Show Line Numbers:", self.line_numbers_check)
        
        # Syntax highlighting checkbox
        self.syntax_highlighting_check = QCheckBox()
        layout.addRow("Syntax Highlighting:", self.syntax_highlighting_check)
        
        # Add group box to layout
        self.layout.addWidget(group_box)
    
    def create_ui_settings_group(self):
        """Create UI settings group."""
        group_box = QGroupBox("UI")
        layout = QFormLayout(group_box)
        
        # Accent color button
        self.accent_color_button = QPushButton()
        self.accent_color_button.setFixedWidth(100)
        self.accent_color_button.clicked.connect(self._on_accent_color_clicked)
        layout.addRow("Accent Color:", self.accent_color_button)
        
        # Background color button
        self.background_color_button = QPushButton()
        self.background_color_button.setFixedWidth(100)
        self.background_color_button.clicked.connect(self._on_background_color_clicked)
        layout.addRow("Background Color:", self.background_color_button)
        
        # Text color button
        self.text_color_button = QPushButton()
        self.text_color_button.setFixedWidth(100)
        self.text_color_button.clicked.connect(self._on_text_color_clicked)
        layout.addRow("Text Color:", self.text_color_button)
        
        # Add group box to layout
        self.layout.addWidget(group_box)
    
    def load_settings(self):
        """Load settings."""
        settings = QSettings()
        
        # Load theme
        theme = settings.value("theme", "System")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Load editor settings
        font = settings.value("editor/font", "Consolas")
        index = self.font_combo.findText(font)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        
        font_size = settings.value("editor/fontSize", 12, type=int)
        self.font_size_spin.setValue(font_size)
        
        line_numbers = settings.value("editor/lineNumbers", True, type=bool)
        self.line_numbers_check.setChecked(line_numbers)
        
        syntax_highlighting = settings.value("editor/syntaxHighlighting", True, type=bool)
        self.syntax_highlighting_check.setChecked(syntax_highlighting)
        
        # Load UI settings
        accent_color = settings.value("ui/accentColor", "#007bff")
        self.accent_color = QColor(accent_color)
        self._update_color_button(self.accent_color_button, self.accent_color)
        
        background_color = settings.value("ui/backgroundColor", "#ffffff")
        self.background_color = QColor(background_color)
        self._update_color_button(self.background_color_button, self.background_color)
        
        text_color = settings.value("ui/textColor", "#000000")
        self.text_color = QColor(text_color)
        self._update_color_button(self.text_color_button, self.text_color)
    
    def save_settings(self):
        """Save settings."""
        settings = QSettings()
        
        # Save theme
        settings.setValue("theme", self.theme_combo.currentText())
        
        # Save editor settings
        settings.setValue("editor/font", self.font_combo.currentText())
        settings.setValue("editor/fontSize", self.font_size_spin.value())
        settings.setValue("editor/lineNumbers", self.line_numbers_check.isChecked())
        settings.setValue("editor/syntaxHighlighting", self.syntax_highlighting_check.isChecked())
        
        # Save UI settings
        settings.setValue("ui/accentColor", self.accent_color.name())
        settings.setValue("ui/backgroundColor", self.background_color.name())
        settings.setValue("ui/textColor", self.text_color.name())
    
    def accept(self):
        """Handle dialog acceptance."""
        logger.debug("Theme settings dialog accepted")
        
        # Save settings
        self.save_settings()
        
        # Apply theme
        if self.theme_manager:
            self.theme_manager.apply_theme(None)
        
        # Accept dialog
        super().accept()
    
    def _on_accent_color_clicked(self):
        """Handle accent color button clicked."""
        color = QColorDialog.getColor(self.accent_color, self, "Select Accent Color")
        if color.isValid():
            self.accent_color = color
            self._update_color_button(self.accent_color_button, color)
    
    def _on_background_color_clicked(self):
        """Handle background color button clicked."""
        color = QColorDialog.getColor(self.background_color, self, "Select Background Color")
        if color.isValid():
            self.background_color = color
            self._update_color_button(self.background_color_button, color)
    
    def _on_text_color_clicked(self):
        """Handle text color button clicked."""
        color = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if color.isValid():
            self.text_color = color
            self._update_color_button(self.text_color_button, color)
    
    def _update_color_button(self, button, color):
        """
        Update color button.
        
        Args:
            button: The button to update.
            color: The color to set.
        """
        button.setStyleSheet(f"background-color: {color.name()}; color: {self._contrast_color(color).name()}")
        button.setText(color.name())
    
    def _contrast_color(self, color):
        """
        Get contrast color.
        
        Args:
            color: The color to get contrast for.
            
        Returns:
            The contrast color.
        """
        # Calculate luminance
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        
        # Return black or white based on luminance
        return QColor(0, 0, 0) if luminance > 0.5 else QColor(255, 255, 255)
