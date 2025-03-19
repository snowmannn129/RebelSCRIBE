#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Base View Model

This module provides the base view model class for the MVVM architecture.
"""

from typing import Any, Dict, Optional, List, Set, Callable

from src.utils.logging_utils import get_logger
from src.ui.event_bus import get_event_bus
from src.ui.state_manager import get_state_manager
from src.ui.error_handler import get_error_handler

logger = get_logger(__name__)


class BaseViewModel:
    """
    Base class for all view models in the application.
    
    This class provides common functionality for view models, including
    access to the event bus, state manager, and error handler.
    """
    
    def __init__(self):
        """Initialize the view model."""
        self.event_bus = get_event_bus()
        self.state_manager = get_state_manager()
        self.error_handler = get_error_handler()
        self._property_changed_handlers: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._is_initialized = False
        logger.debug(f"{self.__class__.__name__} initialized")
    
    def initialize(self) -> None:
        """
        Initialize the view model.
        
        This method should be called after the view model is created and
        before it is used. It is responsible for setting up event handlers
        and loading initial state.
        
        Subclasses should override this method to perform their own
        initialization, but should call the parent method first.
        """
        if self._is_initialized:
            logger.warning(f"{self.__class__.__name__} already initialized")
            return
        
        self._register_event_handlers()
        self._load_state()
        self._is_initialized = True
        logger.debug(f"{self.__class__.__name__} initialization completed")
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the view model.
        
        This method should be called when the view model is no longer needed.
        It is responsible for unregistering event handlers and saving state.
        
        Subclasses should override this method to perform their own cleanup,
        but should call the parent method last.
        """
        if not self._is_initialized:
            logger.warning(f"{self.__class__.__name__} not initialized, nothing to clean up")
            return
        
        self._unregister_event_handlers()
        self._save_state()
        self._is_initialized = False
        logger.debug(f"{self.__class__.__name__} cleanup completed")
    
    def _register_event_handlers(self) -> None:
        """
        Register event handlers for the view model.
        
        This method should be overridden by subclasses to register
        event handlers for the events they are interested in.
        """
        pass
    
    def _unregister_event_handlers(self) -> None:
        """
        Unregister event handlers for the view model.
        
        This method should be overridden by subclasses to unregister
        event handlers that were registered in _register_event_handlers.
        """
        pass
    
    def _load_state(self) -> None:
        """
        Load state for the view model.
        
        This method should be overridden by subclasses to load
        state from the state manager.
        """
        pass
    
    def _save_state(self) -> None:
        """
        Save state for the view model.
        
        This method should be overridden by subclasses to save
        state to the state manager.
        """
        pass
    
    def register_property_changed_handler(self, property_name: str, handler: Callable[[str, Any], None]) -> None:
        """
        Register a handler for property changed events.
        
        Args:
            property_name: The name of the property to watch for changes.
            handler: The handler to call when the property changes.
                The handler should accept two arguments: the property name and the new value.
        """
        if property_name not in self._property_changed_handlers:
            self._property_changed_handlers[property_name] = []
        
        if handler not in self._property_changed_handlers[property_name]:
            self._property_changed_handlers[property_name].append(handler)
            logger.debug(f"Registered property changed handler for {property_name}")
    
    def unregister_property_changed_handler(self, property_name: str, handler: Callable[[str, Any], None]) -> None:
        """
        Unregister a handler for property changed events.
        
        Args:
            property_name: The name of the property the handler was registered for.
            handler: The handler to unregister.
        """
        if property_name in self._property_changed_handlers and handler in self._property_changed_handlers[property_name]:
            self._property_changed_handlers[property_name].remove(handler)
            logger.debug(f"Unregistered property changed handler for {property_name}")
            
            if not self._property_changed_handlers[property_name]:
                del self._property_changed_handlers[property_name]
    
    def notify_property_changed(self, property_name: str, value: Any) -> None:
        """
        Notify handlers that a property has changed.
        
        Args:
            property_name: The name of the property that changed.
            value: The new value of the property.
        """
        if property_name in self._property_changed_handlers:
            for handler in self._property_changed_handlers[property_name]:
                try:
                    handler(property_name, value)
                except Exception as e:
                    logger.error(f"Error in property changed handler for {property_name}: {str(e)}")
                    self.error_handler.handle_exception(
                        e, 
                        f"Error in property changed handler for {property_name}"
                    )
    
    def handle_error(self, error_type: str, error_message: str) -> None:
        """
        Handle an error in the view model.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
        """
        logger.error(f"{error_type}: {error_message}")
        self.error_handler.handle_error(error_type, error_message)
    
    def handle_exception(self, exception: Exception, context: Optional[str] = None) -> None:
        """
        Handle an exception in the view model.
        
        Args:
            exception: The exception to handle.
            context: Optional context information about where the exception occurred.
        """
        logger.error(f"Exception in {context or self.__class__.__name__}: {str(exception)}")
        self.error_handler.handle_exception(exception, context or self.__class__.__name__)
