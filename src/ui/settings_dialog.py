#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Settings Dialog

This module implements a general settings dialog for RebelSCRIBE.
"""

import sys
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox,
    QFileDialog, QColorDialog, QFontDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from src.utils.logging_utils import get_logger
from src.utils.config_manager import get_config  # Re-export for tests
from src.ui.settings_manager import load_settings
from src.utils.config_manager import get_config
from src.ui.settings_tabs.editor_tab import EditorTab
from src.ui.settings_tabs.interface_tab import InterfaceTab
from src.ui.settings_tabs.file_locations_tab import FileLocationsTab
from src.ui.settings_tabs.shortcuts_tab import ShortcutsTab

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """
    General settings dialog for RebelSCRIBE.
    
    This dialog allows users to configure general application settings including:
    - Editor preferences (font, colors, auto-save)
    - Interface settings (theme, layout)
    - File locations (default save location, backup directory)
    - Keyboard shortcuts
    """
    
    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """
        Initialize the settings dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        # Load current settings
        self._load_settings()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Settings dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing settings dialog UI components")
        
        # Set window properties
        self.setWindowTitle("RebelSCRIBE Settings")
        self.setMinimumSize(600, 450)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.editor_tab = EditorTab()
        self.tab_widget.addTab(self.editor_tab, "Editor")
        
        self.interface_tab = InterfaceTab()
        self.tab_widget.addTab(self.interface_tab, "Interface")
        
        self.file_locations_tab = FileLocationsTab()
        self.tab_widget.addTab(self.file_locations_tab, "File Locations")
        
        self.shortcuts_tab = ShortcutsTab()
        self.tab_widget.addTab(self.shortcuts_tab, "Keyboard Shortcuts")
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply | 
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Settings dialog UI components initialized")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._on_restore_defaults)
        
        # Connect tab signals
        self.editor_tab.connect_signals(self)
        self.interface_tab.connect_signals(self)
        self.file_locations_tab.connect_signals(self)
        self.shortcuts_tab.connect_signals(self)
        
        logger.debug("Signals connected")
    
    def _load_settings(self):
        """Load current settings."""
        logger.debug("Loading current settings")
        
        try:
            # Load settings
            settings = load_settings()
            
            # Load settings into tabs
            self.editor_tab.load_settings(settings)
            self.interface_tab.load_settings(settings)
            self.file_locations_tab.load_settings(settings)
            self.shortcuts_tab.load_settings(settings)
            
            logger.debug("Current settings loaded")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load settings: {e}")
    
    def _get_current_settings(self) -> Dict[str, Any]:
        """
        Get current settings from the dialog.
        
        Returns:
            A dictionary containing the current settings.
        """
        logger.debug("Getting current settings from dialog")
        
        settings = {}
        
        # Get settings from tabs
        settings["editor"] = self.editor_tab.get_settings()
        settings["interface"] = self.interface_tab.get_settings()
        settings["file_locations"] = self.file_locations_tab.get_settings()
        settings["shortcuts"] = self.shortcuts_tab.get_settings()
        
        logger.debug("Current settings retrieved from dialog")
        
        return settings
    
    def _save_settings(self):
        """Save current settings."""
        logger.debug("Saving current settings")
        
        try:
            # Get current settings
            settings = self._get_current_settings()
            
            # Get config instance
            config = get_config()
            
            # Save settings
            if config.update_settings(settings):
                # Emit settings changed signal
                self.settings_changed.emit(settings)
                
                logger.debug("Settings saved successfully")
                return True
            else:
                logger.error("Failed to save settings")
                QMessageBox.warning(self, "Error", "Failed to save settings")
                return False
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
            return False
    
    def _on_accept(self):
        """Handle accept button clicked."""
        logger.debug("Accept button clicked")
        
        # Save settings
        if self._save_settings():
            # Accept dialog
            self.accept()
    
    def _on_apply(self):
        """Handle apply button clicked."""
        logger.debug("Apply button clicked")
        
        # Save settings
        self._save_settings()
    
    def _on_restore_defaults(self):
        """Handle restore defaults button clicked."""
        logger.debug("Restore defaults button clicked")
        
        # Confirm with user
        result = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Get config instance
            config = get_config()
            
            # Reset settings to defaults
            if config.reset_to_defaults():
                # Reload settings
                self._load_settings()
                
                logger.debug("Settings restored to defaults")
            else:
                logger.error("Failed to reset settings to defaults")
                QMessageBox.warning(self, "Error", "Failed to reset settings to defaults")
    
    def _on_select_font(self):
        """Handle select font button clicked."""
        logger.debug("Select font button clicked")
        
        # Get current font
        font_text = self.editor_tab.font_label.text().replace("Current Font: ", "")
        font_parts = font_text.split(", ")
        if len(font_parts) == 2:
            font_family = font_parts[0]
            font_size = int(font_parts[1].replace("pt", ""))
            current_font = QFont(font_family, font_size)
        else:
            current_font = QFont("Arial", 12)
        
        # Show font dialog
        font, ok = QFontDialog.getFont(current_font, self, "Select Font")
        
        if ok:
            # Update font label
            self.editor_tab.font_label.setText(f"Current Font: {font.family()}, {font.pointSize()}pt")
            
            logger.debug(f"Font selected: {font.family()}, {font.pointSize()}pt")
    
    def _on_select_text_color(self):
        """Handle select text color button clicked."""
        logger.debug("Select text color button clicked")
        
        # Get current color
        current_color_str = self.editor_tab.text_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        current_color = QColor(current_color_str)
        
        # Show color dialog
        color = QColorDialog.getColor(current_color, self, "Select Text Color")
        
        if color.isValid():
            # Update color preview
            self.editor_tab.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #CCCCCC;")
            
            logger.debug(f"Text color selected: {color.name()}")
    
    def _on_select_background_color(self):
        """Handle select background color button clicked."""
        logger.debug("Select background color button clicked")
        
        # Get current color
        current_color_str = self.editor_tab.background_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        current_color = QColor(current_color_str)
        
        # Show color dialog
        color = QColorDialog.getColor(current_color, self, "Select Background Color")
        
        if color.isValid():
            # Update color preview
            self.editor_tab.background_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #CCCCCC;")
            
            logger.debug(f"Background color selected: {color.name()}")
    
    def _on_autosave_toggled(self, checked: bool):
        """
        Handle autosave checkbox toggled.
        
        Args:
            checked: Whether the checkbox is checked.
        """
        logger.debug(f"Autosave toggled: {checked}")
        
        # Enable/disable autosave interval spinbox
        self.editor_tab.autosave_interval_spinbox.setEnabled(checked)
    
    def _on_theme_changed(self, theme: str):
        """
        Handle theme combo box changed.
        
        Args:
            theme: The new theme.
        """
        logger.debug(f"Theme changed: {theme}")
        
        # Apply theme preview (optional)
        # This could be implemented to show a preview of the theme
    
    def _on_select_accent_color(self):
        """Handle select accent color button clicked."""
        logger.debug("Select accent color button clicked")
        
        # Get current color
        current_color_str = self.interface_tab.accent_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        current_color = QColor(current_color_str)
        
        # Show color dialog
        color = QColorDialog.getColor(current_color, self, "Select Accent Color")
        
        if color.isValid():
            # Update color preview
            self.interface_tab.accent_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #CCCCCC;")
            
            logger.debug(f"Accent color selected: {color.name()}")
    
    def _on_select_save_location(self):
        """Handle select save location button clicked."""
        logger.debug("Select save location button clicked")
        
        # Show directory dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Save Location",
            self.file_locations_tab.save_location_edit.text() or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Update save location edit
            self.file_locations_tab.save_location_edit.setText(directory)
            
            logger.debug(f"Save location selected: {directory}")
    
    def _on_select_backup_location(self):
        """Handle select backup location button clicked."""
        logger.debug("Select backup location button clicked")
        
        # Show directory dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self.file_locations_tab.backup_location_edit.text() or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Update backup location edit
            self.file_locations_tab.backup_location_edit.setText(directory)
            
            logger.debug(f"Backup location selected: {directory}")
    
    def _on_enable_backups_toggled(self, checked: bool):
        """
        Handle enable backups checkbox toggled.
        
        Args:
            checked: Whether the checkbox is checked.
        """
        logger.debug(f"Enable backups toggled: {checked}")
        
        # Enable/disable backup settings
        self.file_locations_tab.backup_interval_spinbox.setEnabled(checked)
        self.file_locations_tab.max_backups_spinbox.setEnabled(checked)
    
    def _on_reset_shortcuts(self):
        """Handle reset shortcuts button clicked."""
        logger.debug("Reset shortcuts button clicked")
        
        # Confirm with user
        result = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Are you sure you want to reset all keyboard shortcuts to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Reset shortcuts to defaults
            self.shortcuts_tab.reset_to_defaults()
            
            logger.debug("Shortcuts reset to defaults")
    
    # Properties for test compatibility
    
    # Editor tab properties
    @property
    def font_button(self):
        return self.editor_tab.font_button
    
    @property
    def font_label(self):
        return self.editor_tab.font_label
    
    @property
    def text_color_button(self):
        return self.editor_tab.text_color_button
    
    @property
    def text_color_preview(self):
        return self.editor_tab.text_color_preview
    
    @property
    def background_color_button(self):
        return self.editor_tab.background_color_button
    
    @property
    def background_color_preview(self):
        return self.editor_tab.background_color_preview
    
    @property
    def autosave_checkbox(self):
        return self.editor_tab.autosave_checkbox
    
    @property
    def autosave_interval_spinbox(self):
        return self.editor_tab.autosave_interval_spinbox
    
    @property
    def spellcheck_checkbox(self):
        return self.editor_tab.spellcheck_checkbox
    
    @property
    def spellcheck_language_combo(self):
        return self.editor_tab.spellcheck_language_combo
    
    # Interface tab properties
    @property
    def theme_combo(self):
        return self.interface_tab.theme_combo
    
    @property
    def accent_color_button(self):
        return self.interface_tab.accent_color_button
    
    @property
    def accent_color_preview(self):
        return self.interface_tab.accent_color_preview
    
    @property
    def show_toolbar_checkbox(self):
        return self.interface_tab.show_toolbar_checkbox
    
    @property
    def show_statusbar_checkbox(self):
        return self.interface_tab.show_statusbar_checkbox
    
    @property
    def show_line_numbers_checkbox(self):
        return self.interface_tab.show_line_numbers_checkbox
    
    @property
    def restore_session_checkbox(self):
        return self.interface_tab.restore_session_checkbox
    
    @property
    def show_welcome_checkbox(self):
        return self.interface_tab.show_welcome_checkbox
    
    # File locations tab properties
    @property
    def save_location_edit(self):
        return self.file_locations_tab.save_location_edit
    
    @property
    def save_location_button(self):
        return self.file_locations_tab.save_location_button
    
    @property
    def backup_location_edit(self):
        return self.file_locations_tab.backup_location_edit
    
    @property
    def backup_location_button(self):
        return self.file_locations_tab.backup_location_button
    
    @property
    def enable_backups_checkbox(self):
        return self.file_locations_tab.enable_backups_checkbox
    
    @property
    def backup_interval_spinbox(self):
        return self.file_locations_tab.backup_interval_spinbox
    
    @property
    def max_backups_spinbox(self):
        return self.file_locations_tab.max_backups_spinbox
    
    # Shortcuts tab properties
    @property
    def new_project_shortcut(self):
        return self.shortcuts_tab.new_project_shortcut
    
    @property
    def open_project_shortcut(self):
        return self.shortcuts_tab.open_project_shortcut
    
    @property
    def save_shortcut(self):
        return self.shortcuts_tab.save_shortcut
    
    @property
    def save_as_shortcut(self):
        return self.shortcuts_tab.save_as_shortcut
    
    @property
    def undo_shortcut(self):
        return self.shortcuts_tab.undo_shortcut
    
    @property
    def redo_shortcut(self):
        return self.shortcuts_tab.redo_shortcut
    
    @property
    def cut_shortcut(self):
        return self.shortcuts_tab.cut_shortcut
    
    @property
    def copy_shortcut(self):
        return self.shortcuts_tab.copy_shortcut
    
    @property
    def paste_shortcut(self):
        return self.shortcuts_tab.paste_shortcut
    
    @property
    def distraction_free_shortcut(self):
        return self.shortcuts_tab.distraction_free_shortcut
    
    @property
    def focus_mode_shortcut(self):
        return self.shortcuts_tab.focus_mode_shortcut
    
    @property
    def reset_shortcuts_button(self):
        return self.shortcuts_tab.reset_shortcuts_button
