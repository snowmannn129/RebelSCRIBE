#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional tests for cloud storage integration.
"""

import os
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from src.tests.functional.base_functional_test import BaseFunctionalTest
from src.backend.services.cloud_storage_service import CloudStorageService


class TestCloudStorage(BaseFunctionalTest):
    """Test case for cloud storage functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test project
        self.project_path = self.create_test_project(
            title="Cloud Storage Test Project",
            author="Test Author"
        )
        self.project_manager.load_project(self.project_path)
        
        # Create test documents
        self.doc1_id = self.create_test_document(
            title="Document 1",
            content="This is the first test document for cloud storage testing."
        )
        
        self.doc2_id = self.create_test_document(
            title="Document 2",
            content="This is the second test document for cloud storage testing."
        )
        
        # Save all documents
        self.document_manager.save_all_documents()
        
        # Initialize cloud storage service
        self.cloud_storage_service = CloudStorageService(
            project_manager=self.project_manager,
            config_manager=self.config_manager
        )
        
        # Create a temporary directory for cloud storage simulation
        self.cloud_storage_dir = os.path.join(self.test_dir, "cloud_storage")
        os.makedirs(self.cloud_storage_dir, exist_ok=True)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up any cloud storage connections
        if hasattr(self, 'cloud_storage_service') and self.cloud_storage_service:
            self.cloud_storage_service.disconnect()
        
        super().tearDown()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    def test_connect_to_cloud_storage(self, mock_authenticate):
        """Test connecting to cloud storage."""
        # Set up mock
        mock_authenticate.return_value = True
        
        # Configure cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        
        # Connect to cloud storage
        success = self.cloud_storage_service.connect(cloud_config)
        
        # Verify connection was successful
        self.assertTrue(success)
        self.assertTrue(self.cloud_storage_service.is_connected())
        
        # Verify authentication was called
        mock_authenticate.assert_called_once()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    def test_disconnect_from_cloud_storage(self, mock_authenticate):
        """Test disconnecting from cloud storage."""
        # Set up mock
        mock_authenticate.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Disconnect from cloud storage
        self.cloud_storage_service.disconnect()
        
        # Verify disconnection was successful
        self.assertFalse(self.cloud_storage_service.is_connected())
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._upload_file')
    def test_upload_project(self, mock_upload_file, mock_authenticate):
        """Test uploading a project to cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_upload_file.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Upload project
        success = self.cloud_storage_service.upload_project()
        
        # Verify upload was successful
        self.assertTrue(success)
        
        # Verify upload_file was called for project file and documents
        self.assertGreater(mock_upload_file.call_count, 1)
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._download_file')
    def test_download_project(self, mock_download_file, mock_authenticate):
        """Test downloading a project from cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_download_file.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Create a temporary directory for download
        download_dir = os.path.join(self.test_dir, "download")
        os.makedirs(download_dir, exist_ok=True)
        
        # Download project
        success = self.cloud_storage_service.download_project(download_dir)
        
        # Verify download was successful
        self.assertTrue(success)
        
        # Verify download_file was called
        mock_download_file.assert_called()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._list_files')
    def test_list_cloud_projects(self, mock_list_files, mock_authenticate):
        """Test listing projects in cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_list_files.return_value = [
            "project1.rebelscribe",
            "project2.rebelscribe",
            "project3.rebelscribe"
        ]
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # List projects
        projects = self.cloud_storage_service.list_cloud_projects()
        
        # Verify projects were listed
        self.assertEqual(len(projects), 3)
        self.assertIn("project1.rebelscribe", projects)
        self.assertIn("project2.rebelscribe", projects)
        self.assertIn("project3.rebelscribe", projects)
        
        # Verify list_files was called
        mock_list_files.assert_called_once()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._upload_file')
    def test_sync_project(self, mock_upload_file, mock_authenticate):
        """Test syncing a project with cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_upload_file.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Sync project
        success = self.cloud_storage_service.sync_project()
        
        # Verify sync was successful
        self.assertTrue(success)
        
        # Verify upload_file was called
        mock_upload_file.assert_called()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._delete_file')
    def test_delete_cloud_project(self, mock_delete_file, mock_authenticate):
        """Test deleting a project from cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_delete_file.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Delete project
        success = self.cloud_storage_service.delete_cloud_project("test_project.rebelscribe")
        
        # Verify deletion was successful
        self.assertTrue(success)
        
        # Verify delete_file was called
        mock_delete_file.assert_called()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    def test_get_cloud_providers(self, mock_authenticate):
        """Test getting available cloud providers."""
        # Set up mock
        mock_authenticate.return_value = True
        
        # Get cloud providers
        providers = self.cloud_storage_service.get_cloud_providers()
        
        # Verify providers were returned
        self.assertIsNotNone(providers)
        self.assertIsInstance(providers, list)
        self.assertGreater(len(providers), 0)
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._get_file_info')
    def test_get_cloud_project_info(self, mock_get_file_info, mock_authenticate):
        """Test getting information about a cloud project."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_get_file_info.return_value = {
            "name": "test_project.rebelscribe",
            "size": 1024,
            "modified": "2025-03-11T12:00:00Z",
            "owner": "Test User"
        }
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Get project info
        info = self.cloud_storage_service.get_cloud_project_info("test_project.rebelscribe")
        
        # Verify info was returned
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "test_project.rebelscribe")
        self.assertEqual(info["size"], 1024)
        self.assertEqual(info["modified"], "2025-03-11T12:00:00Z")
        self.assertEqual(info["owner"], "Test User")
        
        # Verify get_file_info was called
        mock_get_file_info.assert_called_once_with("test_project.rebelscribe")
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._upload_file')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._download_file')
    def test_auto_sync(self, mock_download_file, mock_upload_file, mock_authenticate):
        """Test automatic syncing with cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_upload_file.return_value = True
        mock_download_file.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir,
            "auto_sync": True,
            "sync_interval": 5  # 5 minutes
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Enable auto-sync
        self.cloud_storage_service.enable_auto_sync()
        
        # Verify auto-sync is enabled
        self.assertTrue(self.cloud_storage_service.is_auto_sync_enabled())
        
        # Simulate a document change
        document = self.document_manager.get_document(self.doc1_id)
        document.content += "\nThis is an update to test auto-sync."
        self.document_manager.save_document(document)
        
        # Manually trigger sync (in a real scenario, this would happen automatically)
        self.cloud_storage_service.sync_project()
        
        # Verify upload_file was called
        mock_upload_file.assert_called()
        
        # Disable auto-sync
        self.cloud_storage_service.disable_auto_sync()
        
        # Verify auto-sync is disabled
        self.assertFalse(self.cloud_storage_service.is_auto_sync_enabled())
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    def test_connection_error_handling(self, mock_authenticate):
        """Test handling of connection errors."""
        # Set up mock to simulate connection failure
        mock_authenticate.return_value = False
        
        # Try to connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "invalid_token",
            "storage_path": self.cloud_storage_dir
        }
        success = self.cloud_storage_service.connect(cloud_config)
        
        # Verify connection failed
        self.assertFalse(success)
        self.assertFalse(self.cloud_storage_service.is_connected())
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._upload_file')
    def test_upload_error_handling(self, mock_upload_file, mock_authenticate):
        """Test handling of upload errors."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_upload_file.side_effect = Exception("Upload error")
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Try to upload project
        success = self.cloud_storage_service.upload_project()
        
        # Verify upload failed but didn't crash
        self.assertFalse(success)
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._download_file')
    def test_download_error_handling(self, mock_download_file, mock_authenticate):
        """Test handling of download errors."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_download_file.side_effect = Exception("Download error")
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Create a temporary directory for download
        download_dir = os.path.join(self.test_dir, "download")
        os.makedirs(download_dir, exist_ok=True)
        
        # Try to download project
        success = self.cloud_storage_service.download_project(download_dir)
        
        # Verify download failed but didn't crash
        self.assertFalse(success)
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._upload_file')
    def test_selective_sync(self, mock_upload_file, mock_authenticate):
        """Test selective syncing of project files."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_upload_file.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Define files to sync
        files_to_sync = [self.doc1_id]
        
        # Sync selected files
        success = self.cloud_storage_service.sync_selected_files(files_to_sync)
        
        # Verify sync was successful
        self.assertTrue(success)
        
        # Verify upload_file was called only for selected files
        self.assertEqual(mock_upload_file.call_count, len(files_to_sync))
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._get_storage_quota')
    def test_storage_quota(self, mock_get_storage_quota, mock_authenticate):
        """Test getting storage quota information."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_get_storage_quota.return_value = {
            "used": 1024 * 1024,  # 1 MB
            "total": 1024 * 1024 * 10,  # 10 MB
            "percentage": 10
        }
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Get storage quota
        quota = self.cloud_storage_service.get_storage_quota()
        
        # Verify quota information
        self.assertIsNotNone(quota)
        self.assertEqual(quota["used"], 1024 * 1024)
        self.assertEqual(quota["total"], 1024 * 1024 * 10)
        self.assertEqual(quota["percentage"], 10)
        
        # Verify get_storage_quota was called
        mock_get_storage_quota.assert_called_once()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._share_project')
    def test_share_project(self, mock_share_project, mock_authenticate):
        """Test sharing a project with other users."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_share_project.return_value = {
            "success": True,
            "share_url": "https://cloud.example.com/shared/project123",
            "permissions": "read"
        }
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Share project
        result = self.cloud_storage_service.share_project(
            email="collaborator@example.com",
            permissions="read"
        )
        
        # Verify sharing was successful
        self.assertTrue(result["success"])
        self.assertEqual(result["share_url"], "https://cloud.example.com/shared/project123")
        self.assertEqual(result["permissions"], "read")
        
        # Verify share_project was called
        mock_share_project.assert_called_once_with(
            email="collaborator@example.com",
            permissions="read"
        )
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._get_shared_projects')
    def test_get_shared_projects(self, mock_get_shared_projects, mock_authenticate):
        """Test getting projects shared with the user."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_get_shared_projects.return_value = [
            {
                "name": "Shared Project 1",
                "owner": "user1@example.com",
                "permissions": "read",
                "modified": "2025-03-10T15:30:00Z"
            },
            {
                "name": "Shared Project 2",
                "owner": "user2@example.com",
                "permissions": "write",
                "modified": "2025-03-11T09:45:00Z"
            }
        ]
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Get shared projects
        shared_projects = self.cloud_storage_service.get_shared_projects()
        
        # Verify shared projects were returned
        self.assertEqual(len(shared_projects), 2)
        self.assertEqual(shared_projects[0]["name"], "Shared Project 1")
        self.assertEqual(shared_projects[0]["owner"], "user1@example.com")
        self.assertEqual(shared_projects[1]["name"], "Shared Project 2")
        self.assertEqual(shared_projects[1]["permissions"], "write")
        
        # Verify get_shared_projects was called
        mock_get_shared_projects.assert_called_once()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._get_project_history')
    def test_get_project_history(self, mock_get_project_history, mock_authenticate):
        """Test getting project version history from cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_get_project_history.return_value = [
            {
                "version": "1.0",
                "modified": "2025-03-09T10:15:00Z",
                "size": 1024 * 5
            },
            {
                "version": "1.1",
                "modified": "2025-03-10T14:30:00Z",
                "size": 1024 * 6
            },
            {
                "version": "1.2",
                "modified": "2025-03-11T09:45:00Z",
                "size": 1024 * 7
            }
        ]
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Get project history
        history = self.cloud_storage_service.get_project_history()
        
        # Verify history was returned
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["version"], "1.0")
        self.assertEqual(history[1]["modified"], "2025-03-10T14:30:00Z")
        self.assertEqual(history[2]["size"], 1024 * 7)
        
        # Verify get_project_history was called
        mock_get_project_history.assert_called_once()
    
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._authenticate')
    @patch('src.backend.services.cloud_storage_service.CloudStorageService._restore_project_version')
    def test_restore_project_version(self, mock_restore_project_version, mock_authenticate):
        """Test restoring a previous project version from cloud storage."""
        # Set up mocks
        mock_authenticate.return_value = True
        mock_restore_project_version.return_value = True
        
        # Connect to cloud storage
        cloud_config = {
            "provider": "test_provider",
            "auth_token": "test_token",
            "storage_path": self.cloud_storage_dir
        }
        self.cloud_storage_service.connect(cloud_config)
        
        # Restore project version
        success = self.cloud_storage_service.restore_project_version("1.0")
        
        # Verify restoration was successful
        self.assertTrue(success)
        
        # Verify restore_project_version was called
        mock_restore_project_version.assert_called_once_with("1.0")


if __name__ == "__main__":
    unittest.main()
