#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced unit tests for the local_models module.

This module contains additional tests for the local AI models functionality,
focusing on edge cases, error handling, and advanced features.
"""

import os
import unittest
import tempfile
import shutil
import threading
import queue
from unittest.mock import patch, MagicMock, call

import pytest
from src.tests.base_test import BaseTest
from src.ai.local_models import (
    check_dependencies, is_local_models_available, get_models_directory,
    get_available_models, download_model, load_model, unload_model,
    clear_model_cache, optimize_model, quantize_model,
    generate_text, summarize_text, correct_grammar,
    start_inference_thread, stop_inference_thread,
    async_generate_text, async_summarize_text, async_correct_grammar,
    fine_tune_model, ModelNotAvailableError, ModelLoadError, InferenceError,
    INFERENCE_QUEUE, INFERENCE_RUNNING, INFERENCE_THREAD, MODEL_CACHE
)


class TestLocalModelsAdvanced(BaseTest):
    """Advanced unit tests for the local_models module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Skip tests if local models are not available
        if not is_local_models_available():
            self.skipTest("Local models functionality is not available")
        
        # Create a mock model directory
        self.models_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Create multiple mock models
        self.model_dirs = {}
        for model_name in ["mock_model_1", "mock_model_2", "mock_model_3"]:
            model_dir = os.path.join(self.models_dir, model_name)
            os.makedirs(model_dir, exist_ok=True)
            
            # Create a metadata file
            metadata = {
                "name": model_name,
                "task": "text-generation",
                "quantized": False,
                "download_date": "2025-03-11 12:00:00",
                "description": f"Mock model {model_name} for testing"
            }
            
            import json
            with open(os.path.join(model_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            self.model_dirs[model_name] = model_dir
        
        # Clear model cache before each test
        clear_model_cache()
        
        # Ensure inference thread is stopped
        if INFERENCE_RUNNING:
            stop_inference_thread()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Ensure inference thread is stopped
        if INFERENCE_RUNNING:
            stop_inference_thread()
        
        # Clear model cache
        clear_model_cache()
        
        super().tearDown()
    
    @patch("src.ai.local_models.get_models_directory")
    def test_get_available_models_with_invalid_metadata(self, mock_get_models_dir):
        """Test getting available models with invalid metadata."""
        # Set up mock
        mock_get_models_dir.return_value = self.models_dir
        
        # Create a model with invalid metadata
        invalid_model_dir = os.path.join(self.models_dir, "invalid_model")
        os.makedirs(invalid_model_dir, exist_ok=True)
        
        # Create an invalid metadata file (not JSON)
        with open(os.path.join(invalid_model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            f.write("This is not valid JSON")
        
        # Get available models
        models = get_available_models()
        
        # Verify models (should not include the invalid one)
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 3)  # Only the valid models
        
        # Verify model names
        model_names = [model["name"] for model in models]
        self.assertIn("mock_model_1", model_names)
        self.assertIn("mock_model_2", model_names)
        self.assertIn("mock_model_3", model_names)
        self.assertNotIn("invalid_model", model_names)
    
    @patch("src.ai.local_models.get_models_directory")
    @patch("src.ai.local_models.download_model")
    def test_load_model_with_nonexistent_model(self, mock_download, mock_get_models_dir):
        """Test loading a nonexistent model."""
        # Set up mocks
        mock_get_models_dir.return_value = self.models_dir
        mock_download.return_value = None  # Download fails
        
        # Try to load a nonexistent model
        with self.assertRaises(ModelLoadError):
            load_model("nonexistent_model", "text-generation")
        
        # Verify download was attempted
        mock_download.assert_called_once_with("nonexistent_model", "text-generation")
    
    @patch("src.ai.local_models.MODEL_CACHE", {})
    @patch("src.ai.local_models.AutoModelForCausalLM")
    @patch("src.ai.local_models.AutoTokenizer")
    def test_load_model_with_cache(self, mock_tokenizer, mock_model):
        """Test loading a model with caching."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model first time
        model1, tokenizer1 = load_model(self.model_dirs["mock_model_1"], "text-generation")
        
        # Verify model and tokenizer
        self.assertEqual(model1, mock_model_instance)
        self.assertEqual(tokenizer1, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once_with(self.model_dirs["mock_model_1"])
        mock_tokenizer.from_pretrained.assert_called_once_with(self.model_dirs["mock_model_1"])
        
        # Reset mocks
        mock_model.from_pretrained.reset_mock()
        mock_tokenizer.from_pretrained.reset_mock()
        
        # Load model second time (should use cache)
        model2, tokenizer2 = load_model(self.model_dirs["mock_model_1"], "text-generation")
        
        # Verify model and tokenizer
        self.assertEqual(model2, mock_model_instance)
        self.assertEqual(tokenizer2, mock_tokenizer_instance)
        
        # Verify mocks were not called again
        mock_model.from_pretrained.assert_not_called()
        mock_tokenizer.from_pretrained.assert_not_called()
    
    @patch("src.ai.local_models.MODEL_CACHE", {})
    @patch("src.ai.local_models.AutoModelForCausalLM")
    @patch("src.ai.local_models.AutoTokenizer")
    def test_load_model_without_cache(self, mock_tokenizer, mock_model):
        """Test loading a model without using cache."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model first time
        model1, tokenizer1 = load_model(self.model_dirs["mock_model_1"], "text-generation", use_cache=True)
        
        # Verify model and tokenizer
        self.assertEqual(model1, mock_model_instance)
        self.assertEqual(tokenizer1, mock_tokenizer_instance)
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once_with(self.model_dirs["mock_model_1"])
        mock_tokenizer.from_pretrained.assert_called_once_with(self.model_dirs["mock_model_1"])
        
        # Reset mocks
        mock_model.from_pretrained.reset_mock()
        mock_tokenizer.from_pretrained.reset_mock()
        
        # Load model second time without cache
        model2, tokenizer2 = load_model(self.model_dirs["mock_model_1"], "text-generation", use_cache=False)
        
        # Verify model and tokenizer
        self.assertEqual(model2, mock_model_instance)
        self.assertEqual(tokenizer2, mock_tokenizer_instance)
        
        # Verify mocks were called again
        mock_model.from_pretrained.assert_called_once_with(self.model_dirs["mock_model_1"])
        mock_tokenizer.from_pretrained.assert_called_once_with(self.model_dirs["mock_model_1"])
    
    @patch("src.ai.local_models.MODEL_CACHE", {
        "mock_model_1_text-generation": ("model1", "tokenizer1"),
        "mock_model_2_text-generation": ("model2", "tokenizer2"),
        "mock_model_3_summarization": ("model3", "tokenizer3")
    })
    def test_unload_nonexistent_model(self):
        """Test unloading a model that doesn't exist in the cache."""
        # Unload nonexistent model
        result = unload_model("nonexistent_model", "text-generation")
        
        # Verify result
        self.assertFalse(result)
        
        # Verify cache was not modified
        self.assertEqual(len(MODEL_CACHE), 3)
    
    @patch("src.ai.local_models.MODEL_LOCK")
    @patch("src.ai.local_models.MODEL_CACHE", {
        "mock_model_1_text-generation": ("model1", "tokenizer1"),
        "mock_model_2_text-generation": ("model2", "tokenizer2")
    })
    def test_clear_model_cache_with_lock(self, mock_lock):
        """Test clearing the model cache with lock."""
        # Clear cache
        clear_model_cache()
        
        # Verify lock was used
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()
        
        # Verify cache is empty
        self.assertEqual(len(MODEL_CACHE), 0)
    
    @patch("src.ai.local_models.ONNX_AVAILABLE", False)
    @patch("src.ai.local_models.OPTIMUM_AVAILABLE", False)
    def test_optimize_model_without_dependencies(self):
        """Test optimizing a model without required dependencies."""
        # Try to optimize model
        result = optimize_model(self.model_dirs["mock_model_1"])
        
        # Verify result
        self.assertIsNone(result)
    
    @patch("src.ai.local_models.TORCH_AVAILABLE", False)
    @patch("src.ai.local_models.TRANSFORMERS_AVAILABLE", False)
    def test_quantize_model_without_dependencies(self):
        """Test quantizing a model without required dependencies."""
        # Try to quantize model
        result = quantize_model(self.model_dirs["mock_model_1"])
        
        # Verify result
        self.assertIsNone(result)
    
    @patch("src.ai.local_models.is_local_models_available")
    def test_generate_text_not_available(self, mock_available):
        """Test generating text when local models are not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to generate text
        with self.assertRaises(ModelNotAvailableError):
            generate_text("Test prompt")
    
    @patch("src.ai.local_models.is_local_models_available")
    def test_summarize_text_not_available(self, mock_available):
        """Test summarizing text when local models are not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to summarize text
        with self.assertRaises(ModelNotAvailableError):
            summarize_text("Test text")
    
    @patch("src.ai.local_models.is_local_models_available")
    def test_correct_grammar_not_available(self, mock_available):
        """Test correcting grammar when local models are not available."""
        # Set up mock
        mock_available.return_value = False
        
        # Try to correct grammar
        with self.assertRaises(ModelNotAvailableError):
            correct_grammar("Test text")
    
    @patch("src.ai.local_models.load_model")
    def test_generate_text_with_error(self, mock_load_model):
        """Test generating text with an error."""
        # Set up mock to raise an exception
        mock_load_model.side_effect = Exception("Test error")
        
        # Try to generate text
        with self.assertRaises(InferenceError):
            generate_text("Test prompt")
    
    @patch("src.ai.local_models.threading.Thread")
    def test_start_inference_thread_already_running(self, mock_thread):
        """Test starting the inference thread when it's already running."""
        # Set up global variables
        global INFERENCE_RUNNING
        INFERENCE_RUNNING = True
        
        # Start thread
        start_inference_thread()
        
        # Verify thread was not created
        mock_thread.assert_not_called()
    
    def test_stop_inference_thread_not_running(self):
        """Test stopping the inference thread when it's not running."""
        # Set up global variables
        global INFERENCE_RUNNING
        INFERENCE_RUNNING = False
        
        # Stop thread
        stop_inference_thread()
        
        # Verify INFERENCE_RUNNING is still False
        self.assertFalse(INFERENCE_RUNNING)
    
    @patch("src.ai.local_models.start_inference_thread")
    @patch("src.ai.local_models.INFERENCE_QUEUE")
    def test_async_generate_text_with_callback(self, mock_queue, mock_start_thread):
        """Test generating text asynchronously with a callback."""
        # Set up callback
        callback = MagicMock()
        
        # Generate text asynchronously
        async_generate_text("Test prompt", callback, max_length=50)
        
        # Verify thread was started
        mock_start_thread.assert_called_once()
        
        # Verify task was added to queue
        mock_queue.put.assert_called_once()
        
        # Get the task from the mock
        task = mock_queue.put.call_args[0][0]
        
        # Verify task structure
        self.assertEqual(task[0], generate_text)
        self.assertEqual(task[1], ("Test prompt", None))
        self.assertEqual(task[2], {"max_length": 50})
        self.assertEqual(task[3], callback)
    
    @patch("src.ai.local_models.start_inference_thread")
    @patch("src.ai.local_models.INFERENCE_QUEUE")
    def test_async_summarize_text_with_callback(self, mock_queue, mock_start_thread):
        """Test summarizing text asynchronously with a callback."""
        # Set up callback
        callback = MagicMock()
        
        # Summarize text asynchronously
        async_summarize_text("Test text", callback, max_length=50)
        
        # Verify thread was started
        mock_start_thread.assert_called_once()
        
        # Verify task was added to queue
        mock_queue.put.assert_called_once()
        
        # Get the task from the mock
        task = mock_queue.put.call_args[0][0]
        
        # Verify task structure
        self.assertEqual(task[0], summarize_text)
        self.assertEqual(task[1], ("Test text", None))
        self.assertEqual(task[2], {"max_length": 50})
        self.assertEqual(task[3], callback)
    
    @patch("src.ai.local_models.start_inference_thread")
    @patch("src.ai.local_models.INFERENCE_QUEUE")
    def test_async_correct_grammar_with_callback(self, mock_queue, mock_start_thread):
        """Test correcting grammar asynchronously with a callback."""
        # Set up callback
        callback = MagicMock()
        
        # Correct grammar asynchronously
        async_correct_grammar("Test text", callback)
        
        # Verify thread was started
        mock_start_thread.assert_called_once()
        
        # Verify task was added to queue
        mock_queue.put.assert_called_once()
        
        # Get the task from the mock
        task = mock_queue.put.call_args[0][0]
        
        # Verify task structure
        self.assertEqual(task[0], correct_grammar)
        self.assertEqual(task[1], ("Test text", None))
        self.assertEqual(task[2], {})
        self.assertEqual(task[3], callback)
    
    def test_inference_worker_with_error(self):
        """Test the inference worker with an error in the task."""
        # Create a queue
        test_queue = queue.Queue()
        
        # Create a mock function that raises an exception
        def mock_func(*args, **kwargs):
            raise Exception("Test error")
        
        # Create a mock callback
        callback = MagicMock()
        
        # Add a task to the queue
        test_queue.put((mock_func, (), {}, callback))
        
        # Add a sentinel value to stop the worker
        test_queue.put(None)
        
        # Patch the global queue
        with patch("src.ai.local_models.INFERENCE_QUEUE", test_queue):
            # Set INFERENCE_RUNNING to True
            global INFERENCE_RUNNING
            INFERENCE_RUNNING = True
            
            # Import the worker function
            from src.ai.local_models import _inference_worker
            
            # Run the worker
            _inference_worker()
            
            # Verify callback was called with error
            callback.assert_called_once()
            args = callback.call_args[0]
            self.assertIsNone(args[0])  # Result is None
            self.assertEqual(args[1], "Test error")  # Error message
    
    def test_inference_worker_with_callback_error(self):
        """Test the inference worker with an error in the callback."""
        # Create a queue
        test_queue = queue.Queue()
        
        # Create a mock function
        mock_func = MagicMock(return_value="Test result")
        
        # Create a mock callback that raises an exception
        def callback(result, error):
            raise Exception("Callback error")
        
        # Add a task to the queue
        test_queue.put((mock_func, (), {}, callback))
        
        # Add a sentinel value to stop the worker
        test_queue.put(None)
        
        # Patch the global queue
        with patch("src.ai.local_models.INFERENCE_QUEUE", test_queue):
            # Set INFERENCE_RUNNING to True
            global INFERENCE_RUNNING
            INFERENCE_RUNNING = True
            
            # Import the worker function
            from src.ai.local_models import _inference_worker
            
            # Run the worker
            _inference_worker()
            
            # Verify function was called
            mock_func.assert_called_once()
    
    @patch("src.ai.local_models.TORCH_AVAILABLE", False)
    @patch("src.ai.local_models.TRANSFORMERS_AVAILABLE", False)
    def test_fine_tune_model_without_dependencies(self):
        """Test fine-tuning a model without required dependencies."""
        # Try to fine-tune model
        result = fine_tune_model(
            self.model_dirs["mock_model_1"],
            [{"prompt": "Test", "completion": "Test"}],
            os.path.join(self.test_dir, "fine_tuned")
        )
        
        # Verify result
        self.assertIsNone(result)
    
    @patch("src.ai.local_models.load_model")
    def test_fine_tune_model_with_error(self, mock_load_model):
        """Test fine-tuning a model with an error."""
        # Set up mock to raise an exception
        mock_load_model.side_effect = Exception("Test error")
        
        # Try to fine-tune model
        result = fine_tune_model(
            self.model_dirs["mock_model_1"],
            [{"prompt": "Test", "completion": "Test"}],
            os.path.join(self.test_dir, "fine_tuned")
        )
        
        # Verify result
        self.assertIsNone(result)


# Pytest-style tests
class TestLocalModelsAdvancedPytest:
    """Pytest-style advanced tests for the local_models module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Skip tests if local models are not available
        if not is_local_models_available():
            pytest.skip("Local models functionality is not available")
        
        # Create a mock model directory
        models_dir = os.path.join(base_test_fixture["test_dir"], "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Create multiple mock models
        model_dirs = {}
        for model_name in ["mock_model_1", "mock_model_2", "mock_model_3"]:
            model_dir = os.path.join(models_dir, model_name)
            os.makedirs(model_dir, exist_ok=True)
            
            # Create a metadata file
            metadata = {
                "name": model_name,
                "task": "text-generation",
                "quantized": False,
                "download_date": "2025-03-11 12:00:00",
                "description": f"Mock model {model_name} for testing"
            }
            
            import json
            with open(os.path.join(model_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            model_dirs[model_name] = model_dir
        
        # Clear model cache before each test
        clear_model_cache()
        
        # Ensure inference thread is stopped
        if INFERENCE_RUNNING:
            stop_inference_thread()
        
        yield {
            **base_test_fixture,
            "models_dir": models_dir,
            "model_dirs": model_dirs
        }
        
        # Cleanup after tests
        if INFERENCE_RUNNING:
            stop_inference_thread()
        clear_model_cache()
    
    @patch("src.ai.local_models.MODEL_CACHE", {})
    @patch("src.ai.local_models.AutoModelForCausalLM")
    @patch("src.ai.local_models.AutoTokenizer")
    def test_load_model_with_cache_pytest(self, mock_tokenizer, mock_model, setup):
        """Test loading a model with caching using pytest style."""
        # Set up mocks
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Load model first time
        model1, tokenizer1 = load_model(setup["model_dirs"]["mock_model_1"], "text-generation")
        
        # Verify model and tokenizer
        assert model1 == mock_model_instance
        assert tokenizer1 == mock_tokenizer_instance
        
        # Verify mocks were called
        mock_model.from_pretrained.assert_called_once_with(setup["model_dirs"]["mock_model_1"])
        mock_tokenizer.from_pretrained.assert_called_once_with(setup["model_dirs"]["mock_model_1"])
        
        # Reset mocks
        mock_model.from_pretrained.reset_mock()
        mock_tokenizer.from_pretrained.reset_mock()
        
        # Load model second time (should use cache)
        model2, tokenizer2 = load_model(setup["model_dirs"]["mock_model_1"], "text-generation")
        
        # Verify model and tokenizer
        assert model2 == mock_model_instance
        assert tokenizer2 == mock_tokenizer_instance
        
        # Verify mocks were not called again
        mock_model.from_pretrained.assert_not_called()
        mock_tokenizer.from_pretrained.assert_not_called()
    
    @patch("src.ai.local_models.start_inference_thread")
    @patch("src.ai.local_models.INFERENCE_QUEUE")
    def test_async_generate_text_with_callback_pytest(self, mock_queue, mock_start_thread):
        """Test generating text asynchronously with a callback using pytest style."""
        # Set up callback
        callback = MagicMock()
        
        # Generate text asynchronously
        async_generate_text("Test prompt", callback, max_length=50)
        
        # Verify thread was started
        mock_start_thread.assert_called_once()
        
        # Verify task was added to queue
        mock_queue.put.assert_called_once()
        
        # Get the task from the mock
        task = mock_queue.put.call_args[0][0]
        
        # Verify task structure
        assert task[0] == generate_text
        assert task[1] == ("Test prompt", None)
        assert task[2] == {"max_length": 50}
        assert task[3] == callback


if __name__ == '__main__':
    unittest.main()
