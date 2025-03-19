#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Error Handler Initialization

This module initializes and configures the enhanced error handler.
It should be imported early in the application startup process.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QApplication

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ui.enhanced_error_handler import (
    ErrorSeverity, DialogType, NotificationPosition, get_enhanced_error_handler
)
from src.ui.error_handler_integration import replace_error_handler

logger = get_logger(__name__)
config = ConfigManager()


def initialize_error_handler(app: Optional[QApplication] = None) -> None:
    """
    Initialize and configure the enhanced error handler.
    
    This function should be called early in the application startup process,
    before any other code that might use the error handler.
    
    Args:
        app: The QApplication instance, if available.
    """
    logger.info("Initializing enhanced error handler")
    
    # Get enhanced error handler instance
    error_handler = get_enhanced_error_handler()
    
    # Configure UI treatments based on config
    _configure_ui_treatments(error_handler)
    
    # Configure error aggregation
    _configure_error_aggregation(error_handler)
    
    # Configure rate limiting
    _configure_rate_limiting(error_handler)
    
    # Configure notification manager
    _configure_notification_manager(error_handler)
    
    # Replace original error handler with enhanced one
    replace_error_handler()
    
    logger.info("Enhanced error handler initialized and configured")


def _configure_ui_treatments(error_handler) -> None:
    """
    Configure UI treatments for different error severities.
    
    Args:
        error_handler: The enhanced error handler instance.
    """
    # Get UI treatment configuration from config
    ui_treatments = config.get("error_handler", "ui_treatments", {})
    
    # Default UI treatments if not configured
    if not ui_treatments:
        ui_treatments = {
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
        }
    
    # Configure UI treatments for each severity
    for severity_name, treatment in ui_treatments.items():
        try:
            # Convert string values to enums
            severity = ErrorSeverity.from_string(severity_name)
            dialog_type = _get_dialog_type(treatment.get("dialog_type", "MODAL"))
            position = _get_notification_position(treatment.get("position"))
            
            # Configure UI treatment
            error_handler.configure_ui_treatment(
                severity=severity,
                dialog_type=dialog_type,
                use_non_blocking=treatment.get("use_non_blocking", False),
                timeout=treatment.get("timeout"),
                position=position
            )
            
            logger.debug(f"Configured UI treatment for severity {severity_name}")
        except Exception as e:
            logger.error(f"Error configuring UI treatment for severity {severity_name}: {e}")


def _configure_error_aggregation(error_handler) -> None:
    """
    Configure error aggregation.
    
    Args:
        error_handler: The enhanced error handler instance.
    """
    # Get error aggregation configuration from config
    aggregation_config = config.get("error_handler", "error_aggregation", {})
    
    # Default configuration if not configured
    if not aggregation_config:
        aggregation_config = {
            "enabled": True,
            "timeout": 5000,
            "pattern_matching": False
        }
    
    # Configure error aggregation
    error_handler.enable_error_aggregation(
        enabled=aggregation_config.get("enabled", True),
        timeout=aggregation_config.get("timeout", 5000),
        pattern_matching=aggregation_config.get("pattern_matching", False)
    )
    
    logger.debug("Configured error aggregation")


def _configure_rate_limiting(error_handler) -> None:
    """
    Configure rate limiting.
    
    Args:
        error_handler: The enhanced error handler instance.
    """
    # Get rate limiting configuration from config
    rate_limiting_config = config.get("error_handler", "rate_limiting", {})
    
    # Default configuration if not configured
    if not rate_limiting_config:
        rate_limiting_config = {
            "enabled": True,
            "threshold": 5,
            "time_window": 60000,
            "use_exponential_backoff": True
        }
    
    # Configure rate limiting if enabled
    if rate_limiting_config.get("enabled", True):
        error_handler.configure_rate_limiting(
            threshold=rate_limiting_config.get("threshold", 5),
            time_window=rate_limiting_config.get("time_window", 60000),
            use_exponential_backoff=rate_limiting_config.get("use_exponential_backoff", True)
        )
        
        logger.debug("Configured rate limiting")


def _configure_notification_manager(error_handler) -> None:
    """
    Configure notification manager.
    
    Args:
        error_handler: The enhanced error handler instance.
    """
    # Get notification manager configuration from config
    notification_config = config.get("error_handler", "notification_manager", {})
    
    # Default configuration if not configured
    if not notification_config:
        notification_config = {
            "max_notifications": 5,
            "spacing": 10,
            "animation_duration": 250,
            "fade_effect": True,
            "slide_effect": True,
            "stacking_order": "newest_on_top"
        }
    
    # Configure notification manager
    error_handler.notification_manager.configure(
        max_notifications=notification_config.get("max_notifications", 5),
        spacing=notification_config.get("spacing", 10),
        animation_duration=notification_config.get("animation_duration", 250),
        fade_effect=notification_config.get("fade_effect", True),
        slide_effect=notification_config.get("slide_effect", True),
        stacking_order=notification_config.get("stacking_order", "newest_on_top")
    )
    
    # Configure default timeouts
    timeouts = notification_config.get("default_timeouts", {})
    for severity_name, timeout in timeouts.items():
        try:
            severity = ErrorSeverity.from_string(severity_name)
            error_handler.notification_manager.set_default_timeout(severity, timeout)
        except Exception as e:
            logger.error(f"Error configuring notification timeout for severity {severity_name}: {e}")
    
    logger.debug("Configured notification manager")


def _get_dialog_type(dialog_type_str: str) -> DialogType:
    """
    Convert dialog type string to DialogType enum.
    
    Args:
        dialog_type_str: The dialog type string.
        
    Returns:
        The DialogType enum value.
    """
    dialog_type_map = {
        "MODAL": DialogType.MODAL,
        "NON_MODAL": DialogType.NON_MODAL,
        "NOTIFICATION": DialogType.NOTIFICATION
    }
    
    return dialog_type_map.get(dialog_type_str.upper(), DialogType.MODAL)


def _get_notification_position(position_str: Optional[str]) -> Optional[NotificationPosition]:
    """
    Convert position string to NotificationPosition enum.
    
    Args:
        position_str: The position string.
        
    Returns:
        The NotificationPosition enum value, or None if position_str is None.
    """
    if position_str is None:
        return None
    
    position_map = {
        "TOP_RIGHT": NotificationPosition.TOP_RIGHT,
        "TOP_LEFT": NotificationPosition.TOP_LEFT,
        "BOTTOM_RIGHT": NotificationPosition.BOTTOM_RIGHT,
        "BOTTOM_LEFT": NotificationPosition.BOTTOM_LEFT,
        "CENTER": NotificationPosition.CENTER
    }
    
    return position_map.get(position_str.upper(), NotificationPosition.TOP_RIGHT)
