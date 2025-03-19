#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Settings Manager

This module handles loading and saving settings for the RebelSCRIBE application.
"""

from typing import Dict, Any, Optional

from src.utils.logging_utils import get_logger
from src.utils.config_manager import get_config as get_config_original

logger = get_logger(__name__)

# Get the config instance, but allow it to be overridden for testing
_config = None

def get_config_instance():
    """Get the config instance, initializing it if necessary."""
    global _config
    if _config is None:
        # Import here to avoid circular imports
        try:
            from src.ui.settings_dialog import get_config
            _config = get_config()
        except ImportError:
            _config = get_config_original()
    return _config

def load_settings() -> Dict[str, Any]:
    """
    Load current settings from the configuration.
    
    Returns:
        A dictionary containing the current settings.
    """
    logger.debug("Loading current settings")
    
    try:
        config_instance = get_config_instance()
        
        # For compatibility with tests
        if hasattr(config_instance, 'get_settings'):
            settings = config_instance.get_settings()
            logger.debug("Settings loaded using get_settings")
        else:
            # Load settings from config
            settings = {
                "editor": config_instance.get("ui", "editor", {}),
                "interface": {
                    "theme": config_instance.get("ui", "theme", "Light"),
                    "accent_color": config_instance.get("ui", "colors", {}).get("primary", "#0078D7"),
                    "show_toolbar": True,
                    "show_statusbar": True,
                    "show_line_numbers": config_instance.get("ui", "editor", {}).get("line_numbers", True),
                    "restore_session": True,
                    "show_welcome": True
                },
                "file_locations": {
                    "save_location": config_instance.get("application", "data_directory", ""),
                    "backup_location": config_instance.get("application", "backup", {}).get("directory", ""),
                    "enable_backups": config_instance.get("application", "backup", {}).get("enabled", True),
                    "backup_interval": config_instance.get("application", "backup", {}).get("interval", 30) // 60,  # Convert seconds to minutes
                    "max_backups": config_instance.get("application", "backup", {}).get("max_backups", 10)
                },
                "shortcuts": config_instance.get("ui", "shortcuts", {
                    "new_project": "Ctrl+N",
                    "open_project": "Ctrl+O",
                    "save": "Ctrl+S",
                    "save_as": "Ctrl+Shift+S",
                    "undo": "Ctrl+Z",
                    "redo": "Ctrl+Y",
                    "cut": "Ctrl+X",
                    "copy": "Ctrl+C",
                    "paste": "Ctrl+V",
                    "distraction_free": "F11",
                    "focus_mode": "Ctrl+Shift+F"
                })
            }
            logger.debug("Settings loaded using config.get")
        
        logger.debug("Current settings loaded")
        return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        raise

def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to the configuration.
    
    Args:
        settings: A dictionary containing the settings to save.
        
    Returns:
        True if successful, False otherwise.
    """
    logger.debug("Saving current settings")
    
    try:
        # Get the config instance
        config_instance = get_config_instance()
        
        # For compatibility with tests
        if hasattr(config_instance, 'update_settings'):
            # Use the update_settings method if it exists (for tests)
            config_instance.update_settings(settings)
            logger.debug("Settings saved using update_settings")
        else:
            # Update UI settings
            editor_settings = settings.get("editor", {})
            interface_settings = settings.get("interface", {})
            file_locations = settings.get("file_locations", {})
            shortcuts = settings.get("shortcuts", {})
            
            # Update editor settings
            config_instance.set("ui", "editor", {
                "font_family": editor_settings.get("font_family", "Arial"),
                "font_size": editor_settings.get("font_size", 12),
                "line_numbers": interface_settings.get("show_line_numbers", True),
                "highlight_current_line": True,
                "word_wrap": True,
                "spell_check": editor_settings.get("spellcheck_enabled", True),
                "auto_save": editor_settings.get("autosave_enabled", True)
            })
            
            # Update theme
            config_instance.set("ui", "theme", interface_settings.get("theme", "Light").lower())
            
            # Update colors
            colors = config_instance.get("ui", "colors", {})
            colors["primary"] = interface_settings.get("accent_color", "#0078D7")
            config_instance.set("ui", "colors", colors)
            
            # Update backup settings
            backup_settings = {
                "enabled": file_locations.get("enable_backups", True),
                "interval": file_locations.get("backup_interval", 30) * 60,  # Convert minutes to seconds
                "max_backups": file_locations.get("max_backups", 10),
                "directory": file_locations.get("backup_location", "")
            }
            config_instance.set("application", "backup", backup_settings)
            
            # Update data directory
            config_instance.set("application", "data_directory", file_locations.get("save_location", ""))
            
            # Update shortcuts
            config_instance.set("ui", "shortcuts", shortcuts)
            
            # Save config
            config_instance.save_config()
            logger.debug("Settings saved using set and save_config")
        
        logger.debug("Settings saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False

def reset_to_defaults() -> bool:
    """
    Reset settings to defaults.
    
    Returns:
        True if successful, False otherwise.
    """
    logger.debug("Resetting settings to defaults")
    
    try:
        config_instance = get_config_instance()
        
        # For compatibility with tests
        if hasattr(config_instance, 'reset_to_defaults'):
            # Use the reset_to_defaults method if it exists (for tests)
            config_instance.reset_to_defaults()
            logger.debug("Settings reset using reset_to_defaults")
        else:
            # Fall back to manual reset
            config_instance._create_default_config()
            config_instance.save_config()
            logger.debug("Settings reset using _create_default_config and save_config")
        
        logger.debug("Settings reset to defaults successfully")
        return True
    except Exception as e:
        logger.error(f"Error resetting settings to defaults: {e}")
        return False
