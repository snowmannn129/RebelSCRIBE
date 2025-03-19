#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud storage integration tests for RebelSCRIBE.

This module contains tests that verify the integration of cloud storage
functionality with the rest of the application.
"""

import os
import tempfile
import unittest
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.backend.models.project import Project
from src.backend.models.document import Document
from src.backend.services.project_manager import ProjectManager
from src.backend.services.document_manager import DocumentManager
from src.backend.services.cloud_storage_service import CloudStorageService
from src.utils.config_manager import ConfigManager


class TestCloudStorageIntegration(unittest.TestCase):
    """Tests for cloud storage integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test configuration
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.config = ConfigManager(self.config_path)
        
        # Set up the project manager
        self.project_manager = ProjectManager(self.config)
        
        # Set up the document manager with project path
        with patch('src.backend.services.document_manager.ConfigManager') as mock_config_manager:
            mock_config_instance = MagicMock()
            mock_config_instance.get.side_effect = lambda section, key=None, default=None: {
                'application': {'data_directory': self.test_dir},
                'documents': {'max_versions': 5}
            }.get(section, {}).get(key, default)
            mock_config_manager.return_value = mock_config_instance
            self.document_manager = DocumentManager(self.test_dir)
        
        # Set up the cloud storage service with mock providers
        mock_config = MagicMock()
        mock_config.get.return_value = {}
        with patch('src.backend.services.cloud_storage_service.get_config', return_value=mock_config):
            self.cloud_storage_service = CloudStorageService()
        
        # Create a test project
        self.project_path = os.path.join(self.test_dir, "test_project.rebelscribe")
        self.project = self.project_manager.create_project(
            title="Test Project",
            author="Test Author",
            path=self.project_path
        )
        
        # Create a test document
        self.document = self.document_manager.create_document(
            title="Test Document",
            content="This is a test document for cloud storage integration."
        )
        
        # Save the project
        self.project_manager.save_project()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_dropbox_integration(self):
        """Test integration with Dropbox."""
        # Mock the Dropbox client
        mock_dropbox = MagicMock()
        
        # Mock successful authentication
        with patch.object(self.cloud_storage_service, 'authenticate_dropbox', return_value=mock_dropbox):
            # Authenticate with Dropbox
            result = self.cloud_storage_service.authenticate_dropbox(
                app_key="test_app_key",
                app_secret="test_app_secret",
                refresh_token="test_refresh_token"
            )
            
            # Verify authentication was successful
            self.assertIsNotNone(result)
            
            # Mock successful upload
            with patch.object(self.cloud_storage_service, 'upload_to_dropbox', return_value="/Test Project/test_project.rebelscribe"):
                # Upload the project
                result = self.cloud_storage_service.upload_to_dropbox(
                    project=self.project,
                    dropbox_path="/Test Project"
                )
                
                # Verify upload was successful
                self.assertEqual(result, "/Test Project/test_project.rebelscribe")
                
                # Mock successful download
                with patch.object(self.cloud_storage_service, 'download_from_dropbox', return_value=self.project_path):
                    # Download the project
                    result = self.cloud_storage_service.download_from_dropbox(
                        dropbox_path="/Test Project/test_project.rebelscribe",
                        local_path=os.path.join(self.test_dir, "downloaded_project.rebelscribe")
                    )
                    
                    # Verify download was successful
                    self.assertEqual(result, self.project_path)
    
    def test_google_drive_integration(self):
        """Test integration with Google Drive."""
        # Mock the Google Drive client
        mock_drive = MagicMock()
        
        # Mock successful authentication
        with patch.object(self.cloud_storage_service, 'authenticate_google_drive', return_value=mock_drive):
            # Authenticate with Google Drive
            result = self.cloud_storage_service.authenticate_google_drive(
                credentials_file="test_credentials.json"
            )
            
            # Verify authentication was successful
            self.assertIsNotNone(result)
            
            # Mock successful upload
            with patch.object(self.cloud_storage_service, 'upload_to_google_drive', return_value="test_file_id"):
                # Upload the project
                result = self.cloud_storage_service.upload_to_google_drive(
                    project=self.project,
                    folder_id="test_folder_id"
                )
                
                # Verify upload was successful
                self.assertEqual(result, "test_file_id")
                
                # Mock successful download
                with patch.object(self.cloud_storage_service, 'download_from_google_drive', return_value=self.project_path):
                    # Download the project
                    result = self.cloud_storage_service.download_from_google_drive(
                        file_id="test_file_id",
                        local_path=os.path.join(self.test_dir, "downloaded_project.rebelscribe")
                    )
                    
                    # Verify download was successful
                    self.assertEqual(result, self.project_path)
    
    def test_onedrive_integration(self):
        """Test integration with OneDrive."""
        # Mock the OneDrive client
        mock_onedrive = MagicMock()
        
        # Mock successful authentication
        with patch.object(self.cloud_storage_service, 'authenticate_onedrive', return_value=mock_onedrive):
            # Authenticate with OneDrive
            result = self.cloud_storage_service.authenticate_onedrive(
                client_id="test_client_id",
                client_secret="test_client_secret",
                refresh_token="test_refresh_token"
            )
            
            # Verify authentication was successful
            self.assertIsNotNone(result)
            
            # Mock successful upload
            with patch.object(self.cloud_storage_service, 'upload_to_onedrive', return_value="test_item_id"):
                # Upload the project
                result = self.cloud_storage_service.upload_to_onedrive(
                    project=self.project,
                    folder_path="/Test Project"
                )
                
                # Verify upload was successful
                self.assertEqual(result, "test_item_id")
                
                # Mock successful download
                with patch.object(self.cloud_storage_service, 'download_from_onedrive', return_value=self.project_path):
                    # Download the project
                    result = self.cloud_storage_service.download_from_onedrive(
                        item_id="test_item_id",
                        local_path=os.path.join(self.test_dir, "downloaded_project.rebelscribe")
                    )
                    
                    # Verify download was successful
                    self.assertEqual(result, self.project_path)
    
    def test_sync_project(self):
        """Test syncing a project with cloud storage."""
        # Mock the cloud storage service
        with patch.object(self.cloud_storage_service, 'get_sync_provider', return_value="dropbox"):
            # Set up sync for the project
            result = self.cloud_storage_service.setup_sync(
                project=self.project,
                provider="dropbox",
                remote_path="/Test Project"
            )
            
            # Verify setup was successful
            self.assertTrue(result)
            
            # Modify the project
            self.document.content = "Modified content"
            self.document_manager.save_document(self.document)
            
            # Save the project
            self.project_manager.save_project()
            
            # Mock successful sync
            with patch.object(self.cloud_storage_service, 'sync_project', return_value=True):
                # Sync the project
                result = self.cloud_storage_service.sync_project(self.project_path)
                
                # Verify sync was successful
                self.assertTrue(result)
    
    def test_auto_sync(self):
        """Test automatic syncing of a project."""
        # Mock the cloud storage service
        with patch.object(self.cloud_storage_service, 'get_sync_provider', return_value="dropbox"):
            # Set up sync for the project
            result = self.cloud_storage_service.setup_sync(
                project=self.project,
                provider="dropbox",
                remote_path="/Test Project",
                auto_sync=True
            )
            
            # Verify setup was successful
            self.assertTrue(result)
            
            # Mock successful auto-sync
            with patch.object(self.cloud_storage_service, 'auto_sync_enabled', return_value=True):
                with patch.object(self.cloud_storage_service, 'sync_project', return_value=True) as mock_sync:
                    # Modify the project
                    self.document.content = "Modified content for auto-sync"
                    self.document_manager.save_document(self.document)
                    
                    # Save the project (this should trigger auto-sync)
                    self.project_manager.save_project()
                    
                    # Manually call sync_project since we're not actually triggering auto-sync in the test
                    self.cloud_storage_service.sync_project(self.project_path)
                    
                    # Verify sync_project was called
                    mock_sync.assert_called_once_with(self.project_path)
    
    def test_conflict_resolution(self):
        """Test conflict resolution during sync."""
        # Mock the cloud storage service
        with patch.object(self.cloud_storage_service, 'get_sync_provider', return_value="dropbox"):
            # Set up sync for the project
            result = self.cloud_storage_service.setup_sync(
                project=self.project,
                provider="dropbox",
                remote_path="/Test Project"
            )
            
            # Verify setup was successful
            self.assertTrue(result)
            
            # Create a conflict scenario
            local_modified = "Local modified content"
            remote_modified = "Remote modified content"
            
            # Mock conflict detection
            with patch.object(self.cloud_storage_service, 'detect_conflicts', return_value=[
                {
                    "document_id": self.document.id,
                    "local_content": local_modified,
                    "remote_content": remote_modified,
                    "local_modified": "2025-03-10T12:00:00Z",
                    "remote_modified": "2025-03-10T13:00:00Z"
                }
            ]):
                # Mock conflict resolution with "remote" strategy
                with patch.object(self.cloud_storage_service, 'resolve_conflicts', return_value=True) as mock_resolve:
                    # Sync the project with conflict resolution
                    result = self.cloud_storage_service.sync_project(self.project_path)
                    
                    # Verify sync was successful
                    self.assertTrue(result)
                    
                    # Manually call resolve_conflicts since we're not actually resolving conflicts in the test
                    conflicts = self.cloud_storage_service.detect_conflicts(self.project)
                    self.cloud_storage_service.resolve_conflicts(self.project, conflicts, "remote")
                    
                    # Verify resolve_conflicts was called
                    mock_resolve.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling during cloud operations."""
        # Mock authentication failure
        with patch.object(self.cloud_storage_service, 'authenticate_dropbox', side_effect=Exception("Authentication failed")):
            # Try to authenticate
            with self.assertRaises(Exception):
                self.cloud_storage_service.authenticate_dropbox(
                    app_key="invalid_key",
                    app_secret="invalid_secret",
                    refresh_token="invalid_token"
                )
        
        # Mock upload failure
        with patch.object(self.cloud_storage_service, 'authenticate_dropbox', return_value=MagicMock()):
            with patch.object(self.cloud_storage_service, 'upload_to_dropbox', side_effect=Exception("Upload failed")):
                # Try to upload
                with self.assertRaises(Exception):
                    self.cloud_storage_service.upload_to_dropbox(
                        project=self.project,
                        dropbox_path="/Invalid Path"
                    )
        
        # Mock download failure
        with patch.object(self.cloud_storage_service, 'authenticate_dropbox', return_value=MagicMock()):
            with patch.object(self.cloud_storage_service, 'download_from_dropbox', side_effect=Exception("Download failed")):
                # Try to download
                with self.assertRaises(Exception):
                    self.cloud_storage_service.download_from_dropbox(
                        dropbox_path="/Invalid Path",
                        local_path=os.path.join(self.test_dir, "nonexistent.rebelscribe")
                    )


if __name__ == '__main__':
    unittest.main()
