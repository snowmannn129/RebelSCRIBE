#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Base View

This module provides the base view class for the MVVM architecture.
"""

from typing import Any, Dict, Optional, List, Callable, Type, TypeVar, Generic

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from src.utils.logging_utils import get_logger
from src.ui.event_bus import get_event_bus
from src.ui.state_manager import get_state_manager
from src.ui.error_handler import get_error_handler
from src.ui.base_view_model import BaseViewModel

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseViewModel)


class BaseView(QWidget, Generic[T]):
    """
    Base class for all views in the application.
    
    This class provides common functionality for views, including
    access to the event bus, state manager, and error handler.
    It also provides a framework for connecting views to view models.
    """
    
    # Signal emitted when the view is about to be closed
    closing = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None, view_model_class: Optional[Type[T]] = None):
        """
        Initialize the view.
        
        Args:
            parent: The parent widget.
            view_model_class: The class of the view model to create.
                If None, no view model will be created automatically.
        """
        super().__init__(parent)
        
        # Get common services
        self.event_bus = get_event_bus()
        self.state_manager = get_state_manager()
        self.error_handler = get_error_handler()
        
        # Initialize view model
        self.view_model: Optional[T] = None
        if view_model_class is not None:
            self.view_model = view_model_class()
        
        # Initialize UI
        self._is_initialized = False
        self.init_ui()
        
        # Connect view model if available
        if self.view_model is not None:
            self.connect_view_model()
            self.view_model.initialize()
        
        self._is_initialized = True
        logger.debug(f"{self.__class__.__name__} initialized")
    
    def init_ui(self) -> None:
        """
        Initialize the UI components.
        
        This method should be overridden by subclasses to create
        and configure their UI components.
        """
        # Create a default layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
    
    def connect_view_model(self) -> None:
        """
        Connect the view to the view model.
        
        This method should be overridden by subclasses to connect
        their UI components to the view model's properties and methods.
        """
        if self.view_model is None:
            logger.warning(f"{self.__class__.__name__} has no view model to connect")
            return
        
        # Connect property changed handlers
        self._connect_property_changed_handlers()
    
    def _connect_property_changed_handlers(self) -> None:
        """
        Connect handlers for property changed events from the view model.
        
        This method should be overridden by subclasses to register
        handlers for the view model's property changed events.
        """
        pass
    
    def update_view(self) -> None:
        """
        Update the view based on the view model state.
        
        This method should be overridden by subclasses to update
        their UI components based on the current state of the view model.
        """
        pass
    
    def show_error(self, error_type: str, error_message: str) -> None:
        """
        Show an error message to the user.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
        """
        QMessageBox.critical(
            self,
            f"Error: {error_type}",
            error_message
        )
    
    def show_warning(self, warning_title: str, warning_message: str) -> None:
        """
        Show a warning message to the user.
        
        Args:
            warning_title: The title of the warning.
            warning_message: The warning message.
        """
        QMessageBox.warning(
            self,
            warning_title,
            warning_message
        )
    
    def show_info(self, info_title: str, info_message: str) -> None:
        """
        Show an information message to the user.
        
        Args:
            info_title: The title of the information.
            info_message: The information message.
        """
        QMessageBox.information(
            self,
            info_title,
            info_message
        )
    
    def show_confirmation(self, confirm_title: str, confirm_message: str) -> bool:
        """
        Show a confirmation dialog to the user.
        
        Args:
            confirm_title: The title of the confirmation.
            confirm_message: The confirmation message.
            
        Returns:
            True if the user confirmed, False otherwise.
        """
        result = QMessageBox.question(
            self,
            confirm_title,
            confirm_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        return result == QMessageBox.StandardButton.Yes
    
    def closeEvent(self, event) -> None:
        """
        Handle the close event.
        
        This method is called when the view is about to be closed.
        It emits the closing signal and cleans up the view model.
        
        Args:
            event: The close event.
        """
        # Emit closing signal
        self.closing.emit()
        
        # Clean up view model
        if self.view_model is not None:
            self.view_model.cleanup()
        
        # Accept the event
        event.accept()
        
        logger.debug(f"{self.__class__.__name__} closed")
    
    def sizeHint(self) -> QSize:
        """
        Get the recommended size for the view.
        
        Returns:
            The recommended size.
        """
        return QSize(400, 300)
