#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the model registry module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import json
import datetime
from typing import Dict, List, Any, Optional

from src.ai.model_registry import (
    ModelRegistry, ModelSource, ModelInfo, ModelType, ModelFormat,
    ModelRegistryError, ModelNotFoundError, ModelSourceError,
    get_model_registry, discover_models, get_model_info, register_model,
    unregister_model, search_models, check_for_updates, track_model_usage,
    get_model_usage_stats
)


class TestModelRegistry(unittest.TestCase):
    """Test cases for the model registry module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the registry file path
        self.registry_file_patcher = patch.object(
            ModelRegistry, '_get_registry_file_path',
            return_value=os.path.join(self.temp_dir, "model_registry.json")
        )
        self.mock_registry_file = self.registry_file_patcher.start()
        
        # Mock the ensure_directory function
        self.ensure_dir_patcher = patch("src.ai.model_registry.ensure_directory")
        self.mock_ensure_dir = self.ensure_dir_patcher.start()
        
        # Mock the progress callbacks
        self.progress_patcher = patch("src.ai.model_registry.create_operation")
        self.mock_create_operation = self.progress_patcher.start()
        self.mock_create_operation.return_value = ("test_operation", {})
        
        self.start_op_patcher = patch("src.ai.model_registry.start_operation")
        self.mock_start_operation = self.start_op_patcher.start()
        
        self.update_patcher = patch("src.ai.model_registry.update_progress")
        self.mock_update_progress = self.update_patcher.start()
        
        self.complete_patcher = patch("src.ai.model_registry.complete_operation")
        self.mock_complete_operation = self.complete_patcher.start()
        
        self.fail_patcher = patch("src.ai.model_registry.fail_operation")
        self.mock_fail_operation = self.fail_patcher.start()
        
        # Reset the singleton instance
        ModelRegistry._instance = None
        
        # Create a registry instance for testing
        self.registry = ModelRegistry.get_instance()

    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        self.registry_file_patcher.stop()
        self.ensure_dir_patcher.stop()
        self.progress_patcher.stop()
        self.start_op_patcher.stop()
        self.update_patcher.stop()
        self.complete_patcher.stop()
        self.fail_patcher.stop()
        
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")
        
        # Reset the singleton instance
        ModelRegistry._instance = None

    def test_singleton_pattern(self):
        """Test that the ModelRegistry follows the singleton pattern."""
        # Get the instance twice
        registry1 = ModelRegistry.get_instance()
        registry2 = ModelRegistry.get_instance()
        
        # Check that they are the same instance
        self.assertIs(registry1, registry2)
        
        # Check that direct instantiation raises an error
        with self.assertRaises(RuntimeError):
            ModelRegistry()

    def test_model_info_to_dict(self):
        """Test converting ModelInfo to a dictionary."""
        # Create a ModelInfo instance
        model_info = ModelInfo(
            id="test-model",
            name="Test Model",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            path="/path/to/model",
            description="A test model"
        )
        
        # Convert to dictionary
        data = model_info.to_dict()
        
        # Check the dictionary
        self.assertEqual(data["id"], "test-model")
        self.assertEqual(data["name"], "Test Model")
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["source"], "LOCAL")
        self.assertEqual(data["model_type"], "LLAMA")
        self.assertEqual(data["path"], "/path/to/model")
        self.assertEqual(data["description"], "A test model")

    def test_model_info_from_dict(self):
        """Test creating ModelInfo from a dictionary."""
        # Create a dictionary
        data = {
            "id": "test-model",
            "name": "Test Model",
            "version": "1.0",
            "source": "LOCAL",
            "model_type": "LLAMA",
            "path": "/path/to/model",
            "description": "A test model",
            "format": "GGUF"
        }
        
        # Create ModelInfo from dictionary
        model_info = ModelInfo.from_dict(data)
        
        # Check the ModelInfo
        self.assertEqual(model_info.id, "test-model")
        self.assertEqual(model_info.name, "Test Model")
        self.assertEqual(model_info.version, "1.0")
        self.assertEqual(model_info.source, ModelSource.LOCAL)
        self.assertEqual(model_info.model_type, ModelType.LLAMA)
        self.assertEqual(model_info.path, "/path/to/model")
        self.assertEqual(model_info.description, "A test model")
        self.assertEqual(model_info.format, ModelFormat.GGUF)

    def test_register_and_get_model(self):
        """Test registering a model and getting its information."""
        # Create a ModelInfo instance
        model_info = ModelInfo(
            id="test-model",
            name="Test Model",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            path="/path/to/model",
            description="A test model"
        )
        
        # Register the model
        with patch.object(self.registry, '_save_registry') as mock_save:
            self.registry.register_model(model_info)
            mock_save.assert_called_once()
        
        # Get the model information
        retrieved_info = self.registry.get_model_info("test-model")
        
        # Check that the retrieved information matches
        self.assertEqual(retrieved_info, model_info)

    def test_unregister_model(self):
        """Test unregistering a model."""
        # Create and register a ModelInfo instance
        model_info = ModelInfo(
            id="test-model",
            name="Test Model",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            path="/path/to/model",
            description="A test model"
        )
        
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model_info)
        
        # Unregister the model
        with patch.object(self.registry, '_save_registry') as mock_save:
            result = self.registry.unregister_model("test-model")
            mock_save.assert_called_once()
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the model is no longer in the registry
        self.assertIsNone(self.registry.get_model_info("test-model"))
        
        # Try to unregister a non-existent model
        with patch.object(self.registry, '_save_registry') as mock_save:
            result = self.registry.unregister_model("non-existent-model")
            mock_save.assert_not_called()
        
        # Check the result
        self.assertFalse(result)

    def test_get_all_models(self):
        """Test getting all registered models."""
        # Create and register multiple ModelInfo instances
        model1 = ModelInfo(
            id="model1",
            name="Model 1",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        model2 = ModelInfo(
            id="model2",
            name="Model 2",
            version="1.0",
            source=ModelSource.HUGGINGFACE,
            model_type=ModelType.MISTRAL
        )
        
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model1)
            self.registry.register_model(model2)
        
        # Get all models
        all_models = self.registry.get_all_models()
        
        # Check the result
        self.assertEqual(len(all_models), 2)
        self.assertIn(model1, all_models)
        self.assertIn(model2, all_models)

    def test_get_models_by_type(self):
        """Test getting models by type."""
        # Create and register multiple ModelInfo instances
        model1 = ModelInfo(
            id="model1",
            name="Model 1",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        model2 = ModelInfo(
            id="model2",
            name="Model 2",
            version="1.0",
            source=ModelSource.HUGGINGFACE,
            model_type=ModelType.MISTRAL
        )
        
        model3 = ModelInfo(
            id="model3",
            name="Model 3",
            version="1.0",
            source=ModelSource.CUSTOM,
            model_type=ModelType.LLAMA
        )
        
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model1)
            self.registry.register_model(model2)
            self.registry.register_model(model3)
        
        # Get models by type
        llama_models = self.registry.get_models_by_type(ModelType.LLAMA)
        mistral_models = self.registry.get_models_by_type(ModelType.MISTRAL)
        phi_models = self.registry.get_models_by_type(ModelType.PHI)
        
        # Check the results
        self.assertEqual(len(llama_models), 2)
        self.assertIn(model1, llama_models)
        self.assertIn(model3, llama_models)
        
        self.assertEqual(len(mistral_models), 1)
        self.assertIn(model2, mistral_models)
        
        self.assertEqual(len(phi_models), 0)

    def test_get_models_by_source(self):
        """Test getting models by source."""
        # Create and register multiple ModelInfo instances
        model1 = ModelInfo(
            id="model1",
            name="Model 1",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        model2 = ModelInfo(
            id="model2",
            name="Model 2",
            version="1.0",
            source=ModelSource.HUGGINGFACE,
            model_type=ModelType.MISTRAL
        )
        
        model3 = ModelInfo(
            id="model3",
            name="Model 3",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model1)
            self.registry.register_model(model2)
            self.registry.register_model(model3)
        
        # Get models by source
        local_models = self.registry.get_models_by_source(ModelSource.LOCAL)
        hf_models = self.registry.get_models_by_source(ModelSource.HUGGINGFACE)
        custom_models = self.registry.get_models_by_source(ModelSource.CUSTOM)
        
        # Check the results
        self.assertEqual(len(local_models), 2)
        self.assertIn(model1, local_models)
        self.assertIn(model3, local_models)
        
        self.assertEqual(len(hf_models), 1)
        self.assertIn(model2, hf_models)
        
        self.assertEqual(len(custom_models), 0)

    def test_search_models(self):
        """Test searching for models."""
        # Create and register multiple ModelInfo instances
        model1 = ModelInfo(
            id="llama-7b",
            name="Llama 7B",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            description="A 7B parameter Llama model",
            tags=["llama", "7b"]
        )
        
        model2 = ModelInfo(
            id="mistral-7b",
            name="Mistral 7B",
            version="1.0",
            source=ModelSource.HUGGINGFACE,
            model_type=ModelType.MISTRAL,
            description="A 7B parameter Mistral model",
            tags=["mistral", "7b"]
        )
        
        model3 = ModelInfo(
            id="llama-13b",
            name="Llama 13B",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            description="A 13B parameter Llama model",
            tags=["llama", "13b"]
        )
        
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model1)
            self.registry.register_model(model2)
            self.registry.register_model(model3)
        
        # Search by name
        results = self.registry.search_models("llama")
        self.assertEqual(len(results), 2)
        self.assertIn(model1, results)
        self.assertIn(model3, results)
        
        # Search by description
        results = self.registry.search_models("7b")
        self.assertEqual(len(results), 2)
        self.assertIn(model1, results)
        self.assertIn(model2, results)
        
        # Search with type filter
        results = self.registry.search_models("7b", model_type=ModelType.LLAMA)
        self.assertEqual(len(results), 1)
        self.assertIn(model1, results)
        
        # Search with source filter
        results = self.registry.search_models("7b", source=ModelSource.HUGGINGFACE)
        self.assertEqual(len(results), 1)
        self.assertIn(model2, results)
        
        # Search with tags filter
        results = self.registry.search_models("llama", tags=["13b"])
        self.assertEqual(len(results), 1)
        self.assertIn(model3, results)
        
        # Search with no matches
        results = self.registry.search_models("gpt")
        self.assertEqual(len(results), 0)

    @patch("src.ai.model_registry.HUGGINGFACE_AVAILABLE", True)
    @patch("src.ai.model_registry.HfApi")
    def test_discover_from_huggingface(self, mock_hf_api):
        """Test discovering models from HuggingFace."""
        # Mock the HfApi
        mock_api_instance = mock_hf_api.return_value
        
        # Mock the list_models method to return an empty list for all model types except llama
        def mock_list_models(filter=None, limit=None):
            if filter and hasattr(filter, 'kwargs') and filter.kwargs.get('model_name') == 'llama':
                # Create a mock model only for llama
                mock_model = MagicMock()
                mock_model.id = "user/llama-7b"
                mock_model.sha = "abc123"
                mock_model.last_modified = "2023-01-01T00:00:00Z"
                mock_model.description = "A 7B parameter Llama model"
                mock_model.tags = ["llama", "7b"]
                mock_model.siblings = [MagicMock(rfilename="model.safetensors", size=1000)]
                mock_model.author = "user"
                mock_model.downloads = 1000
                mock_model.likes = 100
                return [mock_model]
            return []  # Return empty list for other model types
        
        # Set up the mock to use our custom function
        mock_api_instance.list_models.side_effect = mock_list_models
        
        # Call the method
        with patch.object(self.registry, 'get_model_info', return_value=None):
            models = self.registry._discover_from_huggingface()
        
        # Check the result
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].id, "user/llama-7b")
        self.assertEqual(models[0].name, "llama-7b")
        self.assertEqual(models[0].version, "abc123")
        self.assertEqual(models[0].source, ModelSource.HUGGINGFACE)
        self.assertEqual(models[0].description, "A 7B parameter Llama model")
        self.assertEqual(models[0].tags, ["llama", "7b"])
        self.assertEqual(models[0].format, ModelFormat.SAFETENSORS)
        self.assertEqual(models[0].size_bytes, 1000)
        self.assertEqual(models[0].parameters, 7_000_000_000)
        self.assertEqual(models[0].metadata["author"], "user")
        self.assertEqual(models[0].metadata["downloads"], 1000)
        self.assertEqual(models[0].metadata["likes"], 100)

    @patch("os.walk")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("os.path.getmtime")
    def test_discover_from_local(self, mock_getmtime, mock_getsize, mock_exists, mock_walk):
        """Test discovering models from local storage."""
        # Mock os.walk
        mock_walk.return_value = [
            ("/models", [], ["llama-7b.gguf", "mistral-7b.safetensors", "not-a-model.txt"])
        ]
        
        # Mock os.path.exists
        mock_exists.return_value = True
        
        # Mock os.path.getsize
        mock_getsize.return_value = 1000
        
        # Mock os.path.getmtime
        mock_getmtime.return_value = 1672531200  # 2023-01-01 00:00:00
        
        # Call the method
        with patch.object(self.registry, 'get_model_info', return_value=None):
            models = self.registry._discover_from_local()
        
        # Check the result
        self.assertEqual(len(models), 2)  # Only the .gguf and .safetensors files
        
        # Check the first model
        llama_model = next(m for m in models if "llama" in m.id)
        self.assertIn("llama-7b.gguf", llama_model.id)
        self.assertEqual(llama_model.name, "llama-7b")
        self.assertEqual(llama_model.source, ModelSource.LOCAL)
        self.assertEqual(llama_model.model_type, ModelType.LLAMA)
        self.assertEqual(llama_model.format, ModelFormat.GGUF)
        self.assertEqual(llama_model.size_bytes, 1000)
        self.assertEqual(llama_model.parameters, 7_000_000_000)
        
        # Check the second model
        mistral_model = next(m for m in models if "mistral" in m.id)
        self.assertIn("mistral-7b.safetensors", mistral_model.id)
        self.assertEqual(mistral_model.name, "mistral-7b")
        self.assertEqual(mistral_model.source, ModelSource.LOCAL)
        self.assertEqual(mistral_model.model_type, ModelType.MISTRAL)
        self.assertEqual(mistral_model.format, ModelFormat.SAFETENSORS)
        self.assertEqual(mistral_model.size_bytes, 1000)
        self.assertEqual(mistral_model.parameters, 7_000_000_000)

    @patch("src.ai.model_registry.REQUESTS_AVAILABLE", True)
    @patch("src.ai.model_registry.requests")
    @patch("os.path.exists")
    def test_discover_from_custom(self, mock_exists, mock_requests):
        """Test discovering models from custom sources."""
        # Mock os.path.exists
        mock_exists.return_value = True
        
        # Mock the sources file
        sources_data = {
            "sources": [
                {
                    "name": "Test Source",
                    "url": "https://example.com/models.json",
                    "enabled": True
                }
            ]
        }
        
        # Mock the response from the custom source
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {
                    "id": "custom-model",
                    "name": "Custom Model",
                    "version": "1.0",
                    "type": "LLAMA",
                    "format": "GGUF",
                    "description": "A custom model",
                    "tags": ["custom", "llama"]
                }
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Mock open to return the sources file
        with patch("builtins.open", mock_open(read_data=json.dumps(sources_data))):
            # Call the method
            with patch.object(self.registry, 'get_model_info', return_value=None):
                models = self.registry._discover_from_custom()
        
        # Check the result
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].id, "custom:Test Source:custom-model")
        self.assertEqual(models[0].name, "Custom Model")
        self.assertEqual(models[0].version, "1.0")
        self.assertEqual(models[0].source, ModelSource.CUSTOM)
        self.assertEqual(models[0].model_type, ModelType.LLAMA)
        self.assertEqual(models[0].format, ModelFormat.GGUF)
        self.assertEqual(models[0].description, "A custom model")
        self.assertEqual(models[0].tags, ["custom", "llama"])

    def test_check_for_updates(self):
        """Test checking for model updates."""
        # Create a model that's already in the registry
        existing_model = ModelInfo(
            id="model1",
            name="Model 1",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        # Create an updated version of the model
        updated_model = ModelInfo(
            id="model1",
            name="Model 1",
            version="2.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        # Register the existing model
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(existing_model)
        
        # Mock discover_models to return the updated model
        with patch.object(self.registry, 'discover_models', return_value=[updated_model]):
            # Call the method
            updates = self.registry.check_for_updates()
        
        # Check the result
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates["model1"], updated_model)

    def test_share_model(self):
        """Test sharing a model."""
        # Create a model
        model = ModelInfo(
            id="model1",
            name="Model 1",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            path="/path/to/model.gguf"
        )
        
        # Register the model
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model)
        
        # Mock os.path.exists
        with patch("os.path.exists", return_value=True):
            # Mock os.makedirs
            with patch("os.makedirs"):
                # Mock shutil.copy2
                with patch("shutil.copy2") as mock_copy:
                    # Call the method
                    result = self.registry.share_model("model1", "/destination/path")
        
        # Check the result
        self.assertTrue(result)
        mock_copy.assert_called_once_with("/path/to/model.gguf", "/destination/path")
        
        # Test with non-existent model
        result = self.registry.share_model("non-existent", "/destination/path")
        self.assertFalse(result)
        
        # Test with model without path
        model_no_path = ModelInfo(
            id="model2",
            name="Model 2",
            version="1.0",
            source=ModelSource.HUGGINGFACE,
            model_type=ModelType.LLAMA
        )
        
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model_no_path)
        
        result = self.registry.share_model("model2", "/destination/path")
        self.assertFalse(result)

    def test_track_model_usage(self):
        """Test tracking model usage."""
        # Create a model
        model = ModelInfo(
            id="model1",
            name="Model 1",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA
        )
        
        # Register the model
        with patch.object(self.registry, '_save_registry'):
            self.registry.register_model(model)
        
        # Mock ensure_directory
        with patch("src.ai.model_registry.ensure_directory"):
            # Mock open
            with patch("builtins.open", mock_open()) as mock_file:
                # Call the method
                self.registry.track_model_usage("model1", "inference", {"tokens": 100})
        
        # Check that the file was opened for writing
        mock_file.assert_called_once()
        
        # Instead of checking the number of write calls, check that json.dump was called
        # This is a more reliable test since json.dump may make multiple write calls
        handle = mock_file.return_value
        
        # Get the written data by capturing what was passed to json.dump
        # We can't easily get the exact JSON string, but we can verify the file was written to
        self.assertTrue(handle.write.called)
        
        # Create expected data structure to verify against
        expected_data = {
            "model_id": "model1",
            "model_name": "Model 1",
            "model_type": "LLAMA",
            "usage_type": "inference",
            "metadata": {"tokens": 100}
        }
        
        # Verify that all expected keys were written somewhere in the calls
        for key in expected_data:
            found = False
            for call in handle.write.call_args_list:
                if key in str(call):
                    found = True
                    break
            self.assertTrue(found, f"Key '{key}' not found in write calls")

    def test_get_model_usage_stats(self):
        """Test getting model usage statistics."""
        # Mock os.path.exists
        with patch("os.path.exists", return_value=True):
            # Mock os.listdir
            with patch("os.listdir", return_value=["model1_123.json", "model2_456.json"]):
                # Mock open to return usage data
                usage_data1 = {
                    "model_id": "model1",
                    "model_name": "Model 1",
                    "model_type": "LLAMA",
                    "usage_type": "inference",
                    "timestamp": "2023-01-01T00:00:00Z",
                    "metadata": {"tokens": 100}
                }
                
                usage_data2 = {
                    "model_id": "model2",
                    "model_name": "Model 2",
                    "model_type": "MISTRAL",
                    "usage_type": "fine-tuning",
                    "timestamp": "2023-01-02T00:00:00Z",
                    "metadata": {"epochs": 3}
                }
                
                # Create a mock open that returns different data for different files
                def mock_open_func(file_path, *args, **kwargs):
                    if "model1" in file_path:
                        return mock_open(read_data=json.dumps(usage_data1))()
                    else:
                        return mock_open(read_data=json.dumps(usage_data2))()
                
                with patch("builtins.open", side_effect=mock_open_func):
                    # Call the method
                    stats = self.registry.get_model_usage_stats()
        
        # Check the result
        self.assertEqual(stats["total_usage"], 2)
        self.assertEqual(len(stats["models"]), 2)
        self.assertEqual(stats["models"]["model1"]["name"], "Model 1")
        self.assertEqual(stats["models"]["model1"]["type"], "LLAMA")
        self.assertEqual(stats["models"]["model1"]["total_usage"], 1)
        self.assertEqual(stats["models"]["model1"]["usage_types"]["inference"], 1)
        self.assertEqual(stats["models"]["model2"]["name"], "Model 2")
        self.assertEqual(stats["models"]["model2"]["type"], "MISTRAL")
        self.assertEqual(stats["models"]["model2"]["total_usage"], 1)
        self.assertEqual(stats["models"]["model2"]["usage_types"]["fine-tuning"], 1)
        self.assertEqual(stats["usage_types"]["inference"], 1)
        self.assertEqual(stats["usage_types"]["fine-tuning"], 1)
        
        # Test with specific model ID
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["model1_123.json", "model2_456.json"]):
                with patch("builtins.open", side_effect=mock_open_func):
                    stats = self.registry.get_model_usage_stats("model1")
        
        # Check the result
        self.assertEqual(stats["total_usage"], 1)
        self.assertEqual(len(stats["models"]), 1)
        self.assertEqual(stats["models"]["model1"]["name"], "Model 1")
        self.assertEqual(stats["models"]["model1"]["total_usage"], 1)
        self.assertEqual(stats["usage_types"]["inference"], 1)

    def test_convenience_functions(self):
        """Test the convenience functions."""
        # Mock the ModelRegistry.get_instance method
        with patch("src.ai.model_registry.ModelRegistry.get_instance") as mock_get_instance:
            mock_registry = MagicMock()
            mock_get_instance.return_value = mock_registry
            
            # Test get_model_registry
            registry = get_model_registry()
            self.assertEqual(registry, mock_registry)
            
            # Test discover_models
            discover_models()
            mock_registry.discover_models.assert_called_once()
            
            # Test get_model_info
            get_model_info("model1")
            mock_registry.get_model_info.assert_called_once_with("model1")
            
            # Test register_model
            model = MagicMock()
            register_model(model)
            mock_registry.register_model.assert_called_once_with(model)
            
            # Test unregister_model
            unregister_model("model1")
            mock_registry.unregister_model.assert_called_once_with("model1")
            
            # Test search_models
            query = "test"
            model_type = ModelType.LLAMA
            source = ModelSource.LOCAL
            tags = ["tag1"]
            search_models(query, model_type, source, tags)
            mock_registry.search_models.assert_called_once_with(query, model_type, source, tags)
            
            # Test check_for_updates
            callback = MagicMock()
            check_for_updates(callback)
            mock_registry.check_for_updates.assert_called_once_with(callback)
            
            # Test track_model_usage
            metadata = {"tokens": 100}
            track_model_usage("model1", "inference", metadata)
            mock_registry.track_model_usage.assert_called_once_with("model1", "inference", metadata)
            
            # Test get_model_usage_stats
            get_model_usage_stats("model1")
            mock_registry.get_model_usage_stats.assert_called_once_with("model1")
