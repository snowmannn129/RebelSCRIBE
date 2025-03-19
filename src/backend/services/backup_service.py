#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup Service for RebelSCRIBE.

This module provides functionality for creating, managing, and restoring backups
of RebelSCRIBE projects.
"""

import os
import shutil
import logging
import datetime
import zipfile
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils import file_utils
from src.utils.config_manager import get_config

logger = logging.getLogger(__name__)

class BackupService:
    """
    Manages backups for RebelSCRIBE projects.
    
    This class provides functionality for creating automatic backups,
    restoring from backups, managing backup rotation, and verifying
    backup integrity.
    """
    
    # Default backup settings
    DEFAULT_SETTINGS = {
        "auto_backup_enabled": True,
        "backup_interval_minutes": 30,
        "max_backups": 10,
        "compression_level": 9,  # 0-9, where 9 is highest compression
        "include_exports": False,
        "backup_on_save": True,
        "backup_on_close": True,
        "verify_backups": True
    }
    
    def __init__(self):
        """Initialize the BackupService."""
        self.config = get_config()
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.last_backup_time = None
        
        # Load custom settings if available
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load backup settings from configuration."""
        backup_config = self.config.get("backup", {}) or {}  # Ensure we have a dictionary
        for key, value in backup_config.items():
            if key in self.settings:
                self.settings[key] = value
    
    def create_backup(self, project_path: str, manual: bool = False) -> Optional[str]:
        """
        Create a backup of a project.
        
        Args:
            project_path: Path to the project file or directory.
            manual: Whether this is a manual backup (True) or automatic (False).
            
        Returns:
            The path to the created backup file, or None if backup failed.
        """
        try:
            # Check if project exists
            if not file_utils.file_exists(project_path) and not file_utils.directory_exists(project_path):
                logger.error(f"Project not found: {project_path}")
                return None
            
            # Get project directory
            if file_utils.file_exists(project_path):
                project_dir = os.path.dirname(project_path)
                project_file = os.path.basename(project_path)
            else:
                project_dir = project_path
                project_file = "project.json"
            
            # Check if project.json exists in the directory
            project_json_path = os.path.join(project_dir, "project.json")
            if not file_utils.file_exists(project_json_path):
                logger.error(f"Project file not found in directory: {project_json_path}")
                return None
            
            # Load project data to get title
            project_data = file_utils.read_json_file(project_json_path)
            if not project_data:
                logger.error(f"Failed to read project data from: {project_json_path}")
                return None
            
            project_title = project_data.get("title", "Untitled")
            
            # Create backup directory if it doesn't exist
            backups_dir = os.path.join(project_dir, "backups")
            file_utils.ensure_directory(backups_dir)
            
            # Generate backup filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_type = "manual" if manual else "auto"
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in project_title)
            safe_title = safe_title.replace(" ", "_")
            
            backup_filename = f"{safe_title}_{backup_type}_{timestamp}.zip"
            backup_path = os.path.join(backups_dir, backup_filename)
            
            # Create backup
            self._create_zip_backup(project_dir, backup_path)
            
            # Verify backup if enabled
            if self.settings["verify_backups"]:
                if not self._verify_backup(backup_path, project_dir):
                    logger.error(f"Backup verification failed: {backup_path}")
                    # Delete the failed backup
                    if file_utils.file_exists(backup_path):
                        os.remove(backup_path)
                    return None
            
            # Update last backup time
            self.last_backup_time = datetime.datetime.now()
            
            # Rotate backups if needed
            self._rotate_backups(backups_dir)
            
            logger.info(f"Created {'manual' if manual else 'automatic'} backup: {backup_filename}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return None
    
    def _create_zip_backup(self, source_dir: str, backup_path: str) -> bool:
        """
        Create a zip backup of a directory.
        
        Args:
            source_dir: The source directory to backup.
            backup_path: The path to save the backup zip file.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            compression = zipfile.ZIP_DEFLATED
            compression_level = self.settings["compression_level"]
            
            with zipfile.ZipFile(backup_path, 'w', compression=compression, compresslevel=compression_level) as zipf:
                # Walk through the directory
                for root, dirs, files in os.walk(source_dir):
                    # Skip the backups directory itself
                    if os.path.basename(root) == "backups" and os.path.dirname(root) == source_dir:
                        continue
                    
                    # Skip exports directory if not included
                    if not self.settings["include_exports"] and os.path.basename(root) == "exports" and os.path.dirname(root) == source_dir:
                        continue
                    
                    # Add files
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path for the archive
                        rel_path = os.path.relpath(file_path, source_dir)
                        # Add file to zip
                        zipf.write(file_path, rel_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating zip backup: {e}", exc_info=True)
            return False
    
    def _verify_backup(self, backup_path: str, original_dir: str) -> bool:
        """
        Verify the integrity of a backup.
        
        Args:
            backup_path: The path to the backup zip file.
            original_dir: The original directory that was backed up.
            
        Returns:
            bool: True if verification passed, False otherwise.
        """
        try:
            # Check if backup exists
            if not file_utils.file_exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create a temporary directory for extraction
            temp_dir = os.path.join(os.path.dirname(backup_path), "temp_verify")
            if file_utils.directory_exists(temp_dir):
                shutil.rmtree(temp_dir)
            file_utils.ensure_directory(temp_dir)
            
            try:
                # Extract backup to temporary directory
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Compare critical files
                critical_files = ["project.json"]
                for file in critical_files:
                    original_file = os.path.join(original_dir, file)
                    backup_file = os.path.join(temp_dir, file)
                    
                    if not file_utils.file_exists(original_file) or not file_utils.file_exists(backup_file):
                        logger.error(f"Critical file missing during verification: {file}")
                        return False
                    
                    # Compare file contents (hash)
                    if not self._compare_files(original_file, backup_file):
                        logger.error(f"File content mismatch during verification: {file}")
                        return False
                
                # Check documents directory
                original_docs_dir = os.path.join(original_dir, "documents")
                backup_docs_dir = os.path.join(temp_dir, "documents")
                
                if file_utils.directory_exists(original_docs_dir) and file_utils.directory_exists(backup_docs_dir):
                    # Get document files
                    original_docs = set(file_utils.list_files(original_docs_dir, "*.json"))
                    backup_docs = set(file_utils.list_files(backup_docs_dir, "*.json"))
                    
                    # Check if all original documents are in backup
                    missing_docs = [os.path.basename(doc) for doc in original_docs if os.path.join(backup_docs_dir, os.path.basename(doc)) not in backup_docs]
                    if missing_docs:
                        logger.error(f"Missing documents in backup: {', '.join(missing_docs)}")
                        return False
                
                return True
            
            finally:
                # Clean up temporary directory
                if file_utils.directory_exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            logger.error(f"Error verifying backup: {e}", exc_info=True)
            return False
    
    def _compare_files(self, file1: str, file2: str) -> bool:
        """
        Compare two files by computing their SHA-256 hash.
        
        Args:
            file1: Path to the first file.
            file2: Path to the second file.
            
        Returns:
            bool: True if files have the same content, False otherwise.
        """
        try:
            # Compute hash for file1
            hash1 = hashlib.sha256()
            with open(file1, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash1.update(chunk)
            
            # Compute hash for file2
            hash2 = hashlib.sha256()
            with open(file2, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash2.update(chunk)
            
            # Compare hashes
            return hash1.hexdigest() == hash2.hexdigest()
        
        except Exception as e:
            logger.error(f"Error comparing files: {e}", exc_info=True)
            return False
    
    def _rotate_backups(self, backups_dir: str) -> None:
        """
        Rotate backups to keep only the specified number of backups.
        
        Args:
            backups_dir: The directory containing backups.
        """
        try:
            # Check if rotation is needed
            max_backups = self.settings["max_backups"]
            if max_backups <= 0:
                return  # No limit
            
            # Get list of backup files
            backup_files = file_utils.list_files(backups_dir, "*.zip")
            if len(backup_files) <= max_backups:
                return  # No need to rotate
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x))
            
            # Delete oldest backups
            files_to_delete = backup_files[:-max_backups]
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted old backup: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.error(f"Error deleting old backup {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error rotating backups: {e}", exc_info=True)
    
    def restore_from_backup(self, backup_path: str, target_dir: Optional[str] = None) -> bool:
        """
        Restore a project from a backup.
        
        Args:
            backup_path: Path to the backup zip file.
            target_dir: Directory to restore to. If None, restores to the original location.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if backup exists
            if not file_utils.file_exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Determine target directory
            if not target_dir:
                target_dir = os.path.dirname(os.path.dirname(backup_path))
            
            # Create target directory if it doesn't exist
            file_utils.ensure_directory(target_dir)
            
            # Create a temporary directory for extraction
            temp_dir = os.path.join(os.path.dirname(backup_path), "temp_restore")
            if file_utils.directory_exists(temp_dir):
                shutil.rmtree(temp_dir)
            file_utils.ensure_directory(temp_dir)
            
            try:
                # Extract backup to temporary directory
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Check if it's a valid project
                project_json_path = os.path.join(temp_dir, "project.json")
                if not file_utils.file_exists(project_json_path):
                    logger.error(f"Invalid backup: project.json not found in {backup_path}")
                    return False
                
                # Copy files to target directory
                for item in os.listdir(temp_dir):
                    source_item = os.path.join(temp_dir, item)
                    target_item = os.path.join(target_dir, item)
                    
                    # Skip backups directory
                    if item == "backups":
                        continue
                    
                    # Remove existing item if it exists
                    if file_utils.file_exists(target_item) or file_utils.directory_exists(target_item):
                        if os.path.isdir(target_item):
                            shutil.rmtree(target_item)
                        else:
                            os.remove(target_item)
                    
                    # Copy item
                    if os.path.isdir(source_item):
                        shutil.copytree(source_item, target_item)
                    else:
                        shutil.copy2(source_item, target_item)
                
                logger.info(f"Restored project from backup: {os.path.basename(backup_path)}")
                return True
            
            finally:
                # Clean up temporary directory
                if file_utils.directory_exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}", exc_info=True)
            return False
    
    def get_backup_list(self, project_path: str) -> List[Dict[str, Any]]:
        """
        Get a list of available backups for a project.
        
        Args:
            project_path: Path to the project file or directory.
            
        Returns:
            A list of backup metadata dictionaries.
        """
        backups = []
        
        try:
            # Get project directory
            if file_utils.file_exists(project_path):
                project_dir = os.path.dirname(project_path)
            else:
                project_dir = project_path
            
            # Check backups directory
            backups_dir = os.path.join(project_dir, "backups")
            if not file_utils.directory_exists(backups_dir):
                return backups
            
            # List backup files
            backup_files = file_utils.list_files(backups_dir, "*.zip")
            
            # Extract metadata
            for backup_file in backup_files:
                try:
                    # Get file info
                    filename = os.path.basename(backup_file)
                    file_size = os.path.getsize(backup_file)
                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(backup_file))
                    
                    # Parse filename for additional info
                    parts = filename.split("_")
                    backup_type = "unknown"
                    if len(parts) >= 2:
                        backup_type = parts[-3] if len(parts) >= 3 else parts[-2]
                    
                    backups.append({
                        "filename": filename,
                        "path": backup_file,
                        "size": file_size,
                        "size_formatted": self._format_file_size(file_size),
                        "date": mod_time.isoformat(),
                        "date_formatted": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "type": backup_type
                    })
                
                except Exception as e:
                    logger.error(f"Error processing backup file {backup_file}: {e}", exc_info=True)
            
            # Sort by date (newest first)
            backups.sort(key=lambda x: x["date"], reverse=True)
            
            return backups
        
        except Exception as e:
            logger.error(f"Error getting backup list: {e}", exc_info=True)
            return []
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes.
            
        Returns:
            Formatted size string.
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"
    
    def should_auto_backup(self, project_path: str) -> bool:
        """
        Check if automatic backup should be performed.
        
        Args:
            project_path: Path to the project file or directory.
            
        Returns:
            bool: True if auto backup should be performed, False otherwise.
        """
        # Check if auto backup is enabled
        if not self.settings["auto_backup_enabled"]:
            return False
        
        # Check if project exists
        if not file_utils.file_exists(project_path) and not file_utils.directory_exists(project_path):
            return False
        
        # Check if enough time has passed since last backup
        if self.last_backup_time:
            elapsed_minutes = (datetime.datetime.now() - self.last_backup_time).total_seconds() / 60
            if elapsed_minutes < self.settings["backup_interval_minutes"]:
                return False
        
        return True
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update backup settings.
        
        Args:
            settings: Dictionary of settings to update.
        """
        for key, value in settings.items():
            if key in self.settings:
                self.settings[key] = value
        
        # Update config
        backup_config = self.config.get("backup", {})
        backup_config.update(settings)
        self.config.set("backup", backup_config)
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get current backup settings.
        
        Returns:
            Dictionary of current settings.
        """
        return self.settings.copy()
