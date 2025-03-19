#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Theme Settings Dialog

This module implements a dialog for configuring UI themes in RebelSCRIBE.
"""

import os
from typing import Dict, List, Optional, Any, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QCheckBox, QColorDialog, QFontDialog,
    QDialogButtonBox, QGroupBox, QScrollArea, QSpinBox,
    QMessageBox, QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette

from src.utils.logging_utils import get_logger
from src.ui.theme_manager import ThemeManager, Theme

logger = get_logger(__name__)


class ColorButton(QPushButton):
    """
    A button that displays a color and opens a color dialog when clicked.
    """
    
    # Signal emitted when the color is changed
    color_changed = pyqtSignal(str, str)  # key, color
    
    def __init__(self, key: str, color: str, parent=None):
        """
        Initialize the color button.
        
        Args:
            key: The color key.
            color: The initial color (hex code).
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.key = key
        self.color = color
        
        # Set button style
        self._update_style()
        
        # Connect clicked signal
        self.clicked.connect(self._on_clicked)
    
    def _update_style(self) -> None:
        """Update the button style to show the current color."""
        self.setStyleSheet(f"background-color: {self.color}; min-width: 60px; min-height: 20px;")
        
        # Set text color based on background brightness
        r, g, b = int(self.color[1:3], 16), int(self.color[3:5], 16), int(self.color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "#000000" if brightness > 128 else "#FFFFFF"
        
        self.setStyleSheet(f"background-color: {self.color}; color: {text_color}; min-width: 60px; min-height: 20px;")
        self.setText(self.color)
    
    def _on_clicked(self) -> None:
        """Handle button click event."""
        # Show color dialog
        color = QColorDialog.getColor(QColor(self.color), self, "Select Color")
        
        if color.isValid():
            # Update color
            self.color = color.name()
            
            # Update button style
            self._update_style()
            
            # Emit color changed signal
            self.color_changed.emit(self.key, self.color)
    
    def set_color(self, color: str) -> None:
        """
        Set the button color.
        
        Args:
            color: The new color (hex code).
        """
        self.color = color
        self._update_style()


class FontButton(QPushButton):
    """
    A button that displays a font and opens a font dialog when clicked.
    """
    
    # Signal emitted when the font is changed
    font_changed = pyqtSignal(str, dict)  # key, font_dict
    
    def __init__(self, key: str, font_dict: Dict[str, Any], parent=None):
        """
        Initialize the font button.
        
        Args:
            key: The font key.
            font_dict: The initial font properties.
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.key = key
        self.font_dict = font_dict
        
        # Set button text
        self._update_text()
        
        # Connect clicked signal
        self.clicked.connect(self._on_clicked)
    
    def _update_text(self) -> None:
        """Update the button text to show the current font."""
        family = self.font_dict.get("family", "Arial")
        size = self.font_dict.get("size", 10)
        weight = "Bold" if self.font_dict.get("weight", 400) >= 700 else "Normal"
        italic = "Italic" if self.font_dict.get("italic", False) else ""
        
        self.setText(f"{family}, {size}pt, {weight} {italic}".strip())
    
    def _on_clicked(self) -> None:
        """Handle button click event."""
        # Create initial font
        initial_font = QFont(
            self.font_dict.get("family", "Arial"),
            self.font_dict.get("size", 10),
            self.font_dict.get("weight", 400),
            self.font_dict.get("italic", False)
        )
        
        # Show font dialog
        ok, font = QFontDialog.getFont(initial_font, self, "Select Font")
        
        if ok:
            # Update font dictionary
            self.font_dict = {
                "family": font.family(),
                "size": font.pointSize(),
                "weight": font.weight(),
                "italic": font.italic()
            }
            
            # Update button text
            self._update_text()
            
            # Emit font changed signal
            self.font_changed.emit(self.key, self.font_dict)
    
    def set_font(self, font_dict: Dict[str, Any]) -> None:
        """
        Set the button font.
        
        Args:
            font_dict: The new font properties.
        """
        self.font_dict = font_dict
        self._update_text()


class ThemePreviewWidget(QWidget):
    """
    A widget that displays a preview of a theme.
    """
    
    def __init__(self, theme: Theme, parent=None):
        """
        Initialize the theme preview widget.
        
        Args:
            theme: The theme to preview.
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.theme = theme
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create preview elements
        self._create_preview()
        
        # Apply theme to preview
        self._apply_theme()
    
    def _create_preview(self) -> None:
        """Create the preview elements."""
        # Window frame
        self.window_frame = QGroupBox("Window")
        window_layout = QVBoxLayout(self.window_frame)
        
        # Menu bar
        menu_layout = QHBoxLayout()
        menu_layout.addWidget(QLabel("File"))
        menu_layout.addWidget(QLabel("Edit"))
        menu_layout.addWidget(QLabel("View"))
        menu_layout.addWidget(QLabel("Project"))
        menu_layout.addWidget(QLabel("AI"))
        menu_layout.addWidget(QLabel("Help"))
        menu_layout.addStretch()
        window_layout.addLayout(menu_layout)
        
        # Content area
        content_layout = QHBoxLayout()
        
        # Binder
        self.binder_frame = QGroupBox("Binder")
        binder_layout = QVBoxLayout(self.binder_frame)
        binder_layout.addWidget(QLabel("Project"))
        binder_layout.addWidget(QLabel("  Manuscript"))
        binder_layout.addWidget(QLabel("    Chapter 1"))
        binder_layout.addWidget(QLabel("    Chapter 2"))
        binder_layout.addWidget(QLabel("  Characters"))
        binder_layout.addWidget(QLabel("  Settings"))
        binder_layout.addWidget(QLabel("  Research"))
        binder_layout.addStretch()
        content_layout.addWidget(self.binder_frame, 1)
        
        # Editor
        self.editor_frame = QGroupBox("Editor")
        editor_layout = QVBoxLayout(self.editor_frame)
        editor_layout.addWidget(QLabel("# Chapter 1"))
        editor_layout.addWidget(QLabel(""))
        editor_layout.addWidget(QLabel("The sun was setting over the mountains, casting long shadows across the valley."))
        editor_layout.addWidget(QLabel(""))
        editor_layout.addWidget(QLabel("\"We should find shelter before nightfall,\" said John, scanning the horizon."))
        editor_layout.addWidget(QLabel(""))
        editor_layout.addWidget(QLabel("*The wind picked up, carrying a chill that made them both shiver.*"))
        editor_layout.addStretch()
        content_layout.addWidget(self.editor_frame, 2)
        
        # Inspector
        self.inspector_frame = QGroupBox("Inspector")
        inspector_layout = QVBoxLayout(self.inspector_frame)
        inspector_layout.addWidget(QLabel("Document"))
        inspector_layout.addWidget(QLabel("Title: Chapter 1"))
        inspector_layout.addWidget(QLabel("Words: 42"))
        inspector_layout.addWidget(QLabel("Characters: 215"))
        inspector_layout.addWidget(QLabel(""))
        inspector_layout.addWidget(QLabel("Synopsis"))
        inspector_layout.addWidget(QLabel("Introduction to the main characters and setting."))
        inspector_layout.addStretch()
        content_layout.addWidget(self.inspector_frame, 1)
        
        window_layout.addLayout(content_layout)
        
        # Status bar
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Chapter 1 - 42 words, 215 characters"))
        status_layout.addStretch()
        window_layout.addLayout(status_layout)
        
        # Add window frame to main layout
        self.layout.addWidget(self.window_frame)
    
    def _apply_theme(self) -> None:
        """Apply the theme to the preview elements."""
        # Set window frame style
        self.window_frame.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.theme.get_color("window")};
                color: {self.theme.get_color("window_text")};
                border: 1px solid {self.theme.get_color("window_text")};
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
            QLabel {{
                color: {self.theme.get_color("window_text")};
            }}
        """)
        
        # Set binder frame style
        self.binder_frame.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.theme.get_color("base")};
                color: {self.theme.get_color("text")};
                border: 1px solid {self.theme.get_color("text")};
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
            QLabel {{
                color: {self.theme.get_color("text")};
            }}
        """)
        
        # Set editor frame style
        self.editor_frame.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.theme.get_color("base")};
                color: {self.theme.get_color("text")};
                border: 1px solid {self.theme.get_color("text")};
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
            QLabel {{
                color: {self.theme.get_color("text")};
            }}
        """)
        
        # Set inspector frame style
        self.inspector_frame.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.theme.get_color("base")};
                color: {self.theme.get_color("text")};
                border: 1px solid {self.theme.get_color("text")};
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
            QLabel {{
                color: {self.theme.get_color("text")};
            }}
        """)
    
    def update_theme(self, theme: Theme) -> None:
        """
        Update the preview with a new theme.
        
        Args:
            theme: The new theme to preview.
        """
        self.theme = theme
        self._apply_theme()


class ThemeSettingsDialog(QDialog):
    """
    Dialog for configuring UI themes in RebelSCRIBE.
    
    This dialog allows users to select, customize, and manage themes.
    """
    
    # Signal emitted when a theme is applied
    theme_applied = pyqtSignal(str)  # theme_name
    
    def __init__(self, parent=None):
        """
        Initialize the theme settings dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.setWindowTitle("Theme Settings")
        self.setMinimumSize(800, 600)
        
        # Create theme manager
        self.theme_manager = ThemeManager()
        
        # Current theme
        self.current_theme_name = self.theme_manager.get_current_theme().name
        self.current_theme = self.theme_manager.get_current_theme()
        
        # Working copy of the current theme (for editing)
        self.working_theme = Theme(
            name=self.current_theme.name,
            description=self.current_theme.description,
            is_dark=self.current_theme.is_dark
        )
        
        # Copy theme properties
        for key, value in self.current_theme.colors.items():
            self.working_theme.set_color(key, value)
        
        for key, value in self.current_theme.fonts.items():
            self.working_theme.set_font(
                key=key,
                family=value.get("family", "Arial"),
                size=value.get("size", 10),
                weight=value.get("weight", 400),
                italic=value.get("italic", False)
            )
        
        for key, value in self.current_theme.editor_settings.items():
            self.working_theme.set_editor_setting(key, value)
        
        for key, value in self.current_theme.syntax_highlighting.items():
            self.working_theme.set_syntax_highlighting(key, value)
        
        # Initialize UI components
        self._init_ui()
        
        logger.info("Theme settings dialog initialized")
    
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        logger.debug("Initializing theme settings dialog UI")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create theme selection area
        self._create_theme_selection()
        
        # Create splitter for preview and settings
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter, 1)
        
        # Create theme preview
        self._create_theme_preview()
        
        # Create theme settings tabs
        self._create_theme_settings()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.layout.addWidget(self.button_box)
        
        # Connect signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        
        logger.debug("Theme settings dialog UI initialized")
    
    def _create_theme_selection(self) -> None:
        """Create the theme selection area."""
        # Create layout
        selection_layout = QHBoxLayout()
        
        # Theme label
        selection_layout.addWidget(QLabel("Theme:"))
        
        # Theme combo box
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_theme_names())
        self.theme_combo.setCurrentText(self.current_theme_name)
        self.theme_combo.currentTextChanged.connect(self._on_theme_selected)
        selection_layout.addWidget(self.theme_combo, 1)
        
        # New theme button
        self.new_theme_button = QPushButton("New")
        self.new_theme_button.clicked.connect(self._on_new_theme)
        selection_layout.addWidget(self.new_theme_button)
        
        # Save theme button
        self.save_theme_button = QPushButton("Save")
        self.save_theme_button.clicked.connect(self._on_save_theme)
        selection_layout.addWidget(self.save_theme_button)
        
        # Delete theme button
        self.delete_theme_button = QPushButton("Delete")
        self.delete_theme_button.clicked.connect(self._on_delete_theme)
        selection_layout.addWidget(self.delete_theme_button)
        
        # Add to main layout
        self.layout.addLayout(selection_layout)
        
        # Update button states
        self._update_button_states()
    
    def _create_theme_preview(self) -> None:
        """Create the theme preview area."""
        # Create preview widget
        self.preview_widget = ThemePreviewWidget(self.working_theme)
        
        # Add to splitter
        self.splitter.addWidget(self.preview_widget)
    
    def _create_theme_settings(self) -> None:
        """Create the theme settings tabs."""
        # Create tab widget
        self.settings_tabs = QTabWidget()
        
        # Create tabs
        self._create_general_tab()
        self._create_colors_tab()
        self._create_fonts_tab()
        self._create_editor_tab()
        self._create_syntax_tab()
        
        # Add to splitter
        self.splitter.addWidget(self.settings_tabs)
        
        # Set splitter sizes
        self.splitter.setSizes([400, 400])
    
    def _create_general_tab(self) -> None:
        """Create the general settings tab."""
        # Create tab widget
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        # Theme name
        self.name_edit = QLineEdit(self.working_theme.name)
        self.name_edit.setEnabled(False)  # Name can't be changed after creation
        general_layout.addRow("Name:", self.name_edit)
        
        # Theme description
        self.description_edit = QLineEdit(self.working_theme.description)
        self.description_edit.textChanged.connect(self._on_description_changed)
        general_layout.addRow("Description:", self.description_edit)
        
        # Dark theme checkbox
        self.dark_theme_checkbox = QCheckBox("Dark Theme")
        self.dark_theme_checkbox.setChecked(self.working_theme.is_dark)
        self.dark_theme_checkbox.toggled.connect(self._on_dark_theme_toggled)
        general_layout.addRow("", self.dark_theme_checkbox)
        
        # Add to tab widget
        self.settings_tabs.addTab(general_tab, "General")
    
    def _create_colors_tab(self) -> None:
        """Create the colors settings tab."""
        # Create tab widget
        colors_tab = QWidget()
        colors_layout = QFormLayout(colors_tab)
        
        # Create color buttons
        self.color_buttons = {}
        
        for key, color in self.working_theme.colors.items():
            # Create button
            button = ColorButton(key, color)
            button.color_changed.connect(self._on_color_changed)
            
            # Add to layout
            colors_layout.addRow(f"{key.replace('_', ' ').title()}:", button)
            
            # Store button
            self.color_buttons[key] = button
        
        # Add to tab widget
        self.settings_tabs.addTab(colors_tab, "Colors")
    
    def _create_fonts_tab(self) -> None:
        """Create the fonts settings tab."""
        # Create tab widget
        fonts_tab = QWidget()
        fonts_layout = QFormLayout(fonts_tab)
        
        # Create font buttons
        self.font_buttons = {}
        
        for key, font_dict in self.working_theme.fonts.items():
            # Create button
            button = FontButton(key, font_dict)
            button.font_changed.connect(self._on_font_changed)
            
            # Add to layout
            fonts_layout.addRow(f"{key.replace('_', ' ').title()}:", button)
            
            # Store button
            self.font_buttons[key] = button
        
        # Add to tab widget
        self.settings_tabs.addTab(fonts_tab, "Fonts")
    
    def _create_editor_tab(self) -> None:
        """Create the editor settings tab."""
        # Create tab widget
        editor_tab = QWidget()
        editor_layout = QFormLayout(editor_tab)
        
        # Line numbers
        self.line_numbers_checkbox = QCheckBox()
        self.line_numbers_checkbox.setChecked(self.working_theme.get_editor_setting("line_numbers", True))
        self.line_numbers_checkbox.toggled.connect(lambda checked: self._on_editor_setting_changed("line_numbers", checked))
        editor_layout.addRow("Show Line Numbers:", self.line_numbers_checkbox)
        
        # Highlight current line
        self.highlight_line_checkbox = QCheckBox()
        self.highlight_line_checkbox.setChecked(self.working_theme.get_editor_setting("highlight_current_line", True))
        self.highlight_line_checkbox.toggled.connect(lambda checked: self._on_editor_setting_changed("highlight_current_line", checked))
        editor_layout.addRow("Highlight Current Line:", self.highlight_line_checkbox)
        
        # Show whitespace
        self.show_whitespace_checkbox = QCheckBox()
        self.show_whitespace_checkbox.setChecked(self.working_theme.get_editor_setting("show_whitespace", False))
        self.show_whitespace_checkbox.toggled.connect(lambda checked: self._on_editor_setting_changed("show_whitespace", checked))
        editor_layout.addRow("Show Whitespace:", self.show_whitespace_checkbox)
        
        # Word wrap
        self.word_wrap_checkbox = QCheckBox()
        self.word_wrap_checkbox.setChecked(self.working_theme.get_editor_setting("word_wrap", True))
        self.word_wrap_checkbox.toggled.connect(lambda checked: self._on_editor_setting_changed("word_wrap", checked))
        editor_layout.addRow("Word Wrap:", self.word_wrap_checkbox)
        
        # Tab width
        self.tab_width_spinbox = QSpinBox()
        self.tab_width_spinbox.setRange(1, 8)
        self.tab_width_spinbox.setValue(self.working_theme.get_editor_setting("tab_width", 4))
        self.tab_width_spinbox.valueChanged.connect(lambda value: self._on_editor_setting_changed("tab_width", value))
        editor_layout.addRow("Tab Width:", self.tab_width_spinbox)
        
        # Use spaces
        self.use_spaces_checkbox = QCheckBox()
        self.use_spaces_checkbox.setChecked(self.working_theme.get_editor_setting("use_spaces", True))
        self.use_spaces_checkbox.toggled.connect(lambda checked: self._on_editor_setting_changed("use_spaces", checked))
        editor_layout.addRow("Use Spaces for Tabs:", self.use_spaces_checkbox)
        
        # Auto indent
        self.auto_indent_checkbox = QCheckBox()
        self.auto_indent_checkbox.setChecked(self.working_theme.get_editor_setting("auto_indent", True))
        self.auto_indent_checkbox.toggled.connect(lambda checked: self._on_editor_setting_changed("auto_indent", checked))
        editor_layout.addRow("Auto Indent:", self.auto_indent_checkbox)
        
        # Line spacing
        self.line_spacing_spinbox = QSpinBox()
        self.line_spacing_spinbox.setRange(100, 200)
        self.line_spacing_spinbox.setSingleStep(10)
        self.line_spacing_spinbox.setSuffix("%")
        self.line_spacing_spinbox.setValue(int(self.working_theme.get_editor_setting("line_spacing", 1.2) * 100))
        self.line_spacing_spinbox.valueChanged.connect(lambda value: self._on_editor_setting_changed("line_spacing", value / 100))
        editor_layout.addRow("Line Spacing:", self.line_spacing_spinbox)
        
        # Add to tab widget
        self.settings_tabs.addTab(editor_tab, "Editor")
    
    def _create_syntax_tab(self) -> None:
        """Create the syntax highlighting settings tab."""
        # Create tab widget
        syntax_tab = QWidget()
        syntax_layout = QFormLayout(syntax_tab)
        
        # Create color buttons
        self.syntax_buttons = {}
        
        for element, color in self.working_theme.syntax_highlighting.items():
            # Create button
            button = ColorButton(element, color)
            button.color_changed.connect(self._on_syntax_color_changed)
            
            # Add to layout
            syntax_layout.addRow(f"{element.replace('_', ' ').title()}:", button)
            
            # Store button
            self.syntax_buttons[element] = button
        
        # Add to tab widget
        self.settings_tabs.addTab(syntax_tab, "Syntax Highlighting")
    
    def _update_button_states(self) -> None:
        """Update the states of the theme management buttons."""
        # Get current theme name
        theme_name = self.theme_combo.currentText()
        
        # Check if theme is a default theme
        is_default = theme_name in self.theme_manager.default_themes
        
        # Save button is enabled for custom themes only
        self.save_theme_button.setEnabled(not is_default)
        
        # Delete button is enabled for custom themes only
        self.delete_theme_button.setEnabled(not is_default)
    
    def _on_theme_selected(self, theme_name: str) -> None:
        """
        Handle theme selection change.
        
        Args:
            theme_name: The name of the selected theme.
        """
        # Get the theme
        theme = self.theme_manager.get_theme(theme_name)
        if not theme:
            logger.error(f"Theme {theme_name} not found")
            return
        
        # Update working theme
        self.working_theme = Theme(
            name=theme.name,
            description=theme.description,
            is_dark=theme.is_dark
        )
        
        # Copy theme properties
        for key, value in theme.colors.items():
            self.working_theme.set_color(key, value)
        
        for key, value in theme.fonts.items():
            self.working_theme.set_font(
                key=key,
                family=value.get("family", "Arial"),
                size=value.get("size", 10),
                weight=value.get("weight", 400),
                italic=value.get("italic", False)
            )
        
        for key, value in theme.editor_settings.items():
            self.working_theme.set_editor_setting(key, value)
        
        for key, value in theme.syntax_highlighting.items():
            self.working_theme.set_syntax_highlighting(key, value)
        
        # Update UI
        self._update_ui()
        
        # Update button states
        self._update_button_states()
    
    def _update_ui(self) -> None:
        """Update the UI to reflect the current working theme."""
        # Update general tab
        self.name_edit.setText(self.working_theme.name)
        self.description_edit.setText(self.working_theme.description)
        self.dark_theme_checkbox.setChecked(self.working_theme.is_dark)
        
        # Update color buttons
        for key, button in self.color_buttons.items():
            button.set_color(self.working_theme.get_color(key, "#000000"))
        
        # Update font buttons
        for key, button in self.font_buttons.items():
            button.set_font(self.working_theme.get_font(key))
        
        # Update editor settings
        self.line_numbers_checkbox.setChecked(self.working_theme.get_editor_setting("line_numbers", True))
        self.highlight_line_checkbox.setChecked(self.working_theme.get_editor_setting("highlight_current_line", True))
        self.show_whitespace_checkbox.setChecked(self.working_theme.get_editor_setting("show_whitespace", False))
        self.word_wrap_checkbox.setChecked(self.working_theme.get_editor_setting("word_wrap", True))
        self.tab_width_spinbox.setValue(self.working_theme.get_editor_setting("tab_width", 4))
        self.use_spaces_checkbox.setChecked(self.working_theme.get_editor_setting("use_spaces", True))
        self.auto_indent_checkbox.setChecked(self.working_theme.get_editor_setting("auto_indent", True))
        self.line_spacing_spinbox.setValue(int(self.working_theme.get_editor_setting("line_spacing", 1.2) * 100))
        
        # Update syntax highlighting buttons
        for element, button in self.syntax_buttons.items():
            button.set_color(self.working_theme.get_syntax_highlighting(element, "#000000"))
        
        # Update preview
        self.preview_widget.update_theme(self.working_theme)
    
    def _on_description_changed(self, description: str) -> None:
        """
        Handle description change.
        
        Args:
            description: The new description.
        """
        self.working_theme.description = description
    
    def _on_dark_theme_toggled(self, checked: bool) -> None:
        """
        Handle dark theme toggle.
        
        Args:
            checked: Whether the checkbox is checked.
        """
        self.working_theme.is_dark = checked
    
    def _on_color_changed(self, key: str, color: str) -> None:
        """
        Handle color change.
        
        Args:
            key: The color key.
            color: The new color.
        """
        # Update working theme
        self.working_theme.set_color(key, color)
        
        # Update preview
        self.preview_widget.update_theme(self.working_theme)
    
    def _on_font_changed(self, key: str, font_dict: Dict[str, Any]) -> None:
        """
        Handle font change.
        
        Args:
            key: The font key.
            font_dict: The new font properties.
        """
        # Update working theme
        self.working_theme.set_font(
            key=key,
            family=font_dict.get("family", "Arial"),
            size=font_dict.get("size", 10),
            weight=font_dict.get("weight", 400),
            italic=font_dict.get("italic", False)
        )
        
        # Update preview
        self.preview_widget.update_theme(self.working_theme)
    
    def _on_editor_setting_changed(self, key: str, value: Any) -> None:
        """
        Handle editor setting change.
        
        Args:
            key: The setting key.
            value: The new value.
        """
        # Update working theme
        self.working_theme.set_editor_setting(key, value)
        
        # Update preview
        self.preview_widget.update_theme(self.working_theme)
    
    def _on_syntax_color_changed(self, element: str, color: str) -> None:
        """
        Handle syntax highlighting color change.
        
        Args:
            element: The syntax element.
            color: The new color.
        """
        # Update working theme
        self.working_theme.set_syntax_highlighting(element, color)
        
        # Update preview
        self.preview_widget.update_theme(self.working_theme)
    
    def _on_new_theme(self) -> None:
        """Handle new theme button click."""
        # Get theme name
        name, ok = QInputDialog.getText(
            self,
            "New Theme",
            "Enter theme name:"
        )
        
        if not ok or not name:
            return
        
        # Check if theme already exists
        if name in self.theme_manager.get_theme_names():
            QMessageBox.warning(
                self,
                "Theme Exists",
                f"A theme with the name '{name}' already exists."
            )
            return
        
        # Get theme description
        description, ok = QInputDialog.getText(
            self,
            "New Theme",
            "Enter theme description:"
        )
        
        if not ok:
            return
        
        # Get base theme
        base_theme_name, ok = QInputDialog.getItem(
            self,
            "New Theme",
            "Select base theme:",
            self.theme_manager.get_theme_names(),
            0,
            False
        )
        
        if not ok:
            return
        
        # Get base theme
        base_theme = self.theme_manager.get_theme(base_theme_name)
        if not base_theme:
            logger.error(f"Base theme {base_theme_name} not found")
            return
        
        try:
            # Create new theme
            theme = self.theme_manager.create_theme(
                name=name,
                description=description,
                is_dark=base_theme.is_dark
            )
            
            # Copy properties from base theme
            for key, value in base_theme.colors.items():
                theme.set_color(key, value)
            
            for key, value in base_theme.fonts.items():
                theme.set_font(
                    key=key,
                    family=value.get("family", "Arial"),
                    size=value.get("size", 10),
                    weight=value.get("weight", 400),
                    italic=value.get("italic", False)
                )
            
            for key, value in base_theme.editor_settings.items():
                theme.set_editor_setting(key, value)
            
            for key, value in base_theme.syntax_highlighting.items():
                theme.set_syntax_highlighting(key, value)
            
            # Save theme
            self.theme_manager.save_theme(theme)
            
            # Update theme combo
            self.theme_combo.addItem(name)
            self.theme_combo.setCurrentText(name)
            
            # Update button states
            self._update_button_states()
            
            QMessageBox.information(
                self,
                "Theme Created",
                f"Theme '{name}' created successfully."
            )
        except Exception as e:
            logger.error(f"Failed to create theme: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create theme: {str(e)}"
            )
    
    def _on_save_theme(self) -> None:
        """Handle save theme button click."""
        # Get current theme name
        theme_name = self.theme_combo.currentText()
        
        # Check if theme is a default theme
        if theme_name in self.theme_manager.default_themes:
            QMessageBox.warning(
                self,
                "Cannot Save",
                f"Cannot save default theme '{theme_name}'. Create a new theme instead."
            )
            return
        
        try:
            # Get theme
            theme = self.theme_manager.get_theme(theme_name)
            if not theme:
                logger.error(f"Theme {theme_name} not found")
                return
            
            # Update theme properties
            theme.description = self.working_theme.description
            theme.is_dark = self.working_theme.is_dark
            
            # Copy colors
            for key, value in self.working_theme.colors.items():
                theme.set_color(key, value)
            
            # Copy fonts
            for key, value in self.working_theme.fonts.items():
                theme.set_font(
                    key=key,
                    family=value.get("family", "Arial"),
                    size=value.get("size", 10),
                    weight=value.get("weight", 400),
                    italic=value.get("italic", False)
                )
            
            # Copy editor settings
            for key, value in self.working_theme.editor_settings.items():
                theme.set_editor_setting(key, value)
            
            # Copy syntax highlighting
            for key, value in self.working_theme.syntax_highlighting.items():
                theme.set_syntax_highlighting(key, value)
            
            # Save theme
            success = self.theme_manager.save_theme(theme)
            
            if success:
                QMessageBox.information(
                    self,
                    "Theme Saved",
                    f"Theme '{theme_name}' saved successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save theme '{theme_name}'."
                )
        except Exception as e:
            logger.error(f"Failed to save theme: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save theme: {str(e)}"
            )
    
    def _on_delete_theme(self) -> None:
        """Handle delete theme button click."""
        # Get current theme name
        theme_name = self.theme_combo.currentText()
        
        # Check if theme is a default theme
        if theme_name in self.theme_manager.default_themes:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"Cannot delete default theme '{theme_name}'."
            )
            return
        
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete theme '{theme_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Delete theme
            success = self.theme_manager.delete_theme(theme_name)
            
            if success:
                # Remove from combo box
                index = self.theme_combo.findText(theme_name)
                if index >= 0:
                    self.theme_combo.removeItem(index)
                
                # Select Light theme
                self.theme_combo.setCurrentText("Light")
                
                QMessageBox.information(
                    self,
                    "Theme Deleted",
                    f"Theme '{theme_name}' deleted successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete theme '{theme_name}'."
                )
        except Exception as e:
            logger.error(f"Failed to delete theme: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete theme: {str(e)}"
            )
    
    def _on_apply(self) -> None:
        """Handle apply button click."""
        # Get current theme name
        theme_name = self.theme_combo.currentText()
        
        # Check if theme is a default theme
        is_default = theme_name in self.theme_manager.default_themes
        
        if is_default:
            # Apply theme directly
            self.theme_manager.set_current_theme(theme_name)
            self.theme_applied.emit(theme_name)
        else:
            try:
                # Get theme
                theme = self.theme_manager.get_theme(theme_name)
                if not theme:
                    logger.error(f"Theme {theme_name} not found")
                    return
                
                # Update theme properties
                theme.description = self.working_theme.description
                theme.is_dark = self.working_theme.is_dark
                
                # Copy colors
                for key, value in self.working_theme.colors.items():
                    theme.set_color(key, value)
                
                # Copy fonts
                for key, value in self.working_theme.fonts.items():
                    theme.set_font(
                        key=key,
                        family=value.get("family", "Arial"),
                        size=value.get("size", 10),
                        weight=value.get("weight", 400),
                        italic=value.get("italic", False)
                    )
                
                # Copy editor settings
                for key, value in self.working_theme.editor_settings.items():
                    theme.set_editor_setting(key, value)
                
                # Copy syntax highlighting
                for key, value in self.working_theme.syntax_highlighting.items():
                    theme.set_syntax_highlighting(key, value)
                
                # Save theme
                success = self.theme_manager.save_theme(theme)
                
                if success:
                    # Apply theme
                    self.theme_manager.set_current_theme(theme_name)
                    self.theme_applied.emit(theme_name)
                else:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to save theme '{theme_name}'."
                    )
            except Exception as e:
                logger.error(f"Failed to apply theme: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to apply theme: {str(e)}"
                )
    
    def accept(self) -> None:
        """Handle OK button click."""
        # Apply theme
        self._on_apply()
        
        # Close dialog
        super().accept()
