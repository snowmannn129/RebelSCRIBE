#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Editor Settings Tab

This module implements the editor settings tab for the settings dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
    QPushButton, QLabel, QCheckBox, QSpinBox, QComboBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class EditorTab(QWidget):
    """Editor settings tab for the settings dialog."""
    
    def __init__(self, parent=None):
        """
        Initialize the editor tab.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Editor tab initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Font settings group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        self.font_button = QPushButton("Select Font...")
        self.font_label = QLabel("Current Font: Default")
        font_layout.addRow(self.font_button, self.font_label)
        
        layout.addWidget(font_group)
        
        # Colors group
        colors_group = QGroupBox("Colors")
        colors_layout = QFormLayout(colors_group)
        
        self.text_color_button = QPushButton("Text Color...")
        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(24, 24)
        self.text_color_preview.setStyleSheet("background-color: #000000; border: 1px solid #CCCCCC;")
        colors_layout.addRow(self.text_color_button, self.text_color_preview)
        
        self.background_color_button = QPushButton("Background Color...")
        self.background_color_preview = QLabel()
        self.background_color_preview.setFixedSize(24, 24)
        self.background_color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CCCCCC;")
        colors_layout.addRow(self.background_color_button, self.background_color_preview)
        
        layout.addWidget(colors_group)
        
        # Auto-save group
        autosave_group = QGroupBox("Auto-Save")
        autosave_layout = QFormLayout(autosave_group)
        
        self.autosave_checkbox = QCheckBox("Enable Auto-Save")
        autosave_layout.addRow(self.autosave_checkbox)
        
        self.autosave_interval_spinbox = QSpinBox()
        self.autosave_interval_spinbox.setMinimum(1)
        self.autosave_interval_spinbox.setMaximum(60)
        self.autosave_interval_spinbox.setValue(5)
        self.autosave_interval_spinbox.setSuffix(" minutes")
        autosave_layout.addRow("Auto-Save Interval:", self.autosave_interval_spinbox)
        
        layout.addWidget(autosave_group)
        
        # Spell check group
        spellcheck_group = QGroupBox("Spell Check")
        spellcheck_layout = QFormLayout(spellcheck_group)
        
        self.spellcheck_checkbox = QCheckBox("Enable Spell Check")
        spellcheck_layout.addRow(self.spellcheck_checkbox)
        
        self.spellcheck_language_combo = QComboBox()
        self.spellcheck_language_combo.addItems(["English (US)", "English (UK)", "Spanish", "French", "German"])
        spellcheck_layout.addRow("Language:", self.spellcheck_language_combo)
        
        layout.addWidget(spellcheck_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def load_settings(self, settings):
        """
        Load settings into the tab.
        
        Args:
            settings: The settings dictionary.
        """
        editor_settings = settings.get("editor", {})
        
        # Font settings
        font_family = editor_settings.get("font_family", "Arial")
        font_size = editor_settings.get("font_size", 12)
        self.font_label.setText(f"Current Font: {font_family}, {font_size}pt")
        
        # Color settings
        text_color = editor_settings.get("text_color", "#000000")
        self.text_color_preview.setStyleSheet(f"background-color: {text_color}; border: 1px solid #CCCCCC;")
        
        background_color = editor_settings.get("background_color", "#FFFFFF")
        self.background_color_preview.setStyleSheet(f"background-color: {background_color}; border: 1px solid #CCCCCC;")
        
        # Auto-save settings
        autosave_enabled = editor_settings.get("autosave_enabled", True)
        self.autosave_checkbox.setChecked(autosave_enabled)
        
        autosave_interval = editor_settings.get("autosave_interval", 5)
        self.autosave_interval_spinbox.setValue(autosave_interval)
        self.autosave_interval_spinbox.setEnabled(autosave_enabled)
        
        # Spell check settings
        spellcheck_enabled = editor_settings.get("spellcheck_enabled", True)
        self.spellcheck_checkbox.setChecked(spellcheck_enabled)
        
        spellcheck_language = editor_settings.get("spellcheck_language", "English (US)")
        self.spellcheck_language_combo.setCurrentText(spellcheck_language)
    
    def get_settings(self):
        """
        Get the current settings from the tab.
        
        Returns:
            A dictionary containing the current settings.
        """
        settings = {}
        
        # Font settings
        font_text = self.font_label.text().replace("Current Font: ", "")
        font_parts = font_text.split(", ")
        if len(font_parts) == 2:
            font_family = font_parts[0]
            font_size = int(font_parts[1].replace("pt", ""))
            settings["font_family"] = font_family
            settings["font_size"] = font_size
        
        # Color settings
        text_color = self.text_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        settings["text_color"] = text_color
        
        background_color = self.background_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        settings["background_color"] = background_color
        
        # Auto-save settings
        settings["autosave_enabled"] = self.autosave_checkbox.isChecked()
        settings["autosave_interval"] = self.autosave_interval_spinbox.value()
        
        # Spell check settings
        settings["spellcheck_enabled"] = self.spellcheck_checkbox.isChecked()
        settings["spellcheck_language"] = self.spellcheck_language_combo.currentText()
        
        return settings
    
    def connect_signals(self, dialog):
        """
        Connect signals to the dialog.
        
        Args:
            dialog: The parent dialog.
        """
        self.font_button.clicked.connect(dialog._on_select_font)
        self.text_color_button.clicked.connect(dialog._on_select_text_color)
        self.background_color_button.clicked.connect(dialog._on_select_background_color)
        self.autosave_checkbox.toggled.connect(dialog._on_autosave_toggled)
