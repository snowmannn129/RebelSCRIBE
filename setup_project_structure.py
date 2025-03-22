import os
import sys

def create_directory(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def create_file(file_path, content):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Created file: {file_path}")
    else:
        print(f"File already exists: {file_path}")

def main():
    print("Setting up RebelSCRIBE project structure...")
    
    # Create directories
    create_directory("src")
    create_directory("src/backend")
    create_directory("src/backend/models")
    create_directory("src/backend/services")
    create_directory("src/utils")
    
    # Create utility files
    create_file("src/utils/__init__.py", "")
    
    # Create logging_utils.py
    logging_utils_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Logging utilities for RebelSCRIBE.

This module provides logging functionality for the application.
\"\"\"

import os
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(log_file="rebelscribe.log", console_output=True, file_output=True, log_level=logging.INFO):
    \"\"\"
    Set up logging for the application.
    
    Args:
        log_file: The log file path.
        console_output: Whether to output logs to the console.
        file_output: Whether to output logs to a file.
        log_level: The logging level.
    \"\"\"
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Clear existing handlers
    logger.handlers = []
    
    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler
    if file_output:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    \"\"\"
    Get a logger with the specified name.
    
    Args:
        name: The logger name.
        
    Returns:
        The logger.
    \"\"\"
    return logging.getLogger(name)
"""
    create_file("src/utils/logging_utils.py", logging_utils_content)
    
    # Create file_utils.py
    file_utils_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
File utilities for RebelSCRIBE.

This module provides file-related functionality for the application.
\"\"\"

import os
import json
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any

def ensure_directory(directory_path: str) -> bool:
    \"\"\"
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: The directory path.
        
    Returns:
        bool: True if successful, False otherwise.
    \"\"\"
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except Exception as e:
        print(f"Error ensuring directory {directory_path}: {e}")
        return False

def file_exists(file_path: str) -> bool:
    \"\"\"
    Check if a file exists.
    
    Args:
        file_path: The file path.
        
    Returns:
        bool: True if the file exists, False otherwise.
    \"\"\"
    return os.path.exists(file_path) and os.path.isfile(file_path)

def directory_exists(directory_path: str) -> bool:
    \"\"\"
    Check if a directory exists.
    
    Args:
        directory_path: The directory path.
        
    Returns:
        bool: True if the directory exists, False otherwise.
    \"\"\"
    return os.path.exists(directory_path) and os.path.isdir(directory_path)

def read_file(file_path: str) -> Optional[str]:
    \"\"\"
    Read a file.
    
    Args:
        file_path: The file path.
        
    Returns:
        The file contents, or None if reading failed.
    \"\"\"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def write_file(file_path: str, content: str) -> bool:
    \"\"\"
    Write to a file.
    
    Args:
        file_path: The file path.
        content: The content to write.
        
    Returns:
        bool: True if successful, False otherwise.
    \"\"\"
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")
        return False

def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    \"\"\"
    Read a JSON file.
    
    Args:
        file_path: The file path.
        
    Returns:
        The parsed JSON data, or None if reading or parsing failed.
    \"\"\"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return None

def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    \"\"\"
    Write to a JSON file.
    
    Args:
        file_path: The file path.
        data: The data to write.
        
    Returns:
        bool: True if successful, False otherwise.
    \"\"\"
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing to JSON file {file_path}: {e}")
        return False

def list_files(directory_path: str, pattern: str = "*") -> List[str]:
    \"\"\"
    List files in a directory.
    
    Args:
        directory_path: The directory path.
        pattern: The file pattern to match.
        
    Returns:
        A list of file paths.
    \"\"\"
    try:
        return glob.glob(os.path.join(directory_path, pattern))
    except Exception as e:
        print(f"Error listing files in {directory_path}: {e}")
        return []

def copy_file(source_path: str, destination_path: str) -> bool:
    \"\"\"
    Copy a file.
    
    Args:
        source_path: The source file path.
        destination_path: The destination file path.
        
    Returns:
        bool: True if successful, False otherwise.
    \"\"\"
    try:
        # Ensure destination directory exists
        destination_dir = os.path.dirname(destination_path)
        if destination_dir:
            ensure_directory(destination_dir)
        
        shutil.copy2(source_path, destination_path)
        return True
    except Exception as e:
        print(f"Error copying file from {source_path} to {destination_path}: {e}")
        return False

def delete_file(file_path: str) -> bool:
    \"\"\"
    Delete a file.
    
    Args:
        file_path: The file path.
        
    Returns:
        bool: True if successful, False otherwise.
    \"\"\"
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False

def expand_path(path: str) -> str:
    \"\"\"
    Expand a path, resolving ~ to the user's home directory.
    
    Args:
        path: The path to expand.
        
    Returns:
        The expanded path.
    \"\"\"
    return os.path.expanduser(path)
"""
    create_file("src/utils/file_utils.py", file_utils_content)
    
    # Create config_manager.py
    config_manager_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Configuration manager for RebelSCRIBE.

This module provides configuration management functionality for the application.
\"\"\"

import os
import json
from typing import Dict, List, Optional, Any

class ConfigManager:
    \"\"\"
    Configuration manager for RebelSCRIBE.
    
    This class provides functionality for loading, saving, and accessing configuration settings.
    \"\"\"
    
    def __init__(self, config_file: Optional[str] = None):
        \"\"\"
        Initialize the ConfigManager.
        
        Args:
            config_file: The configuration file path. If None, uses the default path.
        \"\"\"
        self.config_file = config_file or os.path.join(os.path.expanduser("~"), ".rebelscribe", "config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        \"\"\"
        Load the configuration from the file.
        
        Returns:
            The configuration data.
        \"\"\"
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return self._create_default_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        \"\"\"
        Create the default configuration.
        
        Returns:
            The default configuration data.
        \"\"\"
        config = {
            "application": {
                "data_directory": os.path.join(os.path.expanduser("~"), ".rebelscribe", "data"),
                "theme": "light",
                "language": "en",
                "auto_save": True,
                "auto_save_interval": 300,  # 5 minutes
                "max_recent_projects": 10
            },
            "documents": {
                "max_versions": 10,
                "default_type": "scene",
                "default_status": "Draft"
            },
            "editor": {
                "font_family": "Arial",
                "font_size": 12,
                "line_spacing": 1.5,
                "show_line_numbers": False,
                "spell_check": True,
                "auto_correct": True,
                "tab_size": 4,
                "word_wrap": True
            },
            "performance": {
                "max_cached_documents": 50,
                "max_content_cache_mb": 100,
                "document_cache_ttl": 3600,  # 1 hour
                "metadata_cache_ttl": 7200,  # 2 hours
                "max_workers": 4
            },
            "ai": {
                "enabled": True,
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
                "api_key": "",
                "use_gpu": True
            },
            "export": {
                "default_format": "docx",
                "include_metadata": False,
                "include_synopsis": False,
                "include_notes": False,
                "default_directory": os.path.join(os.path.expanduser("~"), "Documents", "RebelSCRIBE Exports")
            },
            "backup": {
                "enabled": True,
                "interval": 3600,  # 1 hour
                "max_backups": 10,
                "include_versions": True,
                "backup_directory": os.path.join(os.path.expanduser("~"), ".rebelscribe", "backups")
            },
            "cloud": {
                "enabled": False,
                "provider": "none",
                "auto_sync": False,
                "sync_interval": 3600  # 1 hour
            }
        }
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Save default config
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving default configuration: {e}")
        
        return config
    
    def save_config(self) -> bool:
        \"\"\"
        Save the configuration to the file.
        
        Returns:
            bool: True if successful, False otherwise.
        \"\"\"
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        \"\"\"
        Get a configuration value.
        
        Args:
            section: The configuration section.
            key: The configuration key.
            default: The default value to return if the key doesn't exist.
            
        Returns:
            The configuration value, or the default if the key doesn't exist.
        \"\"\"
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        \"\"\"
        Set a configuration value.
        
        Args:
            section: The configuration section.
            key: The configuration key.
            value: The configuration value.
            
        Returns:
            bool: True if successful, False otherwise.
        \"\"\"
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            return self.save_config()
        except Exception as e:
            print(f"Error setting configuration value: {e}")
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        \"\"\"
        Get a configuration section.
        
        Args:
            section: The configuration section.
            
        Returns:
            The configuration section, or an empty dictionary if the section doesn't exist.
        \"\"\"
        return self.config.get(section, {})
    
    def set_section(self, section: str, values: Dict[str, Any]) -> bool:
        \"\"\"
        Set a configuration section.
        
        Args:
            section: The configuration section.
            values: The configuration values.
            
        Returns:
            bool: True if successful, False otherwise.
        \"\"\"
        try:
            self.config[section] = values
            return self.save_config()
        except Exception as e:
            print(f"Error setting configuration section: {e}")
            return False
"""
    create_file("src/utils/config_manager.py", config_manager_content)
    
    # Create document_cache.py
    document_cache_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Document cache for RebelSCRIBE.

This module provides caching functionality for documents.
\"\"\"

import time
from typing import Dict, List, Optional, Any, Set
import logging

logger = logging.getLogger(__name__)

class DocumentCache:
    \"\"\"
    Cache for documents.
    
    This class provides caching functionality for documents, including content and metadata caching.
    \"\"\"
    
    def __init__(self, max_documents: int = 50, max_content_size_mb: int = 100,
                document_ttl: int = 3600, metadata_ttl: int = 7200):
        \"\"\"
        Initialize the DocumentCache.
        
        Args:
            max_documents: The maximum number of documents to cache.
            max_content_size_mb: The maximum content cache size in MB.
            document_ttl: The document time-to-live in seconds.
            metadata_ttl: The metadata time-to-live in seconds.
        \"\"\"
        self.max_documents = max_documents
        self.max_content_size_bytes = max_content_size_mb * 1024 * 1024
        self.document_ttl = document_ttl
        self.metadata_ttl = metadata_ttl
        
        # Cache dictionaries
        self.document_cache: Dict[str, Dict[str, Any]] = {}
        self.content_cache: Dict[str, Dict[str, Any]] = {}
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache statistics
        self.document_cache_hits = 0
        self.document_cache_misses = 0
        self.content_cache_hits = 0
        self.content_cache_misses = 0
        self.metadata_cache_hits = 0
        self.metadata_cache_misses = 0
        
        # Current cache size
        self.current_content_size_bytes = 0
    
    def put_document(self, document_id: str, document: Any) -> None:
        \"\"\"
        Put a document in the cache.
        
        Args:
            document_id: The document ID.
            document: The document to cache.
        \"\"\"
        try:
            # Check if we need to evict documents
            if len(self.document_cache) >= self.max_documents:
                self._evict_documents()
            
            # Add to document cache
            self.document_cache[document_id] = {
                "document": document,
                "timestamp": time.time()
            }
            
            # Add content to content cache if available
            if hasattr(document, "content") and document.content:
                self.put_document_content(document_id, document.content)
            
            # Add metadata to metadata cache
            if hasattr(document, "to_dict"):
                metadata = document.to_dict()
                if "content" in metadata:
                    metadata["content"] = None  # Don't store content in metadata cache
                self.put_document_metadata(document_id, metadata)
            
            logger.debug(f"Added document to cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error putting document in cache: {e}", exc_info=True)
    
    def get_document(self, document_id: str) -> Optional[Any]:
        \"\"\"
        Get a document from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document, or None if not found or expired.
        \"\"\"
        try:
            # Check if document is in cache
            if document_id in self.document_cache:
                cache_entry = self.document_cache[document_id]
                
                # Check if document has expired
                if time.time() - cache_entry["timestamp"] > self.document_ttl:
                    # Remove expired document
                    del self.document_cache[document_id]
                    self.document_cache_misses += 1
                    logger.debug(f"Document cache miss (expired): {document_id}")
                    return None
                
                # Update timestamp
                cache_entry["timestamp"] = time.time()
                
                self.document_cache_hits += 1
                logger.debug(f"Document cache hit: {document_id}")
                return cache_entry["document"]
            
            self.document_cache_misses += 1
            logger.debug(f"Document cache miss: {document_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting document from cache: {e}", exc_info=True)
            self.document_cache_misses += 1
            return None
    
    def put_document_content(self, document_id: str, content: str) -> None:
        \"\"\"
        Put document content in the cache.
        
        Args:
            document_id: The document ID.
            content: The document content.
        \"\"\"
        try:
            # Calculate content size
            content_size = len(content.encode("utf-8"))
            
            # Check if we need to evict content
            if self.current_content_size_bytes + content_size > self.max_content_size_bytes:
                self._evict_content(content_size)
            
            # Add to content cache
            self.content_cache[document_id] = {
                "content": content,
                "size": content_size,
                "timestamp": time.time()
            }
            
            # Update current content size
            self.current_content_size_bytes += content_size
            
            logger.debug(f"Added document content to cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error putting document content in cache: {e}", exc_info=True)
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        \"\"\"
        Get document content from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document content, or None if not found or expired.
        \"\"\"
        try:
            # Check if content is in cache
            if document_id in self.content_cache:
                cache_entry = self.content_cache[document_id]
                
                # Check if content has expired
                if time.time() - cache_entry["timestamp"] > self.document_ttl:
                    # Remove expired content
                    self._remove_content(document_id)
                    self.content_cache_misses += 1
                    logger.debug(f"Content cache miss (expired): {document_id}")
                    return None
                
                # Update timestamp
                cache_entry["timestamp"] = time.time()
                
                self.content_cache_hits += 1
                logger.debug(f"Content cache hit: {document_id}")
                return cache_entry["content"]
            
            self.content_cache_misses += 1
            logger.debug(f"Content cache miss: {document_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting document content from cache: {e}", exc_info=True)
            self.content_cache_misses += 1
            return None
    
    def put_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        \"\"\"
        Put document metadata in the cache.
        
        Args:
            document_id: The document ID.
            metadata: The document metadata.
        \"\"\"
        try:
            # Add to metadata cache
            self.metadata_cache[document_id] = {
                "metadata": metadata,
                "timestamp": time.time()
            }
            
            logger.debug(f"Added document metadata to cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error putting document metadata in cache: {e}", exc_info=True)
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        \"\"\"
        Get document metadata from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document metadata, or None if not found or expired.
        \"\"\"
        try:
            # Check if metadata is in cache
            if document_id in self.metadata_cache:
                cache_entry = self.metadata_cache[document_id]
                
                # Check if metadata has expired
                if time.time() - cache_entry["timestamp"] > self.metadata_ttl:
                    # Remove expired metadata
                    del self.metadata_cache[document_id]
                    self.metadata_cache_misses += 1
                    logger.debug(f"Metadata cache miss (expired): {document_id}")
                    return None
                
                # Update timestamp
                cache_entry["timestamp"] = time.time()
                
                self.metadata_cache_hits += 1
                logger.debug(f"Metadata cache hit: {document_id}")
                return cache_entry["metadata"]
            
            self.metadata_cache_misses += 1
            logger.debug(f"Metadata cache miss: {document_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting document metadata from cache: {e}", exc_info=True)
            self.metadata_cache_misses += 1
            return None
    
    def remove_document(self, document_id: str) -> None:
        \"\"\"
        Remove a document from the cache.
        
        Args:
            document_id: The document ID.
        \"\"\"
        try:
            # Remove from document cache
            if document_id in self.document_cache:
                del self.document_cache[document_id]
            
            # Remove from content cache
            self._remove_content(document_id)
            
            # Remove from metadata cache
            if document_id in self.metadata_cache:
                del self.metadata_cache[document_id]
            
            logger.debug(f"Removed document from cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error removing document from cache: {e}", exc_info=True)
    
    def _remove_content(self, document_id: str) -> None:
        \"\"\"
        Remove document content from the cache.
        
        Args:
            document_id: The document ID.
        \"\"\"
        try:
            # Check if content is in cache
            if document_id in self.content_cache:
                # Update current content size
                self.current_content_size_bytes -= self.content_cache[document_id]["size"]
                
                # Remove from content cache
                del self.content_cache[document_id]
        
        except Exception as e:
            logger.error(f"Error removing document content from cache: {e}", exc_info=True)
    
    def _evict_documents(self) -> None:
        \"\"\"
        Evict documents from the cache based on LRU policy.
        \"\"\"
        try:
            # Sort documents by timestamp
            sorted_documents = sorted(
                self.document_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest documents
            num_to_remove = max(1, len(self.document_cache) // 4)  # Remove at least 1, up to 25%
            for i in range(min(num_to_remove, len(sorted_documents))):
                document_id = sorted_documents[i][0]
                self.remove_document(document_id)
                logger.debug(f"Evicted document from cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error evicting documents from cache: {e}", exc_info=True)
    
    def _evict_content(self, required_size: int) -> None:
        \"\"\"
        Evict document content from the cache based on LRU policy.
        
        Args:
            required_size: The required size in bytes.
        \"\"\"
        try:
            # Sort content by timestamp
            sorted_content = sorted(
                self.content_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest content until we have enough space
            for document_id, _ in sorted_content:
                self._remove_content(document_id)
                logger.debug(f"Evicted document content from cache: {document_id}")
                
                # Check if we have enough space
                if self.current_content_size_bytes + required_size <= self.max_content_size_bytes:
                    break
        
        except Exception as e:
            logger.error(f"Error evicting content from cache: {e}", exc_info=True)
    
    def clear(self) -> None:
        \"\"\"
        Clear the cache.
        \"\"\"
        try:
            self.document_cache = {}
            self.content_cache = {}
            self.metadata_cache = {}
            self.current_content_size_bytes = 0
            
            logger.debug("Cleared cache")
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        \"\"\"
        Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        \"\"\"
        try:
            return {
                "document_cache_size": len(self.document_cache),
                "content_cache_size": len(self.content_cache),
                "metadata_cache_size": len(self.metadata_cache),
                "content_cache_size_bytes": self.current_content_size_bytes,
                "content_cache_size_mb": self.current_content_size_bytes / (1024 * 1024),
                "document_cache_hits": self.document_cache_hits,
                "document_cache_misses": self.document_cache_misses,
                "content_cache_hits": self.content_cache_hits,
                "content_cache_misses": self.content_cache_misses,
                "metadata_cache_hits": self.metadata_cache_hits,
                "metadata_cache_misses": self.metadata_cache_misses
            }
        
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}", exc_info=True)
            return {}
"""
    create_file("src/utils/document_cache.py", document_cache_content)
    
    # Create base_model.py
    base_model_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Base model for RebelSCRIBE.

This module defines the BaseModel class which is the base class for all models.
\"\"\"

import datetime
import uuid
from typing import Dict, List, Optional, Set, Any

class BaseModel:
    \"\"\"
    Base class for all models.
    
    This class provides common functionality for all models, such as
    tracking changes and serialization.
    
    Attributes:
