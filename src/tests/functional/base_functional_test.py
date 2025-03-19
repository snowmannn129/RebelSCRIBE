#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class for functional tests.
"""

import os
import tempfile
import unittest
import shutil
from typing import Optional

from src.tests.base_test import BaseTest
from src.backend.services.project_manager import ProjectManager
from src.backend.services.document_manager import DocumentManager
from src.backend.services.search_service import SearchService
from src.backend.services.export_service import ExportService
from src.backend.services.backup_service import BackupService
from src.backend.services.cloud_storage_service import CloudStorageService
from src.ai.ai_service import AIService
from src.utils.config_manager import ConfigManager


class BaseFunctionalTest(BaseTest):
    """
    Base class for functional tests.
    
    This class provides common setup and teardown functionality for functional tests,
    including creating temporary directories and initializing services.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test configuration
        self.config_path = os.path.join(self.test_dir, "config.yaml")
        self.config_manager = ConfigManager(self.config_path)
        
        # Initialize services with real implementations
        self.project_manager = self._create_project_manager()
        self.document_manager = self._create_document_manager()
        self.search_service = self._create_search_service()
        self.export_service = self._create_export_service()
        self.backup_service = self._create_backup_service()
        self.cloud_storage_service = self._create_cloud_storage_service()
        self.ai_service = self._create_ai_service()
    
    def tearDown(self):
        """Tear down test fixtures."""
        super().tearDown()
        
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
    
    def _create_project_manager(self) -> ProjectManager:
        """
        Create a project manager instance.
        
        Returns:
            A project manager instance.
        """
        return ProjectManager(config_manager=self.config_manager)
    
    def _create_document_manager(self) -> DocumentManager:
        """
        Create a document manager instance.
        
        Returns:
            A document manager instance.
        """
        document_manager = DocumentManager(self.project_manager.get_project_path() if self.project_manager.current_project else None)
        return document_manager
    
    def _create_search_service(self) -> SearchService:
        """
        Create a search service instance.
        
        Returns:
            A search service instance.
        """
        return SearchService(documents=self.document_manager.documents)
    
    def _create_export_service(self) -> ExportService:
        """
        Create an export service instance.
        
        Returns:
            An export service instance.
        """
        return ExportService(
            document_manager=self.document_manager,
            project_manager=self.project_manager
        )
    
    def _create_backup_service(self) -> BackupService:
        """
        Create a backup service instance.
        
        Returns:
            A backup service instance.
        """
        return BackupService()
    
    def _create_cloud_storage_service(self) -> CloudStorageService:
        """
        Create a cloud storage service instance.
        
        Returns:
            A cloud storage service instance.
        """
        # Create a mock CloudStorageService for testing
        class MockCloudStorageService:
            def __init__(self):
                self.settings = {
                    "enabled": False,
                    "provider": "dropbox",
                    "auto_sync": False
                }
                
            def is_connected(self) -> bool:
                return False
                
            def get_provider_name(self) -> str:
                return "Mock Cloud Provider"
                
            def get_connection_status(self) -> dict:
                return {
                    "connected": False,
                    "provider": "Mock",
                    "enabled": False,
                    "last_sync_time": None,
                    "error": "Mock cloud storage is disabled"
                }
                
            def sync_project(self, project_path: str) -> dict:
                return {
                    "success": False,
                    "error": "Mock cloud storage is disabled"
                }
        
        return MockCloudStorageService()
    
    def _create_ai_service(self) -> AIService:
        """
        Create an AI service instance.
        
        Returns:
            An AI service instance.
        """
        return AIService(config_manager=self.config_manager)
    
    def create_test_project(self, title: str = "Test Project", author: str = "Test Author") -> str:
        """
        Create a test project.
        
        Args:
            title: The project title.
            author: The project author.
            
        Returns:
            The path to the created project.
        """
        project_path = os.path.join(self.test_dir, f"{title.lower().replace(' ', '_')}.rebelscribe")
        self.project_manager.create_project(
            title=title,
            author=author,
            path=project_path
        )
        return project_path
    
    def load_test_project(self, project_path: str) -> None:
        """
        Load a test project.
        
        Args:
            project_path: The path to the project.
        """
        self.project_manager.load_project(project_path)
    
    def create_test_document(self, title: str = "Test Document", content: str = "Test content") -> str:
        """
        Create a test document.
        
        Args:
            title: The document title.
            content: The document content.
            
        Returns:
            The ID of the created document.
        """
        document = self.document_manager.create_document(
            title=title,
            content=content
        )
        return document.id
    
    def load_test_document(self, document_id: str) -> Optional[object]:
        """
        Load a test document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The loaded document, or None if the document could not be loaded.
        """
        return self.document_manager.load_document(document_id)
