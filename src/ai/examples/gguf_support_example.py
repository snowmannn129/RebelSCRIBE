#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the GGUF model support module.

This example demonstrates how to use the GGUF model support module to load and use
GGUF format models for text generation and chat completion.

Note: This example requires the llama-cpp-python package to be installed.
You can install it with: pip install llama-cpp-python
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

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
from src.utils.logging_utils import get_logger, configure_logging

# Configure logging
configure_logging()
logger = get_logger(__name__)


def check_gguf_availability():
    """Check if GGUF model support is available."""
    print("\n=== Checking GGUF Availability ===")
    
    available = is_gguf_available()
    print(f"GGUF model support available: {available}")
    
    deps = check_dependencies()
    print(f"Dependencies: {deps}")
    
    if not available:
        print("GGUF model support is not available. Please install llama-cpp-python.")
        print("You can install it with: pip install llama-cpp-python")
        return False
    
    return True


def download_example_model():
    """Download an example GGUF model."""
    print("\n=== Downloading Example Model ===")
    
    # Get the models directory
    models_dir = get_models_directory()
    print(f"Models directory: {models_dir}")
    
    # Define the model URL and path
    # Note: This is a small example model for demonstration purposes
    model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    model_path = os.path.join(models_dir, "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    
    # Check if the model already exists
    if os.path.exists(model_path):
        print(f"Model already exists at {model_path}")
        return model_path
    
    # Define a progress callback
    def progress_callback(progress_info):
        print(f"Download progress: {progress_info.progress:.1%} - {progress_info.message}")
    
    # Download the model
    print(f"Downloading model from {model_url}...")
    try:
        result = download_gguf_model(model_url, model_path, progress_callback)
        if result:
            print(f"Model downloaded successfully to {result}")
            return result
        else:
            print("Failed to download model")
            return None
    except Exception as e:
        print(f"Error downloading model: {e}")
        return None


def text_generation_example(model_path):
    """Example of text generation with a GGUF model."""
    print("\n=== Text Generation Example ===")
    
    try:
        # Load the model
        print(f"Loading model from {model_path}...")
        model = load_gguf_model(
            model_path,
            n_ctx=2048,
            n_batch=512,
            n_gpu_layers=0  # CPU only
        )
        print("Model loaded successfully")
        
        # Generate text
        prompt = "Once upon a time in a land far away,"
        print(f"Generating text with prompt: '{prompt}'")
        
        response = generate_text(
            model,
            prompt,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
        
        print("\nGenerated text:")
        print(f"{prompt}{response}")
        
        # Unload the model
        unload_gguf_model(model)
        print("Model unloaded")
    
    except Exception as e:
        print(f"Error in text generation example: {e}")


def streaming_text_generation_example(model_path):
    """Example of streaming text generation with a GGUF model."""
    print("\n=== Streaming Text Generation Example ===")
    
    try:
        # Load the model
        print(f"Loading model from {model_path}...")
        model = load_gguf_model(
            model_path,
            n_ctx=2048,
            n_batch=512,
            n_gpu_layers=0  # CPU only
        )
        print("Model loaded successfully")
        
        # Generate text with streaming
        prompt = "Tell me a short story about"
        print(f"Generating text with prompt: '{prompt}'")
        
        print("\nGenerated text (streaming):")
        print(prompt, end="", flush=True)
        
        for chunk in generate_text_stream(
            model,
            prompt,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        ):
            print(chunk, end="", flush=True)
            time.sleep(0.01)  # Simulate slower output for demonstration
        
        print("\n\nStreaming complete")
        
        # Unload the model
        unload_gguf_model(model)
        print("Model unloaded")
    
    except Exception as e:
        print(f"Error in streaming text generation example: {e}")


def chat_completion_example(model_path):
    """Example of chat completion with a GGUF model."""
    print("\n=== Chat Completion Example ===")
    
    try:
        # Load the model
        print(f"Loading model from {model_path}...")
        model = load_gguf_model(
            model_path,
            n_ctx=2048,
            n_batch=512,
            n_gpu_layers=0  # CPU only
        )
        print("Model loaded successfully")
        
        # Define chat messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, who are you?"}
        ]
        
        print("Chat messages:")
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")
        
        # Generate chat completion
        response = chat_completion(
            model,
            messages,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
        
        print("\nChat completion response:")
        print(f"assistant: {response['choices'][0]['message']['content']}")
        
        # Unload the model
        unload_gguf_model(model)
        print("Model unloaded")
    
    except Exception as e:
        print(f"Error in chat completion example: {e}")


def streaming_chat_completion_example(model_path):
    """Example of streaming chat completion with a GGUF model."""
    print("\n=== Streaming Chat Completion Example ===")
    
    try:
        # Load the model
        print(f"Loading model from {model_path}...")
        model = load_gguf_model(
            model_path,
            n_ctx=2048,
            n_batch=512,
            n_gpu_layers=0  # CPU only
        )
        print("Model loaded successfully")
        
        # Define chat messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a short poem about programming."}
        ]
        
        print("Chat messages:")
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")
        
        # Generate chat completion with streaming
        print("\nChat completion response (streaming):")
        print("assistant: ", end="", flush=True)
        
        for chunk in chat_completion_stream(
            model,
            messages,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        ):
            content = chunk["choices"][0]["delta"]["content"]
            print(content, end="", flush=True)
            time.sleep(0.01)  # Simulate slower output for demonstration
        
        print("\n\nStreaming complete")
        
        # Unload the model
        unload_gguf_model(model)
        print("Model unloaded")
    
    except Exception as e:
        print(f"Error in streaming chat completion example: {e}")


def async_text_generation_example(model_path):
    """Example of asynchronous text generation with a GGUF model."""
    print("\n=== Asynchronous Text Generation Example ===")
    
    try:
        # Load the model
        print(f"Loading model from {model_path}...")
        model = load_gguf_model(
            model_path,
            n_ctx=2048,
            n_batch=512,
            n_gpu_layers=0  # CPU only
        )
        print("Model loaded successfully")
        
        # Start the inference thread
        start_inference_thread()
        
        # Define a callback function
        result_received = False
        
        def callback(result, error):
            nonlocal result_received
            if error:
                print(f"Error: {error}")
            else:
                print("\nGenerated text (async):")
                print(f"{prompt}{result}")
            result_received = True
        
        # Generate text asynchronously
        prompt = "The future of artificial intelligence is"
        print(f"Generating text asynchronously with prompt: '{prompt}'")
        
        async_generate_text(
            model,
            prompt,
            callback,
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
        
        # Wait for the result
        print("Waiting for result...")
        while not result_received:
            time.sleep(0.1)
        
        # Stop the inference thread
        stop_inference_thread()
        
        # Unload the model
        unload_gguf_model(model)
        print("Model unloaded")
    
    except Exception as e:
        print(f"Error in asynchronous text generation example: {e}")


def model_info_example(model_path):
    """Example of getting model information."""
    print("\n=== Model Information Example ===")
    
    try:
        # Get model information
        print(f"Getting information for model at {model_path}...")
        info = get_gguf_model_info(model_path)
        
        print("\nModel information:")
        for key, value in info.items():
            print(f"{key}: {value}")
    
    except Exception as e:
        print(f"Error getting model information: {e}")


def main():
    """Run the GGUF support examples."""
    print("=== GGUF Support Examples ===")
    
    # Check if GGUF model support is available
    if not check_gguf_availability():
        return
    
    # Download an example model
    model_path = download_example_model()
    if not model_path:
        return
    
    # Run the examples
    text_generation_example(model_path)
    streaming_text_generation_example(model_path)
    chat_completion_example(model_path)
    streaming_chat_completion_example(model_path)
    async_text_generation_example(model_path)
    model_info_example(model_path)
    
    # Clear the model cache
    clear_gguf_model_cache()
    print("\nModel cache cleared")
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
