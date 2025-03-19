#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Document model.
"""

import pytest
import unittest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.document import Document


class TestDocument(unittest.TestCase):
    """Test suite for the Document model."""

    def test_init_default_values(self):
        """Test that a document is initialized with default values."""
        doc = Document()
        
        assert doc.title == ""
        assert doc.content == ""
        assert doc.type == Document.TYPE_SCENE
        assert doc.parent_id is None
        assert doc.children_ids == []
        assert doc.order == 0
        assert isinstance(doc.created_at, datetime.datetime)
        assert isinstance(doc.updated_at, datetime.datetime)
        assert doc.word_count == 0
        assert doc.character_count == 0
        assert doc.tags == []
        assert doc.metadata == {}
        assert doc.is_included_in_compile is True
        assert doc.synopsis == ""
        assert doc.status == "Draft"
        assert doc.color is None

    def test_init_with_values(self):
        """Test that a document is initialized with provided values."""
        title = "Test Document"
        content = "This is a test document."
        doc_type = Document.TYPE_CHAPTER
        
        doc = Document(
            title=title,
            content=content,
            type=doc_type
        )
        
        assert doc.title == title
        assert doc.content == content
        assert doc.type == doc_type
        assert doc.word_count == 5  # "This is a test document."
        assert doc.character_count == 21  # "Thisisatestdocument."

    def test_init_with_invalid_type(self):
        """Test that a document with invalid type defaults to scene."""
        doc = Document(type="invalid_type")
        
        assert doc.type == Document.TYPE_SCENE

    def test_update_counts(self):
        """Test that word and character counts are updated correctly."""
        doc = Document()
        
        # Empty content
        doc.update_counts()
        assert doc.word_count == 0
        assert doc.character_count == 0
        
        # Set content
        doc.content = "This is a test."
        doc.update_counts()
        assert doc.word_count == 4
        assert doc.character_count == 11  # "Thisisatest."
        
        # More complex content
        doc.content = "This is a longer test with multiple words and some punctuation!"
        doc.update_counts()
        assert doc.word_count == 11
        assert doc.character_count == 54  # Without spaces

    def test_set_content(self):
        """Test setting document content."""
        doc = Document()
        content = "New content for testing."
        
        # Mock datetime.now() to return a fixed value
        with patch('datetime.datetime') as mock_datetime:
            fixed_time = datetime.datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_time
            
            doc.set_content(content)
            
            assert doc.content == content
            assert doc.updated_at == fixed_time
            assert doc.word_count == 4
            assert doc.character_count == 18  # "Newcontentfortesting."

    def test_append_content(self):
        """Test appending content to a document."""
        doc = Document(content="Initial content. ")
        append_text = "Appended content."
        
        # Mock datetime.now() to return a fixed value
        with patch('datetime.datetime') as mock_datetime:
            fixed_time = datetime.datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_time
            
            doc.append_content(append_text)
            
            assert doc.content == "Initial content. Appended content."
            assert doc.updated_at == fixed_time
            assert doc.word_count == 4
            assert doc.character_count == 30  # "Initialcontent.Appendedcontent."

    def test_set_type(self):
        """Test setting document type."""
        doc = Document()
        
        # Valid type
        doc.set_type(Document.TYPE_CHAPTER)
        assert doc.type == Document.TYPE_CHAPTER
        
        # Invalid type
        doc.set_type("invalid_type")
        assert doc.type == Document.TYPE_CHAPTER  # Unchanged

    def test_add_child(self):
        """Test adding a child document."""
        doc = Document()
        child_id = "child123"
        
        doc.add_child(child_id)
        assert child_id in doc.children_ids
        
        # Adding the same child again should not duplicate
        doc.add_child(child_id)
        assert doc.children_ids.count(child_id) == 1

    def test_remove_child(self):
        """Test removing a child document."""
        doc = Document()
        child_id = "child123"
        
        # Add child
        doc.add_child(child_id)
        assert child_id in doc.children_ids
        
        # Remove child
        doc.remove_child(child_id)
        assert child_id not in doc.children_ids
        
        # Removing a non-existent child should not error
        doc.remove_child("nonexistent")

    def test_set_parent(self):
        """Test setting the parent document."""
        doc = Document()
        parent_id = "parent123"
        
        # Set parent
        doc.set_parent(parent_id)
        assert doc.parent_id == parent_id
        
        # Remove parent
        doc.set_parent(None)
        assert doc.parent_id is None

    def test_add_tag(self):
        """Test adding a tag to the document."""
        doc = Document()
        tag = "test-tag"
        
        doc.add_tag(tag)
        assert tag in doc.tags
        
        # Adding the same tag again should not duplicate
        doc.add_tag(tag)
        assert doc.tags.count(tag) == 1

    def test_remove_tag(self):
        """Test removing a tag from the document."""
        doc = Document()
        tag = "test-tag"
        
        # Add tag
        doc.add_tag(tag)
        assert tag in doc.tags
        
        # Remove tag
        doc.remove_tag(tag)
        assert tag not in doc.tags
        
        # Removing a non-existent tag should not error
        doc.remove_tag("nonexistent")

    def test_metadata_operations(self):
        """Test metadata operations."""
        doc = Document()
        
        # Set metadata
        doc.set_metadata("key1", "value1")
        assert doc.metadata["key1"] == "value1"
        
        # Get metadata
        assert doc.get_metadata("key1") == "value1"
        assert doc.get_metadata("nonexistent") is None
        assert doc.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        doc.set_metadata("key1", "updated")
        assert doc.get_metadata("key1") == "updated"
        
        # Remove metadata
        doc.remove_metadata("key1")
        assert "key1" not in doc.metadata
        
        # Removing non-existent metadata should not error
        doc.remove_metadata("nonexistent")

    def test_set_status(self):
        """Test setting document status."""
        doc = Document()
        status = "Final"
        
        doc.set_status(status)
        assert doc.status == status

    def test_set_synopsis(self):
        """Test setting document synopsis."""
        doc = Document()
        synopsis = "This is a test synopsis."
        
        doc.set_synopsis(synopsis)
        assert doc.synopsis == synopsis

    def test_set_color(self):
        """Test setting document color."""
        doc = Document()
        color = "#FF0000"
        
        # Set color
        doc.set_color(color)
        assert doc.color == color
        
        # Remove color
        doc.set_color(None)
        assert doc.color is None

    def test_set_compile_inclusion(self):
        """Test setting compile inclusion."""
        doc = Document()
        
        # Default is True
        assert doc.is_included_in_compile is True
        
        # Set to False
        doc.set_compile_inclusion(False)
        assert doc.is_included_in_compile is False
        
        # Set back to True
        doc.set_compile_inclusion(True)
        assert doc.is_included_in_compile is True

    def test_type_check_methods(self):
        """Test the type check methods."""
        # Folder
        doc = Document(type=Document.TYPE_FOLDER)
        assert doc.is_folder() is True
        assert doc.is_chapter() is False
        assert doc.is_scene() is False
        assert doc.is_note() is False
        
        # Chapter
        doc = Document(type=Document.TYPE_CHAPTER)
        assert doc.is_folder() is False
        assert doc.is_chapter() is True
        assert doc.is_scene() is False
        assert doc.is_note() is False
        
        # Scene
        doc = Document(type=Document.TYPE_SCENE)
        assert doc.is_folder() is False
        assert doc.is_chapter() is False
        assert doc.is_scene() is True
        assert doc.is_note() is False
        
        # Note
        doc = Document(type=Document.TYPE_NOTE)
        assert doc.is_folder() is False
        assert doc.is_chapter() is False
        assert doc.is_scene() is False
        assert doc.is_note() is True

    def test_str_representation(self):
        """Test the string representation of a document."""
        doc = Document(title="Test Document", type=Document.TYPE_CHAPTER)
        doc.content = "This is a test document."
        doc.update_counts()
        
        expected = "Document(title='Test Document', type='chapter', words=5)"
        assert str(doc) == expected

    def test_to_dict(self):
        """Test converting a document to a dictionary."""
        doc = Document(
            title="Test Document",
            content="This is a test document.",
            type=Document.TYPE_CHAPTER
        )
        
        doc_dict = doc.to_dict()
        
        assert doc_dict["title"] == "Test Document"
        assert doc_dict["content"] == "This is a test document."
        assert doc_dict["type"] == Document.TYPE_CHAPTER
        assert "id" in doc_dict
        assert "created_at" in doc_dict
        assert "updated_at" in doc_dict

    def test_from_dict(self):
        """Test creating a document from a dictionary."""
        data: Dict[str, Any] = {
            "title": "Test Document",
            "content": "This is a test document.",
            "type": Document.TYPE_CHAPTER,
            "tags": ["test", "document"],
            "is_included_in_compile": False
        }
        
        doc = Document.from_dict(data)
        
        assert doc.title == "Test Document"
        assert doc.content == "This is a test document."
        assert doc.type == Document.TYPE_CHAPTER
        assert doc.tags == ["test", "document"]
        assert doc.is_included_in_compile is False

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Document(
            title="Test Document",
            content="This is a test document.",
            type=Document.TYPE_CHAPTER,
            tags=["test", "document"],
            is_included_in_compile=False
        )
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Document.from_json(json_str)
        
        # Check that the restored document has the same properties
        assert restored.title == original.title
        assert restored.content == original.content
        assert restored.type == original.type
        assert restored.tags == original.tags
        assert restored.is_included_in_compile == original.is_included_in_compile
