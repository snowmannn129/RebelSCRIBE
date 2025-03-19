#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the Cloud Storage Service.

This module contains tests for the CloudStorageService class.
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import datetime
from pathlib import Path

from src.backend.services.cloud_storage_service import CloudStorageService, CloudProvider


class TestCloudStorageService(unittest.TestCase):
    """Test cases for the CloudStorageService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config
        self.mock_config = {
            "cloud_storage": {
                "enabled": True,
                "provider": "dropbox",
                "auto_sync": False,
                "sync_on_save": False,
                "sync_on_open": False,
                "sync_interval_minutes": 30,
                "last_sync_time": None,
                "conflict_resolution": "ask",
                "sync_folders": ["documents", "research", "notes"],
                "exclude_patterns": ["*.tmp", "*.bak", "backups/*"],
                "dropbox": {
                    "api_key": "test_api_key",
                    "folder": "/RebelSCRIBE"
                },
                "google_drive": {
                    "credentials_file": "/path/to/credentials.json",
                    "folder": "RebelSCRIBE"
                },
                "onedrive": {
                    "client_id": "test_client_id",
                    "folder": "RebelSCRIBE"
                }
            }
        }

        # Patch the config manager
        self.config_patcher = patch('src.backend.services.cloud_storage_service.get_config')
        self.mock_get_config = self.config_patcher.start()
        self.mock_get_config.return_value = MagicMock()
        self.mock_get_config.return_value.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)
        
        # Create the service
        self.service = CloudStorageService()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.config_patcher.stop()
    
    def test_init(self):
        """Test initialization of the service."""
        self.assertEqual(self.service.settings["enabled"], True)
        self.assertEqual(self.service.settings["provider"], "dropbox")
        self.assertEqual(self.service.settings["sync_interval_minutes"], 30)
        self.assertEqual(len(self.service.settings["sync_folders"]), 3)
    
    def test_get_provider_name(self):
        """Test getting provider display name."""
        self.service.settings["provider"] = CloudProvider.DROPBOX.value
        self.assertEqual(self.service.get_provider_name(), "Dropbox")
        
        self.service.settings["provider"] = CloudProvider.GOOGLE_DRIVE.value
        self.assertEqual(self.service.get_provider_name(), "Google Drive")
        
        self.service.settings["provider"] = CloudProvider.ONEDRIVE.value
        self.assertEqual(self.service.get_provider_name(), "OneDrive")
        
        self.service.settings["provider"] = "unknown"
        self.assertEqual(self.service.get_provider_name(), "Unknown")
    
    def test_get_connection_status(self):
        """Test getting connection status."""
        # Test when disabled
        self.service.settings["enabled"] = False
        status = self.service.get_connection_status()
        self.assertFalse(status["connected"])
        self.assertEqual(status["error"], "Cloud storage is disabled")
        
        # Test when enabled but not connected
        self.service.settings["enabled"] = True
        self.service.clients = {}
        status = self.service.get_connection_status()
        self.assertFalse(status["connected"])
        self.assertTrue("Not connected" in status["error"])
        
        # Test when connected
        self.service.clients["dropbox"] = MagicMock()
        self.service.settings["provider"] = "dropbox"
        status = self.service.get_connection_status()
        self.assertTrue(status["connected"])
        self.assertIsNone(status["error"])
    
    @patch('src.backend.services.cloud_storage_service.DROPBOX_AVAILABLE', True)
    @patch('src.backend.services.cloud_storage_service.dropbox')
    def test_initialize_dropbox_client(self, mock_dropbox):
        """Test initializing Dropbox client."""
        # Set up mock
        mock_dropbox_instance = MagicMock()
        mock_dropbox.Dropbox.return_value = mock_dropbox_instance
        
        # Call method
        self.service._initialize_dropbox_client()
        
        # Verify
        mock_dropbox.Dropbox.assert_called_once_with("test_api_key")
        mock_dropbox_instance.users_get_current_account.assert_called_once()
        self.assertEqual(self.service.clients["dropbox"], mock_dropbox_instance)
    
    @patch('src.backend.services.cloud_storage_service.GOOGLE_DRIVE_AVAILABLE', True)
    @patch('src.backend.services.cloud_storage_service.os.path.exists')
    @patch('src.backend.services.cloud_storage_service.Credentials')
    @patch('src.backend.services.cloud_storage_service.build')
    def test_initialize_google_drive_client(self, mock_build, mock_credentials, mock_exists):
        """Test initializing Google Drive client."""
        # Set up mocks
        mock_exists.return_value = True
        mock_drive_service = MagicMock()
        mock_build.return_value = mock_drive_service
        
        # Mock open to return credentials JSON
        mock_json_data = '{"token": "test_token"}'
        with patch('builtins.open', mock_open(read_data=mock_json_data)):
            # Call method
            self.service._initialize_google_drive_client()
        
        # Verify
        mock_build.assert_called_once()
        self.assertEqual(self.service.clients["google_drive"], mock_drive_service)
    
    def test_initialize_onedrive_client(self):
        """Test initializing OneDrive client."""
        # Create mock for msal module
        mock_msal = MagicMock()
        mock_app = MagicMock()
        mock_msal.PublicClientApplication.return_value = mock_app
        mock_app.get_accounts.return_value = [{"username": "test@example.com"}]
        mock_app.acquire_token_silent.return_value = {"access_token": "test_token"}
        
        # Create mock for requests module
        mock_requests = MagicMock()
        
        # Patch the module imports
        with patch.dict('sys.modules', {
            'msal': mock_msal,
            'requests': mock_requests
        }):
            # Set ONEDRIVE_AVAILABLE to True
            with patch('src.backend.services.cloud_storage_service.ONEDRIVE_AVAILABLE', True):
                # Call method
                self.service._initialize_onedrive_client()
                
                # Verify
                mock_msal.PublicClientApplication.assert_called_once()
                mock_app.acquire_token_silent.assert_called_once()
                self.assertIn("onedrive", self.service.clients)
                self.assertEqual(self.service.clients["onedrive"]["app"], mock_app)
                self.assertEqual(self.service.clients["onedrive"]["token"]["access_token"], "test_token")
    
    def test_is_connected(self):
        """Test checking if connected."""
        # Test when disabled
        self.service.settings["enabled"] = False
        self.assertFalse(self.service.is_connected())
        
        # Test when enabled but no client
        self.service.settings["enabled"] = True
        self.service.settings["provider"] = "dropbox"
        self.service.clients = {}
        self.assertFalse(self.service.is_connected())
        
        # Test when enabled and client exists
        self.service.clients["dropbox"] = MagicMock()
        self.assertTrue(self.service.is_connected())
    
    @patch('src.backend.services.cloud_storage_service.file_utils')
    def test_upload_file(self, mock_file_utils):
        """Test uploading a file."""
        # Set up mocks
        mock_file_utils.file_exists.return_value = True
        self.service.clients["dropbox"] = MagicMock()
        self.service.settings["provider"] = "dropbox"
        
        # Mock the provider-specific upload method
        with patch.object(self.service, '_upload_to_dropbox', return_value=True) as mock_upload:
            # Call method
            result = self.service.upload_file("local_file.txt", "remote_file.txt")
            
            # Verify
            self.assertTrue(result)
            mock_upload.assert_called_once_with("local_file.txt", "/remote_file.txt")
    
    @patch('src.backend.services.cloud_storage_service.file_utils')
    def test_download_file(self, mock_file_utils):
        """Test downloading a file."""
        # Set up mocks
        self.service.clients["dropbox"] = MagicMock()
        self.service.settings["provider"] = "dropbox"
        
        # Mock the provider-specific download method
        with patch.object(self.service, '_download_from_dropbox', return_value=True) as mock_download:
            # Call method
            result = self.service.download_file("remote_file.txt", "local_file.txt")
            
            # Verify
            self.assertTrue(result)
            mock_download.assert_called_once_with("/remote_file.txt", "local_file.txt")
    
    def test_list_files(self):
        """Test listing files."""
        # Set up mocks
        self.service.clients["dropbox"] = MagicMock()
        self.service.settings["provider"] = "dropbox"
        
        # Mock the provider-specific list method
        expected_files = [{"name": "file1.txt"}, {"name": "file2.txt"}]
        with patch.object(self.service, '_list_files_dropbox', return_value=expected_files) as mock_list:
            # Call method
            result = self.service.list_files()
            
            # Verify
            self.assertEqual(result, expected_files)
            mock_list.assert_called_once()
    
    @patch('src.backend.services.cloud_storage_service.file_utils')
    @patch('src.backend.services.cloud_storage_service.os.walk')
    def test_sync_project(self, mock_walk, mock_file_utils):
        """Test syncing a project."""
        # Set up mocks
        mock_file_utils.directory_exists.return_value = True
        mock_file_utils.file_exists.return_value = True
        mock_file_utils.read_json_file.return_value = {"title": "Test Project"}
        mock_file_utils.match_pattern.return_value = False  # Don't exclude any files
        
        # Mock os.walk to return some files
        mock_walk.return_value = [
            ("/project", ["documents"], ["project.json"]),
            ("/project/documents", [], ["doc1.txt", "doc2.txt"])
        ]
        
        self.service.clients["dropbox"] = MagicMock()
        self.service.settings["provider"] = "dropbox"
        self.service.settings["sync_folders"] = ["documents"]
        
        # Create a side effect function to track uploaded files
        uploaded_files = []
        def upload_side_effect(local_path, remote_path):
            uploaded_files.append(os.path.basename(local_path))
            return True
        
        # Mock upload_file method
        with patch.object(self.service, 'upload_file', side_effect=upload_side_effect) as mock_upload:
            # Call method
            result = self.service.sync_project("/project")
            
            # Verify
            self.assertTrue(result["success"])
            
            # We should have at least 3 files (project.json + 2 docs)
            self.assertGreaterEqual(mock_upload.call_count, 3)
            
            # Check that the expected files were uploaded
            self.assertIn("project.json", uploaded_files)
            self.assertIn("doc1.txt", uploaded_files)
            self.assertIn("doc2.txt", uploaded_files)
    
    def test_update_settings(self):
        """Test updating settings."""
        # Initial settings
        self.service.settings["enabled"] = False
        self.service.settings["provider"] = "dropbox"
        
        # Update settings
        new_settings = {
            "enabled": True,
            "provider": "google_drive",
            "sync_interval_minutes": 60
        }
        
        # Mock _initialize_clients
        with patch.object(self.service, '_initialize_clients') as mock_init:
            # Call method
            self.service.update_settings(new_settings)
            
            # Verify
            self.assertTrue(self.service.settings["enabled"])
            self.assertEqual(self.service.settings["provider"], "google_drive")
            self.assertEqual(self.service.settings["sync_interval_minutes"], 60)
            mock_init.assert_called_once()
    
    def test_get_settings(self):
        """Test getting settings."""
        # Set some settings
        self.service.settings["enabled"] = True
        self.service.settings["provider"] = "dropbox"
        
        # Call method
        settings = self.service.get_settings()
        
        # Verify
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["provider"], "dropbox")
        self.assertIsNot(settings, self.service.settings)  # Should be a copy


if __name__ == '__main__':
    unittest.main()
