#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Shortcuts Settings Tab

This module implements the keyboard shortcuts settings tab for the settings dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
    QPushButton, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ShortcutsTab(QWidget):
    """Keyboard shortcuts settings tab for the settings dialog."""
    
    def __init__(self, parent=None):
        """
        Initialize the shortcuts tab.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Shortcuts tab initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Shortcuts group
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QFormLayout(shortcuts_group)
        
        # File shortcuts
        shortcuts_layout.addRow(QLabel("<b>File</b>"))
        
        self.new_project_shortcut = QLineEdit("Ctrl+N")
        shortcuts_layout.addRow("New Project:", self.new_project_shortcut)
        
        self.open_project_shortcut = QLineEdit("Ctrl+O")
        shortcuts_layout.addRow("Open Project:", self.open_project_shortcut)
        
        self.save_shortcut = QLineEdit("Ctrl+S")
        shortcuts_layout.addRow("Save:", self.save_shortcut)
        
        self.save_as_shortcut = QLineEdit("Ctrl+Shift+S")
        shortcuts_layout.addRow("Save As:", self.save_as_shortcut)
        
        # Edit shortcuts
        shortcuts_layout.addRow(QLabel("<b>Edit</b>"))
        
        self.undo_shortcut = QLineEdit("Ctrl+Z")
        shortcuts_layout.addRow("Undo:", self.undo_shortcut)
        
        self.redo_shortcut = QLineEdit("Ctrl+Y")
        shortcuts_layout.addRow("Redo:", self.redo_shortcut)
        
        self.cut_shortcut = QLineEdit("Ctrl+X")
        shortcuts_layout.addRow("Cut:", self.cut_shortcut)
        
        self.copy_shortcut = QLineEdit("Ctrl+C")
        shortcuts_layout.addRow("Copy:", self.copy_shortcut)
        
        self.paste_shortcut = QLineEdit("Ctrl+V")
        shortcuts_layout.addRow("Paste:", self.paste_shortcut)
        
        # View shortcuts
        shortcuts_layout.addRow(QLabel("<b>View</b>"))
        
        self.distraction_free_shortcut = QLineEdit("F11")
        shortcuts_layout.addRow("Distraction Free Mode:", self.distraction_free_shortcut)
        
        self.focus_mode_shortcut = QLineEdit("Ctrl+Shift+F")
        shortcuts_layout.addRow("Focus Mode:", self.focus_mode_shortcut)
        
        layout.addWidget(shortcuts_group)
        
        # Reset shortcuts button
        self.reset_shortcuts_button = QPushButton("Reset to Defaults")
        layout.addWidget(self.reset_shortcuts_button)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def load_settings(self, settings):
        """
        Load settings into the tab.
        
        Args:
            settings: The settings dictionary.
        """
        shortcuts = settings.get("shortcuts", {})
        
        # File shortcuts
        self.new_project_shortcut.setText(shortcuts.get("new_project", "Ctrl+N"))
        self.open_project_shortcut.setText(shortcuts.get("open_project", "Ctrl+O"))
        self.save_shortcut.setText(shortcuts.get("save", "Ctrl+S"))
        self.save_as_shortcut.setText(shortcuts.get("save_as", "Ctrl+Shift+S"))
        
        # Edit shortcuts
        self.undo_shortcut.setText(shortcuts.get("undo", "Ctrl+Z"))
        self.redo_shortcut.setText(shortcuts.get("redo", "Ctrl+Y"))
        self.cut_shortcut.setText(shortcuts.get("cut", "Ctrl+X"))
        self.copy_shortcut.setText(shortcuts.get("copy", "Ctrl+C"))
        self.paste_shortcut.setText(shortcuts.get("paste", "Ctrl+V"))
        
        # View shortcuts
        self.distraction_free_shortcut.setText(shortcuts.get("distraction_free", "F11"))
        self.focus_mode_shortcut.setText(shortcuts.get("focus_mode", "Ctrl+Shift+F"))
    
    def get_settings(self):
        """
        Get the current settings from the tab.
        
        Returns:
            A dictionary containing the current settings.
        """
        settings = {}
        
        # File shortcuts
        settings["new_project"] = self.new_project_shortcut.text()
        settings["open_project"] = self.open_project_shortcut.text()
        settings["save"] = self.save_shortcut.text()
        settings["save_as"] = self.save_as_shortcut.text()
        
        # Edit shortcuts
        settings["undo"] = self.undo_shortcut.text()
        settings["redo"] = self.redo_shortcut.text()
        settings["cut"] = self.cut_shortcut.text()
        settings["copy"] = self.copy_shortcut.text()
        settings["paste"] = self.paste_shortcut.text()
        
        # View shortcuts
        settings["distraction_free"] = self.distraction_free_shortcut.text()
        settings["focus_mode"] = self.focus_mode_shortcut.text()
        
        return settings
    
    def reset_to_defaults(self):
        """Reset shortcuts to default values."""
        self.new_project_shortcut.setText("Ctrl+N")
        self.open_project_shortcut.setText("Ctrl+O")
        self.save_shortcut.setText("Ctrl+S")
        self.save_as_shortcut.setText("Ctrl+Shift+S")
        self.undo_shortcut.setText("Ctrl+Z")
        self.redo_shortcut.setText("Ctrl+Y")
        self.cut_shortcut.setText("Ctrl+X")
        self.copy_shortcut.setText("Ctrl+C")
        self.paste_shortcut.setText("Ctrl+V")
        self.distraction_free_shortcut.setText("F11")
        self.focus_mode_shortcut.setText("Ctrl+Shift+F")
    
    def connect_signals(self, dialog):
        """
        Connect signals to the dialog.
        
        Args:
            dialog: The parent dialog.
        """
        self.reset_shortcuts_button.clicked.connect(dialog._on_reset_shortcuts)
