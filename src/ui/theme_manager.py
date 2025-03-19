#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Theme Manager

This module implements theme management for RebelSCRIBE, allowing users to
customize the appearance of the application.
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QTextEdit
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QSettings

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.utils.file_utils import ensure_directory, read_json_file, write_json_file

logger = get_logger(__name__)
config = ConfigManager()


class Theme:
    """
    Represents a UI theme for RebelSCRIBE.
    
    A theme defines colors, fonts, and other visual properties for the application.
    """
    
    def __init__(self, name: str, description: str = "", is_dark: bool = False):
        """
        Initialize a theme.
        
        Args:
            name: The name of the theme.
            description: A description of the theme.
            is_dark: Whether this is a dark theme.
        """
        self.name = name
        self.description = description
        self.is_dark = is_dark
        
        # Colors
        self.colors: Dict[str, str] = {}
        
        # Fonts
        self.fonts: Dict[str, Dict[str, Any]] = {}
        
        # Editor settings
        self.editor_settings: Dict[str, Any] = {}
        
        # Syntax highlighting
        self.syntax_highlighting: Dict[str, str] = {}
        
        logger.debug(f"Theme initialized: {name}")
    
    def set_color(self, key: str, color: str) -> None:
        """
        Set a color value.
        
        Args:
            key: The color key.
            color: The color value (hex code).
        """
        self.colors[key] = color
    
    def get_color(self, key: str, default: str = "#000000") -> str:
        """
        Get a color value.
        
        Args:
            key: The color key.
            default: The default color to return if the key is not found.
            
        Returns:
            The color value.
        """
        return self.colors.get(key, default)
    
    def set_font(self, key: str, family: str, size: int, weight: int = 400, italic: bool = False) -> None:
        """
        Set a font.
        
        Args:
            key: The font key.
            family: The font family.
            size: The font size.
            weight: The font weight (400 = normal, 700 = bold).
            italic: Whether the font is italic.
        """
        self.fonts[key] = {
            "family": family,
            "size": size,
            "weight": weight,
            "italic": italic
        }
    
    def get_font(self, key: str) -> Dict[str, Any]:
        """
        Get a font.
        
        Args:
            key: The font key.
            
        Returns:
            The font properties.
        """
        return self.fonts.get(key, {
            "family": "Arial",
            "size": 10,
            "weight": 400,
            "italic": False
        })
    
    def set_editor_setting(self, key: str, value: Any) -> None:
        """
        Set an editor setting.
        
        Args:
            key: The setting key.
            value: The setting value.
        """
        self.editor_settings[key] = value
    
    def get_editor_setting(self, key: str, default: Any = None) -> Any:
        """
        Get an editor setting.
        
        Args:
            key: The setting key.
            default: The default value to return if the key is not found.
            
        Returns:
            The setting value.
        """
        return self.editor_settings.get(key, default)
    
    def set_syntax_highlighting(self, element: str, color: str) -> None:
        """
        Set a syntax highlighting color.
        
        Args:
            element: The syntax element.
            color: The color value (hex code).
        """
        self.syntax_highlighting[element] = color
    
    def get_syntax_highlighting(self, element: str, default: str = "#000000") -> str:
        """
        Get a syntax highlighting color.
        
        Args:
            element: The syntax element.
            default: The default color to return if the element is not found.
            
        Returns:
            The color value.
        """
        return self.syntax_highlighting.get(element, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the theme to a dictionary.
        
        Returns:
            A dictionary representation of the theme.
        """
        return {
            "name": self.name,
            "description": self.description,
            "is_dark": self.is_dark,
            "colors": self.colors,
            "fonts": self.fonts,
            "editor_settings": self.editor_settings,
            "syntax_highlighting": self.syntax_highlighting
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """
        Create a theme from a dictionary.
        
        Args:
            data: The dictionary data.
            
        Returns:
            A new Theme instance.
        """
        theme = cls(
            name=data.get("name", "Unnamed Theme"),
            description=data.get("description", ""),
            is_dark=data.get("is_dark", False)
        )
        
        # Set colors
        for key, value in data.get("colors", {}).items():
            theme.set_color(key, value)
        
        # Set fonts
        for key, font_data in data.get("fonts", {}).items():
            theme.set_font(
                key=key,
                family=font_data.get("family", "Arial"),
                size=font_data.get("size", 10),
                weight=font_data.get("weight", 400),
                italic=font_data.get("italic", False)
            )
        
        # Set editor settings
        for key, value in data.get("editor_settings", {}).items():
            theme.set_editor_setting(key, value)
        
        # Set syntax highlighting
        for element, color in data.get("syntax_highlighting", {}).items():
            theme.set_syntax_highlighting(element, color)
        
        return theme


class ThemeManager:
    """
    Manages themes for RebelSCRIBE.
    
    This class handles loading, saving, and applying themes to the application.
    """
    
    def __init__(self):
        """Initialize the theme manager."""
        # Default themes
        self.default_themes: Dict[str, Theme] = {}
        
        # Custom themes
        self.custom_themes: Dict[str, Theme] = {}
        
        # Current theme
        self.current_theme: Optional[Theme] = None
        
        # Theme directory
        self.theme_dir = os.path.join(
            config.get("application", "data_directory", str(Path.home() / ".rebelscribe")),
            "themes"
        )
        
        # Ensure theme directory exists
        ensure_directory(self.theme_dir)
        
        # Initialize default themes
        self._init_default_themes()
        
        # Load custom themes
        self._load_custom_themes()
        
        # Load current theme
        self._load_current_theme()
        
        logger.info("Theme manager initialized")
    
    def _init_default_themes(self) -> None:
        """Initialize default themes."""
        logger.debug("Initializing default themes")
        
        # Light theme
        light_theme = Theme("Light", "Default light theme", False)
        
        # Set colors
        light_theme.set_color("window", "#FFFFFF")
        light_theme.set_color("window_text", "#000000")
        light_theme.set_color("base", "#F0F0F0")
        light_theme.set_color("alternate_base", "#E0E0E0")
        light_theme.set_color("text", "#000000")
        light_theme.set_color("button", "#E0E0E0")
        light_theme.set_color("button_text", "#000000")
        light_theme.set_color("bright_text", "#FFFFFF")
        light_theme.set_color("highlight", "#308CC6")
        light_theme.set_color("highlighted_text", "#FFFFFF")
        light_theme.set_color("link", "#0000FF")
        light_theme.set_color("visited_link", "#800080")
        
        # Set fonts
        light_theme.set_font("default", "Arial", 10)
        light_theme.set_font("editor", "Consolas", 12)
        light_theme.set_font("heading", "Arial", 14, 700)
        light_theme.set_font("monospace", "Consolas", 10)
        
        # Set editor settings
        light_theme.set_editor_setting("line_numbers", True)
        light_theme.set_editor_setting("highlight_current_line", True)
        light_theme.set_editor_setting("show_whitespace", False)
        light_theme.set_editor_setting("word_wrap", True)
        light_theme.set_editor_setting("tab_width", 4)
        light_theme.set_editor_setting("use_spaces", True)
        light_theme.set_editor_setting("auto_indent", True)
        light_theme.set_editor_setting("line_spacing", 1.2)
        
        # Set syntax highlighting
        light_theme.set_syntax_highlighting("keyword", "#0000FF")
        light_theme.set_syntax_highlighting("operator", "#000000")
        light_theme.set_syntax_highlighting("brace", "#000000")
        light_theme.set_syntax_highlighting("defclass", "#007F7F")
        light_theme.set_syntax_highlighting("string", "#808000")
        light_theme.set_syntax_highlighting("string2", "#808000")
        light_theme.set_syntax_highlighting("comment", "#007F00")
        light_theme.set_syntax_highlighting("self", "#0000FF")
        light_theme.set_syntax_highlighting("numbers", "#7F007F")
        light_theme.set_syntax_highlighting("heading", "#8E44AD")
        light_theme.set_syntax_highlighting("subheading", "#2471A3")
        light_theme.set_syntax_highlighting("dialogue", "#2E86C1")
        light_theme.set_syntax_highlighting("comment_note", "#27AE60")
        
        # Add to default themes
        self.default_themes["Light"] = light_theme
        
        # Dark theme
        dark_theme = Theme("Dark", "Default dark theme", True)
        
        # Set colors
        dark_theme.set_color("window", "#2D2D30")
        dark_theme.set_color("window_text", "#FFFFFF")
        dark_theme.set_color("base", "#1E1E1E")
        dark_theme.set_color("alternate_base", "#3C3C3C")
        dark_theme.set_color("text", "#FFFFFF")
        dark_theme.set_color("button", "#3C3C3C")
        dark_theme.set_color("button_text", "#FFFFFF")
        dark_theme.set_color("bright_text", "#FFFFFF")
        dark_theme.set_color("highlight", "#264F78")
        dark_theme.set_color("highlighted_text", "#FFFFFF")
        dark_theme.set_color("link", "#3794FF")
        dark_theme.set_color("visited_link", "#BB8FCE")
        
        # Set fonts
        dark_theme.set_font("default", "Arial", 10)
        dark_theme.set_font("editor", "Consolas", 12)
        dark_theme.set_font("heading", "Arial", 14, 700)
        dark_theme.set_font("monospace", "Consolas", 10)
        
        # Set editor settings
        dark_theme.set_editor_setting("line_numbers", True)
        dark_theme.set_editor_setting("highlight_current_line", True)
        dark_theme.set_editor_setting("show_whitespace", False)
        dark_theme.set_editor_setting("word_wrap", True)
        dark_theme.set_editor_setting("tab_width", 4)
        dark_theme.set_editor_setting("use_spaces", True)
        dark_theme.set_editor_setting("auto_indent", True)
        dark_theme.set_editor_setting("line_spacing", 1.2)
        
        # Set syntax highlighting
        dark_theme.set_syntax_highlighting("keyword", "#569CD6")
        dark_theme.set_syntax_highlighting("operator", "#D4D4D4")
        dark_theme.set_syntax_highlighting("brace", "#D4D4D4")
        dark_theme.set_syntax_highlighting("defclass", "#4EC9B0")
        dark_theme.set_syntax_highlighting("string", "#CE9178")
        dark_theme.set_syntax_highlighting("string2", "#CE9178")
        dark_theme.set_syntax_highlighting("comment", "#6A9955")
        dark_theme.set_syntax_highlighting("self", "#569CD6")
        dark_theme.set_syntax_highlighting("numbers", "#B5CEA8")
        dark_theme.set_syntax_highlighting("heading", "#C586C0")
        dark_theme.set_syntax_highlighting("subheading", "#9CDCFE")
        dark_theme.set_syntax_highlighting("dialogue", "#4FC1FF")
        dark_theme.set_syntax_highlighting("comment_note", "#6A9955")
        
        # Add to default themes
        self.default_themes["Dark"] = dark_theme
        
        # Sepia theme
        sepia_theme = Theme("Sepia", "Sepia theme for comfortable reading", False)
        
        # Set colors
        sepia_theme.set_color("window", "#F4ECD8")
        sepia_theme.set_color("window_text", "#5B4636")
        sepia_theme.set_color("base", "#FFF4E0")
        sepia_theme.set_color("alternate_base", "#EFE6D4")
        sepia_theme.set_color("text", "#5B4636")
        sepia_theme.set_color("button", "#E0D6C4")
        sepia_theme.set_color("button_text", "#5B4636")
        sepia_theme.set_color("bright_text", "#FFFFFF")
        sepia_theme.set_color("highlight", "#A67D5D")
        sepia_theme.set_color("highlighted_text", "#FFFFFF")
        sepia_theme.set_color("link", "#8B4513")
        sepia_theme.set_color("visited_link", "#A0522D")
        
        # Set fonts
        sepia_theme.set_font("default", "Georgia", 10)
        sepia_theme.set_font("editor", "Georgia", 12)
        sepia_theme.set_font("heading", "Georgia", 14, 700)
        sepia_theme.set_font("monospace", "Consolas", 10)
        
        # Set editor settings
        sepia_theme.set_editor_setting("line_numbers", False)
        sepia_theme.set_editor_setting("highlight_current_line", False)
        sepia_theme.set_editor_setting("show_whitespace", False)
        sepia_theme.set_editor_setting("word_wrap", True)
        sepia_theme.set_editor_setting("tab_width", 4)
        sepia_theme.set_editor_setting("use_spaces", True)
        sepia_theme.set_editor_setting("auto_indent", True)
        sepia_theme.set_editor_setting("line_spacing", 1.5)
        
        # Set syntax highlighting
        sepia_theme.set_syntax_highlighting("keyword", "#8B4513")
        sepia_theme.set_syntax_highlighting("operator", "#5B4636")
        sepia_theme.set_syntax_highlighting("brace", "#5B4636")
        sepia_theme.set_syntax_highlighting("defclass", "#8B4513")
        sepia_theme.set_syntax_highlighting("string", "#A0522D")
        sepia_theme.set_syntax_highlighting("string2", "#A0522D")
        sepia_theme.set_syntax_highlighting("comment", "#6B8E23")
        sepia_theme.set_syntax_highlighting("self", "#8B4513")
        sepia_theme.set_syntax_highlighting("numbers", "#A0522D")
        sepia_theme.set_syntax_highlighting("heading", "#8B4513")
        sepia_theme.set_syntax_highlighting("subheading", "#A0522D")
        sepia_theme.set_syntax_highlighting("dialogue", "#2E86C1")
        sepia_theme.set_syntax_highlighting("comment_note", "#6B8E23")
        
        # Add to default themes
        self.default_themes["Sepia"] = sepia_theme
        
        logger.debug(f"Initialized {len(self.default_themes)} default themes")
    
    def _load_custom_themes(self) -> None:
        """Load custom themes from the theme directory."""
        logger.debug("Loading custom themes")
        
        # Get theme files
        theme_files = [f for f in os.listdir(self.theme_dir) if f.endswith(".json")]
        
        # Load each theme
        for theme_file in theme_files:
            try:
                # Load theme data
                theme_path = os.path.join(self.theme_dir, theme_file)
                theme_data = read_json_file(theme_path)
                
                # Create theme
                theme = Theme.from_dict(theme_data)
                
                # Add to custom themes
                self.custom_themes[theme.name] = theme
                
                logger.debug(f"Loaded custom theme: {theme.name}")
            except Exception as e:
                logger.error(f"Failed to load theme {theme_file}: {str(e)}", exc_info=True)
        
        logger.debug(f"Loaded {len(self.custom_themes)} custom themes")
    
    def _load_current_theme(self) -> None:
        """Load the current theme from settings."""
        logger.debug("Loading current theme")
        
        # Get current theme name from settings
        settings = QSettings()
        theme_name = settings.value("theme", "Light")
        
        # Try to load the theme
        if theme_name in self.default_themes:
            self.current_theme = self.default_themes[theme_name]
            logger.debug(f"Loaded default theme: {theme_name}")
        elif theme_name in self.custom_themes:
            self.current_theme = self.custom_themes[theme_name]
            logger.debug(f"Loaded custom theme: {theme_name}")
        else:
            # Fall back to Light theme
            self.current_theme = self.default_themes["Light"]
            logger.warning(f"Theme {theme_name} not found, falling back to Light theme")
    
    def get_theme_names(self) -> List[str]:
        """
        Get a list of all available theme names.
        
        Returns:
            A list of theme names.
        """
        # Combine default and custom theme names
        return list(self.default_themes.keys()) + list(self.custom_themes.keys())
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """
        Get a theme by name.
        
        Args:
            name: The name of the theme.
            
        Returns:
            The theme, or None if not found.
        """
        # Check default themes
        if name in self.default_themes:
            return self.default_themes[name]
        
        # Check custom themes
        if name in self.custom_themes:
            return self.custom_themes[name]
        
        # Theme not found
        return None
    
    def get_current_theme(self) -> Theme:
        """
        Get the current theme.
        
        Returns:
            The current theme.
        """
        if not self.current_theme:
            # Fall back to Light theme
            self.current_theme = self.default_themes["Light"]
        
        return self.current_theme
    
    def set_current_theme(self, name: str) -> bool:
        """
        Set the current theme.
        
        Args:
            name: The name of the theme.
            
        Returns:
            True if the theme was set, False otherwise.
        """
        # Get the theme
        theme = self.get_theme(name)
        if not theme:
            logger.error(f"Theme {name} not found")
            return False
        
        # Set current theme
        self.current_theme = theme
        
        # Save to settings
        settings = QSettings()
        settings.setValue("theme", name)
        
        logger.info(f"Current theme set to: {name}")
        return True
    
    def create_theme(self, name: str, description: str = "", is_dark: bool = False) -> Theme:
        """
        Create a new custom theme.
        
        Args:
            name: The name of the theme.
            description: A description of the theme.
            is_dark: Whether this is a dark theme.
            
        Returns:
            The new theme.
        """
        # Check if theme already exists
        if name in self.default_themes or name in self.custom_themes:
            logger.error(f"Theme {name} already exists")
            raise ValueError(f"Theme {name} already exists")
        
        # Create new theme
        theme = Theme(name, description, is_dark)
        
        # Add to custom themes
        self.custom_themes[name] = theme
        
        logger.info(f"Created new theme: {name}")
        return theme
    
    def save_theme(self, theme: Theme) -> bool:
        """
        Save a theme to disk.
        
        Args:
            theme: The theme to save.
            
        Returns:
            True if the theme was saved, False otherwise.
        """
        try:
            # Convert theme to dictionary
            theme_data = theme.to_dict()
            
            # Save to file
            theme_path = os.path.join(self.theme_dir, f"{theme.name}.json")
            write_json_file(theme_path, theme_data)
            
            logger.info(f"Saved theme: {theme.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save theme {theme.name}: {str(e)}", exc_info=True)
            return False
    
    def delete_theme(self, name: str) -> bool:
        """
        Delete a custom theme.
        
        Args:
            name: The name of the theme.
            
        Returns:
            True if the theme was deleted, False otherwise.
        """
        # Check if theme exists
        if name not in self.custom_themes:
            logger.error(f"Custom theme {name} not found")
            return False
        
        try:
            # Remove from custom themes
            del self.custom_themes[name]
            
            # Delete file
            theme_path = os.path.join(self.theme_dir, f"{name}.json")
            if os.path.exists(theme_path):
                os.remove(theme_path)
            
            # If current theme was deleted, fall back to Light theme
            if self.current_theme and self.current_theme.name == name:
                self.current_theme = self.default_themes["Light"]
                
                # Save to settings
                settings = QSettings()
                settings.setValue("theme", "Light")
            
            logger.info(f"Deleted theme: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete theme {name}: {str(e)}", exc_info=True)
            return False
    
    def apply_theme(self, app: QApplication) -> None:
        """
        Apply the current theme to the application.
        
        Args:
            app: The QApplication instance.
        """
        if not self.current_theme:
            logger.error("No current theme to apply")
            return
        
        logger.info(f"Applying theme: {self.current_theme.name}")
        
        # Create palette
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.ColorRole.Window, QColor(self.current_theme.get_color("window")))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.current_theme.get_color("window_text")))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.current_theme.get_color("base")))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.current_theme.get_color("alternate_base")))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.current_theme.get_color("text")))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.current_theme.get_color("button")))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.current_theme.get_color("button_text")))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(self.current_theme.get_color("bright_text")))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.current_theme.get_color("highlight")))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.current_theme.get_color("highlighted_text")))
        palette.setColor(QPalette.ColorRole.Link, QColor(self.current_theme.get_color("link")))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(self.current_theme.get_color("visited_link")))
        
        # Apply palette
        app.setPalette(palette)
        
        # Set default font
        default_font = self.current_theme.get_font("default")
        font = QFont(
            default_font["family"],
            default_font["size"],
            default_font["weight"],
            default_font["italic"]
        )
        app.setFont(font)
        
        logger.info(f"Theme applied: {self.current_theme.name}")
    
    def apply_theme_to_editor(self, editor) -> None:
        """
        Apply the current theme to an editor.
        
        Args:
            editor: The editor instance.
        """
        if not self.current_theme:
            logger.error("No current theme to apply")
            return
        
        logger.debug(f"Applying theme to editor: {self.current_theme.name}")
        
        # Set editor font
        editor_font = self.current_theme.get_font("editor")
        font = QFont(
            editor_font["family"],
            editor_font["size"],
            editor_font["weight"],
            editor_font["italic"]
        )
        editor.text_edit.setFont(font)
        
        # Set editor settings
        editor.text_edit.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth if self.current_theme.get_editor_setting("word_wrap", True) else QTextEdit.LineWrapMode.NoWrap
        )
        
        # Update syntax highlighter
        if hasattr(editor, 'highlighter') and editor.highlighter:
            # Update syntax highlighting colors
            for element, format_name in editor.highlighter.rules:
                if format_name in editor.highlighter.formats:
                    color = self.current_theme.get_syntax_highlighting(format_name, "#000000")
                    editor.highlighter.formats[format_name].setForeground(QColor(color))
            
            # Rehighlight
            editor.highlighter.rehighlight()
        
        logger.debug(f"Theme applied to editor: {self.current_theme.name}")
    
    def get_color_scheme(self) -> Dict[str, str]:
        """
        Get the current color scheme.
        
        Returns:
            A dictionary of color keys and values.
        """
        if not self.current_theme:
            return {}
        
        return self.current_theme.colors
    
    def get_font_scheme(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current font scheme.
        
        Returns:
            A dictionary of font keys and properties.
        """
        if not self.current_theme:
            return {}
        
        return self.current_theme.fonts
    
    def get_editor_settings(self) -> Dict[str, Any]:
        """
        Get the current editor settings.
        
        Returns:
            A dictionary of editor settings.
        """
        if not self.current_theme:
            return {}
        
        return self.current_theme.editor_settings
    
    def get_syntax_highlighting_scheme(self) -> Dict[str, str]:
        """
        Get the current syntax highlighting scheme.
        
        Returns:
            A dictionary of syntax element keys and color values.
        """
        if not self.current_theme:
            return {}
        
        return self.current_theme.syntax_highlighting
    
    def is_dark_theme(self) -> bool:
        """
        Check if the current theme is a dark theme.
        
        Returns:
            True if the current theme is dark, False otherwise.
        """
        if not self.current_theme:
            return False
        
        return self.current_theme.is_dark
