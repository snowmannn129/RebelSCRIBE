#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the llama_support module.

This module contains tests for the Llama model support functionality,
including dependency checking, model loading, text generation, and error handling.
"""

import os
import unittest
import tempfile
import shutil
import threading
from unittest.mock import patch, MagicMock, call

import pytest
from src.tests.base_test import BaseTest
from src.ai.llama_support import (
    check_llama_dependencies, is_llama_available, get_available_llama_models,
    download_llama_model, load_llama_model, generate_text_with_llama,
    async_generate_text_with_llama, DEFAULT_LLAMA_MODELS
)
from src.ai.local_models import (
    ModelNotAvailableError, ModelLoadError, InferenceError
)


class TestLlamaSupport(BaseTest):
    """Unit tests for the llama_support module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a mock models directory
        self.models_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Create a mock Llama model directory
        self.llama_model_dir = os.path.join(self.models_dir, "meta-llama_Llama-2-7b-hf")
        os.makedirs(self.llama_model_dir, exist_ok=True)
        
        # Create a metadata file
        metadata = {
            "name": "meta-llama/Llama-2-7b-hf",
            "task": "text-generation",
            "quantized": False,
            "download_date": "2025-03-11 12:00:00",
            "description": "Llama 2 7B model for text generation",
            "model_type": "llama"
        }
        
        import json
        with open(os.path.join(self.llama_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    
    def tearDown(self):
        """Tear down test fixtures."""
        super().tearDown()
    
    @patch("src.ai.llama_support.TORCH_AVAILABLE", True)
    @patch("src.ai.llama_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.llama_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.llama_support.ACCELERATE_AVAILABLE", True)
    def test_check_llama_dependencies_all_available(self):
        """Test checking dependencies when all are available."""
        # Check dependencies
        deps = check_llama_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(deps, dict)
        self.assertEqual(len(deps), 4)
        self.assertTrue(deps["torch"])
        self.assertTrue(deps["transformers"])
        self.assertTrue(deps["bitsandbytes"])
        self.assertTrue(deps["accelerate"])
    
    @patch("src.ai.llama_support.TORCH_AVAILABLE", False)
    @patch("src.ai.llama_support.TRANSFORMERS_AVAILABLE", False)
    @patch("src.ai.llama_support.BITSANDBYTES_AVAILABLE", False)
    @patch("src.ai.llama_support.ACCELERATE_AVAILABLE", False)
    def test_check_llama_dependencies_none_available(self):
        """Test checking dependencies when none are available."""
        # Check dependencies
        deps = check_llama_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(deps, dict)
        self.assertEqual(len(deps), 4)
        self.assertFalse(deps["torch"])
        self.assertFalse(deps["transformers"])
        self.assertFalse(deps["bitsandbytes"])
        self.assertFalse(deps["accelerate"])
    
    @patch("src.ai.llama_support.TORCH_AVAILABLE", True)
    @patch("src.ai.llama_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.llama_support.BITSANDBYTES_AVAILABLE", False)
    @patch("src.ai.llama_support.ACCELERATE_AVAILABLE", False)
    def test_is_llama_available_minimal_deps(self):
        """Test checking if Llama is available with minimal dependencies."""
        # Check availability
        available = is_llama_available()
        
        # Verify availability
        self.assertTrue(available)
    
    @patch("src.ai.llama_support.TORCH_AVAILABLE", False)
    @patch("src.ai.llama_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.llama_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.llama_support.ACCELERATE_AVAILABLE", True)
    def test_is_llama_available_missing_torch(self):
        """Test checking if Llama is available when torch is missing."""
        # Check availability
        available = is_llama_available()
        
        # Verify availability
        self.assertFalse(available)
    
    @patch("src.ai.llama_support.TORCH_AVAILABLE", True)
    @patch("src.ai.llama_support.TRANSFORMERS_AVAILABLE", False)
    @patch("src.ai.llama_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.llama_support.ACCELERATE_AVAILABLE", True)
    def test_is_llama_available_missing_transformers(self):
        """Test checking if Llama is available when transformers is missing."""
        # Check availability
        available = is_llama_available()
        
        # Verify availability
        self.assertFalse(available)
    
    @patch("src.ai.llama_support.is_llama_available")
    def test_get_available_llama_models_not_available(self, mock_available):
        """Test getting available Llama models when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Get available models
        models = get_available_llama_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 0)
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.get_models_directory")
    def test_get_available_llama_models(self, mock_get_models_dir, mock_available):
        """Test getting available Llama models."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        
        # Get available models
        models = get_available_llama_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "meta-llama/Llama-2-7b-hf")
        self.assertEqual(models[0]["model_type"], "llama")
    
    @patch("src.ai.llama_support.is_llama_available")
    def test_download_llama_model_not_available(self, mock_available):
        """Test downloading a Llama model when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Download model
        result = download_llama_model("meta-llama/Llama-2-7b-hf")
        
        # Verify result
        self.assertIsNone(result)
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.get_models_directory")
    @patch("src.ai.llama_support.ensure_directory")
    @patch("src.ai.llama_support.LlamaTokenizer")
    @patch("src.ai.llama_support.AutoModelForCausalLM")
    def test_download_llama_model(self, mock_model, mock_tokenizer, mock_ensure_dir, 
                                mock_get_models_dir, mock_available):
        """Test downloading a Llama model."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Download model
        result = download_llama_model("meta-llama/Llama-2-7b-hf")
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verify mocks were called
        mock_ensure_dir.assert_called()
        mock_tokenizer.from_pretrained.assert_called_once_with("meta-llama/Llama-2-7b-hf")
        mock_model.from_pretrained.assert_called_once()
        mock_model_instance.save_pretrained.assert_called_once()
        mock_tokenizer_instance.save_pretrained.assert_called_once()
    
    @patch("src.ai.llama_support.is_llama_available")
    def test_load_llama_model_not_available(self, mock_available):
        """Test loading a Llama model when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to load model
        with self.assertRaises(ModelNotAvailableError):
            load_llama_model("meta-llama/Llama-2-7b-hf")
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.download_llama_model")
    def test_load_llama_model_download_fails(self, mock_download, mock_available):
        """Test loading a Llama model when download fails."""
        # Set up mocks
        mock_available.return_value = True
        mock_download.return_value = None
        
        # Try to load model
        with self.assertRaises(ModelLoadError):
            load_llama_model("nonexistent_model")
        
        # Verify download was attempted
        mock_download.assert_called_once_with("nonexistent_model", None)
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.get_models_directory")
    @patch("src.ai.llama_support.LlamaTokenizer")
    @patch("src.ai.llama_support.AutoModelForCausalLM")
    def test_load_llama_model(self, mock_model, mock_tokenizer, mock_get_models_dir, mock_available):
        """Test loading a Llama model."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model
        model, tokenizer = load_llama_model(self.llama_model_dir)
        
        # Verify model and tokenizer
        self.assertEqual(model, mock_model_instance)
        self.assertEqual(tokenizer, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_tokenizer.from_pretrained.assert_called_once_with(self.llama_model_dir)
        mock_model.from_pretrained.assert_called_once()
    
    @patch("src.ai.llama_support.is_llama_available")
    def test_generate_text_with_llama_not_available(self, mock_available):
        """Test generating text with Llama when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to generate text
        with self.assertRaises(ModelNotAvailableError):
            generate_text_with_llama("Test prompt")
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.load_llama_model")
    def test_generate_text_with_llama_load_fails(self, mock_load, mock_available):
        """Test generating text with Llama when model loading fails."""
        # Set up mocks
        mock_available.return_value = True
        mock_load.side_effect = ModelLoadError("Test error")
        
        # Try to generate text
        with self.assertRaises(InferenceError):
            generate_text_with_llama("Test prompt")
        
        # Verify load was attempted
        mock_load.assert_called_once()
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.load_llama_model")
    def test_generate_text_with_llama(self, mock_load, mock_available):
        """Test generating text with Llama."""
        # Set up mocks
        mock_available.return_value = True
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        # Set up tokenizer mock
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        
        # Set up model mock
        mock_outputs = MagicMock()
        mock_model.generate.return_value = [mock_outputs]
        mock_tokenizer.decode.return_value = "Generated text"
        
        # Generate text
        result = generate_text_with_llama("Test prompt")
        
        # Verify result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Generated text")
        
        # Verify mocks were called
        mock_load.assert_called_once()
        mock_tokenizer.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.load_llama_model")
    def test_generate_text_with_llama_streaming(self, mock_load, mock_available):
        """Test generating text with Llama in streaming mode."""
        # Set up mocks
        mock_available.return_value = True
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        # Set up tokenizer mock
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        
        # Set up model mock
        mock_outputs = MagicMock()
        mock_model.generate.return_value = [mock_outputs]
        mock_tokenizer.decode.return_value = "t"
        mock_outputs.__getitem__.return_value = MagicMock()
        mock_outputs.__getitem__.return_value.__getitem__.return_value = MagicMock()
        mock_outputs.__getitem__.return_value.__getitem__.return_value.unsqueeze.return_value = MagicMock()
        mock_outputs.__getitem__.return_value.__getitem__.return_value.unsqueeze.return_value.unsqueeze.return_value = MagicMock()
        
        # Set up callback
        callback = MagicMock()
        
        # Generate text with streaming
        result = generate_text_with_llama("Test prompt", stream=True, callback=callback, max_length=3)
        
        # Verify result
        self.assertIsNone(result)
        
        # Verify callback was called
        self.assertEqual(callback.call_count, 3)  # Initial token + 2 more tokens
    
    @patch("src.ai.llama_support.threading.Thread")
    def test_async_generate_text_with_llama(self, mock_thread):
        """Test generating text asynchronously with Llama."""
        # Set up callback
        callback = MagicMock()
        
        # Generate text asynchronously
        async_generate_text_with_llama("Test prompt", callback)
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


# Pytest-style tests
class TestLlamaSupportPytest:
    """Pytest-style tests for the llama_support module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Create a mock models directory
        models_dir = os.path.join(base_test_fixture["test_dir"], "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Create a mock Llama model directory
        llama_model_dir = os.path.join(models_dir, "meta-llama_Llama-2-7b-hf")
        os.makedirs(llama_model_dir, exist_ok=True)
        
        # Create a metadata file
        metadata = {
            "name": "meta-llama/Llama-2-7b-hf",
            "task": "text-generation",
            "quantized": False,
            "download_date": "2025-03-11 12:00:00",
            "description": "Llama 2 7B model for text generation",
            "model_type": "llama"
        }
        
        import json
        with open(os.path.join(llama_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        yield {
            **base_test_fixture,
            "models_dir": models_dir,
            "llama_model_dir": llama_model_dir
        }
    
    @patch("src.ai.llama_support.TORCH_AVAILABLE", True)
    @patch("src.ai.llama_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.llama_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.llama_support.ACCELERATE_AVAILABLE", True)
    def test_check_llama_dependencies_all_available_pytest(self):
        """Test checking dependencies when all are available using pytest style."""
        # Check dependencies
        deps = check_llama_dependencies()
        
        # Verify dependencies
        assert isinstance(deps, dict)
        assert len(deps) == 4
        assert deps["torch"] is True
        assert deps["transformers"] is True
        assert deps["bitsandbytes"] is True
        assert deps["accelerate"] is True
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.get_models_directory")
    def test_get_available_llama_models_pytest(self, mock_get_models_dir, mock_available, setup):
        """Test getting available Llama models using pytest style."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = setup["models_dir"]
        
        # Get available models
        models = get_available_llama_models()
        
        # Verify models
        assert isinstance(models, list)
        assert len(models) == 1
        assert models[0]["name"] == "meta-llama/Llama-2-7b-hf"
        assert models[0]["model_type"] == "llama"
    
    @patch("src.ai.llama_support.is_llama_available")
    @patch("src.ai.llama_support.load_llama_model")
    def test_generate_text_with_llama_pytest(self, mock_load, mock_available):
        """Test generating text with Llama using pytest style."""
        # Set up mocks
        mock_available.return_value = True
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        # Set up tokenizer mock
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        
        # Set up model mock
        mock_outputs = MagicMock()
        mock_model.generate.return_value = [mock_outputs]
        mock_tokenizer.decode.return_value = "Generated text"
        
        # Generate text
        result = generate_text_with_llama("Test prompt")
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Generated text"
        
        # Verify mocks were called
        mock_load.assert_called_once()
        mock_tokenizer.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()


if __name__ == '__main__':
    unittest.main()
