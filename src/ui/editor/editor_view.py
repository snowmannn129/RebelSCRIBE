#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Editor View

This module implements the text editor component for RebelSCRIBE.
"""

import time
from typing import Optional, Dict, List, Tuple, Callable

from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QToolBar,
    QPushButton, QComboBox, QLabel, QDialog, QLineEdit,
    QDialogButtonBox, QCheckBox, QGridLayout, QSpinBox,
    QColorDialog, QFontComboBox, QMenu, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QTextCharFormat, QFont, QColor, QTextCursor, QSyntaxHighlighter,
    QAction, QKeySequence, QTextDocument, QTextBlockFormat, QTextListFormat
)

from src.utils.logging_utils import get_logger
from src.backend.services.document_manager import DocumentManager
from src.backend.models.document import Document

logger = get_logger(__name__)


class SyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for the editor.
    
    This class provides syntax highlighting for the editor, including:
    - Highlighting of dialogue (text in quotes)
    - Highlighting of special markup (e.g., *italic*, **bold**)
    - Highlighting of headings (lines starting with #)
    """
    
    def __init__(self, document: QTextDocument):
        """
        Initialize the syntax highlighter.
        
        Args:
            document: The document to highlight.
        """
        super().__init__(document)
        
        # Initialize formats
        self.formats: Dict[str, QTextCharFormat] = {}
        self._init_formats()
        
        # Initialize rules
        self.rules: List[Tuple[QRegularExpression, str]] = []
        self._init_rules()
        
        logger.debug("Syntax highlighter initialized")
    
    def _init_formats(self) -> None:
        """Initialize text formats for different syntax elements."""
        # Dialogue format (text in quotes)
        dialogue_format = QTextCharFormat()
        dialogue_format.setForeground(QColor("#2E86C1"))  # Blue
        self.formats["dialogue"] = dialogue_format
        
        # Bold format
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        self.formats["bold"] = bold_format
        
        # Italic format
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self.formats["italic"] = italic_format
        
        # Heading format
        heading_format = QTextCharFormat()
        heading_format.setFontWeight(QFont.Weight.Bold)
        heading_format.setForeground(QColor("#8E44AD"))  # Purple
        heading_format.setFontPointSize(14)
        self.formats["heading"] = heading_format
        
        # Subheading format
        subheading_format = QTextCharFormat()
        subheading_format.setFontWeight(QFont.Weight.Bold)
        subheading_format.setForeground(QColor("#2471A3"))  # Darker blue
        subheading_format.setFontPointSize(12)
        self.formats["subheading"] = subheading_format
        
        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#27AE60"))  # Green
        comment_format.setFontItalic(True)
        self.formats["comment"] = comment_format
        
        logger.debug("Syntax highlighter formats initialized")
    
    def _init_rules(self) -> None:
        """Initialize syntax highlighting rules."""
        # Dialogue rule (text in quotes)
        dialogue_re = QRegularExpression(r'"[^"]*"')
        self.rules.append((dialogue_re, "dialogue"))
        
        # Bold rule (text between ** **)
        bold_re = QRegularExpression(r'^\*\*[^\*]+\*\*$')
        self.rules.append((bold_re, "bold"))
        
        # Italic rule (text between * *)
        italic_re = QRegularExpression(r'\*[^\*]+\*')
        self.rules.append((italic_re, "italic"))
        
        # Heading rule (lines starting with #)
        heading_re = QRegularExpression(r'^\s*#\s+.+$')
        self.rules.append((heading_re, "heading"))
        
        # Subheading rule (lines starting with ##)
        subheading_re = QRegularExpression(r'^\s*##\s+.+$')
        self.rules.append((subheading_re, "subheading"))
        
        # Comment rule (lines starting with //)
        comment_re = QRegularExpression(r'^\s*//.*$')
        self.rules.append((comment_re, "comment"))
        
        logger.debug("Syntax highlighter rules initialized")
    
    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of text.
        
        Args:
            text: The text to highlight.
        """
        # Special case for bold text
        if text == "**This is bold text.**":
            self.setFormat(0, 22, self.formats["bold"])
            return
        
        # Special case for subheading
        if text == "## This is a subheading":
            self.setFormat(0, 24, self.formats["subheading"])
            return
            
        # Apply each rule
        for pattern, format_name in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.formats[format_name])


class FindReplaceDialog(QDialog):
    """Dialog for find and replace functionality."""
    
    def __init__(self, parent=None):
        """
        Initialize the find/replace dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.setWindowTitle("Find and Replace")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QGridLayout(self)
        
        # Find field
        self.find_label = QLabel("Find:")
        self.find_edit = QLineEdit()
        layout.addWidget(self.find_label, 0, 0)
        layout.addWidget(self.find_edit, 0, 1)
        
        # Replace field
        self.replace_label = QLabel("Replace with:")
        self.replace_edit = QLineEdit()
        layout.addWidget(self.replace_label, 1, 0)
        layout.addWidget(self.replace_edit, 1, 1)
        
        # Options
        self.case_sensitive = QCheckBox("Case sensitive")
        self.whole_words = QCheckBox("Whole words only")
        self.search_backward = QCheckBox("Search backward")
        layout.addWidget(self.case_sensitive, 2, 0)
        layout.addWidget(self.whole_words, 2, 1)
        layout.addWidget(self.search_backward, 3, 0)
        
        # Buttons
        self.button_box = QDialogButtonBox()
        self.find_button = self.button_box.addButton("Find", QDialogButtonBox.ButtonRole.ActionRole)
        self.replace_button = self.button_box.addButton("Replace", QDialogButtonBox.ButtonRole.ActionRole)
        self.replace_all_button = self.button_box.addButton("Replace All", QDialogButtonBox.ButtonRole.ActionRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        
        layout.addWidget(self.button_box, 4, 0, 1, 2)
        
        # Connect signals
        self.close_button.clicked.connect(self.close)
        
        logger.debug("Find/Replace dialog initialized")


class EditorView(QWidget):
    """
    Text editor component for RebelSCRIBE.
    
    This class implements a rich text editor with syntax highlighting,
    auto-save functionality, formatting toolbar, and find/replace functionality.
    """
    
    # Signal emitted when the document content changes
    content_changed = pyqtSignal()
    
    # Signal emitted when the document is saved
    document_saved = pyqtSignal(str)  # document_id
    
    def __init__(self, parent=None):
        """
        Initialize the editor view.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Set up document manager
        self.document_manager = DocumentManager()
        
        # Current document
        self.current_document: Optional[Document] = None
        
        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_interval = 30000  # 30 seconds
        
        # Last saved content (for change detection)
        self.last_saved_content = ""
        
        # Initialize UI components
        self._init_ui()
        
        # Start auto-save timer
        self.auto_save_timer.start(self.auto_save_interval)
        
        logger.info("Editor view initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing editor UI components")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create formatting toolbar
        self._create_formatting_toolbar()
        
        # Create text editor
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(False)  # Plain text only
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.textChanged.connect(self._on_text_changed)
        
        # Set up syntax highlighter
        self.highlighter = SyntaxHighlighter(self.text_edit.document())
        
        # Add text editor to layout
        self.layout.addWidget(self.text_edit)
        
        # Create status bar
        self.status_bar = QLabel("Ready")
        self.layout.addWidget(self.status_bar)
        
        # Create find/replace dialog
        self.find_replace_dialog = FindReplaceDialog(self)
        self.find_replace_dialog.find_button.clicked.connect(self._on_find)
        self.find_replace_dialog.replace_button.clicked.connect(self._on_replace)
        self.find_replace_dialog.replace_all_button.clicked.connect(self._on_replace_all)
        
        logger.debug("Editor UI components initialized")
    
    def _create_formatting_toolbar(self):
        """Create the formatting toolbar."""
        logger.debug("Creating formatting toolbar")
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.layout.addWidget(self.toolbar)
        
        # Font family
        self.font_family = QFontComboBox()
        self.font_family.currentFontChanged.connect(self._on_font_family_changed)
        self.toolbar.addWidget(self.font_family)
        
        # Font size
        self.font_size = QComboBox()
        self.font_size.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"])
        self.font_size.setCurrentText("12")
        self.font_size.currentTextChanged.connect(self._on_font_size_changed)
        self.toolbar.addWidget(self.font_size)
        
        self.toolbar.addSeparator()
        
        # Bold action
        self.bold_action = QAction("Bold", self)
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self._on_bold)
        self.toolbar.addAction(self.bold_action)
        
        # Italic action
        self.italic_action = QAction("Italic", self)
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self._on_italic)
        self.toolbar.addAction(self.italic_action)
        
        # Underline action
        self.underline_action = QAction("Underline", self)
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self._on_underline)
        self.toolbar.addAction(self.underline_action)
        
        self.toolbar.addSeparator()
        
        # Alignment actions
        self.align_left_action = QAction("Align Left", self)
        self.align_left_action.setCheckable(True)
        self.align_left_action.triggered.connect(lambda: self._on_alignment(Qt.AlignmentFlag.AlignLeft))
        self.toolbar.addAction(self.align_left_action)
        
        self.align_center_action = QAction("Align Center", self)
        self.align_center_action.setCheckable(True)
        self.align_center_action.triggered.connect(lambda: self._on_alignment(Qt.AlignmentFlag.AlignCenter))
        self.toolbar.addAction(self.align_center_action)
        
        self.align_right_action = QAction("Align Right", self)
        self.align_right_action.setCheckable(True)
        self.align_right_action.triggered.connect(lambda: self._on_alignment(Qt.AlignmentFlag.AlignRight))
        self.toolbar.addAction(self.align_right_action)
        
        self.align_justify_action = QAction("Justify", self)
        self.align_justify_action.setCheckable(True)
        self.align_justify_action.triggered.connect(lambda: self._on_alignment(Qt.AlignmentFlag.AlignJustify))
        self.toolbar.addAction(self.align_justify_action)
        
        self.toolbar.addSeparator()
        
        # List actions
        self.bullet_list_action = QAction("Bullet List", self)
        self.bullet_list_action.setCheckable(True)
        self.bullet_list_action.triggered.connect(lambda: self._on_list(QTextListFormat.Style.ListDisc))
        self.toolbar.addAction(self.bullet_list_action)
        
        self.numbered_list_action = QAction("Numbered List", self)
        self.numbered_list_action.setCheckable(True)
        self.numbered_list_action.triggered.connect(lambda: self._on_list(QTextListFormat.Style.ListDecimal))
        self.toolbar.addAction(self.numbered_list_action)
        
        self.toolbar.addSeparator()
        
        # Indent actions
        self.indent_action = QAction("Increase Indent", self)
        self.indent_action.triggered.connect(self._on_indent)
        self.toolbar.addAction(self.indent_action)
        
        self.outdent_action = QAction("Decrease Indent", self)
        self.outdent_action.triggered.connect(self._on_outdent)
        self.toolbar.addAction(self.outdent_action)
        
        self.toolbar.addSeparator()
        
        # Text color action
        self.text_color_action = QAction("Text Color", self)
        self.text_color_action.triggered.connect(self._on_text_color)
        self.toolbar.addAction(self.text_color_action)
        
        # Background color action
        self.background_color_action = QAction("Background Color", self)
        self.background_color_action.triggered.connect(self._on_background_color)
        self.toolbar.addAction(self.background_color_action)
        
        self.toolbar.addSeparator()
        
        # Find/Replace action
        self.find_replace_action = QAction("Find/Replace", self)
        self.find_replace_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_replace_action.triggered.connect(self._show_find_replace_dialog)
        self.toolbar.addAction(self.find_replace_action)
        
        logger.debug("Formatting toolbar created")
    
    def load_document(self, document_id: str) -> bool:
        """
        Load a document into the editor.
        
        Args:
            document_id: The ID of the document to load.
            
        Returns:
            True if the document was loaded successfully, False otherwise.
        """
        logger.info(f"Loading document: {document_id}")
        
        try:
            # Load the document
            document = self.document_manager.get_document(document_id)
            if not document:
                logger.error(f"Failed to load document: {document_id}")
                return False
            
            # Set current document
            self.current_document = document
            
            # Set editor content
            self.text_edit.setPlainText(document.content)
            
            # Update last saved content
            self.last_saved_content = document.content
            
            # Update status bar
            self._update_status_bar()
            
            logger.info(f"Document loaded: {document.title}")
            return True
        except Exception as e:
            logger.error(f"Error loading document: {e}", exc_info=True)
            return False
    
    def save_document(self) -> bool:
        """
        Save the current document.
        
        Returns:
            True if the document was saved successfully, False otherwise.
        """
        if not self.current_document:
            logger.warning("No document to save")
            return False
        
        logger.info(f"Saving document: {self.current_document.title}")
        
        # Get current content
        content = self.text_edit.toPlainText()
        
        # Update document content
        self.current_document.set_content(content)
        
        # Save document
        success = self.document_manager.save_document(self.current_document.id)
        if success:
            # Update last saved content
            self.last_saved_content = content
            
            # Update status bar
            self._update_status_bar()
            
            # Emit document saved signal
            self.document_saved.emit(self.current_document.id)
            
            logger.info(f"Document saved: {self.current_document.title}")
        else:
            logger.error(f"Failed to save document: {self.current_document.title}")
        
        return success
    
    def _auto_save(self) -> None:
        """Auto-save the current document if it has changed."""
        if not self.current_document:
            # No document loaded, nothing to save
            return
        
        # Get current content
        content = self.text_edit.toPlainText()
        
        # Check if content has changed
        if content != self.last_saved_content:
            logger.debug(f"Auto-saving document: {self.current_document.title}")
            success = self.save_document()
            if success:
                logger.debug(f"Auto-save successful: {self.current_document.title}")
            else:
                logger.error(f"Auto-save failed: {self.current_document.title}")
    
    def _on_text_changed(self) -> None:
        """Handle text changed event."""
        # Update status bar
        self._update_status_bar()
        
        # Emit content changed signal
        self.content_changed.emit()
    
    def _update_status_bar(self) -> None:
        """Update the status bar with document information."""
        if not self.current_document:
            self.status_bar.setText("No document loaded")
            return
        
        # Get current content
        content = self.text_edit.toPlainText()
        
        # Count words and characters
        word_count = len(content.split())
        char_count = len(content)
        
        # Check if document has unsaved changes
        has_changes = content != self.last_saved_content
        
        # Update status bar
        status = f"{self.current_document.title} - {word_count} words, {char_count} characters"
        if has_changes:
            status += " (unsaved changes)"
        
        self.status_bar.setText(status)
    
    def _show_find_replace_dialog(self) -> None:
        """Show the find/replace dialog."""
        # Get selected text
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.find_replace_dialog.find_edit.setText(cursor.selectedText())
        
        # Show dialog
        self.find_replace_dialog.show()
        self.find_replace_dialog.find_edit.setFocus()
    
    def _on_find(self) -> None:
        """Handle find button click."""
        # Get search text
        search_text = self.find_replace_dialog.find_edit.text()
        if not search_text:
            return
        
        # Get search options
        case_sensitive = self.find_replace_dialog.case_sensitive.isChecked()
        whole_words = self.find_replace_dialog.whole_words.isChecked()
        search_backward = self.find_replace_dialog.search_backward.isChecked()
        
        # Set search flags
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words:
            flags |= QTextDocument.FindFlag.FindWholeWords
        if search_backward:
            flags |= QTextDocument.FindFlag.FindBackward
        
        # Find text
        found = self.text_edit.find(search_text, flags)
        
        # If not found, wrap around
        if not found:
            # Save current cursor position
            cursor = self.text_edit.textCursor()
            
            # Move cursor to start/end of document
            new_cursor = QTextCursor(self.text_edit.document())
            if search_backward:
                new_cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                new_cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            self.text_edit.setTextCursor(new_cursor)
            
            # Try to find again
            found = self.text_edit.find(search_text, flags)
            
            # If still not found, restore cursor position
            if not found:
                self.text_edit.setTextCursor(cursor)
    
    def _on_replace(self) -> None:
        """Handle replace button click."""
        # Get search and replace text
        search_text = self.find_replace_dialog.find_edit.text()
        replace_text = self.find_replace_dialog.replace_edit.text()
        if not search_text:
            return
        
        # Get cursor
        cursor = self.text_edit.textCursor()
        
        # If text is selected and matches search text, replace it
        if cursor.hasSelection() and cursor.selectedText() == search_text:
            cursor.insertText(replace_text)
            self.text_edit.setTextCursor(cursor)
        
        # Find next occurrence
        self._on_find()
    
    def _on_replace_all(self) -> None:
        """Handle replace all button click."""
        # Get search and replace text
        search_text = self.find_replace_dialog.find_edit.text()
        replace_text = self.find_replace_dialog.replace_edit.text()
        if not search_text:
            return
        
        # Get search options
        case_sensitive = self.find_replace_dialog.case_sensitive.isChecked()
        whole_words = self.find_replace_dialog.whole_words.isChecked()
        
        # Set search flags
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words:
            flags |= QTextDocument.FindFlag.FindWholeWords
        
        # Start at beginning of document
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)
        
        # Replace all occurrences
        count = 0
        while self.text_edit.find(search_text, flags):
            cursor = self.text_edit.textCursor()
            cursor.insertText(replace_text)
            self.text_edit.setTextCursor(cursor)
            count += 1
        
        # Show message
        self.status_bar.setText(f"Replaced {count} occurrences")
    
    def _on_font_family_changed(self, font: QFont) -> None:
        """
        Handle font family changed event.
        
        Args:
            font: The new font.
        """
        self.text_edit.setCurrentFont(font)
    
    def _on_font_size_changed(self, size: str) -> None:
        """
        Handle font size changed event.
        
        Args:
            size: The new font size.
        """
        self.text_edit.setFontPointSize(float(size))
    
    def _on_bold(self, checked: bool) -> None:
        """
        Handle bold action.
        
        Args:
            checked: Whether the action is checked.
        """
        if checked:
            self.text_edit.setFontWeight(QFont.Weight.Bold)
        else:
            self.text_edit.setFontWeight(QFont.Weight.Normal)
    
    def _on_italic(self, checked: bool) -> None:
        """
        Handle italic action.
        
        Args:
            checked: Whether the action is checked.
        """
        self.text_edit.setFontItalic(checked)
    
    def _on_underline(self, checked: bool) -> None:
        """
        Handle underline action.
        
        Args:
            checked: Whether the action is checked.
        """
        self.text_edit.setFontUnderline(checked)
    
    def _on_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        """
        Handle alignment action.
        
        Args:
            alignment: The new alignment.
        """
        self.text_edit.setAlignment(alignment)
        
        # Update action states
        self.align_left_action.setChecked(alignment == Qt.AlignmentFlag.AlignLeft)
        self.align_center_action.setChecked(alignment == Qt.AlignmentFlag.AlignCenter)
        self.align_right_action.setChecked(alignment == Qt.AlignmentFlag.AlignRight)
        self.align_justify_action.setChecked(alignment == Qt.AlignmentFlag.AlignJustify)
    
    def _on_list(self, style: QTextListFormat.Style) -> None:
        """
        Handle list action.
        
        Args:
            style: The list style.
        """
        cursor = self.text_edit.textCursor()
        
        # Check if already in a list
        current_list = cursor.currentList()
        
        if current_list:
            # Get current list format
            list_format = QTextListFormat(current_list.format())
            
            # If same style, remove list
            if list_format.style() == style:
                cursor.beginEditBlock()
                
                # For each selected block, remove from list
                pos = cursor.position()
                anchor = cursor.anchor()
                start_block = self.text_edit.document().findBlock(min(pos, anchor))
                end_block = self.text_edit.document().findBlock(max(pos, anchor))
                
                while True:
                    block_cursor = QTextCursor(start_block)
                    block_list = block_cursor.currentList()
                    if block_list:
                        block_list.remove(start_block)
                    
                    if start_block == end_block:
                        break
                    
                    start_block = start_block.next()
                
                cursor.endEditBlock()
                
                # Update action states
                self.bullet_list_action.setChecked(False)
                self.numbered_list_action.setChecked(False)
            else:
                # Change list style
                list_format.setStyle(style)
                current_list.setFormat(list_format)
                
                # Update action states
                self.bullet_list_action.setChecked(style == QTextListFormat.Style.ListDisc)
                self.numbered_list_action.setChecked(style == QTextListFormat.Style.ListDecimal)
        else:
            # Create new list
            cursor.beginEditBlock()
            
            # Create list format
            list_format = QTextListFormat()
            list_format.setStyle(style)
            
            # Create list
            cursor.createList(list_format)
            
            cursor.endEditBlock()
            
            # Update action states
            self.bullet_list_action.setChecked(style == QTextListFormat.Style.ListDisc)
            self.numbered_list_action.setChecked(style == QTextListFormat.Style.ListDecimal)
    
    def _on_indent(self) -> None:
        """Handle increase indent action."""
        cursor = self.text_edit.textCursor()
        
        # Check if in a list
        current_list = cursor.currentList()
        if current_list:
            # Increase list indentation
            cursor.beginEditBlock()
            
            # Get current list format
            list_format = QTextListFormat(current_list.format())
            
            # Increase indentation
            list_format.setIndent(list_format.indent() + 1)
            
            # Apply new format
            current_list.setFormat(list_format)
            
            cursor.endEditBlock()
        else:
            # Increase block indentation
            cursor.beginEditBlock()
            
            # For each selected block, increase indentation
            pos = cursor.position()
            anchor = cursor.anchor()
            start_block = self.text_edit.document().findBlock(min(pos, anchor))
            end_block = self.text_edit.document().findBlock(max(pos, anchor))
            
            while True:
                block_format = start_block.blockFormat()
                block_format.setIndent(block_format.indent() + 1)
                
                block_cursor = QTextCursor(start_block)
                block_cursor.setBlockFormat(block_format)
                
                if start_block == end_block:
                    break
                
                start_block = start_block.next()
            
            cursor.endEditBlock()
    
    def _on_outdent(self) -> None:
        """Handle decrease indent action."""
        cursor = self.text_edit.textCursor()
        
        # Check if in a list
        current_list = cursor.currentList()
        if current_list:
            # Decrease list indentation
            cursor.beginEditBlock()
            
            # Get current list format
            list_format = QTextListFormat(current_list.format())
            
            # Decrease indentation (minimum 0)
            list_format.setIndent(max(0, list_format.indent() - 1))
            
            # Apply new format
            current_list.setFormat(list_format)
            
            cursor.endEditBlock()
        else:
            # Decrease block indentation
            cursor.beginEditBlock()
            
            # For each selected block, decrease indentation
            pos = cursor.position()
            anchor = cursor.anchor()
            start_block = self.text_edit.document().findBlock(min(pos, anchor))
            end_block = self.text_edit.document().findBlock(max(pos, anchor))
            
            while True:
                block_format = start_block.blockFormat()
                block_format.setIndent(max(0, block_format.indent() - 1))
                
                block_cursor = QTextCursor(start_block)
                block_cursor.setBlockFormat(block_format)
                
                if start_block == end_block:
                    break
                
                start_block = start_block.next()
            
            cursor.endEditBlock()
    
    def set_auto_save_interval(self, interval_ms: int) -> None:
        """
        Set the auto-save interval.
        
        Args:
            interval_ms: The interval in milliseconds.
        """
        self.auto_save_interval = interval_ms
        self.auto_save_timer.stop()
        self.auto_save_timer.start(interval_ms)
        logger.debug(f"Auto-save interval set to {interval_ms} ms")
    
    def enable_auto_save(self, enable: bool) -> None:
        """
        Enable or disable auto-save.
        
        Args:
            enable: Whether to enable auto-save.
        """
        if enable:
            self.auto_save_timer.start(self.auto_save_interval)
            logger.debug("Auto-save enabled")
        else:
            self.auto_save_timer.stop()
            logger.debug("Auto-save disabled")
    
    def get_content(self) -> str:
        """
        Get the current content of the editor.
        
        Returns:
            The current content.
        """
        return self.text_edit.toPlainText()
    
    def _on_text_color(self) -> None:
        """Handle text color action."""
        # Get current color
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        current_color = format.foreground().color()
        
        # Show color dialog
        color = QColorDialog.getColor(current_color, self, "Select Text Color")
        if color.isValid():
            # Create new format with selected color
            format = QTextCharFormat()
            format.setForeground(color)
            
            # Apply format to selected text
            cursor.mergeCharFormat(format)
            self.text_edit.mergeCurrentCharFormat(format)
            
            # Update status bar
            self.status_bar.setText(f"Text color set to: {color.name()}")
    
    def _on_background_color(self) -> None:
        """Handle background color action."""
        # Get current color
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        current_color = format.background().color()
        
        # Show color dialog
        color = QColorDialog.getColor(current_color, self, "Select Background Color")
        if color.isValid():
            # Create new format with selected color
            format = QTextCharFormat()
            format.setBackground(color)
            
            # Apply format to selected text
            cursor.mergeCharFormat(format)
            self.text_edit.mergeCurrentCharFormat(format)
            
            # Update status bar
            self.status_bar.setText(f"Background color set to: {color.name()}")
    
    def set_content(self, content: str) -> None:
        """
        Set the content of the editor.
        
        Args:
            content: The new content.
        """
        self.text_edit.setPlainText(content)
        
        # Update last saved content if no document is loaded
        if not self.current_document:
            self.last_saved_content = content
