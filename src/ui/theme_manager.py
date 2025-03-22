#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Theme Manager

This module implements the theme manager for RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings, QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ThemeManager(QObject):
    """
    Theme manager for RebelSCRIBE.
    
    This class manages the theme settings for RebelSCRIBE.
    """
    
    # Signal emitted when the theme is changed
    theme_changed = pyqtSignal()
    
    def __init__(self):
        """Initialize the theme manager."""
        super().__init__()
        
        # Load settings
        self.settings = QSettings()
        
        logger.debug("Theme manager initialized")
    
    def apply_theme(self, app=None):
        """
        Apply the current theme to the application.
        
        Args:
            app: The application to apply the theme to. If None, the current application is used.
        """
        logger.debug("Applying theme")
        
        # Get application
        if app is None:
            app = QApplication.instance()
        
        if app is None:
            logger.warning("No application instance found")
            return
        
        # Get theme
        theme = self.settings.value("theme", "System")
        
        # Apply theme
        if theme == "Light":
            self._apply_light_theme(app)
        elif theme == "Dark":
            self._apply_dark_theme(app)
        elif theme == "System":
            self._apply_system_theme(app)
        elif theme == "Custom":
            self._apply_custom_theme(app)
        else:
            logger.warning(f"Unknown theme: {theme}")
            self._apply_system_theme(app)
        
        # Apply editor settings
        self._apply_editor_settings()
        
        # Emit theme changed signal
        self.theme_changed.emit()
        
        logger.debug(f"Applied theme: {theme}")
    
    def _apply_light_theme(self, app):
        """
        Apply light theme to the application.
        
        Args:
            app: The application to apply the theme to.
        """
        # Create palette
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        # Set palette
        app.setPalette(palette)
        
        # Set style sheet
        app.setStyleSheet("")
    
    def _apply_dark_theme(self, app):
        """
        Apply dark theme to the application.
        
        Args:
            app: The application to apply the theme to.
        """
        # Create palette
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        # Set palette
        app.setPalette(palette)
        
        # Set style sheet
        app.setStyleSheet("")
    
    def _apply_system_theme(self, app):
        """
        Apply system theme to the application.
        
        Args:
            app: The application to apply the theme to.
        """
        # Reset palette
        app.setPalette(QPalette())
        
        # Reset style sheet
        app.setStyleSheet("")
    
    def _apply_custom_theme(self, app):
        """
        Apply custom theme to the application.
        
        Args:
            app: The application to apply the theme to.
        """
        # Create palette
        palette = QPalette()
        
        # Get colors
        accent_color = QColor(self.settings.value("ui/accentColor", "#007bff"))
        background_color = QColor(self.settings.value("ui/backgroundColor", "#ffffff"))
        text_color = QColor(self.settings.value("ui/textColor", "#000000"))
        
        # Set colors
        palette.setColor(QPalette.ColorRole.Window, background_color)
        palette.setColor(QPalette.ColorRole.WindowText, text_color)
        palette.setColor(QPalette.ColorRole.Base, background_color.lighter(110))
        palette.setColor(QPalette.ColorRole.AlternateBase, background_color)
        palette.setColor(QPalette.ColorRole.ToolTipBase, background_color)
        palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
        palette.setColor(QPalette.ColorRole.Text, text_color)
        palette.setColor(QPalette.ColorRole.Button, background_color)
        palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        palette.setColor(QPalette.ColorRole.BrightText, text_color.lighter(150))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        # Set palette
        app.setPalette(palette)
        
        # Set style sheet
        app.setStyleSheet(f"""
            QToolTip {{
                color: {text_color.name()};
                background-color: {background_color.name()};
                border: 1px solid {accent_color.name()};
            }}
            
            QPushButton {{
                background-color: {background_color.name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: {accent_color.name()};
                color: white;
            }}
            
            QComboBox {{
                background-color: {background_color.name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                padding: 5px;
            }}
            
            QLineEdit {{
                background-color: {background_color.lighter(110).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                padding: 5px;
            }}
            
            QTextEdit {{
                background-color: {background_color.lighter(110).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                padding: 5px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {accent_color.name()};
            }}
            
            QTabBar::tab {{
                background-color: {background_color.name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                padding: 5px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {accent_color.name()};
                color: white;
            }}
        """)
    
    def _apply_editor_settings(self):
        """Apply editor settings."""
        # Get editor settings
        font = self.settings.value("editor/font", "Consolas")
        font_size = self.settings.value("editor/fontSize", 12, type=int)
        line_numbers = self.settings.value("editor/lineNumbers", True, type=bool)
        syntax_highlighting = self.settings.value("editor/syntaxHighlighting", True, type=bool)
        
        # Apply editor settings
        # This is a placeholder for now
        logger.debug(f"Applied editor settings: font={font}, fontSize={font_size}, lineNumbers={line_numbers}, syntaxHighlighting={syntax_highlighting}")
