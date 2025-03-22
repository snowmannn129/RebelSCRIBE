#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration manager for RebelSCRIBE.

This module provides configuration management functionality for the application.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Union

# Get logger
logger = logging.getLogger(__name__)

# Default configuration path
DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".rebelscribe", "config.yaml")

# Singleton instance
_config_manager_instance = None


def get_config(config_path: Optional[str] = None) -> 'ConfigManager':
    """
    Get the ConfigManager instance.
    
    Args:
        config_path: The configuration file path. If None, uses the default path.
        
    Returns:
        The ConfigManager instance.
    """
    global _config_manager_instance
    
    # If the instance doesn't exist or a different path is specified, create a new instance
    if _config_manager_instance is None or (config_path is not None and config_path != _config_manager_instance.config_path):
        _config_manager_instance = ConfigManager(config_path)
    
    return _config_manager_instance


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Save a configuration to a file.
    
    Args:
        config: The configuration data.
        config_path: The configuration file path. If None, uses the default path.
        
    Returns:
        True if successful, False otherwise.
    """
    # Use the default path if none is specified
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save the configuration
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return False


def get_config_value(key: str, default: Any = None, config_path: Optional[str] = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: The configuration key (dot notation for nested keys).
        default: The default value to return if the key doesn't exist.
        config_path: The configuration file path. If None, uses the default path.
        
    Returns:
        The configuration value, or the default if the key doesn't exist.
    """
    # Get the ConfigManager instance
    config_manager = get_config(config_path)
    
    # Get the value
    return config_manager.get_value(key, default)


def set_config_value(key: str, value: Any, config_path: Optional[str] = None) -> bool:
    """
    Set a configuration value.
    
    Args:
        key: The configuration key (dot notation for nested keys).
        value: The configuration value.
        config_path: The configuration file path. If None, uses the default path.
        
    Returns:
        True if successful, False otherwise.
    """
    # Get the ConfigManager instance
    config_manager = get_config(config_path)
    
    # Set the value
    return config_manager.set_value(key, value)


class ConfigManager:
    """
    Configuration manager for RebelSCRIBE.
    
    This class provides functionality for loading, saving, and accessing configuration settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: The configuration file path. If None, uses the default path.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the file.
        
        Returns:
            The configuration data.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    # Determine the file format based on the extension
                    if self.config_path.endswith(".json"):
                        return json.load(f)
                    elif self.config_path.endswith(".yaml") or self.config_path.endswith(".yml"):
                        return yaml.safe_load(f)
                    else:
                        # Default to YAML
                        return yaml.safe_load(f)
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                return self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create the default configuration.
        
        Returns:
            The default configuration data.
        """
        config = {
            "application": {
                "name": "RebelSCRIBE",
                "version": "0.3.0",
                "data_directory": os.path.join(os.path.expanduser("~"), ".rebelscribe"),
                "autosave_interval": 300,  # 5 minutes
                "backup": {
                    "enabled": True,
                    "interval": 3600,  # 1 hour
                    "max_backups": 10,
                    "directory": os.path.join(os.path.expanduser("~"), ".rebelscribe", "backups")
                }
            },
            "ui": {
                "color_theme": "system",
                "colors": {
                    "primary": "#007bff",
                    "secondary": "#6c757d",
                    "success": "#28a745",
                    "danger": "#dc3545",
                    "warning": "#ffc107",
                    "info": "#17a2b8"
                },
                "font": {
                    "ui": "Segoe UI",
                    "ui_size": 10,
                    "editor": "Consolas",
                    "editor_size": 12
                },
                "show_toolbar": True,
                "show_statusbar": True,
                "editor": {
                    "line_numbers": True,
                    "word_wrap": True,
                    "spell_check": True,
                    "auto_save": True,
                    "highlight_current_line": True
                },
                "distraction_free_mode": {
                    "hide_ui_elements": True,
                    "background_color": "#2d2d2d",
                    "text_color": "#f8f8f2"
                }
            },
            "editor": {
                "font_family": "Courier New",
                "font_size": 12,
                "line_spacing": 1.5,
                "show_line_numbers": True,
                "auto_save": True,
                "auto_save_interval": 60  # 1 minute
            },
            "export": {
                "default_format": "docx",
                "markdown": {
                    "flavor": "github"
                },
                "html": {
                    "include_css": True,
                    "template": ""
                },
                "docx": {
                    "include_metadata": True,
                    "template": "",
                    "page_size": "A4"
                },
                "pdf": {
                    "include_metadata": True,
                    "template": "",
                    "page_size": "A4"
                },
                "epub": {
                    "include_cover": True,
                    "include_toc": True
                }
            },
            "ai": {
                "provider": "openai",
                "models": {
                    "openai": {
                        "chat": "gpt-4-turbo",
                        "completion": "gpt-4-turbo",
                        "embedding": "text-embedding-3-small",
                        "image": "dall-e-3"
                    },
                    "anthropic": {
                        "chat": "claude-3-opus-20240229",
                        "completion": "claude-3-opus-20240229"
                    },
                    "google": {
                        "chat": "gemini-1.5-pro",
                        "completion": "gemini-1.5-pro",
                        "embedding": "embedding-001"
                    },
                    "local": {
                        "chat": "llama3-70b",
                        "completion": "llama3-70b",
                        "embedding": "all-MiniLM-L6-v2",
                        "image": "stable-diffusion-3"
                    }
                },
                "api_keys": {
                    "openai": "",
                    "anthropic": "",
                    "google": ""
                },
                "default_params": {
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9,
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.5
                },
                "local": {
                    "model_path": "",
                    "device": "cpu"
                },
                "rate_limits": {
                    "openai": 10,
                    "anthropic": 5,
                    "google": 10,
                    "local": 20
                }
            },
            "cloud_storage": {
                "enabled": False,
                "provider": "dropbox",
                "dropbox": {
                    "api_key": "",
                    "folder": "/RebelSCRIBE"
                },
                "google_drive": {
                    "credentials_file": "",
                    "folder": "RebelSCRIBE"
                },
                "onedrive": {
                    "client_id": "",
                    "folder": "RebelSCRIBE"
                }
            },
            "error_handler": {
                "ui_treatments": {
                    "INFO": {
                        "dialog_type": "NOTIFICATION",
                        "use_non_blocking": True,
                        "timeout": 5000,
                        "position": "TOP_RIGHT"
                    },
                    "WARNING": {
                        "dialog_type": "NOTIFICATION",
                        "use_non_blocking": True,
                        "timeout": 10000,
                        "position": "TOP_RIGHT"
                    },
                    "ERROR": {
                        "dialog_type": "MODAL",
                        "use_non_blocking": False,
                        "timeout": None,
                        "position": None
                    },
                    "CRITICAL": {
                        "dialog_type": "MODAL",
                        "use_non_blocking": False,
                        "timeout": None,
                        "position": None
                    }
                },
                "error_aggregation": {
                    "enabled": True,
                    "timeout": 5000,
                    "pattern_matching": False
                },
                "rate_limiting": {
                    "enabled": True,
                    "threshold": 5,
                    "time_window": 60000,
                    "use_exponential_backoff": True
                },
                "notification_manager": {
                    "max_notifications": 5,
                    "spacing": 10,
                    "animation_duration": 250,
                    "fade_effect": True,
                    "slide_effect": True,
                    "stacking_order": "newest_on_top",
                    "default_timeouts": {
                        "INFO": 5000,
                        "WARNING": 10000,
                        "ERROR": 15000,
                        "CRITICAL": None
                    }
                },
                "error_reporting": {
                    "service": "local",
                    "endpoint_url": "",
                    "api_key": "",
                    "smtp_server": "",
                    "smtp_port": 587,
                    "smtp_username": "",
                    "smtp_password": "",
                    "from_email": "",
                    "to_email": ""
                }
            }
        }
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save default config
        try:
            # Determine the file format based on the extension
            if self.config_path.endswith(".json"):
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
            else:
                # Default to YAML
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving default configuration: {e}", exc_info=True)
        
        return config
    
    def save_config(self) -> bool:
        """
        Save the configuration to the file.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Determine the file format based on the extension
            if self.config_path.endswith(".json"):
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=2)
            else:
                # Default to YAML
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the entire configuration.
        
        Returns:
            The configuration data.
        """
        return self.config
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: The configuration section.
            key: The configuration key. If None, returns the entire section.
            default: The default value to return if the key doesn't exist.
            
        Returns:
            The configuration value, or the default if the key doesn't exist.
        """
        try:
            if key is None:
                return self.config.get(section, {})
            return self.config.get(section, {}).get(key, default)
        except Exception as e:
            logger.error(f"Error getting configuration value: {e}", exc_info=True)
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Args:
            section: The configuration section.
            key: The configuration key.
            value: The configuration value.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            return self.save_config()
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}", exc_info=True)
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: The configuration section.
            
        Returns:
            The configuration section, or an empty dictionary if the section doesn't exist.
        """
        return self.config.get(section, {})
    
    def set_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        Set a configuration section.
        
        Args:
            section: The configuration section.
            values: The configuration values.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.config[section] = values
            return self.save_config()
        except Exception as e:
            logger.error(f"Error setting configuration section: {e}", exc_info=True)
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: The configuration key (dot notation for nested keys).
            default: The default value to return if the key doesn't exist.
            
        Returns:
            The configuration value, or the default if the key doesn't exist.
        """
        try:
            # Split the key into parts
            parts = key.split(".")
            
            # Start with the entire config
            value = self.config
            
            # Traverse the config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"Error getting configuration value: {e}", exc_info=True)
            return default
    
    def set_value(self, key: str, value: Any) -> bool:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: The configuration key (dot notation for nested keys).
            value: The configuration value.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Split the key into parts
            parts = key.split(".")
            
            # Start with the entire config
            config = self.config
            
            # Traverse the config
            for i, part in enumerate(parts[:-1]):
                # If the part doesn't exist, create it
                if part not in config:
                    config[part] = {}
                
                # If the part is not a dictionary, make it one
                if not isinstance(config[part], dict):
                    config[part] = {}
                
                # Move to the next level
                config = config[part]
            
            # Set the value
            config[parts[-1]] = value
            
            # Save the config
            return self.save_config()
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}", exc_info=True)
            return False
