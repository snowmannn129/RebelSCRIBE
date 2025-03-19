#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the mistral_support module.

This module contains tests for the Mistral model support functionality,
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
from src.ai.mistral_support import (
    check_mistral_dependencies, is_mistral_available, get_available_mistral_models,
    download_mistral_model, load_mistral_model, generate_text_with_mistral,
    async_generate_text_with_mistral, format_chat_prompt, chat_with_mistral,
    async_chat_with_mistral, DEFAULT_MISTRAL_MODELS
)
from src.ai.local_models import (
    ModelNotAvailableError, ModelLoadError, InferenceError
)


class TestMistralSupport(BaseTest):
    """Unit tests for the mistral_support module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a mock models directory
        self.models_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Create a mock Mistral model directory
        self.mistral_model_dir = os.path.join(self.models_dir, "mistralai_Mistral-7B-v0.1")
        os.makedirs(self.mistral_model_dir, exist_ok=True)
        
        # Create a metadata file
        metadata = {
            "name": "mistralai/Mistral-7B-v0.1",
            "task": "text-generation",
            "quantized": False,
            "download_date": "2025-03-11 12:00:00",
            "description": "Mistral 7B model for text generation",
            "model_type": "mistral"
        }
        
        import json
        with open(os.path.join(self.mistral_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    
    def tearDown(self):
        """Tear down test fixtures."""
        super().tearDown()
    
    @patch("src.ai.mistral_support.TORCH_AVAILABLE", True)
    @patch("src.ai.mistral_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.mistral_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.mistral_support.ACCELERATE_AVAILABLE", True)
    def test_check_mistral_dependencies_all_available(self):
        """Test checking dependencies when all are available."""
        # Check dependencies
        deps = check_mistral_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(deps, dict)
        self.assertEqual(len(deps), 4)
        self.assertTrue(deps["torch"])
        self.assertTrue(deps["transformers"])
        self.assertTrue(deps["bitsandbytes"])
        self.assertTrue(deps["accelerate"])
    
    @patch("src.ai.mistral_support.TORCH_AVAILABLE", False)
    @patch("src.ai.mistral_support.TRANSFORMERS_AVAILABLE", False)
    @patch("src.ai.mistral_support.BITSANDBYTES_AVAILABLE", False)
    @patch("src.ai.mistral_support.ACCELERATE_AVAILABLE", False)
    def test_check_mistral_dependencies_none_available(self):
        """Test checking dependencies when none are available."""
        # Check dependencies
        deps = check_mistral_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(deps, dict)
        self.assertEqual(len(deps), 4)
        self.assertFalse(deps["torch"])
        self.assertFalse(deps["transformers"])
        self.assertFalse(deps["bitsandbytes"])
        self.assertFalse(deps["accelerate"])
    
    @patch("src.ai.mistral_support.TORCH_AVAILABLE", True)
    @patch("src.ai.mistral_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.mistral_support.BITSANDBYTES_AVAILABLE", False)
    @patch("src.ai.mistral_support.ACCELERATE_AVAILABLE", False)
    def test_is_mistral_available_minimal_deps(self):
        """Test checking if Mistral is available with minimal dependencies."""
        # Check availability
        available = is_mistral_available()
        
        # Verify availability
        self.assertTrue(available)
    
    @patch("src.ai.mistral_support.TORCH_AVAILABLE", False)
    @patch("src.ai.mistral_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.mistral_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.mistral_support.ACCELERATE_AVAILABLE", True)
    def test_is_mistral_available_missing_torch(self):
        """Test checking if Mistral is available when torch is missing."""
        # Check availability
        available = is_mistral_available()
        
        # Verify availability
        self.assertFalse(available)
    
    @patch("src.ai.mistral_support.TORCH_AVAILABLE", True)
    @patch("src.ai.mistral_support.TRANSFORMERS_AVAILABLE", False)
    @patch("src.ai.mistral_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.mistral_support.ACCELERATE_AVAILABLE", True)
    def test_is_mistral_available_missing_transformers(self):
        """Test checking if Mistral is available when transformers is missing."""
        # Check availability
        available = is_mistral_available()
        
        # Verify availability
        self.assertFalse(available)
    
    @patch("src.ai.mistral_support.is_mistral_available")
    def test_get_available_mistral_models_not_available(self, mock_available):
        """Test getting available Mistral models when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Get available models
        models = get_available_mistral_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 0)
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.get_models_directory")
    def test_get_available_mistral_models(self, mock_get_models_dir, mock_available):
        """Test getting available Mistral models."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        
        # Get available models
        models = get_available_mistral_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "mistralai/Mistral-7B-v0.1")
        self.assertEqual(models[0]["model_type"], "mistral")
    
    @patch("src.ai.mistral_support.is_mistral_available")
    def test_download_mistral_model_not_available(self, mock_available):
        """Test downloading a Mistral model when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Download model
        result = download_mistral_model("mistralai/Mistral-7B-v0.1")
        
        # Verify result
        self.assertIsNone(result)
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.get_models_directory")
    @patch("src.ai.mistral_support.ensure_directory")
    @patch("src.ai.mistral_support.AutoTokenizer")
    @patch("src.ai.mistral_support.AutoModelForCausalLM")
    def test_download_mistral_model(self, mock_model, mock_tokenizer, mock_ensure_dir, 
                                  mock_get_models_dir, mock_available):
        """Test downloading a Mistral model."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Download model
        result = download_mistral_model("mistralai/Mistral-7B-v0.1")
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verify mocks were called
        mock_ensure_dir.assert_called()
        mock_tokenizer.from_pretrained.assert_called_once_with("mistralai/Mistral-7B-v0.1")
        mock_model.from_pretrained.assert_called_once()
        mock_model_instance.save_pretrained.assert_called_once()
        mock_tokenizer_instance.save_pretrained.assert_called_once()
    
    @patch("src.ai.mistral_support.is_mistral_available")
    def test_load_mistral_model_not_available(self, mock_available):
        """Test loading a Mistral model when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to load model
        with self.assertRaises(ModelNotAvailableError):
            load_mistral_model("mistralai/Mistral-7B-v0.1")
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.download_mistral_model")
    def test_load_mistral_model_download_fails(self, mock_download, mock_available):
        """Test loading a Mistral model when download fails."""
        # Set up mocks
        mock_available.return_value = True
        mock_download.return_value = None
        
        # Try to load model
        with self.assertRaises(ModelLoadError):
            load_mistral_model("nonexistent_model")
        
        # Verify download was attempted
        mock_download.assert_called_once_with("nonexistent_model", None)
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.get_models_directory")
    @patch("src.ai.mistral_support.AutoTokenizer")
    @patch("src.ai.mistral_support.AutoModelForCausalLM")
    def test_load_mistral_model(self, mock_model, mock_tokenizer, mock_get_models_dir, mock_available):
        """Test loading a Mistral model."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = self.models_dir
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model
        model, tokenizer = load_mistral_model(self.mistral_model_dir)
        
        # Verify model and tokenizer
        self.assertEqual(model, mock_model_instance)
        self.assertEqual(tokenizer, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_tokenizer.from_pretrained.assert_called_once_with(self.mistral_model_dir)
        mock_model.from_pretrained.assert_called_once()
    
    @patch("src.ai.mistral_support.is_mistral_available")
    def test_generate_text_with_mistral_not_available(self, mock_available):
        """Test generating text with Mistral when not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to generate text
        with self.assertRaises(ModelNotAvailableError):
            generate_text_with_mistral("Test prompt")
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.load_mistral_model")
    def test_generate_text_with_mistral_load_fails(self, mock_load, mock_available):
        """Test generating text with Mistral when model loading fails."""
        # Set up mocks
        mock_available.return_value = True
        mock_load.side_effect = ModelLoadError("Test error")
        
        # Try to generate text
        with self.assertRaises(InferenceError):
            generate_text_with_mistral("Test prompt")
        
        # Verify load was attempted
        mock_load.assert_called_once()
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.load_mistral_model")
    def test_generate_text_with_mistral(self, mock_load, mock_available):
        """Test generating text with Mistral."""
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
        result = generate_text_with_mistral("Test prompt")
        
        # Verify result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Generated text")
        
        # Verify mocks were called
        mock_load.assert_called_once()
        mock_tokenizer.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.load_mistral_model")
    def test_generate_text_with_mistral_streaming(self, mock_load, mock_available):
        """Test generating text with Mistral in streaming mode."""
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
        result = generate_text_with_mistral("Test prompt", stream=True, callback=callback, max_length=3)
        
        # Verify result
        self.assertIsNone(result)
        
        # Verify callback was called
        self.assertEqual(callback.call_count, 3)  # Initial token + 2 more tokens
    
    @patch("src.ai.mistral_support.threading.Thread")
    def test_async_generate_text_with_mistral(self, mock_thread):
        """Test generating text asynchronously with Mistral."""
        # Set up callback
        callback = MagicMock()
        
        # Generate text asynchronously
        async_generate_text_with_mistral("Test prompt", callback)
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
    
    def test_format_chat_prompt_standard_mistral(self):
        """Test formatting chat prompt for standard Mistral models."""
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Format prompt
        prompt = format_chat_prompt(messages, "mistralai/Mistral-7B-Instruct-v0.1")
        
        # Verify prompt format
        self.assertIn("You are a helpful assistant", prompt)
        self.assertIn("Hello, how are you?", prompt)
        self.assertIn("I'm doing well, thank you for asking!", prompt)
        self.assertIn("What can you help me with?", prompt)
        self.assertIn("[INST]", prompt)
        self.assertIn("[/INST]", prompt)
    
    def test_format_chat_prompt_mixtral(self):
        """Test formatting chat prompt for Mixtral models."""
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Format prompt
        prompt = format_chat_prompt(messages, "mistralai/Mixtral-8x7B-Instruct-v0.1")
        
        # Verify prompt format
        self.assertIn("You are a helpful assistant", prompt)
        self.assertIn("Hello, how are you?", prompt)
        self.assertIn("I'm doing well, thank you for asking!", prompt)
        self.assertIn("What can you help me with?", prompt)
        self.assertIn("[INST]", prompt)
        self.assertIn("[/INST]", prompt)
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.generate_text_with_mistral")
    def test_chat_with_mistral(self, mock_generate, mock_available):
        """Test chatting with Mistral."""
        # Set up mocks
        mock_available.return_value = True
        mock_generate.return_value = ["[INST] Test prompt [/INST] Generated response"]
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Chat with Mistral
        response = chat_with_mistral(messages)
        
        # Verify response
        self.assertEqual(response, "Generated response")
        
        # Verify mocks were called
        mock_generate.assert_called_once()
    
    @patch("src.ai.mistral_support.threading.Thread")
    def test_async_chat_with_mistral(self, mock_thread):
        """Test chatting asynchronously with Mistral."""
        # Set up callback
        callback = MagicMock()
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Chat with Mistral asynchronously
        async_chat_with_mistral(messages, callback)
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


# Pytest-style tests
class TestMistralSupportPytest:
    """Pytest-style tests for the mistral_support module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Create a mock models directory
        models_dir = os.path.join(base_test_fixture["test_dir"], "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Create a mock Mistral model directory
        mistral_model_dir = os.path.join(models_dir, "mistralai_Mistral-7B-v0.1")
        os.makedirs(mistral_model_dir, exist_ok=True)
        
        # Create a metadata file
        metadata = {
            "name": "mistralai/Mistral-7B-v0.1",
            "task": "text-generation",
            "quantized": False,
            "download_date": "2025-03-11 12:00:00",
            "description": "Mistral 7B model for text generation",
            "model_type": "mistral"
        }
        
        import json
        with open(os.path.join(mistral_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        yield {
            **base_test_fixture,
            "models_dir": models_dir,
            "mistral_model_dir": mistral_model_dir
        }
    
    @patch("src.ai.mistral_support.TORCH_AVAILABLE", True)
    @patch("src.ai.mistral_support.TRANSFORMERS_AVAILABLE", True)
    @patch("src.ai.mistral_support.BITSANDBYTES_AVAILABLE", True)
    @patch("src.ai.mistral_support.ACCELERATE_AVAILABLE", True)
    def test_check_mistral_dependencies_all_available_pytest(self):
        """Test checking dependencies when all are available using pytest style."""
        # Check dependencies
        deps = check_mistral_dependencies()
        
        # Verify dependencies
        assert isinstance(deps, dict)
        assert len(deps) == 4
        assert deps["torch"] is True
        assert deps["transformers"] is True
        assert deps["bitsandbytes"] is True
        assert deps["accelerate"] is True
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.get_models_directory")
    def test_get_available_mistral_models_pytest(self, mock_get_models_dir, mock_available, setup):
        """Test getting available Mistral models using pytest style."""
        # Set up mocks
        mock_available.return_value = True
        mock_get_models_dir.return_value = setup["models_dir"]
        
        # Get available models
        models = get_available_mistral_models()
        
        # Verify models
        assert isinstance(models, list)
        assert len(models) == 1
        assert models[0]["name"] == "mistralai/Mistral-7B-v0.1"
        assert models[0]["model_type"] == "mistral"
    
    @patch("src.ai.mistral_support.is_mistral_available")
    @patch("src.ai.mistral_support.load_mistral_model")
    def test_generate_text_with_mistral_pytest(self, mock_load, mock_available):
        """Test generating text with Mistral using pytest style."""
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
        result = generate_text_with_mistral("Test prompt")
        
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
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Format prompt
        prompt = format_chat_prompt(messages, "mistralai/Mistral-7B-Instruct-v0.1")
        
        # Verify prompt format
        assert "You are a helpful assistant" in prompt
        assert "Hello, how are you?" in prompt
        assert "I'm doing well, thank you for asking!" in prompt
        assert "What can you help me with?" in prompt
        assert "[INST]" in prompt
        assert "[/INST]" in prompt


if __name__ == '__main__':
    unittest.main()
