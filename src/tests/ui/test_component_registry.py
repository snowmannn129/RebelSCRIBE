#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the ComponentRegistry class.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

from PyQt6.QtCore import QObject

from src.ui.component_registry import (
    ComponentRegistry, ComponentState, ComponentScope, ComponentType,
    ComponentMetadata, get_component_registry
)


class TestComponent(QObject):
    """Test component class."""
    
    def __init__(self, dependency=None, event_bus=None, state_manager=None, error_handler=None, component_registry=None):
        """Initialize the component."""
        super().__init__()
        self.dependency = dependency
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.error_handler = error_handler
        self.component_registry = component_registry
        self.initialized = False
        self.disposed = False
        self.activated = False
        self.deactivated = False
    
    def initialize(self):
        """Initialize the component."""
        self.initialized = True
    
    def dispose(self):
        """Dispose the component."""
        self.disposed = True
    
    def activate(self):
        """Activate the component."""
        self.activated = True
    
    def deactivate(self):
        """Deactivate the component."""
        self.deactivated = True


class TestDependency(QObject):
    """Test dependency class."""
    
    def __init__(self):
        """Initialize the dependency."""
        super().__init__()
        self.initialized = False
    
    def initialize(self):
        """Initialize the dependency."""
        self.initialized = True


class TestComponentRegistry(unittest.TestCase):
    """Tests for the ComponentRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a new component registry for each test
        self.registry = ComponentRegistry()
        
        # Mock the event bus
        self.event_bus_patch = patch('src.ui.component_registry.get_event_bus')
        self.mock_event_bus = self.event_bus_patch.start()
        self.registry.event_bus = MagicMock()
        
        # Mock the state manager
        self.state_manager_patch = patch('src.ui.component_registry.get_state_manager')
        self.mock_state_manager = self.state_manager_patch.start()
        self.registry.state_manager = MagicMock()
        
        # Mock the error handler
        self.error_handler_patch = patch('src.ui.component_registry.get_error_handler')
        self.mock_error_handler = self.error_handler_patch.start()
        self.registry.error_handler = MagicMock()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.event_bus_patch.stop()
        self.state_manager_patch.stop()
        self.error_handler_patch.stop()
    
    def test_singleton_pattern(self):
        """Test that get_component_registry returns the same instance each time."""
        registry1 = get_component_registry()
        registry2 = get_component_registry()
        
        # Check that both instances are the same object
        self.assertIs(registry1, registry2)
    
    def test_register_component(self):
        """Test registering a component."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            name="Test Component",
            description="A test component",
            version="1.0.0",
            scope=ComponentScope.SINGLETON,
            dependencies=["dependency"],
            tags=["test", "component"],
            config={"key": "value"}
        )
        
        # Check that the component was registered
        self.assertEqual(component_id, "test_component")
        self.assertIn(component_id, self.registry.components)
        
        # Check component metadata
        metadata = self.registry.components[component_id]
        self.assertEqual(metadata.component_id, component_id)
        self.assertEqual(metadata.component_class, TestComponent)
        self.assertEqual(metadata.component_type, ComponentType.CUSTOM)
        self.assertEqual(metadata.name, "Test Component")
        self.assertEqual(metadata.description, "A test component")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.scope, ComponentScope.SINGLETON)
        self.assertEqual(metadata.dependencies, ["dependency"])
        self.assertEqual(metadata.tags, ["test", "component"])
        self.assertEqual(metadata.config, {"key": "value"})
        self.assertEqual(metadata.state, ComponentState.REGISTERED)
        
        # Check that the component was added to the component types
        self.assertIn(component_id, self.registry.component_types[ComponentType.CUSTOM])
        
        # Check that the component was added to the tags
        self.assertIn(component_id, self.registry.tags["test"])
        self.assertIn(component_id, self.registry.tags["component"])
        
        # Check that the component was added to the dependency graph
        self.assertEqual(self.registry.dependency_graph[component_id], {"dependency"})
        
        # Check that the component was added to the configurations
        self.assertEqual(self.registry.configurations[component_id], {"key": "value"})
        
        # Check that the event was emitted
        self.registry.event_bus.emit_event.assert_called_once()
    
    def test_register_component_with_parent(self):
        """Test registering a component with a parent."""
        # Register parent component
        parent_id = self.registry.register_component(
            component_id="parent_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Register child component
        child_id = self.registry.register_component(
            component_id="child_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=parent_id
        )
        
        # Check parent-child relationship
        self.assertEqual(self.registry.components[child_id].parent_id, parent_id)
        self.assertIn(child_id, self.registry.components[parent_id].children_ids)
    
    def test_unregister_component(self):
        """Test unregistering a component."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            tags=["test"]
        )
        
        # Unregister the component
        result = self.registry.unregister_component(component_id)
        
        # Check that the component was unregistered
        self.assertTrue(result)
        self.assertNotIn(component_id, self.registry.components)
        self.assertNotIn(component_id, self.registry.component_types[ComponentType.CUSTOM])
        self.assertNotIn(component_id, self.registry.dependency_graph)
        
        # Check that the event was emitted
        self.registry.event_bus.emit_event.assert_called()
    
    def test_unregister_component_with_children(self):
        """Test unregistering a component with children."""
        # Register parent component
        parent_id = self.registry.register_component(
            component_id="parent_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Register child component
        child_id = self.registry.register_component(
            component_id="child_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=parent_id
        )
        
        # Try to unregister the parent component
        result = self.registry.unregister_component(parent_id)
        
        # Check that the parent component was not unregistered
        self.assertFalse(result)
        self.assertIn(parent_id, self.registry.components)
    
    def test_unregister_component_with_dependencies(self):
        """Test unregistering a component that is a dependency for another component."""
        # Register dependency component
        dependency_id = self.registry.register_component(
            component_id="dependency_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Register component that depends on the dependency
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            dependencies=[dependency_id]
        )
        
        # Try to unregister the dependency component
        result = self.registry.unregister_component(dependency_id)
        
        # Check that the dependency component was not unregistered
        self.assertFalse(result)
        self.assertIn(dependency_id, self.registry.components)
    
    def test_get_component(self):
        """Test getting a component by ID."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Get the component
        metadata = self.registry.get_component(component_id)
        
        # Check that the component was returned
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.component_id, component_id)
    
    def test_get_components_by_type(self):
        """Test getting components by type."""
        # Register components
        component_id1 = self.registry.register_component(
            component_id="test_component1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        component_id2 = self.registry.register_component(
            component_id="test_component2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        component_id3 = self.registry.register_component(
            component_id="test_component3",
            component_class=TestComponent,
            component_type=ComponentType.VIEW
        )
        
        # Get components by type
        custom_components = self.registry.get_components_by_type(ComponentType.CUSTOM)
        view_components = self.registry.get_components_by_type(ComponentType.VIEW)
        
        # Check that the correct components were returned
        self.assertEqual(len(custom_components), 2)
        self.assertEqual(len(view_components), 1)
        
        custom_ids = [metadata.component_id for metadata in custom_components]
        self.assertIn(component_id1, custom_ids)
        self.assertIn(component_id2, custom_ids)
        
        view_ids = [metadata.component_id for metadata in view_components]
        self.assertIn(component_id3, view_ids)
    
    def test_get_components_by_tag(self):
        """Test getting components by tag."""
        # Register components
        component_id1 = self.registry.register_component(
            component_id="test_component1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            tags=["tag1", "tag2"]
        )
        
        component_id2 = self.registry.register_component(
            component_id="test_component2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            tags=["tag1"]
        )
        
        component_id3 = self.registry.register_component(
            component_id="test_component3",
            component_class=TestComponent,
            component_type=ComponentType.VIEW,
            tags=["tag2"]
        )
        
        # Get components by tag
        tag1_components = self.registry.get_components_by_tag("tag1")
        tag2_components = self.registry.get_components_by_tag("tag2")
        
        # Check that the correct components were returned
        self.assertEqual(len(tag1_components), 2)
        self.assertEqual(len(tag2_components), 2)
        
        tag1_ids = [metadata.component_id for metadata in tag1_components]
        self.assertIn(component_id1, tag1_ids)
        self.assertIn(component_id2, tag1_ids)
        
        tag2_ids = [metadata.component_id for metadata in tag2_components]
        self.assertIn(component_id1, tag2_ids)
        self.assertIn(component_id3, tag2_ids)
    
    def test_get_components_by_class(self):
        """Test getting components by class."""
        # Define a test class
        class TestClass1(QObject):
            pass
        
        class TestClass2(QObject):
            pass
        
        # Register components
        component_id1 = self.registry.register_component(
            component_id="test_component1",
            component_class=TestClass1,
            component_type=ComponentType.CUSTOM
        )
        
        component_id2 = self.registry.register_component(
            component_id="test_component2",
            component_class=TestClass1,
            component_type=ComponentType.CUSTOM
        )
        
        component_id3 = self.registry.register_component(
            component_id="test_component3",
            component_class=TestClass2,
            component_type=ComponentType.VIEW
        )
        
        # Get components by class
        class1_components = self.registry.get_components_by_class(TestClass1)
        class2_components = self.registry.get_components_by_class(TestClass2)
        
        # Check that the correct components were returned
        self.assertEqual(len(class1_components), 2)
        self.assertEqual(len(class2_components), 1)
        
        class1_ids = [metadata.component_id for metadata in class1_components]
        self.assertIn(component_id1, class1_ids)
        self.assertIn(component_id2, class1_ids)
        
        class2_ids = [metadata.component_id for metadata in class2_components]
        self.assertIn(component_id3, class2_ids)
    
    def test_create_component_instance_singleton(self):
        """Test creating a singleton component instance."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Check that the instance was created
        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, TestComponent)
        self.assertTrue(instance.initialized)
        
        # Check that the component state was updated
        metadata = self.registry.components[component_id]
        self.assertEqual(metadata.state, ComponentState.INITIALIZED)
        self.assertIsNotNone(metadata.initialized_at)
        
        # Check that the instance was stored
        self.assertIs(instance, metadata.instance)
        
        # Create another instance
        instance2 = self.registry.create_component_instance(component_id)
        
        # Check that the same instance was returned
        self.assertIs(instance2, instance)
    
    def test_create_component_instance_transient(self):
        """Test creating a transient component instance."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.TRANSIENT
        )
        
        # Create an instance
        instance1 = self.registry.create_component_instance(component_id)
        
        # Check that the instance was created
        self.assertIsNotNone(instance1)
        self.assertIsInstance(instance1, TestComponent)
        self.assertTrue(instance1.initialized)
        
        # Create another instance
        instance2 = self.registry.create_component_instance(component_id)
        
        # Check that a new instance was created
        self.assertIsNotNone(instance2)
        self.assertIsInstance(instance2, TestComponent)
        self.assertTrue(instance2.initialized)
        self.assertIsNot(instance2, instance1)
    
    def test_create_component_instance_scoped(self):
        """Test creating a scoped component instance."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SCOPED
        )
        
        # Create an instance in scope1
        instance1 = self.registry.create_component_instance(component_id, "scope1")
        
        # Check that the instance was created
        self.assertIsNotNone(instance1)
        self.assertIsInstance(instance1, TestComponent)
        self.assertTrue(instance1.initialized)
        
        # Check that the instance was stored in the scope
        self.assertIn("scope1", self.registry.scopes)
        self.assertIn(component_id, self.registry.scopes["scope1"])
        self.assertIs(instance1, self.registry.scopes["scope1"][component_id])
        
        # Create another instance in scope1
        instance2 = self.registry.create_component_instance(component_id, "scope1")
        
        # Check that the same instance was returned
        self.assertIs(instance2, instance1)
        
        # Create an instance in scope2
        instance3 = self.registry.create_component_instance(component_id, "scope2")
        
        # Check that a new instance was created
        self.assertIsNotNone(instance3)
        self.assertIsInstance(instance3, TestComponent)
        self.assertTrue(instance3.initialized)
        self.assertIsNot(instance3, instance1)
        
        # Check that the instance was stored in the scope
        self.assertIn("scope2", self.registry.scopes)
        self.assertIn(component_id, self.registry.scopes["scope2"])
        self.assertIs(instance3, self.registry.scopes["scope2"][component_id])
    
    def test_create_component_instance_with_dependencies(self):
        """Test creating a component instance with dependencies."""
        # Register dependency component
        dependency_id = self.registry.register_component(
            component_id="dependency",
            component_class=TestDependency,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Register component that depends on the dependency
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON,
            dependencies=[dependency_id]
        )
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Check that the instance was created
        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, TestComponent)
        self.assertTrue(instance.initialized)
        
        # Check that the dependency was injected
        self.assertIsNotNone(instance.dependency)
        self.assertIsInstance(instance.dependency, TestDependency)
        self.assertTrue(instance.dependency.initialized)
    
    def test_create_component_instance_with_common_services(self):
        """Test creating a component instance with common services."""
        # Register component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Check that the instance was created
        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, TestComponent)
        self.assertTrue(instance.initialized)
        
        # Check that the common services were injected
        self.assertIs(instance.event_bus, self.registry.event_bus)
        self.assertIs(instance.state_manager, self.registry.state_manager)
        self.assertIs(instance.error_handler, self.registry.error_handler)
        self.assertIs(instance.component_registry, self.registry)
    
    def test_create_component_instance_with_factory(self):
        """Test creating a component instance with a factory."""
        # Create a factory function
        def factory(event_bus=None, state_manager=None, error_handler=None, component_registry=None):
            component = TestComponent()
            component.event_bus = event_bus
            component.state_manager = state_manager
            component.error_handler = error_handler
            component.component_registry = component_registry
            component.factory_created = True
            return component
        
        # Register component with factory
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON,
            factory=factory
        )
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Check that the instance was created
        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, TestComponent)
        self.assertTrue(instance.initialized)
        
        # Check that the factory was used
        self.assertTrue(hasattr(instance, "factory_created"))
        self.assertTrue(instance.factory_created)
        
        # Check that the common services were injected
        self.assertIs(instance.event_bus, self.registry.event_bus)
        self.assertIs(instance.state_manager, self.registry.state_manager)
    
    def test_dispose_component(self):
        """Test disposing a component."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Dispose the component
        result = self.registry.dispose_component(component_id)
        
        # Check that the component was disposed
        self.assertTrue(result)
        self.assertTrue(instance.disposed)
        
        # Check that the component state was updated
        metadata = self.registry.components[component_id]
        self.assertEqual(metadata.state, ComponentState.DISPOSED)
        self.assertIsNotNone(metadata.disposed_at)
        
        # Check that the instance was removed
        self.assertIsNone(metadata.instance)
    
    def test_dispose_component_scoped(self):
        """Test disposing a scoped component."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SCOPED
        )
        
        # Create instances in different scopes
        instance1 = self.registry.create_component_instance(component_id, "scope1")
        instance2 = self.registry.create_component_instance(component_id, "scope2")
        
        # Dispose the component
        result = self.registry.dispose_component(component_id)
        
        # Check that the component was disposed
        self.assertTrue(result)
        self.assertTrue(instance1.disposed)
        self.assertTrue(instance2.disposed)
        
        # Check that the component state was updated
        metadata = self.registry.components[component_id]
        self.assertEqual(metadata.state, ComponentState.DISPOSED)
        self.assertIsNotNone(metadata.disposed_at)
        
        # Check that the instances were removed from scopes
        self.assertNotIn(component_id, self.registry.scopes["scope1"])
        self.assertNotIn(component_id, self.registry.scopes["scope2"])
    
    def test_activate_deactivate_component(self):
        """Test activating and deactivating a component."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Activate the component
        result = self.registry.activate_component(component_id)
        
        # Check that the component was activated
        self.assertTrue(result)
        self.assertTrue(instance.activated)
        
        # Check that the component state was updated
        metadata = self.registry.components[component_id]
        self.assertEqual(metadata.state, ComponentState.ACTIVE)
        self.assertIsNotNone(metadata.last_active_at)
        
        # Deactivate the component
        result = self.registry.deactivate_component(component_id)
        
        # Check that the component was deactivated
        self.assertTrue(result)
        self.assertTrue(instance.deactivated)
        
        # Check that the component state was updated
        metadata = self.registry.components[component_id]
        self.assertEqual(metadata.state, ComponentState.INACTIVE)
    
    def test_lifecycle_hooks(self):
        """Test lifecycle hooks."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create hooks
        after_initialize_hook = MagicMock()
        before_dispose_hook = MagicMock()
        after_activate_hook = MagicMock()
        before_deactivate_hook = MagicMock()
        
        # Add hooks
        self.registry.add_lifecycle_hook(component_id, "after_initialize", after_initialize_hook)
        self.registry.add_lifecycle_hook(component_id, "before_dispose", before_dispose_hook)
        self.registry.add_lifecycle_hook(component_id, "after_activate", after_activate_hook)
        self.registry.add_lifecycle_hook(component_id, "before_deactivate", before_deactivate_hook)
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Check that the after_initialize hook was called
        after_initialize_hook.assert_called_once_with(instance)
        
        # Activate the component
        self.registry.activate_component(component_id)
        
        # Check that the after_activate hook was called
        after_activate_hook.assert_called_once_with(instance)
        
        # Deactivate the component
        self.registry.deactivate_component(component_id)
        
        # Check that the before_deactivate hook was called
        before_deactivate_hook.assert_called_once_with(instance)
        
        # Dispose the component
        self.registry.dispose_component(component_id)
        
        # Check that the before_dispose hook was called
        before_dispose_hook.assert_called_once_with(instance)
    
    def test_remove_lifecycle_hook(self):
        """Test removing a lifecycle hook."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create hooks
        hook1 = MagicMock()
        hook2 = MagicMock()
        
        # Add hooks
        self.registry.add_lifecycle_hook(component_id, "after_initialize", hook1)
        self.registry.add_lifecycle_hook(component_id, "after_initialize", hook2)
        
        # Remove hook1
        result = self.registry.remove_lifecycle_hook(component_id, "after_initialize", hook1)
        
        # Check that the hook was removed
        self.assertTrue(result)
        self.assertNotIn(hook1, self.registry.lifecycle_hooks[component_id]["after_initialize"])
        self.assertIn(hook2, self.registry.lifecycle_hooks[component_id]["after_initialize"])
        
        # Create an instance
        instance = self.registry.create_component_instance(component_id)
        
        # Check that only hook2 was called
        hook1.assert_not_called()
        hook2.assert_called_once_with(instance)
    
    def test_component_tree(self):
        """Test getting the component tree."""
        # Register components
        root_id = self.registry.register_component(
            component_id="root",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        child1_id = self.registry.register_component(
            component_id="child1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=root_id
        )
        
        child2_id = self.registry.register_component(
            component_id="child2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=root_id
        )
        
        grandchild_id = self.registry.register_component(
            component_id="grandchild",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=child1_id
        )
        
        # Get the component tree
        tree = self.registry.get_component_tree(root_id)
        
        # Check the tree structure
        self.assertEqual(tree["component_id"], root_id)
        self.assertEqual(len(tree["children"]), 2)
        self.assertIn(child1_id, tree["children"])
        self.assertIn(child2_id, tree["children"])
        self.assertEqual(tree["children"][child1_id]["component_id"], child1_id)
        self.assertEqual(tree["children"][child2_id]["component_id"], child2_id)
        self.assertEqual(len(tree["children"][child1_id]["children"]), 1)
        self.assertIn(grandchild_id, tree["children"][child1_id]["children"])
        self.assertEqual(tree["children"][child1_id]["children"][grandchild_id]["component_id"], grandchild_id)
    
    def test_component_hierarchy(self):
        """Test getting the component hierarchy."""
        # Register components
        root_id = self.registry.register_component(
            component_id="root",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        child_id = self.registry.register_component(
            component_id="child",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=root_id
        )
        
        grandchild_id = self.registry.register_component(
            component_id="grandchild",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=child_id
        )
        
        # Get the component hierarchy
        hierarchy = self.registry.get_component_hierarchy(grandchild_id)
        
        # Check the hierarchy
        self.assertEqual(hierarchy, [root_id, child_id, grandchild_id])
    
    def test_clear(self):
        """Test clearing the component registry."""
        # Register components
        component_id1 = self.registry.register_component(
            component_id="test_component1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        component_id2 = self.registry.register_component(
            component_id="test_component2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            scope=ComponentScope.SINGLETON
        )
        
        # Create instances
        instance1 = self.registry.create_component_instance(component_id1)
        instance2 = self.registry.create_component_instance(component_id2)
        
        # Clear the registry
        self.registry.clear()
        
        # Check that the registry was cleared
        self.assertEqual(len(self.registry.components), 0)
        self.assertEqual(len(self.registry.instances), 0)
        self.assertEqual(len(self.registry.dependency_graph), 0)
        self.assertEqual(len(self.registry.tags), 0)
        self.assertEqual(sum(len(components) for components in self.registry.component_types.values()), 0)
        
        # Check that the instances were disposed
        self.assertTrue(instance1.disposed)
        self.assertTrue(instance2.disposed)
    
    def test_discover_components(self):
        """Test discovering components."""
        # Create a temporary directory for component discovery
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a test component module
            with open(os.path.join(temp_dir, "test_component.py"), "w") as f:
                f.write("""
from PyQt6.QtCore import QObject
from src.ui.component_registry import ComponentType

class DiscoveredComponent(QObject):
    __component_type__ = ComponentType.CUSTOM
    __component_id__ = "discovered_component"
    __component_name__ = "Discovered Component"
    __component_description__ = "A component discovered during testing"
    __component_version__ = "1.0.0"
    __component_tags__ = ["test", "discovered"]
""")
            
            # Add the temporary directory to the discovery paths
            self.registry.add_discovery_path(temp_dir)
            
            # Mock the importlib.import_module function
            with patch('src.ui.component_registry.importlib.import_module') as mock_import:
                # Create a mock module with the test component
                mock_module = MagicMock()
                mock_module.__name__ = "test_component"
                
                # Create a mock component class
                class MockDiscoveredComponent(QObject):
                    __component_type__ = ComponentType.CUSTOM
                    __component_id__ = "discovered_component"
                    __component_name__ = "Discovered Component"
                    __component_description__ = "A component discovered during testing"
                    __component_version__ = "1.0.0"
                    __component_tags__ = ["test", "discovered"]
                
                # Add the component class to the mock module
                mock_module.DiscoveredComponent = MockDiscoveredComponent
                
                # Configure the mock import function to return the mock module
                mock_import.return_value = mock_module
                
                # Discover components
                discovered_components = self.registry.discover_components()
                
                # Check that the component was discovered
                self.assertEqual(len(discovered_components), 1)
                self.assertEqual(discovered_components[0], "discovered_component")
                
                # Check that the component was registered
                self.assertIn("discovered_component", self.registry.components)
                
                # Check component metadata
                metadata = self.registry.components["discovered_component"]
                self.assertEqual(metadata.component_id, "discovered_component")
                self.assertEqual(metadata.component_class, MockDiscoveredComponent)
                self.assertEqual(metadata.component_type, ComponentType.CUSTOM)
                self.assertEqual(metadata.name, "Discovered Component")
                self.assertEqual(metadata.description, "A component discovered during testing")
                self.assertEqual(metadata.version, "1.0.0")
                self.assertEqual(metadata.tags, ["test", "discovered"])
        
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
    
    def test_component_config(self):
        """Test component configuration."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            config={"key1": "value1"}
        )
        
        # Get the component config
        config = self.registry.get_component_config(component_id)
        
        # Check that the config was returned
        self.assertEqual(config, {"key1": "value1"})
        
        # Set a new config
        result = self.registry.set_component_config(component_id, {"key2": "value2"})
        
        # Check that the config was set
        self.assertTrue(result)
        self.assertEqual(self.registry.components[component_id].config, {"key2": "value2"})
        self.assertEqual(self.registry.configurations[component_id], {"key2": "value2"})
        
        # Get the updated config
        config = self.registry.get_component_config(component_id)
        
        # Check that the updated config was returned
        self.assertEqual(config, {"key2": "value2"})
    
    def test_component_factory(self):
        """Test component factory."""
        # Create a factory function
        def factory():
            return TestComponent()
        
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            factory=factory
        )
        
        # Get the component factory
        component_factory = self.registry.get_component_factory(component_id)
        
        # Check that the factory was returned
        self.assertEqual(component_factory, factory)
        
        # Create a new factory function
        def new_factory():
            component = TestComponent()
            component.factory_created = True
            return component
        
        # Set a new factory
        result = self.registry.set_component_factory(component_id, new_factory)
        
        # Check that the factory was set
        self.assertTrue(result)
        self.assertEqual(self.registry.components[component_id].factory, new_factory)
        self.assertEqual(self.registry.factories[component_id], new_factory)
        
        # Get the updated factory
        component_factory = self.registry.get_component_factory(component_id)
        
        # Check that the updated factory was returned
        self.assertEqual(component_factory, new_factory)
    
    def test_component_state(self):
        """Test component state."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Get the component state
        state = self.registry.get_component_state(component_id)
        
        # Check that the state was returned
        self.assertEqual(state, ComponentState.REGISTERED)
        
        # Create an instance
        self.registry.create_component_instance(component_id)
        
        # Get the updated state
        state = self.registry.get_component_state(component_id)
        
        # Check that the state was updated
        self.assertEqual(state, ComponentState.INITIALIZED)
        
        # Activate the component
        self.registry.activate_component(component_id)
        
        # Get the updated state
        state = self.registry.get_component_state(component_id)
        
        # Check that the state was updated
        self.assertEqual(state, ComponentState.ACTIVE)
        
        # Deactivate the component
        self.registry.deactivate_component(component_id)
        
        # Get the updated state
        state = self.registry.get_component_state(component_id)
        
        # Check that the state was updated
        self.assertEqual(state, ComponentState.INACTIVE)
        
        # Dispose the component
        self.registry.dispose_component(component_id)
        
        # Get the updated state
        state = self.registry.get_component_state(component_id)
        
        # Check that the state was updated
        self.assertEqual(state, ComponentState.DISPOSED)
    
    def test_component_error(self):
        """Test component error."""
        # Register a component
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Get the component error
        error = self.registry.get_component_error(component_id)
        
        # Check that no error was returned
        self.assertIsNone(error)
        
        # Set an error
        self.registry.components[component_id].state = ComponentState.ERROR
        self.registry.components[component_id].error = "Test error"
        
        # Get the updated error
        error = self.registry.get_component_error(component_id)
        
        # Check that the error was returned
        self.assertEqual(error, "Test error")
    
    def test_component_dependencies(self):
        """Test component dependencies."""
        # Register components
        dependency_id = self.registry.register_component(
            component_id="dependency",
            component_class=TestDependency,
            component_type=ComponentType.CUSTOM
        )
        
        component_id = self.registry.register_component(
            component_id="test_component",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            dependencies=[dependency_id]
        )
        
        # Get the component dependencies
        dependencies = self.registry.get_component_dependencies(component_id)
        
        # Check that the dependencies were returned
        self.assertEqual(dependencies, [dependency_id])
        
        # Get the component dependents
        dependents = self.registry.get_component_dependents(dependency_id)
        
        # Check that the dependents were returned
        self.assertEqual(dependents, [component_id])
    
    def test_component_parent_children(self):
        """Test component parent and children."""
        # Register components
        parent_id = self.registry.register_component(
            component_id="parent",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        child1_id = self.registry.register_component(
            component_id="child1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=parent_id
        )
        
        child2_id = self.registry.register_component(
            component_id="child2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            parent_id=parent_id
        )
        
        # Get the component parent
        parent = self.registry.get_component_parent(child1_id)
        
        # Check that the parent was returned
        self.assertEqual(parent, parent_id)
        
        # Get the component children
        children = self.registry.get_component_children(parent_id)
        
        # Check that the children were returned
        self.assertEqual(set(children), {child1_id, child2_id})
    
    def test_get_all_components(self):
        """Test getting all components."""
        # Register components
        component_id1 = self.registry.register_component(
            component_id="test_component1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        component_id2 = self.registry.register_component(
            component_id="test_component2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM
        )
        
        # Get all components
        components = self.registry.get_all_components()
        
        # Check that all components were returned
        self.assertEqual(len(components), 2)
        self.assertIn(component_id1, components)
        self.assertIn(component_id2, components)
    
    def test_get_all_tags(self):
        """Test getting all tags."""
        # Register components
        self.registry.register_component(
            component_id="test_component1",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            tags=["tag1", "tag2"]
        )
        
        self.registry.register_component(
            component_id="test_component2",
            component_class=TestComponent,
            component_type=ComponentType.CUSTOM,
            tags=["tag2", "tag3"]
        )
        
        # Get all tags
        tags = self.registry.get_all_tags()
        
        # Check that all tags were returned
        self.assertEqual(set(tags), {"tag1", "tag2", "tag3"})


if __name__ == "__main__":
    unittest.main()
