#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the export_utils module.

This module contains unit tests for the export utility functions:
- Export format handling
- Template processing
- Metadata handling
- Batch export
- File format conversion
"""

import os
import tempfile
import json
import zipfile
from unittest.mock import patch, MagicMock, mock_open

import pytest
from src.tests.base_test import BaseTest
from src.utils.export_utils import (
    check_export_dependencies, get_available_formats, validate_export_settings,
    merge_export_settings, convert_markdown_to_html, convert_html_to_plain_text,
    create_temp_export_directory, cleanup_temp_export_directory,
    create_epub_container, apply_template, load_template, batch_export,
    extract_metadata, remove_metadata, get_page_size,
    FORMAT_DOCX, FORMAT_PDF, FORMAT_MARKDOWN, FORMAT_HTML, FORMAT_EPUB, FORMAT_TXT,
    VALID_FORMATS, DEFAULT_EXPORT_SETTINGS
)


class TestExportUtils(BaseTest):
    """Unit tests for the export_utils module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create test files and directories
        self.test_template_path = os.path.join(self.test_dir, "test_template.txt")
        self.test_template_content = "Title: {{title}}\nAuthor: {{author}}\nContent: {{content}}"
        with open(self.test_template_path, "w", encoding="utf-8") as f:
            f.write(self.test_template_content)
        
        self.test_markdown_path = os.path.join(self.test_dir, "test_markdown.md")
        self.test_markdown_content = "# Test Heading\n\nThis is a **bold** test."
        with open(self.test_markdown_path, "w", encoding="utf-8") as f:
            f.write(self.test_markdown_content)
        
        self.test_html_path = os.path.join(self.test_dir, "test_html.html")
        self.test_html_content = "<h1>Test Heading</h1><p>This is a <strong>bold</strong> test.</p>"
        with open(self.test_html_path, "w", encoding="utf-8") as f:
            f.write(self.test_html_content)
        
        self.test_metadata_content = """---
title: Test Document
author: Test Author
date: 2023-01-01
tags: test, document
---

This is the content of the document.
"""
    
    def test_check_export_dependencies(self):
        """Test checking export dependencies."""
        # Get dependencies
        dependencies = check_export_dependencies()
        
        # Verify the dependencies
        self.assertIsInstance(dependencies, dict)
        self.assertIn(FORMAT_DOCX, dependencies)
        self.assertIn(FORMAT_PDF, dependencies)
        self.assertIn(FORMAT_MARKDOWN, dependencies)
        self.assertIn(FORMAT_HTML, dependencies)
        self.assertIn(FORMAT_EPUB, dependencies)
        self.assertIn(FORMAT_TXT, dependencies)
        
        # TXT should always be available
        self.assertTrue(dependencies[FORMAT_TXT])
    
    def test_get_available_formats(self):
        """Test getting available export formats."""
        # Mock dependencies
        with patch("src.utils.export_utils.check_export_dependencies", return_value={
            FORMAT_DOCX: True,
            FORMAT_PDF: False,
            FORMAT_MARKDOWN: True,
            FORMAT_HTML: False,
            FORMAT_EPUB: False,
            FORMAT_TXT: True
        }):
            # Get available formats
            formats = get_available_formats()
            
            # Verify the formats
            self.assertIsInstance(formats, list)
            self.assertIn(FORMAT_DOCX, formats)
            self.assertIn(FORMAT_MARKDOWN, formats)
            self.assertIn(FORMAT_TXT, formats)
            self.assertNotIn(FORMAT_PDF, formats)
            self.assertNotIn(FORMAT_HTML, formats)
            self.assertNotIn(FORMAT_EPUB, formats)
    
    def test_validate_export_settings_valid(self):
        """Test validating valid export settings."""
        # Valid settings
        settings = {
            "page_size": "letter",
            "margin_top": 1.0,
            "margin_bottom": 1.0,
            "margin_left": 1.0,
            "margin_right": 1.0,
            "font_name": "Times New Roman",
            "font_size": 12,
            "line_spacing": 1.5,
            "paragraph_spacing": 12,
            "include_title_page": True
        }
        
        # Validate settings
        valid, errors = validate_export_settings(settings)
        
        # Verify validation
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_export_settings_invalid(self):
        """Test validating invalid export settings."""
        # Invalid settings
        settings = {
            "page_size": "invalid",
            "margin_top": -1.0,
            "font_size": 100,
            "unknown_setting": "value"
        }
        
        # Validate settings
        valid, errors = validate_export_settings(settings)
        
        # Verify validation
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
        
        # Check specific errors
        error_messages = "\n".join(errors)
        self.assertIn("page_size", error_messages)
        self.assertIn("margin_top", error_messages)
        self.assertIn("font_size", error_messages)
        self.assertIn("unknown_setting", error_messages)
    
    def test_merge_export_settings(self):
        """Test merging export settings."""
        # User settings
        user_settings = {
            "page_size": "a4",
            "font_name": "Arial",
            "font_size": 14
        }
        
        # Merge settings
        merged_settings = merge_export_settings(user_settings)
        
        # Verify merged settings
        self.assertEqual(merged_settings["page_size"], "a4")
        self.assertEqual(merged_settings["font_name"], "Arial")
        self.assertEqual(merged_settings["font_size"], 14)
        
        # Verify default settings are preserved
        self.assertEqual(merged_settings["margin_top"], DEFAULT_EXPORT_SETTINGS["margin_top"])
        self.assertEqual(merged_settings["include_title_page"], DEFAULT_EXPORT_SETTINGS["include_title_page"])
        
        # Test with None
        merged_settings = merge_export_settings(None)
        self.assertEqual(merged_settings, DEFAULT_EXPORT_SETTINGS)
    
    def test_convert_markdown_to_html(self):
        """Test converting Markdown to HTML."""
        # Test with Markdown library available
        with patch("src.utils.export_utils.MARKDOWN_AVAILABLE", True):
            with patch("src.utils.export_utils.markdown.markdown", return_value="<p>Converted HTML</p>"):
                html = convert_markdown_to_html("Test Markdown")
                self.assertEqual(html, "<p>Converted HTML</p>")
        
        # Test with Markdown library not available
        with patch("src.utils.export_utils.MARKDOWN_AVAILABLE", False):
            with patch("src.utils.export_utils.logger.warning") as mock_warning:
                html = convert_markdown_to_html("Test Markdown")
                self.assertEqual(html, "<pre>Test Markdown</pre>")
                mock_warning.assert_called_once()
        
        # Test with exception
        with patch("src.utils.export_utils.MARKDOWN_AVAILABLE", True):
            with patch("src.utils.export_utils.markdown.markdown", side_effect=Exception("Test error")):
                with patch("src.utils.export_utils.logger.error") as mock_error:
                    html = convert_markdown_to_html("Test Markdown")
                    self.assertEqual(html, "<pre>Test Markdown</pre>")
                    mock_error.assert_called_once()
    
    def test_convert_html_to_plain_text(self):
        """Test converting HTML to plain text."""
        # Test with BeautifulSoup library available
        with patch("src.utils.export_utils.BS4_AVAILABLE", True):
            mock_soup = MagicMock()
            mock_soup.get_text.return_value = "Plain Text"
            with patch("src.utils.export_utils.BeautifulSoup", return_value=mock_soup):
                text = convert_html_to_plain_text("<p>Test HTML</p>")
                self.assertEqual(text, "Plain Text")
        
        # Test with BeautifulSoup library not available
        with patch("src.utils.export_utils.BS4_AVAILABLE", False):
            with patch("src.utils.export_utils.logger.warning") as mock_warning:
                text = convert_html_to_plain_text("<p>Test HTML</p>")
                self.assertEqual(text, "Test HTML")
                mock_warning.assert_called_once()
        
        # Test with exception
        with patch("src.utils.export_utils.BS4_AVAILABLE", True):
            with patch("src.utils.export_utils.BeautifulSoup", side_effect=Exception("Test error")):
                with patch("src.utils.export_utils.logger.error") as mock_error:
                    text = convert_html_to_plain_text("<p>Test HTML</p>")
                    self.assertEqual(text, "Test HTML")
                    mock_error.assert_called_once()
    
    def test_create_temp_export_directory(self):
        """Test creating a temporary export directory."""
        # Create a temporary directory
        with patch("src.utils.export_utils.tempfile.mkdtemp", return_value="/tmp/test_dir"):
            with patch("src.utils.export_utils.logger.debug") as mock_debug:
                temp_dir = create_temp_export_directory()
                self.assertEqual(temp_dir, "/tmp/test_dir")
                mock_debug.assert_called_once()
    
    def test_cleanup_temp_export_directory(self):
        """Test cleaning up a temporary export directory."""
        # Test successful cleanup
        with patch("src.utils.export_utils.shutil.rmtree") as mock_rmtree:
            with patch("src.utils.export_utils.logger.debug") as mock_debug:
                result = cleanup_temp_export_directory("/tmp/test_dir")
                self.assertTrue(result)
                mock_rmtree.assert_called_once_with("/tmp/test_dir")
                mock_debug.assert_called_once()
        
        # Test failed cleanup
        with patch("src.utils.export_utils.shutil.rmtree", side_effect=Exception("Test error")):
            with patch("src.utils.export_utils.logger.error") as mock_error:
                result = cleanup_temp_export_directory("/tmp/test_dir")
                self.assertFalse(result)
                mock_error.assert_called_once()
    
    def test_create_epub_container(self):
        """Test creating an EPUB container."""
        # Test with BeautifulSoup not available
        with patch("src.utils.export_utils.BS4_AVAILABLE", False):
            with patch("src.utils.export_utils.logger.error") as mock_error:
                result = create_epub_container("output.epub", [], {})
                self.assertFalse(result)
                mock_error.assert_called_once()
        
        # Test with BeautifulSoup available
        with patch("src.utils.export_utils.BS4_AVAILABLE", True):
            # Mock file operations
            with patch("src.utils.export_utils.create_temp_export_directory", return_value="/tmp/test_dir"):
                with patch("src.utils.export_utils.os.makedirs") as mock_makedirs:
                    with patch("builtins.open", mock_open()) as mock_file:
                        with patch("src.utils.export_utils.zipfile.ZipFile") as mock_zipfile:
                            with patch("src.utils.export_utils.cleanup_temp_export_directory", return_value=True):
                                with patch("src.utils.export_utils.logger.info") as mock_info:
                                    # Test data
                                    content_files = [
                                        {"id": "chapter1", "title": "Chapter 1", "content": "<p>Chapter 1 content</p>"},
                                        {"id": "chapter2", "title": "Chapter 2", "content": "<p>Chapter 2 content</p>"}
                                    ]
                                    metadata = {
                                        "title": "Test Book",
                                        "creator": "Test Author",
                                        "identifier": "test-id",
                                        "language": "en"
                                    }
                                    
                                    # Create EPUB
                                    result = create_epub_container("output.epub", content_files, metadata)
                                    
                                    # Verify result
                                    self.assertTrue(result)
                                    mock_makedirs.assert_called()
                                    mock_file.assert_called()
                                    mock_zipfile.assert_called_once_with("output.epub", "w", zipfile.ZIP_DEFLATED)
                                    mock_info.assert_called_once()
        
        # Test with exception
        with patch("src.utils.export_utils.BS4_AVAILABLE", True):
            with patch("src.utils.export_utils.create_temp_export_directory", side_effect=Exception("Test error")):
                with patch("src.utils.export_utils.logger.error") as mock_error:
                    result = create_epub_container("output.epub", [], {})
                    self.assertFalse(result)
                    mock_error.assert_called_once()
    
    def test_apply_template(self):
        """Test applying a template."""
        # Template and data
        template = "Title: {{title}}\nAuthor: {{author}}\nContent: {{content}}"
        data = {
            "title": "Test Title",
            "author": "Test Author",
            "content": "Test Content"
        }
        
        # Apply template
        result = apply_template(template, data)
        
        # Verify result
        self.assertEqual(result, "Title: Test Title\nAuthor: Test Author\nContent: Test Content")
        
        # Test with missing data
        data = {"title": "Test Title"}
        result = apply_template(template, data)
        self.assertEqual(result, "Title: Test Title\nAuthor: {{author}}\nContent: {{content}}")
    
    def test_load_template(self):
        """Test loading a template."""
        # Test with existing template
        with patch("src.utils.export_utils.read_text_file", return_value="Template content"):
            template = load_template("template.txt")
            self.assertEqual(template, "Template content")
        
        # Test with non-existent template
        with patch("src.utils.export_utils.read_text_file", return_value=None):
            template = load_template("nonexistent.txt")
            self.assertIsNone(template)
    
    def test_batch_export(self):
        """Test batch exporting."""
        # Mock export function
        def mock_export_function(item, output_path, format, settings):
            return item.id != "fail"
        
        # Mock items
        class MockItem:
            def __init__(self, id, title):
                self.id = id
                self.title = title
        
        items = [
            MockItem("item1", "Item 1"),
            MockItem("item2", "Item 2"),
            MockItem("fail", "Failing Item")
        ]
        
        # Test with ensure_directory success
        with patch("src.utils.export_utils.ensure_directory", return_value=True):
            with patch("src.utils.export_utils.logger.info") as mock_info:
                with patch("src.utils.export_utils.logger.error") as mock_error:
                    # Batch export
                    results = batch_export(items, mock_export_function, self.test_dir, "txt")
                    
                    # Verify results
                    self.assertEqual(len(results), 3)
                    self.assertTrue(results["item1"])
                    self.assertTrue(results["item2"])
                    self.assertFalse(results["fail"])
                    
                    # Verify logging
                    self.assertEqual(mock_info.call_count, 2)  # Two successful exports
                    self.assertEqual(mock_error.call_count, 1)  # One failed export
        
        # Test with exception
        with patch("src.utils.export_utils.ensure_directory", return_value=True):
            with patch("src.utils.export_utils.logger.error") as mock_error:
                # Create a function that raises an exception
                def failing_export_function(item, output_path, format, settings):
                    raise Exception("Test error")
                
                # Batch export
                results = batch_export(items, failing_export_function, self.test_dir, "txt")
                
                # Verify results
                self.assertEqual(len(results), 3)
                self.assertFalse(results["item1"])
                self.assertFalse(results["item2"])
                self.assertFalse(results["fail"])
                
                # Verify logging
                self.assertEqual(mock_error.call_count, 3)  # Three exceptions
    
    def test_extract_metadata(self):
        """Test extracting metadata."""
        # Extract metadata
        metadata = extract_metadata(self.test_metadata_content)
        
        # Verify metadata
        self.assertEqual(metadata["title"], "Test Document")
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["date"], "2023-01-01")
        self.assertEqual(metadata["tags"], "test, document")
        
        # Test with no metadata
        metadata = extract_metadata("No metadata here")
        self.assertEqual(metadata, {})
    
    def test_remove_metadata(self):
        """Test removing metadata."""
        # Remove metadata
        content = remove_metadata(self.test_metadata_content)
        
        # Verify content
        self.assertEqual(content, "This is the content of the document.")
        
        # Test with no metadata
        content = remove_metadata("No metadata here")
        self.assertEqual(content, "No metadata here")
    
    def test_get_page_size(self):
        """Test getting page size."""
        # Test with valid page sizes
        self.assertEqual(get_page_size("letter"), (8.5 * 72, 11 * 72))
        self.assertEqual(get_page_size("a4"), (595, 842))
        self.assertEqual(get_page_size("legal"), (8.5 * 72, 14 * 72))
        
        # Test with invalid page size
        with patch("src.utils.export_utils.logger.warning") as mock_warning:
            size = get_page_size("invalid")
            self.assertEqual(size, (8.5 * 72, 11 * 72))  # Should default to letter
            mock_warning.assert_called_once()
        
        # Test case insensitivity
        self.assertEqual(get_page_size("LETTER"), (8.5 * 72, 11 * 72))
        self.assertEqual(get_page_size("A4"), (595, 842))


# Pytest-style tests
class TestExportUtilsPytest:
    """Pytest-style tests for the export_utils module."""
    
    @pytest.fixture
    def setup(self, request):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        test_dir = tempfile.mkdtemp()
        
        # Create test files and directories
        test_template_path = os.path.join(test_dir, "test_template.txt")
        test_template_content = "Title: {{title}}\nAuthor: {{author}}\nContent: {{content}}"
        with open(test_template_path, "w", encoding="utf-8") as f:
            f.write(test_template_content)
        
        test_metadata_content = """---
title: Test Document
author: Test Author
date: 2023-01-01
tags: test, document
---

This is the content of the document.
"""
        
        # Create a yield fixture to clean up after the test
        yield {
            "test_dir": test_dir,
            "test_template_path": test_template_path,
            "test_template_content": test_template_content,
            "test_metadata_content": test_metadata_content
        }
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
    
    def test_apply_template_pytest(self, setup):
        """Test applying a template using pytest style."""
        # Template and data
        template = "Title: {{title}}\nAuthor: {{author}}\nContent: {{content}}"
        data = {
            "title": "Test Title",
            "author": "Test Author",
            "content": "Test Content"
        }
        
        # Apply template
        result = apply_template(template, data)
        
        # Verify result
        assert result == "Title: Test Title\nAuthor: Test Author\nContent: Test Content"
    
    def test_extract_metadata_pytest(self, setup):
        """Test extracting metadata using pytest style."""
        # Extract metadata
        metadata = extract_metadata(setup["test_metadata_content"])
        
        # Verify metadata
        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "Test Author"
        assert metadata["date"] == "2023-01-01"
        assert metadata["tags"] == "test, document"


if __name__ == '__main__':
    unittest.main()
