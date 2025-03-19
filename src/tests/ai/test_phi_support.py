#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the phi_support module.

This module contains tests for the Phi model support functionality,
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
from src.ai.phi_support import (
    check_phi_dependencies, is_phi_available, get_available_phi_models,
    download_phi_model, load_phi_model, generate_text_with_phi,
    async_generate_text_with_phi, format_chat_prompt, chat_with_phi,
    async_chat_with_phi, DEFAULT_PHI_MODELS
)
from src.ai.local_models import (
    ModelNotAvailableError, ModelLoadError, InferenceError
)


class TestPhiSupport(BaseTest):
    """Unit tests for the phi_support module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a mock models directory
        self.models_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Create a mock Phi model directory
        self.phi_model_dir = os.path.join(self.models_dir, "microsoft_phi-2")
        os.makedirs(self.phi_model_dir, exist_ok=True)
        
        # Create a metadata file
        metadata = {
            "name": "microsoft/phi-2",
            "task": "text-generation",
            "quantized": False,
            "download_date": "2025-03-11 12:00:00",
            "description": "Phi-2 model for text generation",
            "model_type": "phi"
        }
        
        import json
        with open(os.path.join(self.phi_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    
    def tearDown(self):
        """Tear down test fixtures."""
        super().tearDown()
    
    @patch("src.ai.phi_support.TORCH_AVAILABLE", True)
    @patch("src.ai.phi_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.phi_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.phi_support.ACCELERATE_AVAILABLE", True)
    def test_check_phi_dependencies_all_available(self):
        """Test checking dependencies when all are available."""
        # Check dependencies
        deps = check_phi_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(deps, dict)
        self.assertEqual(len(deps), 4)
        self.assertTrue(deps["torch"])
        self.assertTrue(deps["transformers"])
        self.assertTrue(deps["bitsandbytes"])
        self.assertTrue(deps["accelerate"])
    
    @patch("src.ai.phi_support.TORCH_AVAILABLE", False)
    @patch("src.ai.phi_support.TRANSFORMERS_AVAILABLE", False)
    @patch("src.ai.phi_support.BITSANDBYTES_AVAILABLE", False)
    @patch("src.ai.phi_support.ACCELERATE_AVAILABLE", False)
    def test_check_phi_dependencies_none_available(self):
        """Test checking dependencies when none are available."""
        # Check dependencies
        deps = check_phi_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(deps, dict)
        self.assertEqual(len(deps), 4)
        self.assertFalse(deps["torch"])
        self.assertFalse(deps["transformers"])
        self.assertFalse(deps["bitsandbytes"])
        self.assertFalse(deps["accelerate"])
    
    @patch("src.ai.phi_support.TORCH_AVAILABLE", True)
    @patch("src.ai.phi_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.phi_support.BITSANDBYTES_AVAILABLE", False)
    @patch("src.ai.phi_support.ACCELERATE_AVAILABLE", False)
    def test_is_phi_available_minimal_deps(self):
        """Test checking if Phi is available with minimal dependencies."""
        # Check availability
        available = is_phi_available()
        
        # Verify availability
        self.assertTrue(available)
    
    @patch("src.ai.phi_support.TORCH_AVAILABLE", False)
    @patch("src.ai.phi_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.phi_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.phi_support.ACCELERATE_AVAILABLE", True)
    def test_is_phi_available_missing_torch(self):
        """Test checking if Phi is available when torch is missing."""
        # Check availability
        available = is_phi_available()
        
        # Verify availability
        self.assertFalse(available)
    
    @patch("src.ai.phi_support.TORCH_AVAILABLE", True)
    @patch("src.ai.phi_support.TRANSFORMERS_AVAILABLE", False)
    @patch("src.ai.phi_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.phi_support.ACCELERATE_AVAILABLE", True)
    def test_is_phi_available_missing_transformers(self):
        """Test checking if Phi is available when transformers is missing."""
        # Check availability
        available = is_phi_available()
        
        # Verify availability
        self.assertFalse(available)
    
    @patch("src.ai.phi_support.is_phi_available")
    def test_get_available_phi_models_not_available(self, mock_available):
        """Test getting available Phi models when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Get available models
        models = get_available_phi_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 0)
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.get_models_directory")
    def test_get_available_phi_models(self, mock_get_models_dir, mock_available):
        """Test getting available Phi models."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        
        # Get available models
        models = get_available_phi_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "microsoft/phi-2")
        self.assertEqual(models[0]["model_type"], "phi")
    
    @patch("src.ai.phi_support.is_phi_available")
    def test_download_phi_model_not_available(self, mock_available):
        """Test downloading a Phi model when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Download model
        result = download_phi_model("microsoft/phi-2")
        
        # Verify result
        self.assertIsNone(result)
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.get_models_directory")
    @patch("src.ai.phi_support.ensure_directory")
    @patch("src.ai.phi_support.AutoTokenizer")
    @patch("src.ai.phi_support.AutoModelForCausalLM")
    def test_download_phi_model(self, mock_model, mock_tokenizer, mock_ensure_dir, 
                              mock_get_models_dir, mock_available):
        """Test downloading a Phi model."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Download model
        result = download_phi_model("microsoft/phi-2")
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verify mocks were called
        mock_ensure_dir.assert_called()
        mock_tokenizer.from_pretrained.assert_called_once_with("microsoft/phi-2")
        mock_model.from_pretrained.assert_called_once()
        mock_model_instance.save_pretrained.assert_called_once()
        mock_tokenizer_instance.save_pretrained.assert_called_once()
    
    @patch("src.ai.phi_support.is_phi_available")
    def test_load_phi_model_not_available(self, mock_available):
        """Test loading a Phi model when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to load model
        with self.assertRaises(ModelNotAvailableError):
            load_phi_model("microsoft/phi-2")
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.download_phi_model")
    def test_load_phi_model_download_fails(self, mock_download, mock_available):
        """Test loading a Phi model when download fails."""
        # Set up mocks
        mock_available.return_value = True
        mock_download.return_value = None
        
        # Try to load model
        with self.assertRaises(ModelLoadError):
            load_phi_model("nonexistent_model")
        
        # Verify download was attempted
        mock_download.assert_called_once_with("nonexistent_model", None)
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.get_models_directory")
    @patch("src.ai.phi_support.AutoTokenizer")
    @patch("src.ai.phi_support.AutoModelForCausalLM")
    def test_load_phi_model(self, mock_model, mock_tokenizer, mock_get_models_dir, mock_available):
        """Test loading a Phi model."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model
        model, tokenizer = load_phi_model(self.phi_model_dir)
        
        # Verify model and tokenizer
        self.assertEqual(model, mock_model_instance)
        self.assertEqual(tokenizer, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_tokenizer.from_pretrained.assert_called_once_with(self.phi_model_dir)
        mock_model.from_pretrained.assert_called_once()
    
    @patch("src.ai.phi_support.is_phi_available")
    def test_generate_text_with_phi_not_available(self, mock_available):
        """Test generating text with Phi when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to generate text
        with self.assertRaises(ModelNotAvailableError):
            generate_text_with_phi("Test prompt")
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.load_phi_model")
    def test_generate_text_with_phi_load_fails(self, mock_load, mock_available):
        """Test generating text with Phi when model loading fails."""
        # Set up mocks
        mock_available.return_value = True
        mock_load.side_effect = ModelLoadError("Test error")
        
        # Try to generate text
        with self.assertRaises(InferenceError):
            generate_text_with_phi("Test prompt")
        
        # Verify load was attempted
        mock_load.assert_called_once()
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.load_phi_model")
    def test_generate_text_with_phi(self, mock_load, mock_available):
        """Test generating text with Phi."""
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
        result = generate_text_with_phi("Test prompt")
        
        # Verify result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Generated text")
        
        # Verify mocks were called
        mock_load.assert_called_once()
        mock_tokenizer.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.load_phi_model")
    def test_generate_text_with_phi_streaming(self, mock_load, mock_available):
        """Test generating text with Phi in streaming mode."""
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
        result = generate_text_with_phi("Test prompt", stream=True, callback=callback, max_length=3)
        
        # Verify result
        self.assertIsNone(result)
        
        # Verify callback was called
        self.assertEqual(callback.call_count, 3)  # Initial token + 2 more tokens
    
    @patch("src.ai.phi_support.threading.Thread")
    def test_async_generate_text_with_phi(self, mock_thread):
        """Test generating text asynchronously with Phi."""
        # Set up callback
        callback = MagicMock()
        
        # Generate text asynchronously
        async_generate_text_with_phi("Test prompt", callback)
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
    
    def test_format_chat_prompt_phi2(self):
        """Test formatting chat prompt for Phi-2."""
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Format prompt for Phi-2
        prompt = format_chat_prompt(messages, "microsoft/phi-2")
        
        # Verify prompt format
        self.assertIn("System: You are a helpful assistant.", prompt)
        self.assertIn("Human: Hello, how are you?", prompt)
        self.assertIn("Assistant: I'm doing well, thank you!", prompt)
        self.assertIn("Human: What can you help me with?", prompt)
        self.assertIn("Assistant: ", prompt)
    
    def test_format_chat_prompt_phi3(self):
        """Test formatting chat prompt for Phi-3."""
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Format prompt for Phi-3
        prompt = format_chat_prompt(messages, "microsoft/Phi-3-mini-4k-instruct")
        
        # Verify prompt format
        self.assertIn("<|system|>", prompt)
        self.assertIn("You are a helpful assistant.", prompt)
        self.assertIn("<|user|>", prompt)
        self.assertIn("Hello, how are you?", prompt)
        self.assertIn("<|assistant|>", prompt)
        self.assertIn("I'm doing well, thank you!", prompt)
        self.assertIn("What can you help me with?", prompt)
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.generate_text_with_phi")
    def test_chat_with_phi(self, mock_generate, mock_available):
        """Test chatting with Phi."""
        # Set up mocks
        mock_available.return_value = True
        mock_generate.return_value = ["<|assistant|>\nI can help with many things!"]
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Chat with Phi
        response = chat_with_phi(messages, "microsoft/Phi-3-mini-4k-instruct")
        
        # Verify response
        self.assertEqual(response, "I can help with many things!")
        
        # Verify generate was called
        mock_generate.assert_called_once()
    
    @patch("src.ai.phi_support.threading.Thread")
    def test_async_chat_with_phi(self, mock_thread):
        """Test chatting asynchronously with Phi."""
        # Set up callback
        callback = MagicMock()
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Chat asynchronously
        async_chat_with_phi(messages, callback)
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


# Pytest-style tests
class TestPhiSupportPytest:
    """Pytest-style tests for the phi_support module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Create a mock models directory
        models_dir = os.path.join(base_test_fixture["test_dir"], "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Create a mock Phi model directory
        phi_model_dir = os.path.join(models_dir, "microsoft_phi-2")
        os.makedirs(phi_model_dir, exist_ok=True)
        
        # Create a metadata file
        metadata = {
            "name": "microsoft/phi-2",
            "task": "text-generation",
            "quantized": False,
            "download_date": "2025-03-11 12:00:00",
            "description": "Phi-2 model for text generation",
            "model_type": "phi"
        }
        
        import json
        with open(os.path.join(phi_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        yield {
            **base_test_fixture,
            "models_dir": models_dir,
            "phi_model_dir": phi_model_dir
        }
    
    @patch("src.ai.phi_support.TORCH_AVAILABLE", True)
    @patch("src.ai.phi_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.phi_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.phi_support.ACCELERATE_AVAILABLE", True)
    def test_check_phi_dependencies_all_available_pytest(self):
        """Test checking dependencies when all are available using pytest style."""
        # Check dependencies
        deps = check_phi_dependencies()
        
        # Verify dependencies
        assert isinstance(deps, dict)
        assert len(deps) == 4
        assert deps["torch"] is True
        assert deps["transformers"] is True
        assert deps["bitsandbytes"] is True
        assert deps["accelerate"] is True
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.get_models_directory")
    def test_get_available_phi_models_pytest(self, mock_get_models_dir, mock_available, setup):
        """Test getting available Phi models using pytest style."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = setup["models_dir"]
        
        # Get available models
        models = get_available_phi_models()
        
        # Verify models
        assert isinstance(models, list)
        assert len(models) == 1
        assert models[0]["name"] == "microsoft/phi-2"
        assert models[0]["model_type"] == "phi"
    
    @patch("src.ai.phi_support.is_phi_available")
    @patch("src.ai.phi_support.load_phi_model")
    def test_generate_text_with_phi_pytest(self, mock_load, mock_available):
        """Test generating text with Phi using pytest style."""
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
        result = generate_text_with_phi("Test prompt")
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Generated text"
        
        # Verify mocks were called
        mock_load.assert_called_once()
        mock_tokenizer.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()
    
    def test_format_chat_prompt_pytest(self):
        """Test formatting chat prompt using pytest style."""
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Format prompt for Phi-3
        prompt = format_chat_prompt(messages, "microsoft/Phi-3-mini-4k-instruct")
        
        # Verify prompt format
        assert "<|system|>" in prompt
        assert "You are a helpful assistant." in prompt
        assert "<|user|>" in prompt
        assert "Hello, how are you?" in prompt
        assert "<|assistant|>" in prompt
        assert "I'm doing well, thank you!" in prompt
        assert "What can you help me with?" in prompt


if __name__ == '__main__':
    unittest.main()
