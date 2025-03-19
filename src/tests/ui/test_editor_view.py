#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Editor View.

This module contains tests for the EditorView class.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import pytest
from PyQt6.QtWidgets import (
    QApplication, QTextEdit, QToolBar, QLabel, QDialog,
    QFontComboBox, QComboBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtGui import (
    QTextCharFormat, QFont, QColor, QTextCursor, QSyntaxHighlighter,
    QTextDocument, QTextBlockFormat, QTextListFormat
)

from src.ui.editor.editor_view import EditorView, SyntaxHighlighter, FindReplaceDialog


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to clean up as we're not destroying the app


@pytest.fixture
def editor_view(qtbot, monkeypatch):
    """Create an EditorView instance for testing."""
    # Mock DocumentManager to avoid file operations
    with patch('src.ui.editor.editor_view.DocumentManager') as mock_dm:
        # Configure the mock
        mock_instance = mock_dm.return_value
        mock_instance.get_document.return_value = None
        mock_instance.save_document.return_value = True
        
        # Create editor view
        view = EditorView()
        qtbot.addWidget(view)
        return view


class TestEditorView:
    """Test cases for the EditorView class."""
    
    def test_init(self, editor_view):
        """Test initialization of the editor view."""
        # Check that components are created
        assert editor_view.text_edit is not None
        assert editor_view.toolbar is not None
        assert editor_view.status_bar is not None
        assert editor_view.highlighter is not None
        assert editor_view.find_replace_dialog is not None
        
        # Check auto-save timer
        assert editor_view.auto_save_timer is not None
        assert editor_view.auto_save_timer.isActive()
        assert editor_view.auto_save_interval == 30000  # 30 seconds
        
        # Check document manager
        assert editor_view.document_manager is not None
        assert editor_view.current_document is None
        
        # Check status bar
        assert editor_view.status_bar.text() == "Ready"
    
    def test_toolbar_creation(self, editor_view):
        """Test the creation of the formatting toolbar."""
        # Check toolbar components
        assert isinstance(editor_view.font_family, QFontComboBox)
        assert isinstance(editor_view.font_size, QComboBox)
        
        # Check toolbar actions
        assert editor_view.bold_action is not None
        assert editor_view.italic_action is not None
        assert editor_view.underline_action is not None
        assert editor_view.align_left_action is not None
        assert editor_view.align_center_action is not None
        assert editor_view.align_right_action is not None
        assert editor_view.align_justify_action is not None
        assert editor_view.bullet_list_action is not None
        assert editor_view.numbered_list_action is not None
        assert editor_view.indent_action is not None
        assert editor_view.outdent_action is not None
        assert editor_view.find_replace_action is not None
        
        # Check action properties
        assert editor_view.bold_action.isCheckable()
        assert editor_view.italic_action.isCheckable()
        assert editor_view.underline_action.isCheckable()
        assert editor_view.align_left_action.isCheckable()
        assert editor_view.align_center_action.isCheckable()
        assert editor_view.align_right_action.isCheckable()
        assert editor_view.align_justify_action.isCheckable()
        assert editor_view.bullet_list_action.isCheckable()
        assert editor_view.numbered_list_action.isCheckable()
    
    def test_load_document_success(self, editor_view):
        """Test loading a document successfully."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        mock_document.content = "Test content"
        
        # Configure document manager to return the mock document
        editor_view.document_manager.get_document.return_value = mock_document
        
        # Load document
        result = editor_view.load_document("doc123")
        
        # Check result
        assert result is True
        
        # Check that document was loaded
        editor_view.document_manager.get_document.assert_called_once_with("doc123")
        assert editor_view.current_document == mock_document
        assert editor_view.text_edit.toPlainText() == "Test content"
        assert editor_view.last_saved_content == "Test content"
    
    def test_load_document_failure(self, editor_view):
        """Test loading a document that doesn't exist."""
        # Configure document manager to return None
        editor_view.document_manager.get_document.return_value = None
        
        # Load document
        result = editor_view.load_document("nonexistent")
        
        # Check result
        assert result is False
        
        # Check that document was not loaded
        editor_view.document_manager.get_document.assert_called_once_with("nonexistent")
        assert editor_view.current_document is None
    
    def test_save_document_success(self, editor_view):
        """Test saving a document successfully."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        mock_document.content = "Old content"
        
        # Set up editor view
        editor_view.current_document = mock_document
        editor_view.text_edit.setPlainText("New content")
        
        # Configure document manager
        editor_view.document_manager.save_document.return_value = True
        
        # Mock document_saved signal
        editor_view.document_saved = MagicMock()
        
        # Save document
        result = editor_view.save_document()
        
        # Check result
        assert result is True
        
        # Check that document was saved
        mock_document.set_content.assert_called_once_with("New content")
        editor_view.document_manager.save_document.assert_called_once_with("doc123")
        assert editor_view.last_saved_content == "New content"
        editor_view.document_saved.emit.assert_called_once_with("doc123")
    
    def test_save_document_failure(self, editor_view):
        """Test saving a document with failure."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        mock_document.content = "Old content"
        
        # Set up editor view
        editor_view.current_document = mock_document
        editor_view.text_edit.setPlainText("New content")
        
        # Configure document manager to fail
        editor_view.document_manager.save_document.return_value = False
        
        # Mock document_saved signal
        editor_view.document_saved = MagicMock()
        
        # Save document
        result = editor_view.save_document()
        
        # Check result
        assert result is False
        
        # Check that document was not saved successfully
        mock_document.set_content.assert_called_once_with("New content")
        editor_view.document_manager.save_document.assert_called_once_with("doc123")
        assert editor_view.last_saved_content != "New content"  # Should not update
        editor_view.document_saved.emit.assert_not_called()
    
    def test_save_document_no_document(self, editor_view):
        """Test saving when no document is loaded."""
        # Ensure no document is loaded
        editor_view.current_document = None
        
        # Save document
        result = editor_view.save_document()
        
        # Check result
        assert result is False
        
        # Check that no save was attempted
        editor_view.document_manager.save_document.assert_not_called()
    
    def test_auto_save(self, editor_view):
        """Test auto-save functionality."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        mock_document.content = "Old content"
        
        # Set up editor view
        editor_view.current_document = mock_document
        editor_view.text_edit.setPlainText("New content")
        editor_view.last_saved_content = "Old content"  # Different from current content
        
        # Mock save_document method
        editor_view.save_document = MagicMock(return_value=True)
        
        # Trigger auto-save
        editor_view._auto_save()
        
        # Check that document was saved
        editor_view.save_document.assert_called_once()
    
    def test_auto_save_no_changes(self, editor_view):
        """Test auto-save when no changes have been made."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        mock_document.content = "Content"
        
        # Set up editor view
        editor_view.current_document = mock_document
        editor_view.text_edit.setPlainText("Content")
        editor_view.last_saved_content = "Content"  # Same as current content
        
        # Mock save_document method
        editor_view.save_document = MagicMock(return_value=True)
        
        # Trigger auto-save
        editor_view._auto_save()
        
        # Check that document was not saved
        editor_view.save_document.assert_not_called()
    
    def test_auto_save_no_document(self, editor_view):
        """Test auto-save when no document is loaded."""
        # Ensure no document is loaded
        editor_view.current_document = None
        
        # Mock save_document method
        editor_view.save_document = MagicMock(return_value=True)
        
        # Trigger auto-save
        editor_view._auto_save()
        
        # Check that document was not saved
        editor_view.save_document.assert_not_called()
    
    def test_set_auto_save_interval(self, editor_view):
        """Test setting the auto-save interval."""
        # Mock timer
        editor_view.auto_save_timer = MagicMock()
        
        # Set interval
        editor_view.set_auto_save_interval(60000)  # 1 minute
        
        # Check that timer was updated
        assert editor_view.auto_save_interval == 60000
        editor_view.auto_save_timer.stop.assert_called_once()
        editor_view.auto_save_timer.start.assert_called_once_with(60000)
    
    def test_enable_auto_save(self, editor_view):
        """Test enabling and disabling auto-save."""
        # Mock timer
        editor_view.auto_save_timer = MagicMock()
        
        # Disable auto-save
        editor_view.enable_auto_save(False)
        
        # Check that timer was stopped
        editor_view.auto_save_timer.stop.assert_called_once()
        
        # Reset mock
        editor_view.auto_save_timer.reset_mock()
        
        # Enable auto-save
        editor_view.enable_auto_save(True)
        
        # Check that timer was started
        editor_view.auto_save_timer.start.assert_called_once_with(editor_view.auto_save_interval)
    
    def test_text_changed(self, qtbot, editor_view):
        """Test handling text changed event."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        mock_document.content = "Initial content"
        
        # Set up editor view
        editor_view.current_document = mock_document
        editor_view.text_edit.setPlainText("Initial content")
        editor_view.last_saved_content = "Initial content"
        
        # Mock content_changed signal
        editor_view.content_changed = MagicMock()
        
        # Change text
        qtbot.keyClicks(editor_view.text_edit, " - updated")
        
        # Check that signal was emitted
        editor_view.content_changed.emit.assert_called()
        
        # Check status bar update
        assert "unsaved changes" in editor_view.status_bar.text()
    
    def test_update_status_bar(self, editor_view):
        """Test updating the status bar."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        
        # Set up editor view
        editor_view.current_document = mock_document
        editor_view.text_edit.setPlainText("This is a test document with some content.")
        editor_view.last_saved_content = "This is a test document with some content."
        
        # Update status bar
        editor_view._update_status_bar()
        
        # Check status bar text
        status_text = editor_view.status_bar.text()
        assert "Test Document" in status_text
        assert "8 words" in status_text
        assert "42 characters" in status_text
        assert "unsaved changes" not in status_text
        
        # Change content
        editor_view.text_edit.setPlainText("This is a test document with some updated content.")
        
        # Update status bar
        editor_view._update_status_bar()
        
        # Check status bar text
        status_text = editor_view.status_bar.text()
        assert "Test Document" in status_text
        assert "9 words" in status_text
        assert "50 characters" in status_text
        assert "unsaved changes" in status_text
    
    def test_update_status_bar_no_document(self, editor_view):
        """Test updating the status bar with no document."""
        # Ensure no document is loaded
        editor_view.current_document = None
        
        # Update status bar
        editor_view._update_status_bar()
        
        # Check status bar text
        assert editor_view.status_bar.text() == "No document loaded"
    
    def test_get_set_content(self, editor_view):
        """Test getting and setting content."""
        # Set content
        editor_view.set_content("Test content")
        
        # Check content
        assert editor_view.text_edit.toPlainText() == "Test content"
        assert editor_view.get_content() == "Test content"
        
        # Check last saved content (should be updated when no document is loaded)
        assert editor_view.last_saved_content == "Test content"
        
        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc123"
        mock_document.title = "Test Document"
        
        # Set up editor view with document
        editor_view.current_document = mock_document
        
        # Set content
        editor_view.set_content("New content")
        
        # Check content
        assert editor_view.text_edit.toPlainText() == "New content"
        assert editor_view.get_content() == "New content"
        
        # Check last saved content (should not be updated when document is loaded)
        assert editor_view.last_saved_content == "Test content"
    
    def test_find_replace_dialog(self, qtbot, editor_view):
        """Test the find/replace dialog."""
        # Set content
        editor_view.set_content("This is a test document. It contains test text for testing.")
        
        # Show dialog
        with patch.object(editor_view.find_replace_dialog, 'show') as mock_show:
            editor_view._show_find_replace_dialog()
            mock_show.assert_called_once()
    
    def test_find_functionality(self, qtbot, editor_view):
        """Test the find functionality."""
        # Set content
        editor_view.set_content("This is a test document. It contains test text for testing.")
        
        # Configure find dialog
        editor_view.find_replace_dialog.find_edit.setText("test")
        editor_view.find_replace_dialog.case_sensitive.setChecked(False)
        editor_view.find_replace_dialog.whole_words.setChecked(False)
        editor_view.find_replace_dialog.search_backward.setChecked(False)
        
        # Mock find method
        with patch.object(editor_view.text_edit, 'find', return_value=True) as mock_find:
            # Trigger find
            editor_view._on_find()
            
            # Check that find was called with correct parameters
            mock_find.assert_called_once_with("test", QTextDocument.FindFlag(0))
    
    def test_find_case_sensitive(self, qtbot, editor_view):
        """Test the find functionality with case sensitivity."""
        # Set content
        editor_view.set_content("This is a Test document. It contains test text for testing.")
        
        # Configure find dialog
        editor_view.find_replace_dialog.find_edit.setText("Test")
        editor_view.find_replace_dialog.case_sensitive.setChecked(True)
        editor_view.find_replace_dialog.whole_words.setChecked(False)
        editor_view.find_replace_dialog.search_backward.setChecked(False)
        
        # Mock find method
        with patch.object(editor_view.text_edit, 'find', return_value=True) as mock_find:
            # Trigger find
            editor_view._on_find()
            
            # Check that find was called with correct parameters
            mock_find.assert_called_once_with("Test", QTextDocument.FindFlag.FindCaseSensitively)
    
    def test_find_whole_words(self, qtbot, editor_view):
        """Test the find functionality with whole words only."""
        # Set content
        editor_view.set_content("This is a test document. It contains testing text.")
        
        # Configure find dialog
        editor_view.find_replace_dialog.find_edit.setText("test")
        editor_view.find_replace_dialog.case_sensitive.setChecked(False)
        editor_view.find_replace_dialog.whole_words.setChecked(True)
        editor_view.find_replace_dialog.search_backward.setChecked(False)
        
        # Mock find method
        with patch.object(editor_view.text_edit, 'find', return_value=True) as mock_find:
            # Trigger find
            editor_view._on_find()
            
            # Check that find was called with correct parameters
            mock_find.assert_called_once_with("test", QTextDocument.FindFlag.FindWholeWords)
    
    def test_find_backward(self, qtbot, editor_view):
        """Test the find functionality with backward search."""
        # Set content
        editor_view.set_content("This is a test document. It contains test text for testing.")
        
        # Configure find dialog
        editor_view.find_replace_dialog.find_edit.setText("test")
        editor_view.find_replace_dialog.case_sensitive.setChecked(False)
        editor_view.find_replace_dialog.whole_words.setChecked(False)
        editor_view.find_replace_dialog.search_backward.setChecked(True)
        
        # Mock find method
        with patch.object(editor_view.text_edit, 'find', return_value=True) as mock_find:
            # Trigger find
            editor_view._on_find()
            
            # Check that find was called with correct parameters
            mock_find.assert_called_once_with("test", QTextDocument.FindFlag.FindBackward)
    
    def test_replace_functionality(self, qtbot, editor_view):
        """Test the replace functionality."""
        # Set content
        editor_view.set_content("This is a test document. It contains test text for testing.")
        
        # Configure find/replace dialog
        editor_view.find_replace_dialog.find_edit.setText("test")
        editor_view.find_replace_dialog.replace_edit.setText("example")
        
        # Select text
        cursor = editor_view.text_edit.textCursor()
        cursor.setPosition(10)  # Position at the start of "test"
        cursor.setPosition(14, QTextCursor.MoveMode.KeepAnchor)  # Select "test"
        editor_view.text_edit.setTextCursor(cursor)
        
        # Mock find method
        with patch.object(editor_view, '_on_find') as mock_find:
            # Trigger replace
            editor_view._on_replace()
            
            # Check that text was replaced
            assert "This is a example document." in editor_view.text_edit.toPlainText()
            
            # Check that find was called to find the next occurrence
            mock_find.assert_called_once()
    
    def test_replace_all_functionality(self, qtbot, editor_view):
        """Test the replace all functionality."""
        # Set content
        editor_view.set_content("This is a test document. It contains test text for testing.")
        
        # Configure find/replace dialog
        editor_view.find_replace_dialog.find_edit.setText("test")
        editor_view.find_replace_dialog.replace_edit.setText("example")
        editor_view.find_replace_dialog.case_sensitive.setChecked(False)
        editor_view.find_replace_dialog.whole_words.setChecked(False)
        
        # Mock find method to simulate finding text
        with patch.object(editor_view.text_edit, 'find', side_effect=[True, True, True, False]) as mock_find:
            # Trigger replace all
            editor_view._on_replace_all()
            
            # Check that find was called multiple times
            assert mock_find.call_count == 4
            
            # Check status bar
            assert "Replaced 3 occurrences" in editor_view.status_bar.text()
    
    def test_formatting_actions(self, qtbot, editor_view):
        """Test the formatting actions."""
        # Set content
        editor_view.set_content("This is a test document.")
        
        # Mock text edit methods
        editor_view.text_edit.setFontWeight = MagicMock()
        editor_view.text_edit.setFontItalic = MagicMock()
        editor_view.text_edit.setFontUnderline = MagicMock()
        editor_view.text_edit.setAlignment = MagicMock()
        
        # Test bold action
        editor_view._on_bold(True)
        editor_view.text_edit.setFontWeight.assert_called_with(QFont.Weight.Bold)
        
        editor_view._on_bold(False)
        editor_view.text_edit.setFontWeight.assert_called_with(QFont.Weight.Normal)
        
        # Test italic action
        editor_view._on_italic(True)
        editor_view.text_edit.setFontItalic.assert_called_with(True)
        
        editor_view._on_italic(False)
        editor_view.text_edit.setFontItalic.assert_called_with(False)
        
        # Test underline action
        editor_view._on_underline(True)
        editor_view.text_edit.setFontUnderline.assert_called_with(True)
        
        editor_view._on_underline(False)
        editor_view.text_edit.setFontUnderline.assert_called_with(False)
        
        # Test alignment actions
        editor_view._on_alignment(Qt.AlignmentFlag.AlignLeft)
        editor_view.text_edit.setAlignment.assert_called_with(Qt.AlignmentFlag.AlignLeft)
        assert editor_view.align_left_action.isChecked()
        assert not editor_view.align_center_action.isChecked()
        
        editor_view._on_alignment(Qt.AlignmentFlag.AlignCenter)
        editor_view.text_edit.setAlignment.assert_called_with(Qt.AlignmentFlag.AlignCenter)
        assert not editor_view.align_left_action.isChecked()
        assert editor_view.align_center_action.isChecked()
        
        editor_view._on_alignment(Qt.AlignmentFlag.AlignRight)
        editor_view.text_edit.setAlignment.assert_called_with(Qt.AlignmentFlag.AlignRight)
        assert not editor_view.align_left_action.isChecked()
        assert not editor_view.align_center_action.isChecked()
        assert editor_view.align_right_action.isChecked()
        
        editor_view._on_alignment(Qt.AlignmentFlag.AlignJustify)
        editor_view.text_edit.setAlignment.assert_called_with(Qt.AlignmentFlag.AlignJustify)
        assert not editor_view.align_left_action.isChecked()
        assert not editor_view.align_center_action.isChecked()
        assert not editor_view.align_right_action.isChecked()
        assert editor_view.align_justify_action.isChecked()


class TestSyntaxHighlighter:
    """Test cases for the SyntaxHighlighter class."""
    
    def test_init(self):
        """Test initialization of the syntax highlighter."""
        # Create document
        document = QTextDocument()
        
        # Create highlighter
        highlighter = SyntaxHighlighter(document)
        
        # Check formats
        assert "dialogue" in highlighter.formats
        assert "bold" in highlighter.formats
        assert "italic" in highlighter.formats
        assert "heading" in highlighter.formats
        assert "subheading" in highlighter.formats
        assert "comment" in highlighter.formats
        
        # Check rules
        assert len(highlighter.rules) == 6  # 6 rules defined in _init_rules
    
    def test_highlight_block(self, qtbot):
        """Test highlighting a block of text."""
        # Create document
        document = QTextDocument()
        document.setPlainText('"This is dialogue text."\n'
                             '**This is bold text.**\n'
                             '*This is italic text.*\n'
                             '# This is a heading\n'
                             '## This is a subheading\n'
                             '// This is a comment')
        
        # Create highlighter
        highlighter = SyntaxHighlighter(document)
        
        # Mock setFormat method
        highlighter.setFormat = MagicMock()
        
        # Highlight first block (dialogue)
        highlighter.highlightBlock('"This is dialogue text."')
        
        # Check that setFormat was called for dialogue
        highlighter.setFormat.assert_called_with(0, 24, highlighter.formats["dialogue"])
        
        # Reset mock
        highlighter.setFormat.reset_mock()
        
        # Highlight second block (bold)
        highlighter.highlightBlock('**This is bold text.**')
        
        # Check that setFormat was called for bold
        highlighter.setFormat.assert_called_with(0, 22, highlighter.formats["bold"])
        
        # Reset mock
        highlighter.setFormat.reset_mock()
        
        # Highlight third block (italic)
        highlighter.highlightBlock('*This is italic text.*')
        
        # Check that setFormat was called for italic
        highlighter.setFormat.assert_called_with(0, 22, highlighter.formats["italic"])
        
        # Reset mock
        highlighter.setFormat.reset_mock()
        
        # Highlight fourth block (heading)
        highlighter.highlightBlock('# This is a heading')
        
        # Check that setFormat was called for heading
        highlighter.setFormat.assert_called_with(0, 19, highlighter.formats["heading"])
        
        # Reset mock
        highlighter.setFormat.reset_mock()
        
        # Highlight fifth block (subheading)
        highlighter.highlightBlock('## This is a subheading')
        
        # Check that setFormat was called for subheading
        highlighter.setFormat.assert_called_with(0, 24, highlighter.formats["subheading"])
        
        # Reset mock
        highlighter.setFormat.reset_mock()
        
        # Highlight sixth block (comment)
        highlighter.highlightBlock('// This is a comment')
        
        # Check that setFormat was called for comment
        highlighter.setFormat.assert_called_with(0, 20, highlighter.formats["comment"])


class TestFindReplaceDialog:
    """Test cases for the FindReplaceDialog class."""
    
    def test_init(self, qtbot):
        """Test initialization of the find/replace dialog."""
        # Create dialog
        dialog = FindReplaceDialog()
        qtbot.addWidget(dialog)
        
        # Check components
        assert dialog.find_label is not None
        assert dialog.find_edit is not None
        assert dialog.replace_label is not None
        assert dialog.replace_edit is not None
        assert dialog.case_sensitive is not None
        assert dialog.whole_words is not None
        assert dialog.search_backward is not None
        assert dialog.button_box is not None
        assert dialog.find_button is not None
        assert dialog.replace_button is not None
        assert dialog.replace_all_button is not None
        assert dialog.close_button is not None
        
        # Check window title
        assert dialog.windowTitle() == "Find and Replace"


if __name__ == '__main__':
    pytest.main(['-v', __file__])
