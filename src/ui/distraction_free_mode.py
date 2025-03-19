#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Distraction Free Mode

This module implements a distraction-free writing environment for RebelSCRIBE.
"""

import sys
from typing import Optional, Dict, List, Tuple, Callable

from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QToolBar,
    QPushButton, QDialog, QLabel, QSlider, QComboBox,
    QMainWindow, QApplication, QFrame, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QRect, QEvent
from PyQt6.QtGui import (
    QTextCharFormat, QFont, QColor, QTextCursor, QKeySequence,
    QTextDocument, QTextBlockFormat, QPalette, QAction, QIcon,
    QFontMetrics, QResizeEvent, QMouseEvent, QKeyEvent
)
# Import QShortcut explicitly from QtGui to avoid any confusion
from PyQt6.QtGui import QShortcut

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ui.editor.editor_view import EditorView

logger = get_logger(__name__)
config = ConfigManager()


class DistractionFreeMode(QMainWindow):
    """
    Distraction-free writing environment for RebelSCRIBE.
    
    This class implements a distraction-free writing mode that provides:
    - Full-screen mode with minimal UI
    - Focus mode that highlights only the current paragraph/sentence
    - Typewriter scrolling to keep the cursor at the center of the screen
    - Theme switching between light and dark modes
    """
    
    # Signal emitted when distraction-free mode is closed
    closed = pyqtSignal(str)  # content
    
    def __init__(self, parent=None, content: str = "", document_title: str = "Untitled"):
        """
        Initialize the distraction-free mode.
        
        Args:
            parent: The parent widget.
            content: The initial content to display.
            document_title: The title of the document.
        """
        super().__init__(parent)
        
        # Store document info
        self.document_title = document_title
        self.original_content = content
        
        # Initialize UI components
        self._init_ui()
        
        # Set content
        self.editor.setPlainText(content)
        
        # Initialize settings
        self._init_settings()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Distraction-free mode initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing distraction-free mode UI components")
        
        # Set window properties
        self.setWindowTitle(f"RebelSCRIBE - Distraction Free Mode - {self.document_title}")
        self.setWindowFlags(Qt.WindowType.Window)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(0)
        
        # Create editor
        self.editor = QTextEdit()
        self.editor.setFrameStyle(QFrame.Shape.NoFrame)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.editor.setAcceptRichText(False)  # Plain text only
        
        # Set editor font
        font = QFont("Times New Roman", 14)
        self.editor.setFont(font)
        
        # Add editor to layout
        self.layout.addWidget(self.editor)
        
        # Create toolbar (hidden by default)
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.hide()
        self.layout.addWidget(self.toolbar)
        
        # Create toolbar actions
        self._create_toolbar_actions()
        
        # Create context menu
        self._create_context_menu()
        
        # Create shortcuts
        self._create_shortcuts()
        
        logger.debug("Distraction-free mode UI components initialized")
    
    def _create_toolbar_actions(self):
        """Create toolbar actions."""
        logger.debug("Creating toolbar actions")
        
        # Exit action
        self.exit_action = QAction("Exit Distraction-Free Mode", self)
        self.exit_action.triggered.connect(self.close)
        self.toolbar.addAction(self.exit_action)
        
        self.toolbar.addSeparator()
        
        # Toggle focus mode action
        self.focus_mode_action = QAction("Focus Mode", self)
        self.focus_mode_action.setCheckable(True)
        self.focus_mode_action.triggered.connect(self._toggle_focus_mode)
        self.toolbar.addAction(self.focus_mode_action)
        
        # Toggle typewriter scrolling action
        self.typewriter_scrolling_action = QAction("Typewriter Scrolling", self)
        self.typewriter_scrolling_action.setCheckable(True)
        self.typewriter_scrolling_action.triggered.connect(self._toggle_typewriter_scrolling)
        self.toolbar.addAction(self.typewriter_scrolling_action)
        
        self.toolbar.addSeparator()
        
        # Theme selector
        self.theme_label = QLabel("Theme:")
        self.toolbar.addWidget(self.theme_label)
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark", "Sepia"])
        self.theme_selector.currentTextChanged.connect(self._on_theme_changed)
        self.toolbar.addWidget(self.theme_selector)
        
        self.toolbar.addSeparator()
        
        # Width slider
        self.width_label = QLabel("Width:")
        self.toolbar.addWidget(self.width_label)
        
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(30)
        self.width_slider.setMaximum(100)
        self.width_slider.setValue(70)
        self.width_slider.setFixedWidth(100)
        self.width_slider.valueChanged.connect(self._on_width_changed)
        self.toolbar.addWidget(self.width_slider)
        
        logger.debug("Toolbar actions created")
    
    def _create_context_menu(self):
        """Create context menu."""
        logger.debug("Creating context menu")
        
        self.context_menu = QMenu(self)
        
        # Add actions to context menu
        self.context_menu.addAction(self.exit_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.focus_mode_action)
        self.context_menu.addAction(self.typewriter_scrolling_action)
        
        # Theme submenu
        self.theme_menu = self.context_menu.addMenu("Theme")
        
        self.light_theme_action = QAction("Light", self)
        self.light_theme_action.triggered.connect(lambda: self._set_theme("Light"))
        self.theme_menu.addAction(self.light_theme_action)
        
        self.dark_theme_action = QAction("Dark", self)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme("Dark"))
        self.theme_menu.addAction(self.dark_theme_action)
        
        self.sepia_theme_action = QAction("Sepia", self)
        self.sepia_theme_action.triggered.connect(lambda: self._set_theme("Sepia"))
        self.theme_menu.addAction(self.sepia_theme_action)
        
        logger.debug("Context menu created")
    
    def _create_shortcuts(self):
        """Create keyboard shortcuts."""
        logger.debug("Creating keyboard shortcuts")
        
        # Escape to exit
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.escape_shortcut.activated.connect(self.close)
        
        # F11 to toggle full-screen
        self.fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self.fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
        
        # Ctrl+F to toggle focus mode
        self.focus_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.focus_shortcut.activated.connect(self._toggle_focus_mode)
        
        # Ctrl+T to toggle typewriter scrolling
        self.typewriter_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.typewriter_shortcut.activated.connect(self._toggle_typewriter_scrolling)
        
        # Ctrl+L to toggle toolbar
        self.toolbar_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.toolbar_shortcut.activated.connect(self._toggle_toolbar)
        
        # Theme shortcuts
        self.light_theme_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        self.light_theme_shortcut.activated.connect(lambda: self._set_theme("Light"))
        
        self.dark_theme_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        self.dark_theme_shortcut.activated.connect(lambda: self._set_theme("Dark"))
        
        self.sepia_theme_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        self.sepia_theme_shortcut.activated.connect(lambda: self._set_theme("Sepia"))
        
        logger.debug("Keyboard shortcuts created")
    
    def _init_settings(self):
        """Initialize settings."""
        logger.debug("Initializing settings")
        
        # Default settings
        self.is_fullscreen = False
        self.focus_mode_enabled = False
        self.typewriter_scrolling_enabled = False
        self.current_theme = "Light"
        self.editor_width_percent = 70
        
        # Apply default settings
        self._set_theme(self.current_theme)
        self._update_editor_width()
        
        # Enter full-screen mode by default
        self._toggle_fullscreen()
        
        logger.debug("Settings initialized")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect editor signals
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.cursorPositionChanged.connect(self._on_cursor_position_changed)
        
        logger.debug("Signals connected")
    
    def _toggle_fullscreen(self):
        """Toggle full-screen mode."""
        logger.debug(f"Toggling full-screen mode: {not self.is_fullscreen}")
        
        if self.is_fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        
        self.is_fullscreen = not self.is_fullscreen
    
    def _toggle_focus_mode(self):
        """Toggle focus mode."""
        logger.debug(f"Toggling focus mode: {not self.focus_mode_enabled}")
        
        self.focus_mode_enabled = not self.focus_mode_enabled
        self.focus_mode_action.setChecked(self.focus_mode_enabled)
        
        # Apply focus mode
        self._apply_focus_mode()
    
    def _toggle_typewriter_scrolling(self):
        """Toggle typewriter scrolling."""
        logger.debug(f"Toggling typewriter scrolling: {not self.typewriter_scrolling_enabled}")
        
        self.typewriter_scrolling_enabled = not self.typewriter_scrolling_enabled
        self.typewriter_scrolling_action.setChecked(self.typewriter_scrolling_enabled)
        
        # Apply typewriter scrolling
        if self.typewriter_scrolling_enabled:
            self._apply_typewriter_scrolling()
    
    def _toggle_toolbar(self):
        """Toggle toolbar visibility."""
        logger.debug(f"Toggling toolbar visibility: {not self.toolbar.isVisible()}")
        
        self.toolbar.setVisible(not self.toolbar.isVisible())
    
    def _on_theme_changed(self, theme: str):
        """
        Handle theme selector value changed.
        
        Args:
            theme: The new theme name.
        """
        logger.debug(f"Theme changed: {theme}")
        self._set_theme(theme)
    
    def _set_theme(self, theme: str):
        """
        Set the theme.
        
        Args:
            theme: The theme name ("Light", "Dark", or "Sepia").
        """
        logger.debug(f"Setting theme: {theme}")
        
        self.current_theme = theme
        self.theme_selector.setCurrentText(theme)
        
        # Apply theme
        if theme == "Light":
            self._apply_light_theme()
        elif theme == "Dark":
            self._apply_dark_theme()
        elif theme == "Sepia":
            self._apply_sepia_theme()
    
    def _apply_light_theme(self):
        """Apply light theme."""
        logger.debug("Applying light theme")
        
        # Set editor colors
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                color: #000000;
            }
        """)
        
        # Set window background
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F5F5F5"))
        self.setPalette(palette)
    
    def _apply_dark_theme(self):
        """Apply dark theme."""
        logger.debug("Applying dark theme")
        
        # Set editor colors
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D30;
                color: #E0E0E0;
            }
        """)
        
        # Set window background
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1E1E1E"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#E0E0E0"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#2D2D30"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#E0E0E0"))
        self.setPalette(palette)
        
        # Update toolbar and context menu colors if visible
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: none;
            }
            QToolBar QLabel {
                color: #E0E0E0;
            }
            QToolBar QComboBox {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
            }
            QToolBar QSlider {
                background-color: #2D2D30;
            }
        """)
        
        # Update context menu style
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
            }
            QMenu::item:selected {
                background-color: #3E3E42;
            }
        """)
    
    def _apply_sepia_theme(self):
        """Apply sepia theme."""
        logger.debug("Applying sepia theme")
        
        # Set editor colors
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #F4ECD8;
                color: #5B4636;
            }
        """)
        
        # Set window background
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F0E6D2"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#5B4636"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#F4ECD8"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#5B4636"))
        self.setPalette(palette)
        
        # Update toolbar and context menu colors if visible
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #F0E6D2;
                color: #5B4636;
                border: none;
            }
            QToolBar QLabel {
                color: #5B4636;
            }
            QToolBar QComboBox {
                background-color: #F4ECD8;
                color: #5B4636;
                border: 1px solid #D8C7A9;
            }
            QToolBar QSlider {
                background-color: #F4ECD8;
            }
        """)
        
        # Update context menu style
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #F4ECD8;
                color: #5B4636;
                border: 1px solid #D8C7A9;
            }
            QMenu::item:selected {
                background-color: #E6D9C0;
            }
        """)
    
    def _on_width_changed(self, value: int):
        """
        Handle width slider value changed.
        
        Args:
            value: The new width percentage.
        """
        logger.debug(f"Width changed: {value}%")
        
        self.editor_width_percent = value
        self._update_editor_width()
    
    def _update_editor_width(self):
        """Update editor width based on the width percentage."""
        logger.debug(f"Updating editor width: {self.editor_width_percent}%")
        
        # Calculate margins
        window_width = self.width()
        content_width = int(window_width * self.editor_width_percent / 100)
        margin = (window_width - content_width) // 2
        
        # Set margins
        self.layout.setContentsMargins(margin, 20, margin, 20)
    
    def _apply_focus_mode(self):
        """Apply focus mode highlighting."""
        logger.debug("Applying focus mode")
        
        if not self.focus_mode_enabled:
            # Reset all text formatting
            cursor = self.editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            
            format = QTextCharFormat()
            cursor.setCharFormat(format)
            
            self.editor.setTextCursor(cursor)
            return
        
        # Get current cursor position
        cursor = self.editor.textCursor()
        
        # Select current paragraph
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        
        # Create format for current paragraph
        current_format = QTextCharFormat()
        
        # Create format for other paragraphs
        other_format = QTextCharFormat()
        other_format.setForeground(QColor("#888888"))
        
        # Apply formats
        doc = self.editor.document()
        block = doc.begin()
        
        while block.isValid():
            block_cursor = QTextCursor(block)
            block_cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            
            if block.position() <= cursor.position() and cursor.position() <= block.position() + block.length():
                # Current paragraph
                block_cursor.setCharFormat(current_format)
            else:
                # Other paragraph
                block_cursor.setCharFormat(other_format)
            
            block = block.next()
    
    def _apply_typewriter_scrolling(self):
        """Apply typewriter scrolling to keep cursor at center of screen."""
        logger.debug("Applying typewriter scrolling")
        
        if not self.typewriter_scrolling_enabled:
            return
        
        # Get current cursor position
        cursor = self.editor.textCursor()
        
        # Get cursor rectangle
        cursor_rect = self.editor.cursorRect(cursor)
        
        # Get editor viewport height
        viewport_height = self.editor.viewport().height()
        
        # Calculate scroll offset to center cursor
        scroll_offset = cursor_rect.top() - (viewport_height // 2)
        
        # Apply scroll offset
        scrollbar = self.editor.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + scroll_offset)
    
    def _on_text_changed(self):
        """Handle text changed event."""
        # Apply focus mode if enabled
        if self.focus_mode_enabled:
            self._apply_focus_mode()
    
    def _on_cursor_position_changed(self):
        """Handle cursor position changed event."""
        # Apply focus mode if enabled
        if self.focus_mode_enabled:
            self._apply_focus_mode()
        
        # Apply typewriter scrolling if enabled
        if self.typewriter_scrolling_enabled:
            self._apply_typewriter_scrolling()
    
    def resizeEvent(self, event: QResizeEvent):
        """
        Handle resize event.
        
        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        
        # Update editor width
        self._update_editor_width()
    
    def contextMenuEvent(self, event: QMouseEvent):
        """
        Handle context menu event.
        
        Args:
            event: The context menu event.
        """
        # Show custom context menu
        self.context_menu.exec(event.globalPosition().toPoint())
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press event.
        
        Args:
            event: The key press event.
        """
        # Handle Ctrl+S to save
        if event.key() == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            logger.debug("Ctrl+S pressed, emitting closed signal")
            self.close()
            return
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """
        Handle close event.
        
        Args:
            event: The close event.
        """
        logger.debug("Close event triggered")
        
        # Get current content
        content = self.editor.toPlainText()
        
        # Emit closed signal with content
        self.closed.emit(content)
        
        # Accept the close event
        event.accept()
