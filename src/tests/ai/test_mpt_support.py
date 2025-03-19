#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the mpt_support module.

This module contains tests for the MPT model support functionality,
including model loading, text generation, and optimization.
"""

import os
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from src.tests.base_test import BaseTest
from src.ai.mpt_support import (
    is_mpt_available, check_dependencies, get_available_models,
    load_model, unload_model, clear_model_cache, optimize_model,
    generate_text, generate_text_streaming, chat_completion, chat_completion_streaming,
    MPTModelNotAvailableError, MPTModelLoadError, MPTInferenceError,
    MODEL_CACHE
)


class TestMPTSupport(BaseTest):
    """Unit tests for the mpt_support module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Skip tests if MPT models are not available
        if not is_mpt_available():
            self.skipTest("MPT models are not available")
        
        # Create a test directory for models
        self.models_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Clear model cache before each test
        asyncio.run(clear_model_cache())
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clear model cache
        asyncio.run(clear_model_cache())
        
        super().tearDown()
    
    def test_is_mpt_available(self):
        """Test checking if MPT models are available."""
        # This test will always pass since we skip tests if MPT models are not available
        self.assertTrue(is_mpt_available())
    
    def test_check_dependencies(self):
        """Test checking dependencies for MPT models."""
        dependencies = check_dependencies()
        
        # Verify dependencies
        self.assertIsInstance(dependencies, dict)
        self.assertIn("torch", dependencies)
        self.assertIn("transformers", dependencies)
        
        # All dependencies should be True since we skip tests if MPT models are not available
        for dep, available in dependencies.items():
            self.assertTrue(available, f"Dependency {dep} should be available")
    
    def test_get_available_models(self):
        """Test getting available MPT models."""
        models = get_available_models()
        
        # Verify models
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        
        # Verify model structure
        for model in models:
            self.assertIsInstance(model, dict)
            self.assertIn("name", model)
            self.assertIn("path", model)
            self.assertIn("description", model)
            self.assertIn("type", model)
    
    @patch("src.ai.mpt_support.AutoModelForCausalLM")
    @patch("src.ai.mpt_support.AutoTokenizer")
    async def test_load_model(self, mock_tokenizer, mock_model):
        """Test loading an MPT model."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model
        model, tokenizer = await load_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify model and tokenizer
        self.assertEqual(model, mock_model_instance)
        self.assertEqual(tokenizer, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
        
        # Verify model is in cache
        self.assertIn("mosaicml/mpt-7b-instruct_cpu_None", MODEL_CACHE)
    
    @patch("src.ai.mpt_support.AutoModelForCausalLM")
    @patch("src.ai.mpt_support.AutoTokenizer")
    async def test_load_model_with_cache(self, mock_tokenizer, mock_model):
        """Test loading an MPT model with caching."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model first time
        model1, tokenizer1 = await load_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify model and tokenizer
        self.assertEqual(model1, mock_model_instance)
        self.assertEqual(tokenizer1, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
        
        # Reset mocks
        mock_model.from_pretrained.reset_mock()
        mock_tokenizer.from_pretrained.reset_mock()
        
        # Load model second time (should use cache)
        model2, tokenizer2 = await load_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify model and tokenizer
        self.assertEqual(model2, mock_model_instance)
        self.assertEqual(tokenizer2, mock_tokenizer_instance)
        
        # Verify mocks were not called again
        mock_model.from_pretrained.assert_not_called()
        mock_tokenizer.from_pretrained.assert_not_called()
    
    @patch("src.ai.mpt_support.AutoModelForCausalLM")
    @patch("src.ai.mpt_support.AutoTokenizer")
    async def test_load_model_without_cache(self, mock_tokenizer, mock_model):
        """Test loading an MPT model without using cache."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model first time
        model1, tokenizer1 = await load_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify model and tokenizer
        self.assertEqual(model1, mock_model_instance)
        self.assertEqual(tokenizer1, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
        
        # Reset mocks
        mock_model.from_pretrained.reset_mock()
        mock_tokenizer.from_pretrained.reset_mock()
        
        # Load model second time without cache
        model2, tokenizer2 = await load_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None,
            use_cache=False
        )
        
        # Verify model and tokenizer
        self.assertEqual(model2, mock_model_instance)
        self.assertEqual(tokenizer2, mock_tokenizer_instance)
        
        # Verify mocks were called again
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
    
    @patch("src.ai.mpt_support.MODEL_CACHE", {
        "mosaicml/mpt-7b-instruct_cpu_None": ("model1", "tokenizer1"),
        "mosaicml/mpt-7b_cpu_None": ("model2", "tokenizer2")
    })
    async def test_unload_model(self):
        """Test unloading an MPT model."""
        # Unload model
        result = await unload_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify model is not in cache
        self.assertNotIn("mosaicml/mpt-7b-instruct_cpu_None", MODEL_CACHE)
        self.assertIn("mosaicml/mpt-7b_cpu_None", MODEL_CACHE)
    
    @patch("src.ai.mpt_support.MODEL_CACHE", {
        "mosaicml/mpt-7b-instruct_cpu_None": ("model1", "tokenizer1"),
        "mosaicml/mpt-7b_cpu_None": ("model2", "tokenizer2")
    })
    async def test_unload_nonexistent_model(self):
        """Test unloading a model that doesn't exist in the cache."""
        # Unload nonexistent model
        result = await unload_model(
            model_name_or_path="nonexistent_model",
            device="cpu",
            quantization=None
        )
        
        # Verify result
        self.assertFalse(result)
        
        # Verify cache was not modified
        self.assertIn("mosaicml/mpt-7b-instruct_cpu_None", MODEL_CACHE)
        self.assertIn("mosaicml/mpt-7b_cpu_None", MODEL_CACHE)
    
    @patch("src.ai.mpt_support.MODEL_CACHE", {
        "mosaicml/mpt-7b-instruct_cpu_None": ("model1", "tokenizer1"),
        "mosaicml/mpt-7b_cpu_None": ("model2", "tokenizer2")
    })
    async def test_clear_model_cache(self):
        """Test clearing the MPT model cache."""
        # Clear cache
        await clear_model_cache()
        
        # Verify cache is empty
        self.assertEqual(len(MODEL_CACHE), 0)
    
    @patch("src.ai.mpt_support.load_model")
    async def test_generate_text(self, mock_load_model):
        """Test generating text with an MPT model."""
        # Set up mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load_model.return_value = (mock_model, mock_tokenizer)
        
        # Set up model.generate to return a tensor
        mock_outputs = MagicMock()
        mock_model.generate.return_value = mock_outputs
        
        # Set up tokenizer.decode to return a string
        mock_tokenizer.decode.return_value = "Below is an instruction. Write a response that appropriately completes the request.\n\n### Instruction:\nTest prompt\n\n### Response: This is a test response."
        
        # Generate text
        result = await generate_text(
            prompt="Test prompt",
            model_name_or_path="mosaicml/mpt-7b-instruct",
            max_length=100,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify result
        self.assertEqual(result, "This is a test response.")
        
        # Verify mocks were called
        mock_load_model.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()
    
    @patch("src.ai.mpt_support.load_model")
    async def test_generate_text_with_error(self, mock_load_model):
        """Test generating text with an error."""
        # Set up mock to raise an exception
        mock_load_model.side_effect = Exception("Test error")
        
        # Try to generate text
        with self.assertRaises(MPTInferenceError):
            await generate_text("Test prompt")
    
    @patch("src.ai.mpt_support.load_model")
    async def test_generate_text_streaming(self, mock_load_model):
        """Test generating text with streaming output."""
        # Set up mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load_model.return_value = (mock_model, mock_tokenizer)
        
        # Set up streamer
        mock_streamer = MagicMock()
        mock_streamer.__iter__.return_value = ["This ", "is ", "a ", "test ", "response."]
        
        # Patch TextIteratorStreamer
        with patch("src.ai.mpt_support.TextIteratorStreamer", return_value=mock_streamer):
            # Set up callback
            callback = MagicMock()
            
            # Generate text with streaming
            await generate_text_streaming(
                prompt="Test prompt",
                callback=callback,
                model_name_or_path="mosaicml/mpt-7b-instruct",
                max_length=100,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                device="cpu",
                quantization=None,
                use_cache=True
            )
            
            # Verify callback was called for each chunk
            self.assertEqual(callback.call_count, 5)
            callback.assert_any_call("This ", None)
            callback.assert_any_call("is ", None)
            callback.assert_any_call("a ", None)
            callback.assert_any_call("test ", None)
            callback.assert_any_call("response.", None)
    
    @patch("src.ai.mpt_support.generate_text")
    async def test_chat_completion(self, mock_generate_text):
        """Test chat completion with an MPT model."""
        # Set up mock
        mock_generate_text.return_value = "This is a test response."
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "Tell me a joke."}
        ]
        
        # Generate chat completion
        result = await chat_completion(
            messages=messages,
            model_name_or_path="mosaicml/mpt-7b-chat",
            max_length=100,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify result
        self.assertEqual(result, "This is a test response.")
        
        # Verify mock was called
        mock_generate_text.assert_called_once()
        
        # Verify prompt formatting
        prompt = mock_generate_text.call_args[1]["prompt"]
        self.assertIn("<system>: You are a helpful assistant.", prompt)
        self.assertIn("<human>: Hello, how are you?", prompt)
        self.assertIn("<bot>: I'm doing well, thank you!", prompt)
        self.assertIn("<human>: Tell me a joke.", prompt)
        self.assertIn("<bot>:", prompt)
    
    @patch("src.ai.mpt_support.generate_text_streaming")
    async def test_chat_completion_streaming(self, mock_generate_text_streaming):
        """Test chat completion with streaming output."""
        # Set up mock
        mock_generate_text_streaming.return_value = None
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "Tell me a joke."}
        ]
        
        # Set up callback
        callback = MagicMock()
        
        # Generate chat completion with streaming
        await chat_completion_streaming(
            messages=messages,
            callback=callback,
            model_name_or_path="mosaicml/mpt-7b-chat",
            max_length=100,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify mock was called
        mock_generate_text_streaming.assert_called_once()
        
        # Verify prompt formatting
        prompt = mock_generate_text_streaming.call_args[1]["prompt"]
        self.assertIn("<system>: You are a helpful assistant.", prompt)
        self.assertIn("<human>: Hello, how are you?", prompt)
        self.assertIn("<bot>: I'm doing well, thank you!", prompt)
        self.assertIn("<human>: Tell me a joke.", prompt)
        self.assertIn("<bot>:", prompt)
        
        # Verify callback was passed
        self.assertEqual(mock_generate_text_streaming.call_args[1]["callback"], callback)
    
    @patch("src.ai.mpt_support.load_model")
    async def test_optimize_model(self, mock_load_model):
        """Test optimizing an MPT model."""
        # Set up mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load_model.return_value = (mock_model, mock_tokenizer)
        
        # Optimize model
        output_dir = os.path.join(self.test_dir, "optimized")
        result = await optimize_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            output_dir=output_dir,
            quantization="4bit"
        )
        
        # Verify result
        self.assertEqual(result, output_dir)
        
        # Verify mocks were called
        mock_load_model.assert_called_once()
        mock_model.save_pretrained.assert_called_once_with(output_dir)
        mock_tokenizer.save_pretrained.assert_called_once_with(output_dir)
    
    @patch("src.ai.mpt_support.load_model")
    async def test_optimize_model_with_error(self, mock_load_model):
        """Test optimizing a model with an error."""
        # Set up mock to raise an exception
        mock_load_model.side_effect = Exception("Test error")
        
        # Try to optimize model
        result = await optimize_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            output_dir=os.path.join(self.test_dir, "optimized"),
            quantization="4bit"
        )
        
        # Verify result
        self.assertIsNone(result)


# Pytest-style tests
class TestMPTSupportPytest:
    """Pytest-style tests for the mpt_support module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Skip tests if MPT models are not available
        if not is_mpt_available():
            pytest.skip("MPT models are not available")
        
        # Create a test directory for models
        models_dir = os.path.join(base_test_fixture["test_dir"], "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Clear model cache before each test
        asyncio.run(clear_model_cache())
        
        yield {
            **base_test_fixture,
            "models_dir": models_dir
        }
        
        # Clear model cache after each test
        asyncio.run(clear_model_cache())
    
    def test_is_mpt_available_pytest(self, setup):
        """Test checking if MPT models are available using pytest style."""
        # This test will always pass since we skip tests if MPT models are not available
        assert is_mpt_available()
    
    def test_check_dependencies_pytest(self, setup):
        """Test checking dependencies for MPT models using pytest style."""
        dependencies = check_dependencies()
        
        # Verify dependencies
        assert isinstance(dependencies, dict)
        assert "torch" in dependencies
        assert "transformers" in dependencies
        
        # All dependencies should be True since we skip tests if MPT models are not available
        for dep, available in dependencies.items():
            assert available, f"Dependency {dep} should be available"
    
    def test_get_available_models_pytest(self, setup):
        """Test getting available MPT models using pytest style."""
        models = get_available_models()
        
        # Verify models
        assert isinstance(models, list)
        assert len(models) > 0
        
        # Verify model structure
        for model in models:
            assert isinstance(model, dict)
            assert "name" in model
            assert "path" in model
            assert "description" in model
            assert "type" in model
    
    @pytest.mark.asyncio
    @patch("src.ai.mpt_support.AutoModelForCausalLM")
    @patch("src.ai.mpt_support.AutoTokenizer")
    async def test_load_model_pytest(self, mock_tokenizer, mock_model, setup):
        """Test loading an MPT model using pytest style."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model
        model, tokenizer = await load_model(
            model_name_or_path="mosaicml/mpt-7b-instruct",
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify model and tokenizer
        assert model == mock_model_instance
        assert tokenizer == mock_tokenizer_instance
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
        
        # Verify model is in cache
        assert "mosaicml/mpt-7b-instruct_cpu_None" in MODEL_CACHE
    
    @pytest.mark.asyncio
    @patch("src.ai.mpt_support.load_model")
    async def test_generate_text_pytest(self, mock_load_model, setup):
        """Test generating text with an MPT model using pytest style."""
        # Set up mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load_model.return_value = (mock_model, mock_tokenizer)
        
        # Set up model.generate to return a tensor
        mock_outputs = MagicMock()
        mock_model.generate.return_value = mock_outputs
        
        # Set up tokenizer.decode to return a string
        mock_tokenizer.decode.return_value = "Below is an instruction. Write a response that appropriately completes the request.\n\n### Instruction:\nTest prompt\n\n### Response: This is a test response."
        
        # Generate text
        result = await generate_text(
            prompt="Test prompt",
            model_name_or_path="mosaicml/mpt-7b-instruct",
            max_length=100,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify result
        assert result == "This is a test response."
        
        # Verify mocks were called
        mock_load_model.assert_called_once()
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("src.ai.mpt_support.generate_text")
    async def test_chat_completion_pytest(self, mock_generate_text, setup):
        """Test chat completion with an MPT model using pytest style."""
        # Set up mock
        mock_generate_text.return_value = "This is a test response."
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "Tell me a joke."}
        ]
        
        # Generate chat completion
        result = await chat_completion(
            messages=messages,
            model_name_or_path="mosaicml/mpt-7b-chat",
            max_length=100,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            device="cpu",
            quantization=None,
            use_cache=True
        )
        
        # Verify result
        assert result == "This is a test response."
        
        # Verify mock was called
        mock_generate_text.assert_called_once()
        
        # Verify prompt formatting
        prompt = mock_generate_text.call_args[1]["prompt"]
        assert "<system>: You are a helpful assistant." in prompt
        assert "<human>: Hello, how are you?" in prompt
        assert "<bot>: I'm doing well, thank you!" in prompt
        assert "<human>: Tell me a joke." in prompt
        assert "<bot>:" in prompt


if __name__ == "__main__":
    unittest.main()
