#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager for RebelSCRIBE.

This module provides functions and classes for loading and managing application configuration.
"""

import os
import yaml
from typing import Dict, Any, Optional

import logging
logger = logging.getLogger(__name__)

from src.utils.config_migration import migrate_config, get_config_version


# Default configuration file path
DEFAULT_CONFIG_PATH = "config.yaml"

# Current application version
CURRENT_APP_VERSION = "0.3.0"


class ConfigManager:
    """
    Manages application configuration.
    
    This class provides methods for loading, saving, and accessing configuration values.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: The path to the configuration file. If None, uses the default path.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from file.
        
        Returns:
            The configuration data, or a default config if the configuration could not be loaded.
        """
        try:
            # Check if file exists
            if not os.path.isfile(self.config_path):
                logger.warning(f"Configuration file not found: {self.config_path}")
                # Create a default configuration
                default_config = self._create_default_config()
                # Save the default configuration
                self._save_config_without_logging(default_config)
                return default_config
            
            # Load configuration
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if config is None:
                config = {}
            
            # Check if migration is needed
            config_version = get_config_version(config)
            if config_version != CURRENT_APP_VERSION:
                logger.info(f"Configuration version {config_version} needs migration to {CURRENT_APP_VERSION}")
                # Migrate configuration
                config = self._migrate_config(config)
                # Save migrated configuration
                self._save_config_without_logging(config)
            
            return config
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            return {}
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create a default configuration.
        
        Returns:
            The default configuration data.
        """
        return {
            "application": {
                "name": "RebelSCRIBE",
                "version": CURRENT_APP_VERSION
            },
            "ui": {
                "color_theme": "light",
                "show_toolbar": True,
                "show_statusbar": True
            },
            "editor": {
                "font_family": "Courier New",
                "font_size": 12,
                "line_spacing": 1.5,
                "show_line_numbers": True,
                "auto_save": True,
                "auto_save_interval": 60  # seconds
            },
            "ai": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000,
                "use_local_models": False,
                "local_model_path": ""
            },
            "export": {
                "default_format": "docx",
                "include_metadata": True,
                "include_notes": False,
                "include_comments": False,
                "page_size": "A4",
                "margin": 2.54  # cm
            }
        }
    
    def _save_config_without_logging(self, config: Dict[str, Any]) -> bool:
        """
        Save the configuration to file without logging errors.
        
        Args:
            config: The configuration data to save.
            
        Returns:
            True if the configuration was saved successfully, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(self.config_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Save configuration
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False)
            
            return True
        
        except Exception:
            return False
    
    def _migrate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate the configuration to the current version.
        
        Args:
            config: The configuration data to migrate.
            
        Returns:
            The migrated configuration data.
        """
        try:
            # Create a backup of the original config
            from src.utils.config_migration import backup_config
            backup_path = backup_config(self.config_path)
            if backup_path:
                logger.info(f"Configuration backup created at {backup_path}")
            
            # Migrate the configuration
            migrated_config = migrate_config(config, CURRENT_APP_VERSION)
            
            return migrated_config
        
        except Exception as e:
            logger.error(f"Error migrating configuration: {e}", exc_info=True)
            return config

    def save_config(self) -> bool:
        """
        Save the configuration to file.
        
        Returns:
            True if the configuration was saved successfully, False otherwise.
        """
        try:
            # Ensure the configuration has the correct version
            if "application" not in self.config:
                self.config["application"] = {}
            self.config["application"]["version"] = CURRENT_APP_VERSION
            
            # Save configuration
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the configuration.
        
        Args:
            key: The key to get the value for. Can be a dot-separated path (e.g., "section.subsection.key").
            default: The default value to return if the key is not found.
            
        Returns:
            The value for the key, or the default value if the key is not found.
        """
        try:
            # Split key into parts
            parts = key.split(".")
            
            # Navigate through config
            value = self.config
            for part in parts:
                if not isinstance(value, dict) or part not in value:
                    return default
                value = value[part]
            
            return value
        
        except Exception as e:
            logger.error(f"Error getting configuration value: {e}", exc_info=True)
            return default
    
    def get(self, key: str, subkey: Optional[str] = None, default: Any = None) -> Any:
        """
        Get a value from the configuration.
        
        Args:
            key: The section key.
            subkey: The subkey within the section. If None, returns the entire section.
            default: The default value to return if the key is not found.
            
        Returns:
            The value for the key, or the default value if the key is not found.
        """
        try:
            # If subkey is provided, get the value from the section
            if subkey is not None:
                if key not in self.config or not isinstance(self.config[key], dict):
                    return default
                if subkey not in self.config[key]:
                    return default
                return self.config[key][subkey]
            
            # If no subkey, return the entire section
            if key not in self.config:
                return default
            
            return self.config[key]
        
        except Exception as e:
            logger.error(f"Error getting configuration value: {e}", exc_info=True)
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a value in the configuration.
        
        Args:
            section: The section to set the value in.
            key: The key to set the value for.
            value: The value to set.
            
        Returns:
            True if the value was set successfully, False otherwise.
        """
        try:
            # Ensure section exists
            if section not in self.config or not isinstance(self.config[section], dict):
                self.config[section] = {}
            
            # Set value
            self.config[section][key] = value
            
            # Save configuration
            return self.save_config()
        
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}", exc_info=True)
            return False
    
    def set_value(self, key: str, value: Any) -> bool:
        """
        Set a value in the configuration.
        
        Args:
            key: The key to set the value for. Can be a dot-separated path (e.g., "section.subsection.key").
            value: The value to set.
            
        Returns:
            True if the value was set successfully, False otherwise.
        """
        try:
            # Split key into parts
            parts = key.split(".")
            
            # Navigate through config
            current = self.config
            for i, part in enumerate(parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            
            # Set value
            current[parts[-1]] = value
            
            # Save configuration
            return self.save_config()
        
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}", exc_info=True)
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the entire configuration.
        
        Returns:
            The configuration data.
        """
        return self.config


# Singleton instance of ConfigManager
_config_manager_instance = None

def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get the singleton instance of ConfigManager.
    
    Args:
        config_path: The path to the configuration file. If None, uses the default path.
        
    Returns:
        The singleton instance of ConfigManager.
    """
    global _config_manager_instance
    
    # If the instance doesn't exist or a new config path is provided, create a new instance
    if _config_manager_instance is None or (config_path and config_path != _config_manager_instance.config_path):
        _config_manager_instance = ConfigManager(config_path)
    
    return _config_manager_instance


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Save the application configuration.
    
    Args:
        config: The configuration data to save.
        config_path: The path to the configuration file. If None, uses the default path.
        
    Returns:
        True if the configuration was saved successfully, False otherwise.
    """
    try:
        # Use default path if not specified
        if not config_path:
            config_path = DEFAULT_CONFIG_PATH
        
        # Save configuration
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return False


def get_config_value(key: str, default: Any = None, config_path: Optional[str] = None) -> Any:
    """
    Get a value from the application configuration.
    
    Args:
        key: The key to get the value for. Can be a dot-separated path (e.g., "section.subsection.key").
        default: The default value to return if the key is not found.
        config_path: The path to the configuration file. If None, uses the default path.
        
    Returns:
        The value for the key, or the default value if the key is not found.
    """
    try:
        # Get the singleton instance
        config_manager = get_config(config_path)
        
        # Get the value
        return config_manager.get_value(key, default)
    
    except Exception as e:
        logger.error(f"Error getting configuration value: {e}", exc_info=True)
        return default


def set_config_value(key: str, value: Any, config_path: Optional[str] = None) -> bool:
    """
    Set a value in the application configuration.
    
    Args:
        key: The key to set the value for. Can be a dot-separated path (e.g., "section.subsection.key").
        value: The value to set.
        config_path: The path to the configuration file. If None, uses the default path.
        
    Returns:
        True if the value was set successfully, False otherwise.
    """
    try:
        # Get the singleton instance
        config_manager = get_config(config_path)
        
        # Set the value
        return config_manager.set_value(key, value)
    
    except Exception as e:
        logger.error(f"Error setting configuration value: {e}", exc_info=True)
        return False
