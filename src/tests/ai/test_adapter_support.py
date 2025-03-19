#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the adapter support module.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json
import shutil

# Mock torch and other dependencies before importing adapter_support
sys.modules['torch'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['datasets'] = MagicMock()
sys.modules['peft'] = MagicMock()
sys.modules['nltk'] = MagicMock()
sys.modules['nltk.translate.bleu_score'] = MagicMock()
sys.modules['rouge_score'] = MagicMock()
sys.modules['rouge_score.rouge_scorer'] = MagicMock()

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ai.adapter_support import AdapterInfo, AdapterManager


class TestAdapterInfo(unittest.TestCase):
    """Test cases for the AdapterInfo class."""
    
    def test_init(self):
        """Test initialization of AdapterInfo."""
        adapter_info = AdapterInfo(
            name="test-adapter",
            path="/path/to/adapter",
            base_model="llama-7b",
            adapter_type="lora",
            parameters={"r": 8, "alpha": 16},
            metrics={"perplexity": 5.0},
        )
        
        self.assertEqual(adapter_info.name, "test-adapter")
        self.assertEqual(adapter_info.path, "/path/to/adapter")
        self.assertEqual(adapter_info.base_model, "llama-7b")
        self.assertEqual(adapter_info.adapter_type, "lora")
        self.assertEqual(adapter_info.parameters, {"r": 8, "alpha": 16})
        self.assertEqual(adapter_info.metrics, {"perplexity": 5.0})
    
    def test_to_dict(self):
        """Test converting AdapterInfo to dictionary."""
        adapter_info = AdapterInfo(
            name="test-adapter",
            path="/path/to/adapter",
            base_model="llama-7b",
            adapter_type="lora",
            creation_date="2025-03-12T12:00:00",
            parameters={"r": 8, "alpha": 16},
            metrics={"perplexity": 5.0},
        )
        
        adapter_dict = adapter_info.to_dict()
        
        self.assertEqual(adapter_dict["name"], "test-adapter")
        self.assertEqual(adapter_dict["path"], "/path/to/adapter")
        self.assertEqual(adapter_dict["base_model"], "llama-7b")
        self.assertEqual(adapter_dict["adapter_type"], "lora")
        self.assertEqual(adapter_dict["creation_date"], "2025-03-12T12:00:00")
        self.assertEqual(adapter_dict["parameters"], {"r": 8, "alpha": 16})
        self.assertEqual(adapter_dict["metrics"], {"perplexity": 5.0})
    
    def test_from_dict(self):
        """Test creating AdapterInfo from dictionary."""
        adapter_dict = {
            "name": "test-adapter",
            "path": "/path/to/adapter",
            "base_model": "llama-7b",
            "adapter_type": "lora",
            "creation_date": "2025-03-12T12:00:00",
            "parameters": {"r": 8, "alpha": 16},
            "metrics": {"perplexity": 5.0},
        }
        
        adapter_info = AdapterInfo.from_dict(adapter_dict)
        
        self.assertEqual(adapter_info.name, "test-adapter")
        self.assertEqual(adapter_info.path, "/path/to/adapter")
        self.assertEqual(adapter_info.base_model, "llama-7b")
        self.assertEqual(adapter_info.adapter_type, "lora")
        self.assertEqual(adapter_info.creation_date, "2025-03-12T12:00:00")
        self.assertEqual(adapter_info.parameters, {"r": 8, "alpha": 16})
        self.assertEqual(adapter_info.metrics, {"perplexity": 5.0})


class TestAdapterManager(unittest.TestCase):
    """Test cases for the AdapterManager class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a temporary directory for the adapters
        self.temp_dir = tempfile.TemporaryDirectory()
        self.adapters_dir = os.path.join(self.temp_dir.name, "adapters")
        
        # Create a mock for _ensure_dependencies
        self.ensure_dependencies_mock = MagicMock()
        
        # Patch the _ensure_dependencies method
        with patch.object(AdapterManager, '_ensure_dependencies', self.ensure_dependencies_mock):
            # Create adapter manager with the temporary directory
            self.manager = AdapterManager(adapters_dir=self.adapters_dir)
    
    def tearDown(self):
        """Tear down the test case."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initialization of AdapterManager."""
        self.assertEqual(self.manager.adapters_dir, self.adapters_dir)
        self.assertEqual(self.manager.adapter_registry, [])
        self.ensure_dependencies_mock.assert_called_once()
    
    def test_ensure_adapters_dir(self):
        """Test ensuring adapters directory exists."""
        # Remove the directory created in setUp
        shutil.rmtree(self.adapters_dir, ignore_errors=True)
        
        # Call the method
        self.manager._ensure_adapters_dir()
        
        # Check that the directory was created
        self.assertTrue(os.path.exists(self.adapters_dir))
        
        # Check that the registry file was created
        registry_path = os.path.join(self.adapters_dir, "registry.json")
        self.assertTrue(os.path.exists(registry_path))
        
        # Check that the registry file contains the expected content
        with open(registry_path, "r") as f:
            registry = json.load(f)
        
        self.assertEqual(registry, {"adapters": []})
    
    def test_save_and_load_adapter_registry(self):
        """Test saving and loading the adapter registry."""
        # Create some adapter info objects
        adapter1 = AdapterInfo(
            name="adapter1",
            path=os.path.join(self.adapters_dir, "adapter1"),
            base_model="llama-7b",
            adapter_type="lora",
        )
        
        adapter2 = AdapterInfo(
            name="adapter2",
            path=os.path.join(self.adapters_dir, "adapter2"),
            base_model="mistral-7b",
            adapter_type="qlora",
        )
        
        # Add adapters to registry
        self.manager.adapter_registry = [adapter1, adapter2]
        
        # Save registry
        self.manager._save_adapter_registry()
        
        # Create a new manager to load the registry
        new_manager = AdapterManager(adapters_dir=self.adapters_dir)
        new_manager._ensure_dependencies = MagicMock()
        
        # Check that the registry was loaded correctly
        self.assertEqual(len(new_manager.adapter_registry), 2)
        self.assertEqual(new_manager.adapter_registry[0].name, "adapter1")
        self.assertEqual(new_manager.adapter_registry[0].base_model, "llama-7b")
        self.assertEqual(new_manager.adapter_registry[0].adapter_type, "lora")
        self.assertEqual(new_manager.adapter_registry[1].name, "adapter2")
        self.assertEqual(new_manager.adapter_registry[1].base_model, "mistral-7b")
        self.assertEqual(new_manager.adapter_registry[1].adapter_type, "qlora")
    
    def test_get_adapters(self):
        """Test getting all adapters."""
        # Create some adapter info objects
        adapter1 = AdapterInfo(
            name="adapter1",
            path=os.path.join(self.adapters_dir, "adapter1"),
            base_model="llama-7b",
            adapter_type="lora",
        )
        
        adapter2 = AdapterInfo(
            name="adapter2",
            path=os.path.join(self.adapters_dir, "adapter2"),
            base_model="mistral-7b",
            adapter_type="qlora",
        )
        
        # Add adapters to registry
        self.manager.adapter_registry = [adapter1, adapter2]
        
        # Get adapters
        adapters = self.manager.get_adapters()
        
        # Check that the adapters were returned correctly
        self.assertEqual(len(adapters), 2)
        self.assertEqual(adapters[0].name, "adapter1")
        self.assertEqual(adapters[1].name, "adapter2")
    
    def test_get_adapter_info(self):
        """Test getting adapter info by name."""
        # Create some adapter info objects
        adapter1 = AdapterInfo(
            name="adapter1",
            path=os.path.join(self.adapters_dir, "adapter1"),
            base_model="llama-7b",
            adapter_type="lora",
        )
        
        adapter2 = AdapterInfo(
            name="adapter2",
            path=os.path.join(self.adapters_dir, "adapter2"),
            base_model="mistral-7b",
            adapter_type="qlora",
        )
        
        # Add adapters to registry
        self.manager.adapter_registry = [adapter1, adapter2]
        
        # Get adapter info
        adapter_info = self.manager.get_adapter_info("adapter1")
        
        # Check that the adapter info was returned correctly
        self.assertEqual(adapter_info.name, "adapter1")
        self.assertEqual(adapter_info.base_model, "llama-7b")
        self.assertEqual(adapter_info.adapter_type, "lora")
        
        # Get non-existent adapter info
        adapter_info = self.manager.get_adapter_info("non-existent")
        
        # Check that None was returned
        self.assertIsNone(adapter_info)
    
    def test_register_adapter(self):
        """Test registering an adapter."""
        # Register a new adapter
        adapter_info = self.manager.register_adapter(
            name="test-adapter",
            path=os.path.join(self.adapters_dir, "test-adapter"),
            base_model="llama-7b",
            adapter_type="lora",
            parameters={"r": 8, "alpha": 16},
            metrics={"perplexity": 5.0},
        )
        
        # Check that the adapter was registered correctly
        self.assertEqual(len(self.manager.adapter_registry), 1)
        self.assertEqual(self.manager.adapter_registry[0].name, "test-adapter")
        self.assertEqual(self.manager.adapter_registry[0].base_model, "llama-7b")
        self.assertEqual(self.manager.adapter_registry[0].adapter_type, "lora")
        self.assertEqual(self.manager.adapter_registry[0].parameters, {"r": 8, "alpha": 16})
        self.assertEqual(self.manager.adapter_registry[0].metrics, {"perplexity": 5.0})
        
        # Register an existing adapter
        updated_adapter_info = self.manager.register_adapter(
            name="test-adapter",
            path=os.path.join(self.adapters_dir, "test-adapter-updated"),
            base_model="mistral-7b",
            adapter_type="qlora",
            parameters={"r": 16, "alpha": 32},
            metrics={"perplexity": 4.0},
        )
        
        # Check that the adapter was updated correctly
        self.assertEqual(len(self.manager.adapter_registry), 1)
        self.assertEqual(self.manager.adapter_registry[0].name, "test-adapter")
        self.assertEqual(self.manager.adapter_registry[0].path, os.path.join(self.adapters_dir, "test-adapter-updated"))
        self.assertEqual(self.manager.adapter_registry[0].base_model, "mistral-7b")
        self.assertEqual(self.manager.adapter_registry[0].adapter_type, "qlora")
        self.assertEqual(self.manager.adapter_registry[0].parameters, {"r": 16, "alpha": 32})
        self.assertEqual(self.manager.adapter_registry[0].metrics, {"perplexity": 4.0})
    
    def test_unregister_adapter(self):
        """Test unregistering an adapter."""
        # Register some adapters
        self.manager.register_adapter(
            name="adapter1",
            path=os.path.join(self.adapters_dir, "adapter1"),
            base_model="llama-7b",
            adapter_type="lora",
        )
        
        self.manager.register_adapter(
            name="adapter2",
            path=os.path.join(self.adapters_dir, "adapter2"),
            base_model="mistral-7b",
            adapter_type="qlora",
        )
        
        # Unregister an adapter
        result = self.manager.unregister_adapter("adapter1")
        
        # Check that the adapter was unregistered correctly
        self.assertTrue(result)
        self.assertEqual(len(self.manager.adapter_registry), 1)
        self.assertEqual(self.manager.adapter_registry[0].name, "adapter2")
        
        # Unregister a non-existent adapter
        result = self.manager.unregister_adapter("non-existent")
        
        # Check that the operation failed
        self.assertFalse(result)
        self.assertEqual(len(self.manager.adapter_registry), 1)
    
    def test_delete_adapter(self):
        """Test deleting an adapter."""
        # Create adapter directory
        adapter_path = os.path.join(self.adapters_dir, "adapter1")
        os.makedirs(adapter_path, exist_ok=True)
        
        # Register the adapter
        self.manager.register_adapter(
            name="adapter1",
            path=adapter_path,
            base_model="llama-7b",
            adapter_type="lora",
        )
        
        # Delete the adapter
        result = self.manager.delete_adapter("adapter1")
        
        # Check that the adapter was deleted correctly
        self.assertTrue(result)
        self.assertEqual(len(self.manager.adapter_registry), 0)
        self.assertFalse(os.path.exists(adapter_path))
        
        # Delete a non-existent adapter
        result = self.manager.delete_adapter("non-existent")
        
        # Check that the operation failed
        self.assertFalse(result)
    
    def test_rename_adapter(self):
        """Test renaming an adapter."""
        # Create adapter directory
        adapter_path = os.path.join(self.adapters_dir, "adapter1")
        os.makedirs(adapter_path, exist_ok=True)
        
        # Register the adapter
        self.manager.register_adapter(
            name="adapter1",
            path=adapter_path,
            base_model="llama-7b",
            adapter_type="lora",
        )
        
        # Rename the adapter
        result = self.manager.rename_adapter("adapter1", "adapter2")
        
        # Check that the adapter was renamed correctly
        self.assertTrue(result)
        self.assertEqual(len(self.manager.adapter_registry), 1)
        self.assertEqual(self.manager.adapter_registry[0].name, "adapter2")
        self.assertEqual(os.path.basename(self.manager.adapter_registry[0].path), "adapter2")
        
        # Rename a non-existent adapter
        result = self.manager.rename_adapter("non-existent", "adapter3")
        
        # Check that the operation failed
        self.assertFalse(result)
        
        # Rename to an existing name
        self.manager.register_adapter(
            name="adapter3",
            path=os.path.join(self.adapters_dir, "adapter3"),
            base_model="mistral-7b",
            adapter_type="qlora",
        )
        
        result = self.manager.rename_adapter("adapter2", "adapter3")
        
        # Check that the operation failed
        self.assertFalse(result)
        self.assertEqual(len(self.manager.adapter_registry), 2)
        self.assertEqual(self.manager.adapter_registry[0].name, "adapter2")
        self.assertEqual(self.manager.adapter_registry[1].name, "adapter3")


if __name__ == '__main__':
    print("Running adapter support tests...")
    unittest.main()
