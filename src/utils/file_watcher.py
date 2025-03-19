#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Watcher for RebelSCRIBE.

This module provides functionality for watching files and directories for changes.
"""

import os
import time
import threading
from typing import Dict, List, Callable, Optional, Set, Tuple, Any

import logging
logger = logging.getLogger(__name__)


class FileWatcher:
    """
    Watches files and directories for changes.
    
    This class provides methods for watching files and directories for changes,
    and triggering callbacks when changes are detected.
    """
    
    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize the FileWatcher.
        
        Args:
            poll_interval: The interval in seconds between polls for changes.
        """
        self.poll_interval = poll_interval
        self.watched_files: Dict[str, Tuple[float, List[Callable]]] = {}
        self.watched_directories: Dict[str, Tuple[Dict[str, float], List[Callable]]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Start the file watcher.
        
        Returns:
            True if the watcher was started, False if it was already running.
        """
        with self._lock:
            if self.running:
                return False
            
            self.running = True
            self.thread = threading.Thread(target=self._watch_thread, daemon=True)
            self.thread.start()
            
            return True
    
    def stop(self) -> bool:
        """
        Stop the file watcher.
        
        Returns:
            True if the watcher was stopped, False if it was not running.
        """
        with self._lock:
            if not self.running:
                return False
            
            self.running = False
            if self.thread:
                self.thread.join(timeout=2.0)
                self.thread = None
            
            return True
    
    def watch_file(self, file_path: str, callback: Callable[[str], None]) -> bool:
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
            # Expand and normalize the path
            file_path = os.path.abspath(os.path.expanduser(file_path))
            
            # Check if the file exists
            if not os.path.isfile(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            # Get the file's modification time
            mtime = os.path.getmtime(file_path)
            
            # Add the file to the watch list
            with self._lock:
                if file_path in self.watched_files:
                    # File is already being watched, add the callback
                    _, callbacks = self.watched_files[file_path]
                    if callback not in callbacks:
                        callbacks.append(callback)
                else:
                    # File is not being watched, add it
                    self.watched_files[file_path] = (mtime, [callback])
            
            return True
        
        except Exception as e:
            logger.error(f"Error watching file: {e}", exc_info=True)
            return False
    
    def unwatch_file(self, file_path: str, callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Stop watching a file for changes.
        
        Args:
            file_path: The path to the file to stop watching.
            callback: The callback to remove. If None, all callbacks will be removed.
                
        Returns:
            True if the file was removed from the watch list, False otherwise.
        """
        try:
            # Expand and normalize the path
            file_path = os.path.abspath(os.path.expanduser(file_path))
            
            # Remove the file from the watch list
            with self._lock:
                if file_path not in self.watched_files:
                    return False
                
                if callback is None:
                    # Remove all callbacks
                    del self.watched_files[file_path]
                else:
                    # Remove the specific callback
                    _, callbacks = self.watched_files[file_path]
                    if callback in callbacks:
                        callbacks.remove(callback)
                    
                    # If there are no more callbacks, remove the file
                    if not callbacks:
                        del self.watched_files[file_path]
            
            return True
        
        except Exception as e:
            logger.error(f"Error unwatching file: {e}", exc_info=True)
            return False
    
    def watch_directory(self, directory_path: str, callback: Callable[[str, str], None], recursive: bool = False) -> bool:
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
            # Expand and normalize the path
            directory_path = os.path.abspath(os.path.expanduser(directory_path))
            
            # Check if the directory exists
            if not os.path.isdir(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return False
            
            # Get the files in the directory
            files = {}
            if recursive:
                for root, _, filenames in os.walk(directory_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        files[file_path] = os.path.getmtime(file_path)
            else:
                for filename in os.listdir(directory_path):
                    file_path = os.path.join(directory_path, filename)
                    if os.path.isfile(file_path):
                        files[file_path] = os.path.getmtime(file_path)
            
            # Add the directory to the watch list
            with self._lock:
                if directory_path in self.watched_directories:
                    # Directory is already being watched, add the callback
                    _, callbacks = self.watched_directories[directory_path]
                    if callback not in callbacks:
                        callbacks.append(callback)
                else:
                    # Directory is not being watched, add it
                    self.watched_directories[directory_path] = (files, [callback])
            
            return True
        
        except Exception as e:
            logger.error(f"Error watching directory: {e}", exc_info=True)
            return False
    
    def unwatch_directory(self, directory_path: str, callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Stop watching a directory for changes.
        
        Args:
            directory_path: The path to the directory to stop watching.
            callback: The callback to remove. If None, all callbacks will be removed.
                
        Returns:
            True if the directory was removed from the watch list, False otherwise.
        """
        try:
            # Expand and normalize the path
            directory_path = os.path.abspath(os.path.expanduser(directory_path))
            
            # Remove the directory from the watch list
            with self._lock:
                if directory_path not in self.watched_directories:
                    return False
                
                if callback is None:
                    # Remove all callbacks
                    del self.watched_directories[directory_path]
                else:
                    # Remove the specific callback
                    _, callbacks = self.watched_directories[directory_path]
                    if callback in callbacks:
                        callbacks.remove(callback)
                    
                    # If there are no more callbacks, remove the directory
                    if not callbacks:
                        del self.watched_directories[directory_path]
            
            return True
        
        except Exception as e:
            logger.error(f"Error unwatching directory: {e}", exc_info=True)
            return False
    
    def _watch_thread(self) -> None:
        """
        Thread function for watching files and directories.
        """
        try:
            while self.running:
                # Check for file changes
                self._check_files()
                
                # Check for directory changes
                self._check_directories()
                
                # Sleep for the poll interval
                time.sleep(self.poll_interval)
        
        except Exception as e:
            logger.error(f"Error in watch thread: {e}", exc_info=True)
            self.running = False
    
    def _check_files(self) -> None:
        """
        Check for changes in watched files.
        """
        try:
            # Get a copy of the watched files
            with self._lock:
                files = self.watched_files.copy()
            
            # Check each file
            for file_path, (mtime, callbacks) in files.items():
                try:
                    # Check if the file still exists
                    if not os.path.exists(file_path):
                        # File was deleted, trigger callbacks
                        for callback in callbacks:
                            try:
                                callback(file_path)
                            except Exception as e:
                                logger.error(f"Error in file callback: {e}", exc_info=True)
                        
                        # Remove the file from the watch list
                        with self._lock:
                            if file_path in self.watched_files:
                                del self.watched_files[file_path]
                        
                        continue
                    
                    # Check if the file was modified
                    new_mtime = os.path.getmtime(file_path)
                    if new_mtime > mtime:
                        # File was modified, trigger callbacks
                        for callback in callbacks:
                            try:
                                callback(file_path)
                            except Exception as e:
                                logger.error(f"Error in file callback: {e}", exc_info=True)
                        
                        # Update the modification time
                        with self._lock:
                            if file_path in self.watched_files:
                                self.watched_files[file_path] = (new_mtime, callbacks)
                
                except Exception as e:
                    logger.error(f"Error checking file {file_path}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error checking files: {e}", exc_info=True)
    
    def _check_directories(self) -> None:
        """
        Check for changes in watched directories.
        """
        try:
            # Get a copy of the watched directories
            with self._lock:
                directories = self.watched_directories.copy()
            
            # Check each directory
            for directory_path, (files, callbacks) in directories.items():
                try:
                    # Check if the directory still exists
                    if not os.path.exists(directory_path):
                        # Directory was deleted, trigger callbacks for all files
                        for file_path in files:
                            for callback in callbacks:
                                try:
                                    callback(directory_path, file_path)
                                except Exception as e:
                                    logger.error(f"Error in directory callback: {e}", exc_info=True)
                        
                        # Remove the directory from the watch list
                        with self._lock:
                            if directory_path in self.watched_directories:
                                del self.watched_directories[directory_path]
                        
                        continue
                    
                    # Get the current files in the directory
                    current_files = {}
                    recursive = any(not file_path.startswith(directory_path) for file_path in files)
                    
                    if recursive:
                        for root, _, filenames in os.walk(directory_path):
                            for filename in filenames:
                                file_path = os.path.join(root, filename)
                                current_files[file_path] = os.path.getmtime(file_path)
                    else:
                        for filename in os.listdir(directory_path):
                            file_path = os.path.join(directory_path, filename)
                            if os.path.isfile(file_path):
                                current_files[file_path] = os.path.getmtime(file_path)
                    
                    # Check for new and modified files
                    for file_path, mtime in current_files.items():
                        if file_path not in files or mtime > files[file_path]:
                            # File is new or modified, trigger callbacks
                            for callback in callbacks:
                                try:
                                    callback(directory_path, file_path)
                                except Exception as e:
                                    logger.error(f"Error in directory callback: {e}", exc_info=True)
                    
                    # Check for deleted files
                    for file_path in set(files) - set(current_files):
                        # File was deleted, trigger callbacks
                        for callback in callbacks:
                            try:
                                callback(directory_path, file_path)
                            except Exception as e:
                                logger.error(f"Error in directory callback: {e}", exc_info=True)
                    
                    # Update the files
                    with self._lock:
                        if directory_path in self.watched_directories:
                            self.watched_directories[directory_path] = (current_files, callbacks)
                
                except Exception as e:
                    logger.error(f"Error checking directory {directory_path}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error checking directories: {e}", exc_info=True)
    
    def get_watched_files(self) -> List[str]:
        """
        Get a list of watched files.
        
        Returns:
            A list of watched file paths.
        """
        with self._lock:
            return list(self.watched_files.keys())
    
    def get_watched_directories(self) -> List[str]:
        """
        Get a list of watched directories.
        
        Returns:
            A list of watched directory paths.
        """
        with self._lock:
            return list(self.watched_directories.keys())
    
    def is_running(self) -> bool:
        """
        Check if the file watcher is running.
        
        Returns:
            True if the watcher is running, False otherwise.
        """
        with self._lock:
            return self.running


# Singleton instance of FileWatcher
_file_watcher_instance = None

def get_file_watcher(poll_interval: float = 1.0) -> FileWatcher:
    """
    Get the singleton instance of FileWatcher.
    
    Args:
        poll_interval: The interval in seconds between polls for changes.
        
    Returns:
        The singleton instance of FileWatcher.
    """
    global _file_watcher_instance
    
    # If the instance doesn't exist, create a new instance
    if _file_watcher_instance is None:
        _file_watcher_instance = FileWatcher(poll_interval)
    
    return _file_watcher_instance


def watch_file(file_path: str, callback: Callable[[str], None]) -> bool:
    """
    Watch a file for changes.
    
    Args:
        file_path: The path to the file to watch.
        callback: The function to call when the file changes.
            The callback will be passed the file path.
            
    Returns:
        True if the file was added to the watch list, False otherwise.
    """
    # Get the file watcher
    watcher = get_file_watcher()
    
    # Start the watcher if it's not running
    if not watcher.is_running():
        watcher.start()
    
    # Watch the file
    return watcher.watch_file(file_path, callback)


def unwatch_file(file_path: str, callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    Stop watching a file for changes.
    
    Args:
        file_path: The path to the file to stop watching.
        callback: The callback to remove. If None, all callbacks will be removed.
            
    Returns:
        True if the file was removed from the watch list, False otherwise.
    """
    # Get the file watcher
    watcher = get_file_watcher()
    
    # Unwatch the file
    return watcher.unwatch_file(file_path, callback)


def watch_directory(directory_path: str, callback: Callable[[str, str], None], recursive: bool = False) -> bool:
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
    # Get the file watcher
    watcher = get_file_watcher()
    
    # Start the watcher if it's not running
    if not watcher.is_running():
        watcher.start()
    
    # Watch the directory
    return watcher.watch_directory(directory_path, callback, recursive)


def unwatch_directory(directory_path: str, callback: Optional[Callable[[str, str], None]] = None) -> bool:
    """
    Stop watching a directory for changes.
    
    Args:
        directory_path: The path to the directory to stop watching.
        callback: The callback to remove. If None, all callbacks will be removed.
            
    Returns:
        True if the directory was removed from the watch list, False otherwise.
    """
    # Get the file watcher
    watcher = get_file_watcher()
    
    # Unwatch the directory
    return watcher.unwatch_directory(directory_path, callback)


def stop_file_watcher() -> bool:
    """
    Stop the file watcher.
    
    Returns:
        True if the watcher was stopped, False if it was not running.
    """
    # Get the file watcher
    watcher = get_file_watcher()
    
    # Stop the watcher
    return watcher.stop()
