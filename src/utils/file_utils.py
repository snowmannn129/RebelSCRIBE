#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File utilities for RebelSCRIBE.

This module provides file-related functionality for the application.
"""

import os
import json
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any

def ensure_directory(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: The directory path.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except Exception as e:
        print(f"Error ensuring directory {directory_path}: {e}")
        return False

def file_exists(file_path: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: The file path.
        
    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)

def directory_exists(directory_path: str) -> bool:
    """
    Check if a directory exists.
    
    Args:
        directory_path: The directory path.
        
    Returns:
        bool: True if the directory exists, False otherwise.
    """
    return os.path.exists(directory_path) and os.path.isdir(directory_path)

def read_file(file_path: str) -> Optional[str]:
    """
    Read a file.
    
    Args:
        file_path: The file path.
        
    Returns:
        The file contents, or None if reading failed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def write_file(file_path: str, content: str) -> bool:
    """
    Write to a file.
    
    Args:
        file_path: The file path.
        content: The content to write.
        
    Returns:
        bool: True if successful, False otherwise.
    """
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
    """
    Read a JSON file.
    
    Args:
        file_path: The file path.
        
    Returns:
        The parsed JSON data, or None if reading or parsing failed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return None

def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Write to a JSON file.
    
    Args:
        file_path: The file path.
        data: The data to write.
        
    Returns:
        bool: True if successful, False otherwise.
    """
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
    """
    List files in a directory.
    
    Args:
        directory_path: The directory path.
        pattern: The file pattern to match.
        
    Returns:
        A list of file paths.
    """
    try:
        return glob.glob(os.path.join(directory_path, pattern))
    except Exception as e:
        print(f"Error listing files in {directory_path}: {e}")
        return []

def copy_file(source_path: str, destination_path: str) -> bool:
    """
    Copy a file.
    
    Args:
        source_path: The source file path.
        destination_path: The destination file path.
        
    Returns:
        bool: True if successful, False otherwise.
    """
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
    """
    Delete a file.
    
    Args:
        file_path: The file path.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False

def expand_path(path: str) -> str:
    """
    Expand a path, resolving ~ to the user's home directory.
    
    Args:
        path: The path to expand.
        
    Returns:
        The expanded path.
    """
    return os.path.expanduser(path)
