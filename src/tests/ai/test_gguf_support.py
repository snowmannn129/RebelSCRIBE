#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the GGUF model support module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import json
import threading
import queue
from typing import Dict, List, Any, Optional

from src.ai.gguf_support import (
    is_gguf_available, check_dependencies, get_models_directory,
    load_gguf_model, unload_gguf_model, clear_gguf_model_cache,
    generate_text, generate_text_stream, format_chat_prompt,
    chat_completion, chat_completion_stream,
    start_inference_thread, stop_inference_thread,
    async_generate_text, async_chat_completion,
    download_gguf_model, get_gguf_model_info,
    GgufModelNotAvailableError, GgufModelLoadError, GgufInferenceError
)


class TestGgufSupport(unittest.TestCase):
    """Test cases for the GGUF model support module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test models
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, "test_model.gguf")
        
        # Create a mock model file
        with open(self.model_path, "w") as f:
            f.write("Mock GGUF model content")
        
        # Mock the Llama class
        self.llama_patcher = patch("src.ai.gguf_support.Llama")
        self.mock_llama = self.llama_patcher.start()
        self.mock_model = MagicMock()
        self.mock_llama.return_value = self.mock_model
        
        # Set up mock model behavior
        self.mock_model.return_value = "Generated text"
        
        # Mock the LLAMA_CPP_AVAILABLE flag
        self.available_patcher = patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", True)
        self.available_patcher.start()
        
        # Mock the progress callbacks
        self.progress_patcher = patch("src.ai.gguf_support.create_operation")
        self.mock_create_operation = self.progress_patcher.start()
        self.mock_create_operation.return_value = ("test_operation", {})
        
        self.start_op_patcher = patch("src.ai.gguf_support.start_operation")
        self.mock_start_operation = self.start_op_patcher.start()
        
        self.update_patcher = patch("src.ai.gguf_support.update_progress")
        self.mock_update_progress = self.update_patcher.start()
        
        self.complete_patcher = patch("src.ai.gguf_support.complete_operation")
        self.mock_complete_operation = self.complete_patcher.start()
        
        self.fail_patcher = patch("src.ai.gguf_support.fail_operation")
        self.mock_fail_operation = self.fail_patcher.start()
        
        # Clear the model cache
        clear_gguf_model_cache()

    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        self.llama_patcher.stop()
        self.available_patcher.stop()
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
        
        # Clear the model cache
        clear_gguf_model_cache()
        
        # Stop inference thread if running
        stop_inference_thread()

    def test_is_gguf_available(self):
        """Test checking if GGUF model support is available."""
        # With the mock, it should be available
        self.assertTrue(is_gguf_available())
        
        # Test when not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            self.assertFalse(is_gguf_available())

    def test_check_dependencies(self):
        """Test checking dependencies for GGUF models."""
        # With the mock, llama_cpp should be available
        deps = check_dependencies()
        self.assertIsInstance(deps, dict)
        self.assertTrue(deps["llama_cpp"])
        
        # Test when not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            deps = check_dependencies()
            self.assertFalse(deps["llama_cpp"])

    def test_get_models_directory(self):
        """Test getting the models directory."""
        # Test with default directory
        with patch("os.environ.get", return_value=None):
            with patch("src.ai.gguf_support.ensure_directory") as mock_ensure_dir:
                models_dir = get_models_directory()
                self.assertIn(".rebelscribe", models_dir)
                self.assertIn("models", models_dir)
                mock_ensure_dir.assert_called_once_with(models_dir)
        
        # Test with custom directory from environment
        custom_dir = "/custom/models/dir"
        with patch("os.environ.get", return_value=custom_dir):
            with patch("src.ai.gguf_support.ensure_directory") as mock_ensure_dir:
                models_dir = get_models_directory()
                self.assertEqual(models_dir, custom_dir)
                mock_ensure_dir.assert_called_once_with(custom_dir)

    def test_load_gguf_model(self):
        """Test loading a GGUF model."""
        # Test loading a model
        model = load_gguf_model(self.model_path)
        self.assertEqual(model, self.mock_model)
        self.mock_llama.assert_called_once()
        
        # Test loading from cache
        self.mock_llama.reset_mock()
        cached_model = load_gguf_model(self.model_path)
        self.assertEqual(cached_model, self.mock_model)
        self.mock_llama.assert_not_called()  # Should use cached model
        
        # Test loading with cache disabled
        self.mock_llama.reset_mock()
        model = load_gguf_model(self.model_path, use_cache=False)
        self.assertEqual(model, self.mock_model)
        self.mock_llama.assert_called_once()
        
        # Test loading non-existent model
        with self.assertRaises(GgufModelLoadError):
            load_gguf_model("/nonexistent/model.gguf")
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            with self.assertRaises(GgufModelNotAvailableError):
                load_gguf_model(self.model_path)
        
        # Test error during loading
        self.mock_llama.side_effect = Exception("Test error")
        with self.assertRaises(GgufModelLoadError):
            load_gguf_model(self.model_path, use_cache=False)

    def test_unload_gguf_model(self):
        """Test unloading a GGUF model."""
        # Load a model first
        model = load_gguf_model(self.model_path)
        
        # Test unloading the model
        result = unload_gguf_model(model)
        self.assertTrue(result)
        
        # Test unloading a model that's not in the cache
        result = unload_gguf_model(MagicMock())
        self.assertFalse(result)
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            result = unload_gguf_model(model)
            self.assertFalse(result)

    def test_clear_gguf_model_cache(self):
        """Test clearing the GGUF model cache."""
        # Load a model first
        model1 = load_gguf_model(self.model_path)
        model2 = load_gguf_model(self.model_path + "2")
        
        # Clear the cache
        clear_gguf_model_cache()
        
        # Load again to verify cache was cleared
        self.mock_llama.reset_mock()
        model = load_gguf_model(self.model_path)
        self.mock_llama.assert_called_once()

    def test_generate_text(self):
        """Test generating text with a GGUF model."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Test generating text
        text = generate_text(model, "Test prompt")
        self.assertEqual(text, "Generated text")
        model.assert_called_once()
        
        # Test with API-like output format
        model.return_value = {"choices": [{"text": "API response"}]}
        text = generate_text(model, "Test prompt")
        self.assertEqual(text, "API response")
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            with self.assertRaises(GgufModelNotAvailableError):
                generate_text(model, "Test prompt")
        
        # Test error during generation
        model.side_effect = Exception("Test error")
        with self.assertRaises(GgufInferenceError):
            generate_text(model, "Test prompt")

    def test_generate_text_stream(self):
        """Test generating text with streaming using a GGUF model."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Mock streaming output
        model.return_value = ["Chunk 1", "Chunk 2", "Chunk 3"]
        
        # Test generating text with streaming
        chunks = list(generate_text_stream(model, "Test prompt"))
        self.assertEqual(chunks, ["Chunk 1", "Chunk 2", "Chunk 3"])
        model.assert_called_once()
        
        # Test with API-like output format
        model.return_value = [
            {"choices": [{"text": "API chunk 1"}]},
            {"choices": [{"text": "API chunk 2"}]}
        ]
        chunks = list(generate_text_stream(model, "Test prompt"))
        self.assertEqual(chunks, ["API chunk 1", "API chunk 2"])
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            with self.assertRaises(GgufModelNotAvailableError):
                list(generate_text_stream(model, "Test prompt"))
        
        # Test error during generation
        model.side_effect = Exception("Test error")
        with self.assertRaises(GgufInferenceError):
            list(generate_text_stream(model, "Test prompt"))

    def test_format_chat_prompt(self):
        """Test formatting chat messages into a prompt string."""
        # Test with system, user, and assistant messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = format_chat_prompt(messages)
        self.assertIn("You are a helpful assistant", prompt)
        self.assertIn("Hello!", prompt)
        self.assertIn("Hi there!", prompt)
        self.assertIn("How are you?", prompt)
        
        # Test with only user messages
        messages = [
            {"role": "user", "content": "Hello!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = format_chat_prompt(messages)
        self.assertIn("You are a helpful assistant", prompt)  # Default system message
        self.assertIn("Hello!", prompt)
        self.assertIn("How are you?", prompt)
        
        # Test with custom templates
        system_template = "[SYSTEM: {system}]"
        user_template = "[USER: {user}]"
        assistant_template = "[ASSISTANT: {assistant}]"
        
        prompt = format_chat_prompt(
            messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template
        )
        
        self.assertIn("[SYSTEM: You are a helpful assistant]", prompt)
        self.assertIn("[USER: Hello!]", prompt)
        self.assertIn("[USER: How are you?]", prompt)
        
        # Test with no default system message
        prompt = format_chat_prompt(messages, default_system_message=None)
        self.assertIn("Hello!", prompt)
        self.assertIn("How are you?", prompt)
        self.assertNotIn("You are a helpful assistant", prompt)

    def test_chat_completion(self):
        """Test generating a chat completion with a GGUF model."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Test chat completion
        messages = [
            {"role": "user", "content": "Hello!"}
        ]
        
        model.return_value = "I'm an AI assistant. How can I help you?"
        response = chat_completion(model, messages)
        
        self.assertIsInstance(response, dict)
        self.assertIn("choices", response)
        self.assertEqual(response["choices"][0]["message"]["content"], 
                         "I'm an AI assistant. How can I help you?")
        
        # Test with API-like output format
        model.return_value = {"choices": [{"text": "API response"}]}
        response = chat_completion(model, messages)
        self.assertEqual(response["choices"][0]["message"]["content"], "API response")
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            with self.assertRaises(GgufModelNotAvailableError):
                chat_completion(model, messages)
        
        # Test error during generation
        model.side_effect = Exception("Test error")
        with self.assertRaises(GgufInferenceError):
            chat_completion(model, messages)

    def test_chat_completion_stream(self):
        """Test generating a chat completion with streaming using a GGUF model."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Mock streaming output
        model.return_value = ["I'm ", "an ", "AI ", "assistant."]
        
        # Test chat completion with streaming
        messages = [
            {"role": "user", "content": "Hello!"}
        ]
        
        chunks = list(chat_completion_stream(model, messages))
        
        self.assertEqual(len(chunks), 4)
        self.assertIsInstance(chunks[0], dict)
        self.assertIn("choices", chunks[0])
        self.assertEqual(chunks[0]["choices"][0]["delta"]["content"], "I'm ")
        
        # Test with API-like output format
        model.return_value = [
            {"choices": [{"text": "API "}]},
            {"choices": [{"text": "response"}]}
        ]
        chunks = list(chat_completion_stream(model, messages))
        self.assertEqual(chunks[0]["choices"][0]["delta"]["content"], "API ")
        self.assertEqual(chunks[1]["choices"][0]["delta"]["content"], "response")
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            with self.assertRaises(GgufModelNotAvailableError):
                list(chat_completion_stream(model, messages))
        
        # Test error during generation
        model.side_effect = Exception("Test error")
        with self.assertRaises(GgufInferenceError):
            list(chat_completion_stream(model, messages))

    def test_inference_thread(self):
        """Test the background inference thread."""
        # Start the inference thread
        start_inference_thread()
        
        # Check that the thread is running
        from src.ai.gguf_support import INFERENCE_RUNNING, INFERENCE_THREAD
        self.assertTrue(INFERENCE_RUNNING)
        self.assertIsNotNone(INFERENCE_THREAD)
        
        # Stop the inference thread
        stop_inference_thread()
        
        # Check that the thread is stopped
        self.assertFalse(INFERENCE_RUNNING)

    def test_async_generate_text(self):
        """Test generating text asynchronously."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Create a callback function
        callback_result = None
        callback_error = None
        
        def callback(result, error):
            nonlocal callback_result, callback_error
            callback_result = result
            callback_error = error
        
        # Test async generation
        async_generate_text(model, "Test prompt", callback)
        
        # Wait for the task to complete
        from src.ai.gguf_support import INFERENCE_QUEUE
        INFERENCE_QUEUE.join()
        
        # Check the result
        self.assertEqual(callback_result, "Generated text")
        self.assertIsNone(callback_error)
        
        # Test with error
        model.side_effect = Exception("Test error")
        
        # Reset callback values
        callback_result = None
        callback_error = None
        
        # Test async generation with error
        async_generate_text(model, "Test prompt", callback)
        
        # Wait for the task to complete
        INFERENCE_QUEUE.join()
        
        # Check the result
        self.assertIsNone(callback_result)
        self.assertIn("Test error", callback_error)

    def test_async_chat_completion(self):
        """Test generating a chat completion asynchronously."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Create a callback function
        callback_result = None
        callback_error = None
        
        def callback(result, error):
            nonlocal callback_result, callback_error
            callback_result = result
            callback_error = error
        
        # Test async chat completion
        messages = [
            {"role": "user", "content": "Hello!"}
        ]
        
        model.return_value = "I'm an AI assistant. How can I help you?"
        async_chat_completion(model, messages, callback)
        
        # Wait for the task to complete
        from src.ai.gguf_support import INFERENCE_QUEUE
        INFERENCE_QUEUE.join()
        
        # Check the result
        self.assertIsInstance(callback_result, dict)
        self.assertIn("choices", callback_result)
        self.assertEqual(callback_result["choices"][0]["message"]["content"], 
                         "I'm an AI assistant. How can I help you?")
        self.assertIsNone(callback_error)
        
        # Test with error
        model.side_effect = Exception("Test error")
        
        # Reset callback values
        callback_result = None
        callback_error = None
        
        # Test async chat completion with error
        async_chat_completion(model, messages, callback)
        
        # Wait for the task to complete
        INFERENCE_QUEUE.join()
        
        # Check the result
        self.assertIsNone(callback_result)
        self.assertIn("Test error", callback_error)

    @patch("src.ai.gguf_support.requests")
    def test_download_gguf_model(self, mock_requests):
        """Test downloading a GGUF model."""
        # Mock the requests module
        mock_response = MagicMock()
        mock_response.headers.get.return_value = "1000"
        mock_requests.head.return_value = mock_response
        
        mock_get_response = MagicMock()
        mock_get_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_requests.get.return_value = mock_get_response
        
        # Test downloading a model
        with patch("builtins.open", mock_open()) as mock_file:
            result = download_gguf_model("http://example.com/model.gguf", self.model_path)
            
            # Check the result
            self.assertEqual(result, self.model_path)
            
            # Check that the file was opened for writing
            mock_file.assert_called_once_with(self.model_path, "wb")
            
            # Check that the content was written
            handle = mock_file()
            handle.write.assert_any_call(b"chunk1")
            handle.write.assert_any_call(b"chunk2")
        
        # Test with error
        mock_requests.get.side_effect = Exception("Test error")
        
        with patch("builtins.open", mock_open()):
            result = download_gguf_model("http://example.com/model.gguf", self.model_path)
            
            # Check the result
            self.assertIsNone(result)

    def test_get_gguf_model_info(self):
        """Test getting information about a GGUF model."""
        # Load a model
        model = load_gguf_model(self.model_path)
        
        # Add metadata to the model
        model.metadata = {
            "name": "Test Model",
            "version": "1.0",
            "description": "A test GGUF model"
        }
        
        # Test getting model info
        info = get_gguf_model_info(self.model_path)
        
        # Check the result
        self.assertIsInstance(info, dict)
        self.assertEqual(info["path"], self.model_path)
        self.assertEqual(info["filename"], "test_model.gguf")
        self.assertEqual(info["format"], "GGUF")
        self.assertEqual(info["name"], "Test Model")
        self.assertEqual(info["version"], "1.0")
        self.assertEqual(info["description"], "A test GGUF model")
        
        # Test with non-existent model
        with self.assertRaises(GgufModelLoadError):
            get_gguf_model_info("/nonexistent/model.gguf")
        
        # Test when GGUF is not available
        with patch("src.ai.gguf_support.LLAMA_CPP_AVAILABLE", False):
            with self.assertRaises(GgufModelNotAvailableError):
                get_gguf_model_info(self.model_path)
        
        # Test with error during loading
        self.mock_llama.side_effect = Exception("Test error")
        with self.assertRaises(GgufModelLoadError):
            get_gguf_model_info(self.model_path)


if __name__ == "__main__":
    unittest.main()
