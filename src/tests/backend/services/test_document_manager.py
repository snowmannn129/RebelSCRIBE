#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the DocumentManager service.

This module contains tests for the DocumentManager class, which is responsible
for creating, loading, saving, and managing documents within a project.
"""

import unittest
import os
import tempfile
import shutil
import json
import datetime
from unittest.mock import patch, MagicMock, mock_open

from src.backend.services.document_manager import DocumentManager
from src.backend.models.document import Document


class TestDocumentManager(unittest.TestCase):
    """Test cases for the DocumentManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {self.temp_dir}")
        
        # Mock the config to use the temporary directory
        self.config_patcher = patch('src.backend.services.document_manager.ConfigManager')
        self.mock_config = self.config_patcher.start()
        mock_config_instance = MagicMock()
        
        # Set up the get_config method to return a dictionary
        config_dict = {
            'application': {
                'data_directory': self.temp_dir
            },
            'documents': {
                'max_versions': 5
            }
        }
        mock_config_instance.get_config.return_value = config_dict
        print(f"Mock config_dict: {config_dict}")
        
        # Set up the get method to properly handle section, key, default parameters
        def mock_get(section, key=None, default=None):
            print(f"Mock get called with: section={section}, key={key}, default={default}")
            section_dict = config_dict.get(section, {})
            if key is None:
                return section_dict
            return section_dict.get(key, default)
        
        mock_config_instance.get = mock_get
        self.mock_config.return_value = mock_config_instance
        print("Mock ConfigManager set up")
        
        # Create the document manager instance with a project path
        self.project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.project_path, exist_ok=True)
        print(f"Created project path: {self.project_path}")
        
        try:
            self.document_manager = DocumentManager(self.project_path)
            print("DocumentManager created successfully")
        except Exception as e:
            print(f"Error creating DocumentManager: {e}")
            import traceback
            traceback.print_exc()
            raise

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop the config patcher
        self.config_patcher.stop()
        
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test initialization of DocumentManager."""
        # Test with project path
        self.assertEqual(self.document_manager.project_path, self.project_path)
        self.assertEqual(self.document_manager.documents_dir, os.path.join(self.project_path, "documents"))
        self.assertEqual(self.document_manager.versions_dir, os.path.join(self.project_path, "versions"))
        self.assertEqual(self.document_manager.max_versions, 5)
        
        # Test without project path
        dm_no_project = DocumentManager()
        self.assertIsNone(dm_no_project.project_path)
        self.assertEqual(dm_no_project.documents_dir, os.path.join(self.temp_dir, "documents"))
        self.assertEqual(dm_no_project.versions_dir, os.path.join(self.temp_dir, "versions"))

    def test_set_project_path(self):
        """Test setting the project path."""
        new_path = os.path.join(self.temp_dir, "new_project")
        self.document_manager.set_project_path(new_path)
        
        self.assertEqual(self.document_manager.project_path, new_path)
        self.assertEqual(self.document_manager.documents_dir, os.path.join(new_path, "documents"))
        self.assertEqual(self.document_manager.versions_dir, os.path.join(new_path, "versions"))
        self.assertEqual(self.document_manager.documents, {})
        self.assertEqual(self.document_manager.modified_documents, set())

    def test_create_document(self):
        """Test creating a new document."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Test content"
        )
        
        # Assertions
        self.assertIsNotNone(document)
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.type, Document.TYPE_SCENE)
        self.assertEqual(document.content, "Test content")
        self.assertIsNone(document.parent_id)
        self.assertIn(document.id, self.document_manager.documents)
        self.assertIn(document.id, self.document_manager.modified_documents)

    def test_create_document_with_parent(self):
        """Test creating a new document with a parent."""
        # Create a parent document
        parent = self.document_manager.create_document(
            title="Parent Document",
            doc_type=Document.TYPE_FOLDER
        )
        
        # Create a child document
        child = self.document_manager.create_document(
            title="Child Document",
            doc_type=Document.TYPE_SCENE,
            parent_id=parent.id
        )
        
        # Assertions
        self.assertIsNotNone(child)
        self.assertEqual(child.title, "Child Document")
        self.assertEqual(child.parent_id, parent.id)
        self.assertIn(child.id, self.document_manager.documents)
        self.assertIn(child.id, self.document_manager.modified_documents)

    @patch('src.backend.services.document_manager.file_utils')
    def test_load_document(self, mock_file_utils):
        """Test loading a document by ID."""
        # Mock file_utils methods
        mock_file_utils.file_exists.return_value = True
        
        # Create mock document data
        doc_id = "test-doc-id"
        doc_data = {
            "id": doc_id,
            "title": "Test Document",
            "type": Document.TYPE_SCENE,
            "content": "Test content",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Mock read_json_file to return our document data
        mock_file_utils.read_json_file.return_value = doc_data
        
        # Load the document
        document = self.document_manager.load_document(doc_id)
        
        # Assertions
        self.assertIsNotNone(document)
        self.assertEqual(document.id, doc_id)
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.type, Document.TYPE_SCENE)
        self.assertEqual(document.content, "Test content")
        self.assertIn(doc_id, self.document_manager.documents)
        
        # Verify file_utils methods were called
        doc_path = os.path.join(self.document_manager.documents_dir, f"{doc_id}.json")
        mock_file_utils.file_exists.assert_called_with(doc_path)
        mock_file_utils.read_json_file.assert_called_with(doc_path)

    @patch('src.backend.services.document_manager.file_utils')
    def test_load_all_documents(self, mock_file_utils):
        """Test loading all documents in a project."""
        # Mock file_utils methods
        mock_file_utils.directory_exists.return_value = True
        
        # Create mock document files
        doc1_path = os.path.join(self.document_manager.documents_dir, "doc1.json")
        doc2_path = os.path.join(self.document_manager.documents_dir, "doc2.json")
        
        # Mock list_files to return our document files
        mock_file_utils.list_files.return_value = [doc1_path, doc2_path]
        
        # Create mock document data
        doc1_data = {
            "id": "doc1",
            "title": "Document 1",
            "type": Document.TYPE_SCENE,
            "content": "Content 1",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        doc2_data = {
            "id": "doc2",
            "title": "Document 2",
            "type": Document.TYPE_SCENE,
            "content": "Content 2",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Mock read_json_file to return our document data
        mock_file_utils.read_json_file.side_effect = [doc1_data, doc2_data]
        
        # Load all documents
        documents = self.document_manager.load_all_documents()
        
        # Assertions
        self.assertEqual(len(documents), 2)
        self.assertIn("doc1", documents)
        self.assertIn("doc2", documents)
        self.assertEqual(documents["doc1"].title, "Document 1")
        self.assertEqual(documents["doc2"].title, "Document 2")
        
        # Verify file_utils methods were called
        mock_file_utils.directory_exists.assert_called_with(self.document_manager.documents_dir)
        mock_file_utils.list_files.assert_called_with(self.document_manager.documents_dir, "*.json")

    @patch('src.backend.services.document_manager.file_utils')
    def test_save_document(self, mock_file_utils):
        """Test saving a document."""
        # Mock file_utils methods
        mock_file_utils.write_json_file.return_value = True
        
        # Create a document to save
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Test content"
        )
        
        # Mock _create_document_version
        with patch.object(self.document_manager, '_create_document_version', return_value=True) as mock_create_version:
            # Save the document
            result = self.document_manager.save_document(document.id)
            
            # Assertions
            self.assertTrue(result)
            self.assertNotIn(document.id, self.document_manager.modified_documents)
            
            # Verify methods were called
            mock_create_version.assert_called_once_with(document)
            doc_path = os.path.join(self.document_manager.documents_dir, f"{document.id}.json")
            mock_file_utils.write_json_file.assert_called_with(doc_path, document.to_dict())

    @patch('src.backend.services.document_manager.file_utils')
    def test_save_all_documents(self, mock_file_utils):
        """Test saving all modified documents."""
        # Mock file_utils methods
        mock_file_utils.write_json_file.return_value = True
        
        # Create documents to save
        doc1 = self.document_manager.create_document(
            title="Document 1",
            doc_type=Document.TYPE_SCENE,
        )
        
        doc2 = self.document_manager.create_document(
            title="Document 2",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Mock _create_document_version
        with patch.object(self.document_manager, '_create_document_version', return_value=True) as mock_create_version:
            # Save all documents
            result = self.document_manager.save_all_documents()
            
            # Assertions
            self.assertTrue(result)
            self.assertEqual(len(self.document_manager.modified_documents), 0)
            
            # Verify methods were called
            self.assertEqual(mock_create_version.call_count, 2)
            self.assertEqual(mock_file_utils.write_json_file.call_count, 2)

    @patch('src.backend.services.document_manager.file_utils')
    def test_create_document_version(self, mock_file_utils):
        """Test creating a document version."""
        # Mock file_utils methods
        mock_file_utils.ensure_directory.return_value = True
        mock_file_utils.write_json_file.return_value = True
        
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Test content"
        )
        
        # Mock _manage_version_count
        with patch.object(self.document_manager, '_manage_version_count') as mock_manage_versions:
            # Create a version
            result = self.document_manager._create_document_version(document)
            
            # Assertions
            self.assertTrue(result)
            
            # Verify methods were called
            doc_versions_dir = os.path.join(self.document_manager.versions_dir, document.id)
            mock_file_utils.ensure_directory.assert_called_with(doc_versions_dir)
            mock_file_utils.write_json_file.assert_called_once()
            mock_manage_versions.assert_called_once_with(doc_versions_dir)

    @patch('src.backend.services.document_manager.file_utils')
    def test_manage_version_count(self, mock_file_utils):
        """Test managing the number of versions kept for a document."""
        # Mock file_utils methods
        versions_dir = os.path.join(self.document_manager.versions_dir, "test-doc")
        
        # Create mock version files (more than max_versions)
        version_files = [
            os.path.join(versions_dir, "20250101_000001.json"),
            os.path.join(versions_dir, "20250101_000002.json"),
            os.path.join(versions_dir, "20250101_000003.json"),
            os.path.join(versions_dir, "20250101_000004.json"),
            os.path.join(versions_dir, "20250101_000005.json"),
            os.path.join(versions_dir, "20250101_000006.json"),
            os.path.join(versions_dir, "20250101_000007.json")
        ]
        
        # Mock list_files to return our version files
        mock_file_utils.list_files.return_value = version_files
        
        # Mock os.remove
        with patch('os.remove') as mock_remove:
            # Manage versions
            self.document_manager._manage_version_count(versions_dir)
            
            # Assertions
            # Should delete oldest versions (exceeding max_versions)
            excess = len(version_files) - self.document_manager.max_versions
            self.assertEqual(mock_remove.call_count, excess)
            
            # Verify the oldest versions were deleted
            for i in range(excess):
                mock_remove.assert_any_call(version_files[i])

    @patch('src.backend.services.document_manager.file_utils')
    def test_get_document_versions(self, mock_file_utils):
        """Test getting a list of versions for a document."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Mock file_utils methods
        mock_file_utils.directory_exists.return_value = True
        
        # Create mock version files
        versions_dir = os.path.join(self.document_manager.versions_dir, document.id)
        version_files = [
            os.path.join(versions_dir, "20250101_120000.json"),
            os.path.join(versions_dir, "20250101_130000.json")
        ]
        
        # Mock list_files to return our version files
        mock_file_utils.list_files.return_value = version_files
        
        # Get document versions
        versions = self.document_manager.get_document_versions(document.id)
        
        # Assertions
        self.assertEqual(len(versions), 2)
        # Versions should be sorted in reverse order (newest first)
        self.assertEqual(versions[0]["id"], "20250101_130000")
        self.assertEqual(versions[1]["id"], "20250101_120000")
        
        # Verify file_utils methods were called
        mock_file_utils.directory_exists.assert_called_with(versions_dir)
        mock_file_utils.list_files.assert_called_with(versions_dir, "*.json")

    @patch('src.backend.services.document_manager.file_utils')
    def test_load_document_version(self, mock_file_utils):
        """Test loading a specific version of a document."""
        # Mock file_utils methods
        mock_file_utils.file_exists.return_value = True
        
        # Create mock document data
        doc_id = "test-doc-id"
        version_id = "20250101_120000"
        doc_data = {
            "id": doc_id,
            "title": "Test Document",
            "type": Document.TYPE_SCENE,
            "content": "Test content",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Mock read_json_file to return our document data
        mock_file_utils.read_json_file.return_value = doc_data
        
        # Load the document version
        document = self.document_manager.load_document_version(doc_id, version_id)
        
        # Assertions
        self.assertIsNotNone(document)
        self.assertEqual(document.id, doc_id)
        self.assertEqual(document.title, "Test Document")
        
        # Verify file_utils methods were called
        version_path = os.path.join(self.document_manager.versions_dir, doc_id, f"{version_id}.json")
        mock_file_utils.file_exists.assert_called_with(version_path)
        mock_file_utils.read_json_file.assert_called_with(version_path)

    def test_restore_document_version(self):
        """Test restoring a document to a specific version."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Original content"
        )
        
        # Mock load_document_version to return a modified version
        version_doc = Document(
            id=document.id,
            title="Test Document",
            type=Document.TYPE_SCENE,
            content="Version content"
        )
        
        with patch.object(self.document_manager, 'load_document_version', return_value=version_doc) as mock_load_version:
            with patch.object(self.document_manager, '_create_document_version', return_value=True) as mock_create_version:
                with patch.object(self.document_manager, 'save_document', return_value=True) as mock_save:
                    # Restore the document version
                    result = self.document_manager.restore_document_version(document.id, "20250101_120000")
                    
                    # Assertions
                    self.assertTrue(result)
                    self.assertEqual(self.document_manager.documents[document.id].content, "Version content")
                    self.assertIn(document.id, self.document_manager.modified_documents)
                    
                    # Verify methods were called
                    mock_load_version.assert_called_once_with(document.id, "20250101_120000")
                    mock_create_version.assert_called_once_with(document)
                    mock_save.assert_called_once_with(document.id, False)

    @patch('os.remove')
    @patch('shutil.rmtree')
    def test_delete_document(self, mock_rmtree, mock_remove):
        """Test deleting a document."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Mock file_utils.file_exists and file_utils.directory_exists
        with patch('src.backend.services.document_manager.file_utils.file_exists', return_value=True) as mock_file_exists:
            with patch('src.backend.services.document_manager.file_utils.directory_exists', return_value=True) as mock_dir_exists:
                # Delete the document
                result = self.document_manager.delete_document(document.id)
                
                # Assertions
                self.assertTrue(result)
                self.assertNotIn(document.id, self.document_manager.documents)
                self.assertNotIn(document.id, self.document_manager.modified_documents)
                
                # Verify methods were called
                doc_path = os.path.join(self.document_manager.documents_dir, f"{document.id}.json")
                mock_file_exists.assert_called_with(doc_path)
                mock_remove.assert_called_with(doc_path)
                
                doc_versions_dir = os.path.join(self.document_manager.versions_dir, document.id)
                mock_dir_exists.assert_called_with(doc_versions_dir)
                mock_rmtree.assert_called_with(doc_versions_dir)

    def test_update_document(self):
        """Test updating a document."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Original content"
        )
        
        # Clear modified documents set
        self.document_manager.modified_documents.clear()
        
        # Update the document
        result = self.document_manager.update_document(
            document.id,
            title="Updated Title",
            content="Updated content",
            status="Final"
        )
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(document.title, "Updated Title")
        self.assertEqual(document.content, "Updated content")
        self.assertEqual(document.status, "Final")
        self.assertIn(document.id, self.document_manager.modified_documents)

    def test_update_document_content(self):
        """Test updating a document's content."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Original content"
        )
        
        # Clear modified documents set
        self.document_manager.modified_documents.clear()
        
        # Update the document content
        result = self.document_manager.update_document_content(document.id, "Updated content")
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(document.content, "Updated content")
        self.assertIn(document.id, self.document_manager.modified_documents)

    def test_append_document_content(self):
        """Test appending content to a document."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Original content"
        )
        
        # Clear modified documents set
        self.document_manager.modified_documents.clear()
        
        # Append content to the document
        result = self.document_manager.append_document_content(document.id, " - Appended content")
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(document.content, "Original content - Appended content")
        self.assertIn(document.id, self.document_manager.modified_documents)

    def test_get_document(self):
        """Test getting a document by ID."""
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Get the document
        retrieved_document = self.document_manager.get_document(document.id)
        
        # Assertions
        self.assertEqual(retrieved_document, document)
        
        # Test getting a document that's not loaded
        with patch.object(self.document_manager, 'load_document', return_value=document) as mock_load:
            # Clear documents dictionary
            self.document_manager.documents = {}
            
            # Get the document
            retrieved_document = self.document_manager.get_document(document.id)
            
            # Assertions
            self.assertEqual(retrieved_document, document)
            mock_load.assert_called_once_with(document.id)

    def test_get_documents_by_type(self):
        """Test getting all documents of a specific type."""
        # Create documents of different types
        scene1 = self.document_manager.create_document(
            title="Scene 1",
            doc_type=Document.TYPE_SCENE,
        )
        
        scene2 = self.document_manager.create_document(
            title="Scene 2",
            doc_type=Document.TYPE_SCENE,
        )
        
        note = self.document_manager.create_document(
            title="Note",
            doc_type=Document.TYPE_NOTE
        )
        
        # Get documents by type
        scenes = self.document_manager.get_documents_by_type(Document.TYPE_SCENE)
        notes = self.document_manager.get_documents_by_type(Document.TYPE_NOTE)
        
        # Assertions
        self.assertEqual(len(scenes), 2)
        self.assertEqual(len(notes), 1)
        self.assertIn(scene1, scenes)
        self.assertIn(scene2, scenes)
        self.assertIn(note, notes)

    def test_get_documents_by_tag(self):
        """Test getting all documents with a specific tag."""
        # Create documents with different tags
        doc1 = self.document_manager.create_document(
            title="Document 1",
            doc_type=Document.TYPE_SCENE,
        )
        
        doc2 = self.document_manager.create_document(
            title="Document 2",
            doc_type=Document.TYPE_SCENE,
        )
        
        doc3 = self.document_manager.create_document(
            title="Document 3",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Set tags and update indexes manually
        doc1.tags = ["tag1", "tag2"]
        self.document_manager._update_document_indexes(doc1)
        
        doc2.tags = ["tag1", "tag3"]
        self.document_manager._update_document_indexes(doc2)
        
        doc3.tags = ["tag3"]
        self.document_manager._update_document_indexes(doc3)
        
        # Get documents by tag
        tag1_docs = self.document_manager.get_documents_by_tag("tag1")
        tag2_docs = self.document_manager.get_documents_by_tag("tag2")
        tag3_docs = self.document_manager.get_documents_by_tag("tag3")
        
        # Assertions
        self.assertEqual(len(tag1_docs), 2)
        self.assertEqual(len(tag2_docs), 1)
        self.assertEqual(len(tag3_docs), 2)
        self.assertIn(doc1, tag1_docs)
        self.assertIn(doc2, tag1_docs)
        self.assertIn(doc1, tag2_docs)
        self.assertIn(doc2, tag3_docs)
        self.assertIn(doc3, tag3_docs)

    def test_get_documents_by_metadata(self):
        """Test getting all documents with a specific metadata value."""
        # Create documents with different metadata
        doc1 = self.document_manager.create_document(
            title="Document 1",
            doc_type=Document.TYPE_SCENE,
        )
        doc1.metadata = {"key1": "value1", "key2": "value2"}
        
        doc2 = self.document_manager.create_document(
            title="Document 2",
            doc_type=Document.TYPE_SCENE,
        )
        doc2.metadata = {"key1": "value1", "key3": "value3"}
        
        doc3 = self.document_manager.create_document(
            title="Document 3",
            doc_type=Document.TYPE_SCENE,
        )
        doc3.metadata = {"key1": "different", "key3": "value3"}
        
        # Get documents by metadata
        key1_value1_docs = self.document_manager.get_documents_by_metadata("key1", "value1")
        key2_value2_docs = self.document_manager.get_documents_by_metadata("key2", "value2")
        key3_value3_docs = self.document_manager.get_documents_by_metadata("key3", "value3")
        
        # Assertions
        self.assertEqual(len(key1_value1_docs), 2)
        self.assertEqual(len(key2_value2_docs), 1)
        self.assertEqual(len(key3_value3_docs), 2)
        self.assertIn(doc1, key1_value1_docs)
        self.assertIn(doc2, key1_value1_docs)
        self.assertIn(doc1, key2_value2_docs)
        self.assertIn(doc2, key3_value3_docs)
        self.assertIn(doc3, key3_value3_docs)

    def test_get_modified_documents(self):
        """Test getting all modified documents."""
        # Create documents
        doc1 = self.document_manager.create_document(
            title="Document 1",
            doc_type=Document.TYPE_SCENE,
        )
        
        doc2 = self.document_manager.create_document(
            title="Document 2",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Clear modified documents set
        self.document_manager.modified_documents.clear()
        
        # Modify one document
        self.document_manager.update_document_content(doc1.id, "Modified content")
        
        # Get modified documents
        modified_docs = self.document_manager.get_modified_documents()
        
        # Assertions
        self.assertEqual(len(modified_docs), 1)
        self.assertIn(doc1, modified_docs)
        self.assertNotIn(doc2, modified_docs)

    @patch('src.backend.services.document_manager.file_utils')
    def test_export_document(self, mock_file_utils):
        """Test exporting a document to a file."""
        # Mock file_utils methods
        mock_file_utils.ensure_directory.return_value = True
        
        # Create a document
        document = self.document_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Test content"
        )
        document.synopsis = "Test synopsis"
        
        # Mock open
        mock_open_file = mock_open()
        with patch('builtins.open', mock_open_file):
            # Export as text
            result_txt = self.document_manager.export_document(
                document.id,
                os.path.join(self.temp_dir, "export.txt"),
                "txt"
            )
            
            # Export as markdown
            result_md = self.document_manager.export_document(
                document.id,
                os.path.join(self.temp_dir, "export.md"),
                "md"
            )
            
            # Export as HTML
            result_html = self.document_manager.export_document(
                document.id,
                os.path.join(self.temp_dir, "export.html"),
                "html"
            )
            
            # Export with unsupported format
            result_unsupported = self.document_manager.export_document(
                document.id,
                os.path.join(self.temp_dir, "export.unsupported"),
                "unsupported"
            )
        
        # Assertions
        self.assertTrue(result_txt)
        self.assertTrue(result_md)
        self.assertTrue(result_html)
        self.assertFalse(result_unsupported)
        
        # Verify file_utils methods were called
        mock_file_utils.ensure_directory.assert_called()

    @patch('src.backend.services.document_manager.file_utils')
    def test_import_document(self, mock_file_utils):
        """Test importing a document from a file."""
        # Mock file_utils methods
        mock_file_utils.file_exists.return_value = True
        
        # Mock open to return file content
        mock_content = "Imported document content"
        with patch('builtins.open', mock_open(read_data=mock_content)):
            # Import a document
            document = self.document_manager.import_document(
                import_path=os.path.join(self.temp_dir, "import.txt"),
                title="Imported Document",
                doc_type=Document.TYPE_SCENE,
            )
            
            # Assertions
            self.assertIsNotNone(document)
            self.assertEqual(document.title, "Imported Document")
            self.assertEqual(document.type, Document.TYPE_SCENE)
            self.assertEqual(document.content, mock_content)
            self.assertIn(document.id, self.document_manager.documents)
            self.assertIn(document.id, self.document_manager.modified_documents)
            
            # Verify file_utils methods were called
            mock_file_utils.file_exists.assert_called_with(os.path.join(self.temp_dir, "import.txt"))

    def test_duplicate_document(self):
        """Test duplicating a document."""
        # Create a document
        document = self.document_manager.create_document(
            title="Original Document",
            doc_type=Document.TYPE_SCENE,
            content="Original content"
        )
        document.synopsis = "Original synopsis"
        document.status = "Draft"
        document.tags = ["tag1", "tag2"]
        document.metadata = {"key1": "value1"}
        
        # Clear modified documents set
        self.document_manager.modified_documents.clear()
        
        # Duplicate the document
        duplicate = self.document_manager.duplicate_document(document.id)
        
        # Assertions
        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.title, f"Copy of {document.title}")
        self.assertEqual(duplicate.type, document.type)
        self.assertEqual(duplicate.content, document.content)
        self.assertEqual(duplicate.synopsis, document.synopsis)
        self.assertEqual(duplicate.status, document.status)
        self.assertEqual(duplicate.tags, document.tags)
        self.assertEqual(duplicate.metadata, document.metadata)
        self.assertIn(duplicate.id, self.document_manager.documents)
        self.assertIn(duplicate.id, self.document_manager.modified_documents)
        
        # Test with custom title
        duplicate2 = self.document_manager.duplicate_document(document.id, "Custom Title")
        self.assertEqual(duplicate2.title, "Custom Title")

    def test_merge_documents(self):
        """Test merging multiple documents into a new document."""
        # Create documents to merge
        doc1 = self.document_manager.create_document(
            title="Document 1",
            doc_type=Document.TYPE_SCENE,
            content="Content 1"
        )
        
        doc2 = self.document_manager.create_document(
            title="Document 2",
            doc_type=Document.TYPE_SCENE,
        )
        
        # Clear modified documents set
        self.document_manager.modified_documents.clear()
        
        # Merge the documents
        merged = self.document_manager.merge_documents(
            [doc1.id, doc2.id],
            "Merged Document",
            Document.TYPE_SCENE
        )
        
        # Assertions
        self.assertIsNotNone(merged)
        self.assertEqual(merged.title, "Merged Document")
        self.assertEqual(merged.type, Document.TYPE_SCENE)
        self.assertEqual(merged.content, "Content 1\n\nContent 2")
        self.assertIn(merged.id, self.document_manager.documents)
        self.assertIn(merged.id, self.document_manager.modified_documents)

    def test_split_document(self):
        """Test splitting a document into multiple documents."""
        # Create a document to split
        document = self.document_manager.create_document(
            title="Document to Split",
            doc_type=Document.TYPE_SCENE,
            content="First part content.\n\nSecond part content.\n\nThird part content."
        )
        
        # Define split points
        split_points = [
            (19, "Second Part"),  # After "First part content."
            (41, "Third Part")    # After "Second part content."
        ]
        
        # Split the document
        result_docs = self.document_manager.split_document(document.id, split_points)
        
        # Assertions
        self.assertEqual(len(result_docs), 3)
        
        # First document should be the original with updated content
        self.assertEqual(result_docs[0].id, document.id)
        self.assertEqual(result_docs[0].title, "Document to Split")
        self.assertEqual(result_docs[0].content, "First part content.")
        
        # Second document should be new with second part content
        self.assertEqual(result_docs[1].title, "Second Part")
        self.assertEqual(result_docs[1].content, "Second part content.")
        
        # Third document should be new with third part content
        self.assertEqual(result_docs[2].title, "Third Part")
        self.assertEqual(result_docs[2].content, "Third part content.")


if __name__ == '__main__':
    unittest.main()
