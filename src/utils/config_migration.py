#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Migration for RebelSCRIBE.

This module provides functions for migrating configuration files between versions.
"""

import os
import yaml
from typing import Dict, Any, Optional, List, Tuple

import logging
logger = logging.getLogger(__name__)


def get_config_version(config: Dict[str, Any]) -> str:
    """
    Get the version of a configuration.
    
    Args:
        config: The configuration data.
        
    Returns:
        The version string, or "0.0.0" if not found.
    """
    try:
        return config.get("application", {}).get("version", "0.0.0")
    except Exception as e:
        logger.error(f"Error getting configuration version: {e}", exc_info=True)
        return "0.0.0"


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.
    
    Args:
        version1: The first version string.
        version2: The second version string.
        
    Returns:
        -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2.
    """
    try:
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]
        
        # Pad with zeros if necessary
        while len(v1_parts) < 3:
            v1_parts.append(0)
        while len(v2_parts) < 3:
            v2_parts.append(0)
        
        # Compare parts
        for i in range(3):
            if v1_parts[i] < v2_parts[i]:
                return -1
            if v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0
    
    except Exception as e:
        logger.error(f"Error comparing versions: {e}", exc_info=True)
        return 0


def get_migration_steps(from_version: str, to_version: str) -> List[Tuple[str, str]]:
    """
    Get the migration steps required to migrate from one version to another.
    
    Args:
        from_version: The source version.
        to_version: The target version.
        
    Returns:
        A list of (from_version, to_version) tuples representing the migration steps.
    """
    # Define the available migration paths
    # Each tuple represents a migration from one version to another
    available_migrations = [
        ("0.0.0", "0.1.0"),
        ("0.1.0", "0.2.0"),
        ("0.2.0", "0.3.0"),
        # Add more migrations as needed
    ]
    
    # If versions are the same, no migration is needed
    if compare_versions(from_version, to_version) == 0:
        return []
    
    # If from_version > to_version, we can't migrate
    if compare_versions(from_version, to_version) > 0:
        logger.error(f"Cannot migrate from newer version {from_version} to older version {to_version}")
        return []
    
    # Find the migration path
    migration_steps = []
    current_version = from_version
    
    while compare_versions(current_version, to_version) < 0:
        # Find the next step
        next_step = None
        for step in available_migrations:
            if step[0] == current_version:
                next_step = step
                break
        
        # If no next step is found, we can't migrate
        if next_step is None:
            logger.error(f"No migration path found from {current_version} to {to_version}")
            return []
        
        # Add the step and update current_version
        migration_steps.append(next_step)
        current_version = next_step[1]
        
        # If we've reached or passed the target version, we're done
        if compare_versions(current_version, to_version) >= 0:
            break
    
    return migration_steps


def migrate_config_0_0_0_to_0_1_0(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration from version 0.0.0 to 0.1.0.
    
    Args:
        config: The configuration data.
        
    Returns:
        The migrated configuration data.
    """
    # Create a copy of the config
    new_config = config.copy()
    
    # Set the version
    if "application" not in new_config:
        new_config["application"] = {}
    new_config["application"]["version"] = "0.1.0"
    
    # Add default UI settings if not present
    if "ui" not in new_config:
        new_config["ui"] = {"theme": "light"}
    
    return new_config


def migrate_config_0_1_0_to_0_2_0(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration from version 0.1.0 to 0.2.0.
    
    Args:
        config: The configuration data.
        
    Returns:
        The migrated configuration data.
    """
    # Create a copy of the config
    new_config = config.copy()
    
    # Update the version
    new_config["application"]["version"] = "0.2.0"
    
    # Add new settings
    if "editor" not in new_config:
        new_config["editor"] = {
            "font_family": "Courier New",
            "font_size": 12,
            "line_spacing": 1.5,
            "show_line_numbers": True,
            "auto_save": True,
            "auto_save_interval": 60  # seconds
        }
    
    # Migrate UI settings
    if "ui" in new_config:
        # Rename theme to color_theme
        if "theme" in new_config["ui"]:
            new_config["ui"]["color_theme"] = new_config["ui"].pop("theme")
        
        # Add new UI settings
        new_config["ui"]["show_toolbar"] = True
        new_config["ui"]["show_statusbar"] = True
    
    return new_config


def migrate_config_0_2_0_to_0_3_0(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration from version 0.2.0 to 0.3.0.
    
    Args:
        config: The configuration data.
        
    Returns:
        The migrated configuration data.
    """
    # Create a copy of the config
    new_config = config.copy()
    
    # Update the version
    new_config["application"]["version"] = "0.3.0"
    
    # Add AI settings
    if "ai" not in new_config:
        new_config["ai"] = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000,
            "use_local_models": False,
            "local_model_path": ""
        }
    
    # Add export settings
    if "export" not in new_config:
        new_config["export"] = {
            "default_format": "docx",
            "include_metadata": True,
            "include_notes": False,
            "include_comments": False,
            "page_size": "A4",
            "margin": 2.54  # cm
        }
    
    return new_config


def migrate_config(config: Dict[str, Any], target_version: str) -> Dict[str, Any]:
    """
    Migrate a configuration to a target version.
    
    Args:
        config: The configuration data.
        target_version: The target version.
        
    Returns:
        The migrated configuration data.
    """
    try:
        # Get the current version
        current_version = get_config_version(config)
        
        # Get the migration steps
        migration_steps = get_migration_steps(current_version, target_version)
        
        # If no migration steps are needed, return the original config
        if not migration_steps:
            return config
        
        # Apply the migration steps
        migrated_config = config
        for from_version, to_version in migration_steps:
            # Get the migration function
            migration_func_name = f"migrate_config_{from_version.replace('.', '_')}_to_{to_version.replace('.', '_')}"
            migration_func = globals().get(migration_func_name)
            
            # If the migration function doesn't exist, log an error and return the current config
            if migration_func is None:
                logger.error(f"Migration function {migration_func_name} not found")
                return migrated_config
            
            # Apply the migration
            logger.info(f"Migrating configuration from {from_version} to {to_version}")
            migrated_config = migration_func(migrated_config)
        
        return migrated_config
    
    except Exception as e:
        logger.error(f"Error migrating configuration: {e}", exc_info=True)
        return config


def backup_config(config_path: str) -> Optional[str]:
    """
    Create a backup of a configuration file.
    
    Args:
        config_path: The path to the configuration file.
        
    Returns:
        The path to the backup file, or None if the backup could not be created.
    """
    try:
        import shutil
        from datetime import datetime
        
        # Create backup path
        backup_dir = os.path.join(os.path.dirname(config_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"config_{timestamp}.yaml"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the file
        shutil.copy2(config_path, backup_path)
        
        return backup_path
    
    except Exception as e:
        logger.error(f"Error backing up configuration: {e}", exc_info=True)
        return None


def migrate_config_file(config_path: str, target_version: str) -> bool:
    """
    Migrate a configuration file to a target version.
    
    Args:
        config_path: The path to the configuration file.
        target_version: The target version.
        
    Returns:
        True if the migration was successful, False otherwise.
    """
    try:
        # Check if the file exists
        if not os.path.isfile(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            return False
        
        # Load the configuration
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if config is None:
            config = {}
        
        # Get the current version
        current_version = get_config_version(config)
        
        # If the current version is already the target version, no migration is needed
        if compare_versions(current_version, target_version) == 0:
            logger.info(f"Configuration is already at version {target_version}")
            return True
        
        # Create a backup
        backup_path = backup_config(config_path)
        if backup_path is None:
            logger.error("Failed to create backup, aborting migration")
            return False
        
        # Migrate the configuration
        migrated_config = migrate_config(config, target_version)
        
        # Save the migrated configuration
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(migrated_config, f, default_flow_style=False)
        
        logger.info(f"Configuration migrated from {current_version} to {target_version}")
        logger.info(f"Backup created at {backup_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error migrating configuration file: {e}", exc_info=True)
        return False
