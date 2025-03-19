#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - UI Component Registry

This module implements a central registry for UI components, allowing for
dynamic component loading, instantiation, dependency resolution, lifecycle
management, and configuration.
"""

import importlib
import inspect
import logging
import os
import sys
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

from src.utils.logging_utils import get_logger
from src.ui.event_bus import get_event_bus, ComponentRegisteredEvent, ComponentUnregisteredEvent
from src.ui.state_manager import get_state_manager
from src.ui.error_handler import get_error_handler

logger = get_logger(__name__)

# Type variable for component classes
T = TypeVar('T')


class ComponentState(Enum):
    """Enum for component lifecycle states."""
    REGISTERED = auto()  # Component is registered but not initialized
    INITIALIZING = auto()  # Component is being initialized
    INITIALIZED = auto()  # Component is initialized and ready
    ACTIVE = auto()  # Component is active and in use
    INACTIVE = auto()  # Component is initialized but not active
    DISPOSING = auto()  # Component is being disposed
    DISPOSED = auto()  # Component is disposed and no longer usable
    ERROR = auto()  # Component is in an error state


class ComponentScope(Enum):
    """Enum for component scopes."""
    SINGLETON = auto()  # Single instance for the entire application
    TRANSIENT = auto()  # New instance created each time
    SCOPED = auto()  # Single instance per scope (e.g., per window)


class ComponentType(Enum):
    """Enum for component types."""
    VIEW = auto()  # UI view component
    VIEW_MODEL = auto()  # View model component
    SERVICE = auto()  # Service component
    UTILITY = auto()  # Utility component
    DIALOG = auto()  # Dialog component
    CUSTOM = auto()  # Custom component type


class ComponentMetadata:
    """Class for storing component metadata."""
    
    def __init__(self,
                 component_id: str,
                 component_type: ComponentType,
                 component_class: Type,
                 name: str,
                 description: Optional[str] = None,
                 version: str = "1.0.0",
                 scope: ComponentScope = ComponentScope.SINGLETON,
                 dependencies: Optional[List[str]] = None,
                 tags: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None,
                 factory: Optional[Callable[..., Any]] = None):
        """
        Initialize component metadata.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type of the component
            component_class: Class of the component
            name: Human-readable name of the component
            description: Description of the component
            version: Version of the component
            scope: Scope of the component
            dependencies: List of component IDs that this component depends on
            tags: List of tags for categorizing the component
            config: Configuration for the component
            factory: Factory function for creating the component
        """
        self.component_id = component_id
        self.component_type = component_type
        self.component_class = component_class
        self.name = name
        self.description = description
        self.version = version
        self.scope = scope
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.config = config or {}
        self.factory = factory
        self.state = ComponentState.REGISTERED
        self.instance = None
        self.error = None
        self.parent_id = None
        self.children_ids = []
        self.created_at = None
        self.initialized_at = None
        self.disposed_at = None
        self.last_active_at = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            'component_id': self.component_id,
            'component_type': self.component_type.name,
            'component_class': self.component_class.__name__,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'scope': self.scope.name,
            'dependencies': self.dependencies,
            'tags': self.tags,
            'config': self.config,
            'state': self.state.name,
            'parent_id': self.parent_id,
            'children_ids': self.children_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'initialized_at': self.initialized_at.isoformat() if self.initialized_at else None,
            'disposed_at': self.disposed_at.isoformat() if self.disposed_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None,
        }


class ComponentRegistry(QObject):
    """
    Central registry for UI components.
    
    This class provides a way to register, discover, instantiate, and manage
    UI components dynamically.
    """
    
    # Define signals for component events
    component_registered = pyqtSignal(str)  # component_id
    component_unregistered = pyqtSignal(str)  # component_id
    component_initialized = pyqtSignal(str)  # component_id
    component_disposed = pyqtSignal(str)  # component_id
    component_state_changed = pyqtSignal(str, object)  # component_id, new_state
    component_error = pyqtSignal(str, str)  # component_id, error_message
    
    def __init__(self, parent=None):
        """
        Initialize the component registry.
        
        Args:
            parent: The parent QObject
        """
        super().__init__(parent)
        
        # Initialize component registry
        self.components: Dict[str, ComponentMetadata] = {}
        
        # Initialize component instances
        self.instances: Dict[str, Any] = {}
        
        # Initialize component scopes
        self.scopes: Dict[str, Dict[str, Any]] = {}
        
        # Initialize component dependencies
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Initialize component tags
        self.tags: Dict[str, Set[str]] = {}
        
        # Initialize component types
        self.component_types: Dict[ComponentType, Set[str]] = {
            component_type: set() for component_type in ComponentType
        }
        
        # Get event bus instance
        self.event_bus = get_event_bus()
        
        # Get state manager instance
        self.state_manager = get_state_manager()
        
        # Get error handler instance
        self.error_handler = get_error_handler()
        
        # Initialize component discovery paths
        self.discovery_paths: List[str] = []
        
        # Initialize component factories
        self.factories: Dict[str, Callable[..., Any]] = {}
        
        # Initialize component configurations
        self.configurations: Dict[str, Dict[str, Any]] = {}
        
        # Initialize component lifecycle hooks
        self.lifecycle_hooks: Dict[str, Dict[str, List[Callable]]] = {}
        
        logger.debug("Component Registry initialized")
    
    def register_component(self,
                          component_id: str,
                          component_class: Type[T],
                          component_type: ComponentType,
                          name: Optional[str] = None,
                          description: Optional[str] = None,
                          version: str = "1.0.0",
                          scope: ComponentScope = ComponentScope.SINGLETON,
                          dependencies: Optional[List[str]] = None,
                          tags: Optional[List[str]] = None,
                          config: Optional[Dict[str, Any]] = None,
                          factory: Optional[Callable[..., T]] = None,
                          parent_id: Optional[str] = None) -> str:
        """
        Register a component with the registry.
        
        Args:
            component_id: Unique identifier for the component
            component_class: Class of the component
            component_type: Type of the component
            name: Human-readable name of the component
            description: Description of the component
            version: Version of the component
            scope: Scope of the component
            dependencies: List of component IDs that this component depends on
            tags: List of tags for categorizing the component
            config: Configuration for the component
            factory: Factory function for creating the component
            parent_id: ID of the parent component
            
        Returns:
            The component ID
        """
        # Generate component ID if not provided
        if not component_id:
            component_id = f"{component_class.__name__}_{str(uuid.uuid4())[:8]}"
        
        # Use class name as name if not provided
        if not name:
            name = component_class.__name__
        
        # Check if component is already registered
        if component_id in self.components:
            logger.warning(f"Component with ID {component_id} is already registered")
            return component_id
        
        # Create component metadata
        metadata = ComponentMetadata(
            component_id=component_id,
            component_type=component_type,
            component_class=component_class,
            name=name,
            description=description,
            version=version,
            scope=scope,
            dependencies=dependencies,
            tags=tags,
            config=config,
            factory=factory
        )
        
        # Set parent-child relationship
        if parent_id:
            if parent_id in self.components:
                metadata.parent_id = parent_id
                self.components[parent_id].children_ids.append(component_id)
            else:
                logger.warning(f"Parent component with ID {parent_id} not found")
        
        # Add to registry
        self.components[component_id] = metadata
        
        # Add to component types
        self.component_types[component_type].add(component_id)
        
        # Add to tags
        if tags:
            for tag in tags:
                if tag not in self.tags:
                    self.tags[tag] = set()
                self.tags[tag].add(component_id)
        
        # Add to dependency graph
        self.dependency_graph[component_id] = set(dependencies or [])
        
        # Add configuration
        if config:
            self.configurations[component_id] = config
        
        # Add factory
        if factory:
            self.factories[component_id] = factory
        
        # Emit signals
        self.component_registered.emit(component_id)
        
        # Emit event
        self.event_bus.emit_event(ComponentRegisteredEvent(
            component_id=component_id,
            component_type=component_type.name,
            component_name=name
        ))
        
        logger.debug(f"Component {component_id} registered")
        
        return component_id
    
    def unregister_component(self, component_id: str) -> bool:
        """
        Unregister a component from the registry.
        
        Args:
            component_id: The ID of the component to unregister
            
        Returns:
            True if the component was unregistered, False if it wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return False
        
        # Get component metadata
        metadata = self.components[component_id]
        
        # Check if component has children
        if metadata.children_ids:
            logger.warning(f"Component {component_id} has children and cannot be unregistered")
            return False
        
        # Check if component is a dependency for other components
        for dep_id, deps in self.dependency_graph.items():
            if component_id in deps:
                logger.warning(f"Component {component_id} is a dependency for {dep_id} and cannot be unregistered")
                return False
        
        # Dispose component if it's initialized
        if metadata.state in [ComponentState.INITIALIZED, ComponentState.ACTIVE, ComponentState.INACTIVE]:
            self.dispose_component(component_id)
        
        # Remove from parent's children
        if metadata.parent_id and metadata.parent_id in self.components:
            self.components[metadata.parent_id].children_ids.remove(component_id)
        
        # Remove from registry
        del self.components[component_id]
        
        # Remove from component types
        self.component_types[metadata.component_type].remove(component_id)
        
        # Remove from tags
        for tag in metadata.tags:
            if tag in self.tags and component_id in self.tags[tag]:
                self.tags[tag].remove(component_id)
                if not self.tags[tag]:
                    del self.tags[tag]
        
        # Remove from dependency graph
        del self.dependency_graph[component_id]
        
        # Remove from configurations
        if component_id in self.configurations:
            del self.configurations[component_id]
        
        # Remove from factories
        if component_id in self.factories:
            del self.factories[component_id]
        
        # Remove from lifecycle hooks
        if component_id in self.lifecycle_hooks:
            del self.lifecycle_hooks[component_id]
        
        # Emit signals
        self.component_unregistered.emit(component_id)
        
        # Emit event
        self.event_bus.emit_event(ComponentUnregisteredEvent(
            component_id=component_id,
            component_type=metadata.component_type.name,
            component_name=metadata.name
        ))
        
        logger.debug(f"Component {component_id} unregistered")
        
        return True
    
    def get_component(self, component_id: str) -> Optional[ComponentMetadata]:
        """
        Get a component by ID.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component metadata, or None if not found
        """
        return self.components.get(component_id)
    
    def get_components_by_type(self, component_type: ComponentType) -> List[ComponentMetadata]:
        """
        Get all components of a specific type.
        
        Args:
            component_type: The type of components to get
            
        Returns:
            List of component metadata
        """
        component_ids = self.component_types.get(component_type, set())
        return [self.components[component_id] for component_id in component_ids]
    
    def get_components_by_tag(self, tag: str) -> List[ComponentMetadata]:
        """
        Get all components with a specific tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of component metadata
        """
        component_ids = self.tags.get(tag, set())
        return [self.components[component_id] for component_id in component_ids]
    
    def get_components_by_class(self, component_class: Type) -> List[ComponentMetadata]:
        """
        Get all components of a specific class.
        
        Args:
            component_class: The class to filter by
            
        Returns:
            List of component metadata
        """
        return [metadata for metadata in self.components.values() 
                if metadata.component_class == component_class]
    
    def get_component_instance(self, component_id: str, scope_id: str = "default") -> Optional[Any]:
        """
        Get an instance of a component.
        
        Args:
            component_id: The ID of the component
            scope_id: The ID of the scope (for scoped components)
            
        Returns:
            The component instance, or None if not found or not initialized
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        metadata = self.components[component_id]
        
        # Check if component is initialized
        if metadata.state not in [ComponentState.INITIALIZED, ComponentState.ACTIVE, ComponentState.INACTIVE]:
            logger.warning(f"Component {component_id} is not initialized")
            return None
        
        # Get instance based on scope
        if metadata.scope == ComponentScope.SINGLETON:
            return metadata.instance
        elif metadata.scope == ComponentScope.SCOPED:
            if scope_id not in self.scopes:
                logger.warning(f"Scope with ID {scope_id} not found")
                return None
            return self.scopes[scope_id].get(component_id)
        else:  # TRANSIENT
            # Create a new instance each time
            return self.create_component_instance(component_id, scope_id)
    
    def create_component_instance(self, component_id: str, scope_id: str = "default") -> Optional[Any]:
        """
        Create an instance of a component.
        
        Args:
            component_id: The ID of the component
            scope_id: The ID of the scope (for scoped components)
            
        Returns:
            The component instance, or None if creation failed
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        metadata = self.components[component_id]
        
        # Check if component is already initialized for singletons
        if metadata.scope == ComponentScope.SINGLETON and metadata.instance is not None:
            return metadata.instance
        
        # Check if component is already initialized for scoped components
        if metadata.scope == ComponentScope.SCOPED:
            if scope_id in self.scopes and component_id in self.scopes[scope_id]:
                return self.scopes[scope_id][component_id]
        
        # Update component state
        metadata.state = ComponentState.INITIALIZING
        self.component_state_changed.emit(component_id, metadata.state)
        
        try:
            # Resolve dependencies
            dependencies = self.resolve_dependencies(component_id, scope_id)
            
            # Create instance
            instance = None
            
            # Use factory if provided
            if metadata.factory:
                instance = metadata.factory(**dependencies)
            # Use custom factory from registry
            elif component_id in self.factories:
                instance = self.factories[component_id](**dependencies)
            # Create instance directly
            else:
                # Get constructor parameters
                constructor = metadata.component_class.__init__
                if constructor is object.__init__:
                    # No custom constructor, use default
                    instance = metadata.component_class()
                else:
                    # Get parameter names
                    sig = inspect.signature(constructor)
                    params = {}
                    
                    for name, param in sig.parameters.items():
                        if name == 'self':
                            continue
                        
                        if name in dependencies:
                            params[name] = dependencies[name]
                        elif param.default is not inspect.Parameter.empty:
                            # Use default value
                            pass
                        else:
                            logger.warning(f"Missing dependency {name} for component {component_id}")
                    
                    # Create instance with dependencies
                    instance = metadata.component_class(**params)
            
            # Store instance based on scope
            if metadata.scope == ComponentScope.SINGLETON:
                metadata.instance = instance
            elif metadata.scope == ComponentScope.SCOPED:
                if scope_id not in self.scopes:
                    self.scopes[scope_id] = {}
                self.scopes[scope_id][component_id] = instance
            
            # Initialize instance if it has an initialize method
            if hasattr(instance, 'initialize') and callable(instance.initialize):
                instance.initialize()
            
            # Call lifecycle hooks
            self._call_lifecycle_hooks(component_id, 'after_initialize', instance)
            
            # Update component state
            metadata.state = ComponentState.INITIALIZED
            metadata.initialized_at = datetime.now()
            self.component_state_changed.emit(component_id, metadata.state)
            self.component_initialized.emit(component_id)
            
            logger.debug(f"Component {component_id} initialized")
            
            return instance
            
        except Exception as e:
            # Update component state
            metadata.state = ComponentState.ERROR
            metadata.error = str(e)
            self.component_state_changed.emit(component_id, metadata.state)
            self.component_error.emit(component_id, str(e))
            
            # Log error
            logger.error(f"Error initializing component {component_id}: {e}")
            
            # Handle error
            self.error_handler.handle_exception(
                e,
                context=f"Initializing component {component_id}",
                component=f"ui.component_registry"
            )
            
            return None
    
    def resolve_dependencies(self, component_id: str, scope_id: str = "default") -> Dict[str, Any]:
        """
        Resolve dependencies for a component.
        
        Args:
            component_id: The ID of the component
            scope_id: The ID of the scope (for scoped components)
            
        Returns:
            Dictionary of resolved dependencies
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return {}
        
        metadata = self.components[component_id]
        dependencies = {}
        
        # Get constructor parameters
        constructor = metadata.component_class.__init__
        if constructor is object.__init__:
            # No custom constructor, no dependencies
            return dependencies
        
        # Get parameter names
        sig = inspect.signature(constructor)
        
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            
            # Check if parameter is a dependency
            if name in metadata.dependencies:
                dep_id = name
                # Get dependency instance
                dep_instance = self.get_component_instance(dep_id, scope_id)
                if dep_instance is None:
                    # Try to create dependency instance
                    dep_instance = self.create_component_instance(dep_id, scope_id)
                
                if dep_instance is not None:
                    dependencies[name] = dep_instance
            
            # Check if parameter is a common service
            elif name == 'event_bus':
                dependencies[name] = self.event_bus
            elif name == 'state_manager':
                dependencies[name] = self.state_manager
            elif name == 'error_handler':
                dependencies[name] = self.error_handler
            elif name == 'component_registry':
                dependencies[name] = self
        
        return dependencies
    
    def dispose_component(self, component_id: str) -> bool:
        """
        Dispose a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            True if the component was disposed, False if it wasn't found or couldn't be disposed
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return False
        
        metadata = self.components[component_id]
        
        # Check if component is initialized
        if metadata.state not in [ComponentState.INITIALIZED, ComponentState.ACTIVE, ComponentState.INACTIVE]:
            logger.warning(f"Component {component_id} is not initialized")
            return False
        
        # Update component state
        metadata.state = ComponentState.DISPOSING
        self.component_state_changed.emit(component_id, metadata.state)
        
        try:
            # Get instance
            instance = None
            
            if metadata.scope == ComponentScope.SINGLETON:
                instance = metadata.instance
            elif metadata.scope == ComponentScope.SCOPED:
                # Dispose instances in all scopes
                for scope_id, scope in self.scopes.items():
                    if component_id in scope:
                        instance = scope[component_id]
                        self._dispose_instance(instance, component_id)
                        del scope[component_id]
            
            # Dispose singleton instance
            if metadata.scope == ComponentScope.SINGLETON and instance is not None:
                self._dispose_instance(instance, component_id)
                metadata.instance = None
            
            # Update component state
            metadata.state = ComponentState.DISPOSED
            metadata.disposed_at = datetime.now()
            self.component_state_changed.emit(component_id, metadata.state)
            self.component_disposed.emit(component_id)
            
            logger.debug(f"Component {component_id} disposed")
            
            return True
            
        except Exception as e:
            # Update component state
            metadata.state = ComponentState.ERROR
            metadata.error = str(e)
            self.component_state_changed.emit(component_id, metadata.state)
            self.component_error.emit(component_id, str(e))
            
            # Log error
            logger.error(f"Error disposing component {component_id}: {e}")
            
            # Handle error
            self.error_handler.handle_exception(
                e,
                context=f"Disposing component {component_id}",
                component=f"ui.component_registry"
            )
            
            return False
    
    def _dispose_instance(self, instance: Any, component_id: str) -> None:
        """
        Dispose a component instance.
        
        Args:
            instance: The component instance
            component_id: The ID of the component
        """
        # Call lifecycle hooks
        self._call_lifecycle_hooks(component_id, 'before_dispose', instance)
        
        # Call dispose method if it exists
        if hasattr(instance, 'dispose') and callable(instance.dispose):
            instance.dispose()
        # Call cleanup method if it exists
        elif hasattr(instance, 'cleanup') and callable(instance.cleanup):
            instance.cleanup()
    
    def activate_component(self, component_id: str) -> bool:
        """
        Activate a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            True if the component was activated, False if it wasn't found or couldn't be activated
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return False
        
        metadata = self.components[component_id]
        
        # Check if component is initialized
        if metadata.state not in [ComponentState.INITIALIZED, ComponentState.INACTIVE]:
            logger.warning(f"Component {component_id} is not initialized or is already active")
            return False
        
        try:
            # Get instance
            instance = None
            
            if metadata.scope == ComponentScope.SINGLETON:
                instance = metadata.instance
            
            # Call activate method if it exists
            if instance is not None and hasattr(instance, 'activate') and callable(instance.activate):
                instance.activate()
            
            # Call lifecycle hooks
            self._call_lifecycle_hooks(component_id, 'after_activate', instance)
            
            # Update component state
            metadata.state = ComponentState.ACTIVE
            metadata.last_active_at = datetime.now()
            self.component_state_changed.emit(component_id, metadata.state)
            
            logger.debug(f"Component {component_id} activated")
            
            return True
            
        except Exception as e:
            # Update component state
            metadata.state = ComponentState.ERROR
            metadata.error = str(e)
            self.component_state_changed.emit(component_id, metadata.state)
            self.component_error.emit(component_id, str(e))
            
            # Log error
            logger.error(f"Error activating component {component_id}: {e}")
            
            # Handle error
            self.error_handler.handle_exception(
                e,
                context=f"Activating component {component_id}",
                component=f"ui.component_registry"
            )
            
            return False
    
    def deactivate_component(self, component_id: str) -> bool:
        """
        Deactivate a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            True if the component was deactivated, False if it wasn't found or couldn't be deactivated
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return False
        
        metadata = self.components[component_id]
        
        # Check if component is active
        if metadata.state != ComponentState.ACTIVE:
            logger.warning(f"Component {component_id} is not active")
            return False
        
        try:
            # Get instance
            instance = None
            
            if metadata.scope == ComponentScope.SINGLETON:
                instance = metadata.instance
            
            # Call lifecycle hooks
            self._call_lifecycle_hooks(component_id, 'before_deactivate', instance)
            
            # Call deactivate method if it exists
            if instance is not None and hasattr(instance, 'deactivate') and callable(instance.deactivate):
                instance.deactivate()
            
            # Update component state
            metadata.state = ComponentState.INACTIVE
            self.component_state_changed.emit(component_id, metadata.state)
            
            logger.debug(f"Component {component_id} deactivated")
            
            return True
            
        except Exception as e:
            # Update component state
            metadata.state = ComponentState.ERROR
            metadata.error = str(e)
            self.component_state_changed.emit(component_id, metadata.state)
            self.component_error.emit(component_id, str(e))
            
            # Log error
            logger.error(f"Error deactivating component {component_id}: {e}")
            
            # Handle error
            self.error_handler.handle_exception(
                e,
                context=f"Deactivating component {component_id}",
                component=f"ui.component_registry"
            )
            
            return False
    
    def add_lifecycle_hook(self, component_id: str, hook_type: str, hook: Callable) -> None:
        """
        Add a lifecycle hook for a component.
        
        Args:
            component_id: The ID of the component
            hook_type: The type of hook (after_initialize, before_dispose, after_activate, before_deactivate)
            hook: The hook function
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return
        
        if component_id not in self.lifecycle_hooks:
            self.lifecycle_hooks[component_id] = {}
        
        if hook_type not in self.lifecycle_hooks[component_id]:
            self.lifecycle_hooks[component_id][hook_type] = []
        
        self.lifecycle_hooks[component_id][hook_type].append(hook)
        
        logger.debug(f"Lifecycle hook {hook_type} added for component {component_id}")
    
    def remove_lifecycle_hook(self, component_id: str, hook_type: str, hook: Callable) -> bool:
        """
        Remove a lifecycle hook for a component.
        
        Args:
            component_id: The ID of the component
            hook_type: The type of hook
            hook: The hook function
            
        Returns:
            True if the hook was removed, False if it wasn't found
        """
        if component_id not in self.lifecycle_hooks:
            logger.warning(f"Component with ID {component_id} has no lifecycle hooks")
            return False
        
        if hook_type not in self.lifecycle_hooks[component_id]:
            logger.warning(f"Component with ID {component_id} has no {hook_type} hooks")
            return False
        
        if hook not in self.lifecycle_hooks[component_id][hook_type]:
            logger.warning(f"Hook not found for component {component_id} and type {hook_type}")
            return False
        
        self.lifecycle_hooks[component_id][hook_type].remove(hook)
        
        # Remove empty hook type list
        if not self.lifecycle_hooks[component_id][hook_type]:
            del self.lifecycle_hooks[component_id][hook_type]
        
        # Remove empty component entry
        if not self.lifecycle_hooks[component_id]:
            del self.lifecycle_hooks[component_id]
        
        logger.debug(f"Lifecycle hook {hook_type} removed for component {component_id}")
        
        return True
    
    def _call_lifecycle_hooks(self, component_id: str, hook_type: str, instance: Any) -> None:
        """
        Call lifecycle hooks for a component.
        
        Args:
            component_id: The ID of the component
            hook_type: The type of hook
            instance: The component instance
        """
        if component_id not in self.lifecycle_hooks:
            return
        
        if hook_type not in self.lifecycle_hooks[component_id]:
            return
        
        for hook in self.lifecycle_hooks[component_id][hook_type]:
            try:
                hook(instance)
            except Exception as e:
                logger.error(f"Error in lifecycle hook {hook_type} for component {component_id}: {e}")
                self.error_handler.handle_exception(
                    e,
                    context=f"Lifecycle hook {hook_type} for component {component_id}",
                    component=f"ui.component_registry"
                )
    
    def add_discovery_path(self, path: str) -> None:
        """
        Add a path for component discovery.
        
        Args:
            path: The path to add
        """
        if path not in self.discovery_paths:
            self.discovery_paths.append(path)
            logger.debug(f"Discovery path added: {path}")
    
    def remove_discovery_path(self, path: str) -> bool:
        """
        Remove a path from component discovery.
        
        Args:
            path: The path to remove
            
        Returns:
            True if the path was removed, False if it wasn't found
        """
        if path in self.discovery_paths:
            self.discovery_paths.remove(path)
            logger.debug(f"Discovery path removed: {path}")
            return True
        
        logger.warning(f"Discovery path not found: {path}")
        return False
    
    def discover_components(self, path: Optional[str] = None) -> List[str]:
        """
        Discover components in a path.
        
        Args:
            path: The path to discover components in, or None to use all discovery paths
            
        Returns:
            List of discovered component IDs
        """
        discovered_components = []
        
        paths = [path] if path else self.discovery_paths
        
        for discovery_path in paths:
            if not os.path.exists(discovery_path):
                logger.warning(f"Discovery path does not exist: {discovery_path}")
                continue
            
            # Add path to Python path if not already there
            if discovery_path not in sys.path:
                sys.path.append(discovery_path)
            
            # Walk through directory
            for root, dirs, files in os.walk(discovery_path):
                # Skip __pycache__ directories
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                
                # Process Python files
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        file_path = os.path.join(root, file)
                        module_path = os.path.relpath(file_path, discovery_path)
                        module_name = os.path.splitext(module_path)[0].replace(os.path.sep, '.')
                        
                        try:
                            # Import module
                            module = importlib.import_module(module_name)
                            
                            # Look for component classes
                            for name, obj in inspect.getmembers(module):
                                if inspect.isclass(obj) and hasattr(obj, '__component_type__'):
                                    component_type = getattr(obj, '__component_type__')
                                    component_id = getattr(obj, '__component_id__', None)
                                    
                                    # Register component
                                    component_id = self.register_component(
                                        component_id=component_id,
                                        component_class=obj,
                                        component_type=component_type,
                                        name=getattr(obj, '__component_name__', None),
                                        description=getattr(obj, '__component_description__', None),
                                        version=getattr(obj, '__component_version__', "1.0.0"),
                                        scope=getattr(obj, '__component_scope__', ComponentScope.SINGLETON),
                                        dependencies=getattr(obj, '__component_dependencies__', None),
                                        tags=getattr(obj, '__component_tags__', None),
                                        config=getattr(obj, '__component_config__', None),
                                        factory=getattr(obj, '__component_factory__', None),
                                        parent_id=getattr(obj, '__component_parent_id__', None)
                                    )
                                    
                                    discovered_components.append(component_id)
                        
                        except Exception as e:
                            logger.error(f"Error discovering components in module {module_name}: {e}")
                            self.error_handler.handle_exception(
                                e,
                                context=f"Discovering components in module {module_name}",
                                component=f"ui.component_registry"
                            )
        
        return discovered_components
    
    def set_component_config(self, component_id: str, config: Dict[str, Any]) -> bool:
        """
        Set configuration for a component.
        
        Args:
            component_id: The ID of the component
            config: The configuration to set
            
        Returns:
            True if the configuration was set, False if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return False
        
        # Update component metadata
        self.components[component_id].config = config
        
        # Update configurations
        self.configurations[component_id] = config
        
        logger.debug(f"Configuration set for component {component_id}")
        
        return True
    
    def get_component_config(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component configuration, or None if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].config
    
    def set_component_factory(self, component_id: str, factory: Callable[..., Any]) -> bool:
        """
        Set factory for a component.
        
        Args:
            component_id: The ID of the component
            factory: The factory function
            
        Returns:
            True if the factory was set, False if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return False
        
        # Update component metadata
        self.components[component_id].factory = factory
        
        # Update factories
        self.factories[component_id] = factory
        
        logger.debug(f"Factory set for component {component_id}")
        
        return True
    
    def get_component_factory(self, component_id: str) -> Optional[Callable[..., Any]]:
        """
        Get factory for a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component factory, or None if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].factory
    
    def get_component_state(self, component_id: str) -> Optional[ComponentState]:
        """
        Get state for a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component state, or None if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].state
    
    def get_component_error(self, component_id: str) -> Optional[str]:
        """
        Get error for a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component error, or None if the component wasn't found or has no error
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].error
    
    def get_component_dependencies(self, component_id: str) -> Optional[List[str]]:
        """
        Get dependencies for a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component dependencies, or None if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].dependencies
    
    def get_component_dependents(self, component_id: str) -> List[str]:
        """
        Get components that depend on a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            List of component IDs that depend on the component
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return []
        
        dependents = []
        
        for dep_id, deps in self.dependency_graph.items():
            if component_id in deps:
                dependents.append(dep_id)
        
        return dependents
    
    def get_component_children(self, component_id: str) -> Optional[List[str]]:
        """
        Get children of a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component children, or None if the component wasn't found
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].children_ids
    
    def get_component_parent(self, component_id: str) -> Optional[str]:
        """
        Get parent of a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            The component parent ID, or None if the component wasn't found or has no parent
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return None
        
        return self.components[component_id].parent_id
    
    def get_component_hierarchy(self, component_id: str) -> List[str]:
        """
        Get hierarchy of a component.
        
        Args:
            component_id: The ID of the component
            
        Returns:
            List of component IDs in the hierarchy, from root to leaf
        """
        if component_id not in self.components:
            logger.warning(f"Component with ID {component_id} not found")
            return [component_id]
        
        hierarchy = []
        current_id = component_id
        
        while current_id is not None:
            hierarchy.insert(0, current_id)
            current_id = self.get_component_parent(current_id)
        
        return hierarchy
    
    def get_component_tree(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get component tree.
        
        Args:
            root_id: The ID of the root component, or None to get the entire tree
            
        Returns:
            Dictionary representing the component tree
        """
        if root_id is not None and root_id not in self.components:
            logger.warning(f"Component with ID {root_id} not found")
            return {}
        
        def build_tree(component_id: str) -> Dict[str, Any]:
            metadata = self.components[component_id]
            tree = metadata.to_dict()
            tree['children'] = {}
            
            for child_id in metadata.children_ids:
                tree['children'][child_id] = build_tree(child_id)
            
            return tree
        
        if root_id is not None:
            return build_tree(root_id)
        
        # Build forest of trees
        forest = {}
        
        for component_id, metadata in self.components.items():
            if metadata.parent_id is None:
                forest[component_id] = build_tree(component_id)
        
        return forest
    
    def get_all_components(self) -> Dict[str, ComponentMetadata]:
        """
        Get all components.
        
        Returns:
            Dictionary mapping component IDs to component metadata
        """
        return self.components.copy()
    
    def get_all_tags(self) -> List[str]:
        """
        Get all tags.
        
        Returns:
            List of all tags
        """
        return list(self.tags.keys())
    
    def clear(self) -> None:
        """Clear the component registry."""
        # Dispose all components
        for component_id in list(self.components.keys()):
            self.dispose_component(component_id)
        
        # Clear all data structures
        self.components.clear()
        self.instances.clear()
        self.scopes.clear()
        self.dependency_graph.clear()
        self.tags.clear()
        self.component_types = {
            component_type: set() for component_type in ComponentType
        }
        self.discovery_paths.clear()
        self.factories.clear()
        self.configurations.clear()
        self.lifecycle_hooks.clear()
        
        logger.debug("Component Registry cleared")


# Create a singleton instance of the component registry
_instance: Optional[ComponentRegistry] = None

def get_component_registry(parent=None) -> ComponentRegistry:
    """
    Get the singleton instance of the component registry.
    
    Args:
        parent: The parent QObject
    
    Returns:
        The component registry instance
    """
    global _instance
    if _instance is None:
        _instance = ComponentRegistry(parent)
    return _instance
