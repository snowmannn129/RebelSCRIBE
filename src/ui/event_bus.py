#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - UI Event Bus

This module implements a central event bus for UI component communication.
It allows components to communicate without direct dependencies, making
the code more modular and testable.

The enhanced version includes:
- Improved event typing using a class-based event system
- Event filtering capabilities
- Event logging for debugging
- Event history for troubleshooting
- Event prioritization for critical events
"""

from typing import Dict, List, Callable, Any, Optional, Set, Type, TypeVar, Generic, Union
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
import inspect
import weakref
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class EventPriority(Enum):
    """Event priority levels."""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class EventCategory(Enum):
    """Event categories for filtering."""
    DOCUMENT = auto()
    PROJECT = auto()
    UI = auto()
    ERROR = auto()
    SYSTEM = auto()
    CUSTOM = auto()


@dataclass
class EventMetadata:
    """Metadata for events."""
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    category: EventCategory = EventCategory.CUSTOM


@dataclass
class BaseEvent:
    """Base class for all events."""
    metadata: EventMetadata = field(default_factory=EventMetadata)


# Document Events
@dataclass
class DocumentSelectedEvent(BaseEvent):
    """Event emitted when a document is selected."""
    document_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.DOCUMENT


@dataclass
class DocumentLoadedEvent(BaseEvent):
    """Event emitted when a document is loaded."""
    document_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.DOCUMENT


@dataclass
class DocumentSavedEvent(BaseEvent):
    """Event emitted when a document is saved."""
    document_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.DOCUMENT


@dataclass
class DocumentModifiedEvent(BaseEvent):
    """Event emitted when a document is modified."""
    document_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.DOCUMENT


@dataclass
class DocumentCreatedEvent(BaseEvent):
    """Event emitted when a document is created."""
    document_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.DOCUMENT


@dataclass
class DocumentDeletedEvent(BaseEvent):
    """Event emitted when a document is deleted."""
    document_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.DOCUMENT


# Project Events
@dataclass
class ProjectLoadedEvent(BaseEvent):
    """Event emitted when a project is loaded."""
    project_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.PROJECT


@dataclass
class ProjectSavedEvent(BaseEvent):
    """Event emitted when a project is saved."""
    project_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.PROJECT


@dataclass
class ProjectClosedEvent(BaseEvent):
    """Event emitted when a project is closed."""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.PROJECT


@dataclass
class ProjectCreatedEvent(BaseEvent):
    """Event emitted when a project is created."""
    project_id: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.PROJECT


# UI Events
@dataclass
class UIThemeChangedEvent(BaseEvent):
    """Event emitted when the UI theme is changed."""
    theme_name: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.UI


@dataclass
class UIStateChangedEvent(BaseEvent):
    """Event emitted when the UI state is changed."""
    state_key: str = ""
    state_value: Any = None
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.UI


# Error Events
@dataclass
class ErrorOccurredEvent(BaseEvent):
    """Event emitted when an error occurs."""
    error_type: str = ""
    error_message: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.ERROR
        self.metadata.priority = EventPriority.HIGH


# Component Events
@dataclass
class ComponentRegisteredEvent(BaseEvent):
    """Event emitted when a component is registered."""
    component_id: str = ""
    component_type: str = ""
    component_name: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.SYSTEM
        self.metadata.priority = EventPriority.NORMAL


@dataclass
class ComponentUnregisteredEvent(BaseEvent):
    """Event emitted when a component is unregistered."""
    component_id: str = ""
    component_type: str = ""
    component_name: str = ""
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Initialize metadata."""
        self.metadata.category = EventCategory.SYSTEM
        self.metadata.priority = EventPriority.NORMAL


# Type for event handlers
T = TypeVar('T', bound=BaseEvent)
EventHandler = Callable[[T], None]


class EventFilter:
    """Filter for events."""
    
    def __init__(self, 
                 categories: Optional[Set[EventCategory]] = None,
                 priorities: Optional[Set[EventPriority]] = None,
                 event_types: Optional[Set[Type[BaseEvent]]] = None):
        """
        Initialize the event filter.
        
        Args:
            categories: Set of event categories to include, or None to include all.
            priorities: Set of event priorities to include, or None to include all.
            event_types: Set of event types to include, or None to include all.
        """
        self.categories = categories
        self.priorities = priorities
        self.event_types = event_types
    
    def matches(self, event: BaseEvent) -> bool:
        """
        Check if an event matches this filter.
        
        Args:
            event: The event to check.
            
        Returns:
            True if the event matches this filter, False otherwise.
        """
        # Check category
        if self.categories is not None and event.metadata.category not in self.categories:
            return False
        
        # Check priority
        if self.priorities is not None and event.metadata.priority not in self.priorities:
            return False
        
        # Check event type
        if self.event_types is not None and type(event) not in self.event_types:
            return False
        
        return True


class UIEventBus(QObject):
    """
    Central event bus for UI component communication.
    
    This class provides a way for UI components to communicate without
    direct dependencies, making the code more modular and testable.
    
    The enhanced version includes:
    - Improved event typing using a class-based event system
    - Event filtering capabilities
    - Event logging for debugging
    - Event history for troubleshooting
    - Event prioritization for critical events
    """
    
    # Legacy signals for backward compatibility
    document_selected = pyqtSignal(str)  # document_id
    document_loaded = pyqtSignal(str)    # document_id
    document_saved = pyqtSignal(str)     # document_id
    document_modified = pyqtSignal(str)  # document_id
    document_created = pyqtSignal(str)   # document_id
    document_deleted = pyqtSignal(str)   # document_id
    
    project_loaded = pyqtSignal(str)     # project_id
    project_saved = pyqtSignal(str)      # project_id
    project_closed = pyqtSignal()
    project_created = pyqtSignal(str)    # project_id
    
    ui_theme_changed = pyqtSignal(str)   # theme_name
    ui_state_changed = pyqtSignal(str, object)  # state_key, state_value
    
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    
    # New signal for typed events
    event_emitted = pyqtSignal(object)  # event
    
    def __init__(self, max_history_size: int = 100):
        """
        Initialize the event bus.
        
        Args:
            max_history_size: Maximum number of events to keep in history.
        """
        super().__init__()
        
        # Dictionary of event type to list of handlers
        self._handlers: Dict[Type[BaseEvent], List[weakref.WeakMethod]] = {}
        
        # Dictionary of event type to list of filters and handlers
        self._filtered_handlers: Dict[Type[BaseEvent], List[tuple[EventFilter, weakref.WeakMethod]]] = {}
        
        # Event history
        self._history: deque = deque(maxlen=max_history_size)
        
        # Debug mode flag
        self._debug_mode = False
        
        logger.debug("Enhanced UI Event Bus initialized")
    
    def set_debug_mode(self, enabled: bool) -> None:
        """
        Enable or disable debug mode.
        
        In debug mode, all events are logged at debug level.
        
        Args:
            enabled: Whether to enable debug mode.
        """
        self._debug_mode = enabled
        logger.debug(f"Event bus debug mode {'enabled' if enabled else 'disabled'}")
    
    def register_handler(self, event_type: Type[T], handler: EventHandler[T]) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: The type of event to handle.
            handler: The handler function to call when an event of this type is emitted.
                The handler should accept one argument: the event object.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        # Use weak references to allow handlers to be garbage collected
        handler_ref = weakref.WeakMethod(handler) if inspect.ismethod(handler) else weakref.ref(handler)
        
        if handler_ref not in self._handlers[event_type]:
            self._handlers[event_type].append(handler_ref)
            logger.debug(f"Registered handler for {event_type.__name__}")
    
    def register_filtered_handler(self, event_type: Type[T], handler: EventHandler[T], 
                                 filter: EventFilter) -> None:
        """
        Register a handler for a specific event type with a filter.
        
        Args:
            event_type: The type of event to handle.
            handler: The handler function to call when an event of this type is emitted
                and matches the filter. The handler should accept one argument: the event object.
            filter: The filter to apply to events before calling the handler.
        """
        if event_type not in self._filtered_handlers:
            self._filtered_handlers[event_type] = []
        
        # Use weak references to allow handlers to be garbage collected
        handler_ref = weakref.WeakMethod(handler) if inspect.ismethod(handler) else weakref.ref(handler)
        
        self._filtered_handlers[event_type].append((filter, handler_ref))
        logger.debug(f"Registered filtered handler for {event_type.__name__}")
    
    def unregister_handler(self, event_type: Type[BaseEvent], handler: Callable) -> None:
        """
        Unregister a handler for a specific event type.
        
        Args:
            event_type: The type of event the handler was registered for.
            handler: The handler function to unregister.
        """
        if event_type in self._handlers:
            # Create a new list without the handler
            self._handlers[event_type] = [h for h in self._handlers[event_type] 
                                         if h() is not None and h() != handler]
            
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            
            logger.debug(f"Unregistered handler for {event_type.__name__}")
    
    def unregister_filtered_handler(self, event_type: Type[BaseEvent], handler: Callable) -> None:
        """
        Unregister a filtered handler for a specific event type.
        
        Args:
            event_type: The type of event the handler was registered for.
            handler: The handler function to unregister.
        """
        if event_type in self._filtered_handlers:
            # Create a new list without the handler
            self._filtered_handlers[event_type] = [
                (f, h) for f, h in self._filtered_handlers[event_type]
                if h() is not None and h() != handler
            ]
            
            if not self._filtered_handlers[event_type]:
                del self._filtered_handlers[event_type]
            
            logger.debug(f"Unregistered filtered handler for {event_type.__name__}")
    
    def emit_event(self, event: BaseEvent) -> None:
        """
        Emit an event.
        
        Args:
            event: The event to emit.
        """
        # Set source if not already set
        if not event.metadata.source:
            # Try to get the caller's module and function name
            frame = inspect.currentframe()
            if frame:
                frame = frame.f_back  # Get the caller's frame
                if frame:
                    module = inspect.getmodule(frame)
                    if module:
                        event.metadata.source = f"{module.__name__}.{frame.f_code.co_name}"
        
        # Add to history
        self._history.append(event)
        
        # Log the event if in debug mode
        if self._debug_mode:
            logger.debug(f"Emitting event: {type(event).__name__} - {event}")
        
        # Emit the event signal
        self.event_emitted.emit(event)
        
        # Call handlers for this event type
        event_type = type(event)
        
        # Call direct handlers
        if event_type in self._handlers:
            for handler_ref in self._handlers[event_type]:
                handler = handler_ref()
                if handler is not None:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {str(e)}")
        
        # Call filtered handlers
        if event_type in self._filtered_handlers:
            for filter, handler_ref in self._filtered_handlers[event_type]:
                if filter.matches(event):
                    handler = handler_ref()
                    if handler is not None:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error(f"Error in filtered event handler: {str(e)}")
        
        # Emit legacy signals for backward compatibility
        self._emit_legacy_signals(event)
    
    def _emit_legacy_signals(self, event: BaseEvent) -> None:
        """
        Emit legacy signals for backward compatibility.
        
        Args:
            event: The event to emit legacy signals for.
        """
        if isinstance(event, DocumentSelectedEvent):
            self.document_selected.emit(event.document_id)
        elif isinstance(event, DocumentLoadedEvent):
            self.document_loaded.emit(event.document_id)
        elif isinstance(event, DocumentSavedEvent):
            self.document_saved.emit(event.document_id)
        elif isinstance(event, DocumentModifiedEvent):
            self.document_modified.emit(event.document_id)
        elif isinstance(event, DocumentCreatedEvent):
            self.document_created.emit(event.document_id)
        elif isinstance(event, DocumentDeletedEvent):
            self.document_deleted.emit(event.document_id)
        elif isinstance(event, ProjectLoadedEvent):
            self.project_loaded.emit(event.project_id)
        elif isinstance(event, ProjectSavedEvent):
            self.project_saved.emit(event.project_id)
        elif isinstance(event, ProjectClosedEvent):
            self.project_closed.emit()
        elif isinstance(event, ProjectCreatedEvent):
            self.project_created.emit(event.project_id)
        elif isinstance(event, UIThemeChangedEvent):
            self.ui_theme_changed.emit(event.theme_name)
        elif isinstance(event, UIStateChangedEvent):
            self.ui_state_changed.emit(event.state_key, event.state_value)
        elif isinstance(event, ErrorOccurredEvent):
            self.error_occurred.emit(event.error_type, event.error_message)
    
    def get_history(self, max_events: Optional[int] = None, 
                   filter: Optional[EventFilter] = None) -> List[BaseEvent]:
        """
        Get the event history.
        
        Args:
            max_events: Maximum number of events to return, or None to return all.
            filter: Filter to apply to events, or None to return all.
            
        Returns:
            List of events in the history, newest first.
        """
        if filter is None:
            events = list(self._history)
        else:
            events = [e for e in self._history if filter.matches(e)]
        
        if max_events is not None:
            events = events[-max_events:]
        
        return events
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()
        logger.debug("Event history cleared")
    
    # Legacy methods for backward compatibility
    
    def emit_document_selected(self, document_id: str) -> None:
        """
        Emit document selected event.
        
        Args:
            document_id: The ID of the selected document.
        """
        logger.debug(f"Emitting document_selected event: {document_id}")
        self.emit_event(DocumentSelectedEvent(document_id=document_id))
    
    def emit_document_loaded(self, document_id: str) -> None:
        """
        Emit document loaded event.
        
        Args:
            document_id: The ID of the loaded document.
        """
        logger.debug(f"Emitting document_loaded event: {document_id}")
        self.emit_event(DocumentLoadedEvent(document_id=document_id))
    
    def emit_document_saved(self, document_id: str) -> None:
        """
        Emit document saved event.
        
        Args:
            document_id: The ID of the saved document.
        """
        logger.debug(f"Emitting document_saved event: {document_id}")
        self.emit_event(DocumentSavedEvent(document_id=document_id))
    
    def emit_document_modified(self, document_id: str) -> None:
        """
        Emit document modified event.
        
        Args:
            document_id: The ID of the modified document.
        """
        logger.debug(f"Emitting document_modified event: {document_id}")
        self.emit_event(DocumentModifiedEvent(document_id=document_id))
    
    def emit_document_created(self, document_id: str) -> None:
        """
        Emit document created event.
        
        Args:
            document_id: The ID of the created document.
        """
        logger.debug(f"Emitting document_created event: {document_id}")
        self.emit_event(DocumentCreatedEvent(document_id=document_id))
    
    def emit_document_deleted(self, document_id: str) -> None:
        """
        Emit document deleted event.
        
        Args:
            document_id: The ID of the deleted document.
        """
        logger.debug(f"Emitting document_deleted event: {document_id}")
        self.emit_event(DocumentDeletedEvent(document_id=document_id))
    
    def emit_project_loaded(self, project_id: str) -> None:
        """
        Emit project loaded event.
        
        Args:
            project_id: The ID of the loaded project.
        """
        logger.debug(f"Emitting project_loaded event: {project_id}")
        self.emit_event(ProjectLoadedEvent(project_id=project_id))
    
    def emit_project_saved(self, project_id: str) -> None:
        """
        Emit project saved event.
        
        Args:
            project_id: The ID of the saved project.
        """
        logger.debug(f"Emitting project_saved event: {project_id}")
        self.emit_event(ProjectSavedEvent(project_id=project_id))
    
    def emit_project_closed(self) -> None:
        """Emit project closed event."""
        logger.debug("Emitting project_closed event")
        self.emit_event(ProjectClosedEvent())
    
    def emit_project_created(self, project_id: str) -> None:
        """
        Emit project created event.
        
        Args:
            project_id: The ID of the created project.
        """
        logger.debug(f"Emitting project_created event: {project_id}")
        self.emit_event(ProjectCreatedEvent(project_id=project_id))
    
    def emit_ui_theme_changed(self, theme_name: str) -> None:
        """
        Emit UI theme changed event.
        
        Args:
            theme_name: The name of the new theme.
        """
        logger.debug(f"Emitting ui_theme_changed event: {theme_name}")
        self.emit_event(UIThemeChangedEvent(theme_name=theme_name))
    
    def emit_ui_state_changed(self, state_key: str, state_value: Any) -> None:
        """
        Emit UI state changed event.
        
        Args:
            state_key: The key of the changed state.
            state_value: The new value of the state.
        """
        logger.debug(f"Emitting ui_state_changed event: {state_key}={state_value}")
        self.emit_event(UIStateChangedEvent(state_key=state_key, state_value=state_value))
    
    def emit_error_occurred(self, error_type: str, error_message: str) -> None:
        """
        Emit error occurred event.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
        """
        logger.debug(f"Emitting error_occurred event: {error_type}: {error_message}")
        event = ErrorOccurredEvent(error_type=error_type, error_message=error_message)
        self.emit_event(event)


# Create a singleton instance of the event bus
_instance: Optional[UIEventBus] = None

def get_event_bus() -> UIEventBus:
    """
    Get the singleton instance of the event bus.
    
    Returns:
        The event bus instance.
    """
    global _instance
    if _instance is None:
        _instance = UIEventBus()
    return _instance
