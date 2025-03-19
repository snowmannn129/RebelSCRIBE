#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File utilities for RebelSCRIBE.

This module provides utility functions for file operations,
including reading, writing, and managing files and directories.
"""

import os
import json
import pickle
import shutil
import tempfile
from typing import Dict, List, Optional, Any, Union, BinaryIO, Callable

import logging
logger = logging.getLogger(__name__)

from src.utils.file_watcher import (
    watch_file,
    unwatch_file,
    watch_directory,
    unwatch_directory,
    stop_file_watcher
)


def expand_path(path: str) -> str:
    """
    Expand the path, including expanding the tilde character to the user's home directory.
    
    Args:
        path: The path to expand.
        
    Returns:
        The expanded path.
    """
    try:
        # Expand tilde
        if path and path.startswith("~"):
            path = os.path.expanduser(path)
        
        # Normalize path
        path = os.path.normpath(path)
        
        return path
    
    except Exception as e:
        logger.error(f"Error expanding path: {e}", exc_info=True)
        return path


def ensure_directory(directory_path: str) -> bool:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: The path to the directory.
        
    Returns:
        True if the directory exists or was created, False otherwise.
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    
    except Exception as e:
        logger.error(f"Error ensuring directory: {e}", exc_info=True)
        return False


def file_exists(file_path: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        True if the file exists, False otherwise.
    """
    return os.path.isfile(file_path)


def read_file(file_path: str) -> Optional[str]:
    """
    Read the contents of a file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The contents of the file, or None if the file could not be read.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    except Exception as e:
        logger.error(f"Error reading file: {e}", exc_info=True)
        return None


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: The path to the file.
        content: The content to write.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return True
    
    except Exception as e:
        logger.error(f"Error writing file: {e}", exc_info=True)
        return False


def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Read a JSON file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The parsed JSON data, or None if the file could not be read or parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    except Exception as e:
        logger.error(f"Error reading JSON file: {e}", exc_info=True)
        return None


def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Write data to a JSON file.
    
    Args:
        file_path: The path to the file.
        data: The data to write.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Custom JSON encoder to handle datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                import datetime
                if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
                    return obj.isoformat()
                return super().default(obj)
        
        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=DateTimeEncoder)
        
        return True
    
    except Exception as e:
        logger.error(f"Error writing JSON file: {e}", exc_info=True)
        return False


def delete_file(file_path: str) -> bool:
    """
    Delete a file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        True if the file was deleted successfully, False otherwise.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        return False


def copy_file(source_path: str, destination_path: str) -> bool:
    """
    Copy a file.
    
    Args:
        source_path: The path to the source file.
        destination_path: The path to the destination file.
        
    Returns:
        True if the file was copied successfully, False otherwise.
    """
    try:
        # Ensure destination directory exists
        directory = os.path.dirname(destination_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Copy file
        shutil.copy2(source_path, destination_path)
        
        return True
    
    except Exception as e:
        logger.error(f"Error copying file: {e}", exc_info=True)
        return False


def list_files(directory_path: str, pattern: Optional[str] = None, recursive: bool = False) -> List[str]:
    """
    List files in a directory.
    
    Args:
        directory_path: The path to the directory.
        pattern: Optional glob pattern to filter files (e.g., "*.txt").
        recursive: Whether to list files recursively.
        
    Returns:
        A list of file paths.
    """
    try:
        import fnmatch
        
        if not os.path.exists(directory_path):
            return []
        
        file_list = []
        
        if recursive:
            # List files recursively
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if pattern is None or fnmatch.fnmatch(file, pattern):
                        file_list.append(file_path)
        else:
            # List files in directory only
            for f in os.listdir(directory_path):
                file_path = os.path.join(directory_path, f)
                if os.path.isfile(file_path) and (pattern is None or fnmatch.fnmatch(f, pattern)):
                    file_list.append(file_path)
        
        return file_list
    
    except Exception as e:
        logger.error(f"Error listing files: {e}", exc_info=True)
        return []


def read_text_file(file_path: str) -> Optional[str]:
    """
    Read the contents of a text file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The contents of the file, or None if the file could not be read.
    """
    return read_file(file_path)


def write_text_file(file_path: str, content: str) -> bool:
    """
    Write content to a text file.
    
    Args:
        file_path: The path to the file.
        content: The content to write.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    return write_file(file_path, content)


def read_binary_file(file_path: str) -> Optional[bytes]:
    """
    Read the contents of a binary file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The contents of the file, or None if the file could not be read.
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    
    except Exception as e:
        logger.error(f"Error reading binary file: {e}", exc_info=True)
        return None


def write_binary_file(file_path: str, content: bytes) -> bool:
    """
    Write content to a binary file.
    
    Args:
        file_path: The path to the file.
        content: The content to write.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(content)
        
        return True
    
    except Exception as e:
        logger.error(f"Error writing binary file: {e}", exc_info=True)
        return False


def read_pickle_file(file_path: str) -> Optional[Any]:
    """
    Read a pickle file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The unpickled data, or None if the file could not be read or unpickled.
    """
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    
    except Exception as e:
        logger.error(f"Error reading pickle file: {e}", exc_info=True)
        return None


def write_pickle_file(file_path: str, data: Any) -> bool:
    """
    Write data to a pickle file.
    
    Args:
        file_path: The path to the file.
        data: The data to write.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write file
        with open(file_path, "wb") as f:
            pickle.dump(data, f)
        
        return True
    
    except Exception as e:
        logger.error(f"Error writing pickle file: {e}", exc_info=True)
        return False


def move_file(source_path: str, destination_path: str) -> bool:
    """
    Move a file.
    
    Args:
        source_path: The path to the source file.
        destination_path: The path to the destination file.
        
    Returns:
        True if the file was moved successfully, False otherwise.
    """
    try:
        # Ensure destination directory exists
        directory = os.path.dirname(destination_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Move file
        shutil.move(source_path, destination_path)
        
        return True
    
    except Exception as e:
        logger.error(f"Error moving file: {e}", exc_info=True)
        return False


def create_temp_file(content: Optional[str] = None, suffix: Optional[str] = None) -> Optional[str]:
    """
    Create a temporary file.
    
    Args:
        content: The content to write to the file.
        suffix: The file suffix (e.g., ".txt").
        
    Returns:
        The path to the temporary file, or None if the file could not be created.
    """
    try:
        # Create temporary file
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        
        # Write content if provided
        if content is not None:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return path
    
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}", exc_info=True)
        return None


def create_temp_directory() -> Optional[str]:
    """
    Create a temporary directory.
    
    Returns:
        The path to the temporary directory, or None if the directory could not be created.
    """
    try:
        return tempfile.mkdtemp()
    
    except Exception as e:
        logger.error(f"Error creating temporary directory: {e}", exc_info=True)
        return None


def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The size of the file in bytes, or None if the file does not exist.
    """
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return None
    
    except Exception as e:
        logger.error(f"Error getting file size: {e}", exc_info=True)
        return None


def get_file_modification_time(file_path: str) -> Optional[float]:
    """
    Get the modification time of a file.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The modification time of the file (as seconds since the epoch), or None if the file does not exist.
    """
    try:
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return None
    
    except Exception as e:
        logger.error(f"Error getting file modification time: {e}", exc_info=True)
        return None


def directory_exists(directory_path: str) -> bool:
    """
    Check if a directory exists.
    
    Args:
        directory_path: The path to the directory.
        
    Returns:
        True if the directory exists, False otherwise.
    """
    return os.path.isdir(directory_path)


def watch_for_file_changes(file_path: str, callback: Callable[[str], None]) -> bool:
    """
    Watch a file for changes.
    
    Args:
        file_path: The path to the file to watch.
        callback: The function to call when the file changes.
            The callback will be passed the file path.
            
    Returns:
        True if the file was added to the watch list, False otherwise.
    """
    try:
        # Expand the path
        file_path = expand_path(file_path)
        
        # Watch the file
        return watch_file(file_path, callback)
    
    except Exception as e:
        logger.error(f"Error watching file: {e}", exc_info=True)
        return False


def stop_watching_file(file_path: str, callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    Stop watching a file for changes.
    
    Args:
        file_path: The path to the file to stop watching.
        callback: The callback to remove. If None, all callbacks will be removed.
            
    Returns:
        True if the file was removed from the watch list, False otherwise.
    """
    try:
        # Expand the path
        file_path = expand_path(file_path)
        
        # Unwatch the file
        return unwatch_file(file_path, callback)
    
    except Exception as e:
        logger.error(f"Error unwatching file: {e}", exc_info=True)
        return False


def watch_for_directory_changes(directory_path: str, callback: Callable[[str, str], None], recursive: bool = False) -> bool:
    """
    Watch a directory for changes.
    
    Args:
        directory_path: The path to the directory to watch.
        callback: The function to call when a file in the directory changes.
            The callback will be passed the directory path and the file path.
        recursive: Whether to watch subdirectories recursively.
            
    Returns:
        True if the directory was added to the watch list, False otherwise.
    """
    try:
        # Expand the path
        directory_path = expand_path(directory_path)
        
        # Watch the directory
        return watch_directory(directory_path, callback, recursive)
    
    except Exception as e:
        logger.error(f"Error watching directory: {e}", exc_info=True)
        return False


def stop_watching_directory(directory_path: str, callback: Optional[Callable[[str, str], None]] = None) -> bool:
    """
    Stop watching a directory for changes.
    
    Args:
        directory_path: The path to the directory to stop watching.
        callback: The callback to remove. If None, all callbacks will be removed.
            
    Returns:
        True if the directory was removed from the watch list, False otherwise.
    """
    try:
        # Expand the path
        directory_path = expand_path(directory_path)
        
        # Unwatch the directory
        return unwatch_directory(directory_path, callback)
    
    except Exception as e:
        logger.error(f"Error unwatching directory: {e}", exc_info=True)
        return False


def stop_all_file_watching() -> bool:
    """
    Stop all file watching.
    
    Returns:
        True if the file watcher was stopped, False if it was not running.
    """
    try:
        # Stop the file watcher
        return stop_file_watcher()
    
    except Exception as e:
        logger.error(f"Error stopping file watcher: {e}", exc_info=True)
        return False
