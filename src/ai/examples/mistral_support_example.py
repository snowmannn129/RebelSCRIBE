#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the mistral_support module.

This module demonstrates how to use the Mistral model support functionality
in RebelSCRIBE, including checking dependencies, loading models, and generating text.
"""

import os
import sys
import time
from typing import List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.ai.mistral_support import (
    check_mistral_dependencies, is_mistral_available, get_available_mistral_models,
    download_mistral_model, load_mistral_model, generate_text_with_mistral,
    async_generate_text_with_mistral, format_chat_prompt, chat_with_mistral,
    async_chat_with_mistral, DEFAULT_MISTRAL_MODELS
)
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def check_dependencies_example():
    """Example of checking Mistral dependencies."""
    print("\n=== Checking Mistral Dependencies ===")
    
    # Check all dependencies
    deps = check_mistral_dependencies()
    print(f"Dependencies: {deps}")
    
    # Check if Mistral is available
    available = is_mistral_available()
    print(f"Mistral available: {available}")
    
    if not available:
        print("Mistral models are not available. Please install the required dependencies:")
        print("  pip install torch transformers bitsandbytes accelerate")
        return False
    
    return True


def list_models_example():
    """Example of listing available Mistral models."""
    print("\n=== Listing Available Mistral Models ===")
    
    # Get available models
    models = get_available_mistral_models()
    
    if not models:
        print("No Mistral models found.")
        print("Default models that can be downloaded:")
        for key, model in DEFAULT_MISTRAL_MODELS.items():
            print(f"  - {key}: {model['name']} ({model['description']})")
    else:
        print(f"Found {len(models)} Mistral models:")
        for model in models:
            print(f"  - {model['name']}")
            print(f"    Description: {model.get('description', 'N/A')}")
            print(f"    Path: {model.get('path', 'N/A')}")
            print(f"    Quantized: {model.get('quantized', False)}")
            print()


def download_model_example():
    """Example of downloading a Mistral model."""
    print("\n=== Downloading a Mistral Model ===")
    print("Note: This example will not actually download the model unless you uncomment the code.")
    print("Downloading Mistral models requires internet connection.")
    
    # Uncomment to actually download a model
    # model_name = DEFAULT_MISTRAL_MODELS["mistral-7b"]["name"]
    # print(f"Downloading model: {model_name}")
    # model_path = download_mistral_model(model_name)
    # if model_path:
    #     print(f"Model downloaded to: {model_path}")
    # else:
    #     print("Failed to download model.")


def generate_text_example():
    """Example of generating text with a Mistral model."""
    print("\n=== Generating Text with Mistral ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Mistral model downloaded to generate text.")
    
    # Uncomment to actually generate text
    # prompt = "Once upon a time in a land far away,"
    # print(f"Prompt: {prompt}")
    # 
    # try:
    #     # Generate text
    #     generated_texts = generate_text_with_mistral(
    #         prompt,
    #         max_length=100,
    #         temperature=0.7,
    #         top_p=0.9,
    #         top_k=50,
    #         num_return_sequences=1
    #     )
    #     
    #     # Print generated text
    #     for i, text in enumerate(generated_texts):
    #         print(f"\nGenerated text {i+1}:")
    #         print(text)
    # 
    # except Exception as e:
    #     print(f"Error generating text: {e}")


def streaming_generation_example():
    """Example of streaming text generation with a Mistral model."""
    print("\n=== Streaming Text Generation with Mistral ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Mistral model downloaded to generate text.")
    
    # Uncomment to actually generate text with streaming
    # prompt = "Write a short story about a robot who dreams:"
    # print(f"Prompt: {prompt}")
    # 
    # # Define a callback function for streaming
    # def stream_callback(token: str):
    #     print(token, end="", flush=True)
    # 
    # try:
    #     # Generate text with streaming
    #     print("\nGenerated text:")
    #     generate_text_with_mistral(
    #         prompt,
    #         max_length=100,
    #         temperature=0.7,
    #         stream=True,
    #         callback=stream_callback
    #     )
    #     print()  # Add a newline at the end
    # 
    # except Exception as e:
    #     print(f"\nError generating text: {e}")


def async_generation_example():
    """Example of asynchronous text generation with a Mistral model."""
    print("\n=== Asynchronous Text Generation with Mistral ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Mistral model downloaded to generate text.")
    
    # Uncomment to actually generate text asynchronously
    # prompt = "Explain the theory of relativity in simple terms:"
    # print(f"Prompt: {prompt}")
    # 
    # # Define a callback function for async generation
    # def async_callback(result: Optional[List[str]], error: Optional[str]):
    #     if error:
    #         print(f"\nError: {error}")
    #     else:
    #         print("\nGenerated text:")
    #         for text in result:
    #             print(text)
    # 
    # try:
    #     # Generate text asynchronously
    #     print("Generating text asynchronously...")
    #     async_generate_text_with_mistral(
    #         prompt,
    #         async_callback,
    #         max_length=100,
    #         temperature=0.7
    #     )
    #     
    #     # Wait for the generation to complete
    #     print("Waiting for generation to complete...")
    #     time.sleep(10)  # Adjust the sleep time as needed
    # 
    # except Exception as e:
    #     print(f"Error setting up async generation: {e}")


def chat_example():
    """Example of chatting with a Mistral model."""
    print("\n=== Chatting with Mistral ===")
    print("Note: This example will not actually chat unless you uncomment the code.")
    print("You need to have a Mistral Instruct model downloaded to chat.")
    
    # Uncomment to actually chat
    # # Create messages
    # messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Hello, can you tell me about Mistral AI?"}
    # ]
    # 
    # try:
    #     # Chat with Mistral
    #     response = chat_with_mistral(
    #         messages,
    #         model_name_or_path=DEFAULT_MISTRAL_MODELS["mistral-7b-instruct"]["name"],
    #         max_length=200,
    #         temperature=0.7
    #     )
    #     
    #     # Print response
    #     print("\nMistral's response:")
    #     print(response)
    # 
    # except Exception as e:
    #     print(f"Error chatting with Mistral: {e}")


def async_chat_example():
    """Example of asynchronous chatting with a Mistral model."""
    print("\n=== Asynchronous Chatting with Mistral ===")
    print("Note: This example will not actually chat unless you uncomment the code.")
    print("You need to have a Mistral Instruct model downloaded to chat.")
    
    # Uncomment to actually chat asynchronously
    # # Create messages
    # messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "What are the main features of Mistral models?"}
    # ]
    # 
    # # Define a callback function for async chat
    # def async_callback(result: Optional[str], error: Optional[str]):
    #     if error:
    #         print(f"\nError: {error}")
    #     else:
    #         print("\nMistral's response:")
    #         print(result)
    # 
    # try:
    #     # Chat with Mistral asynchronously
    #     print("Chatting asynchronously...")
    #     async_chat_with_mistral(
    #         messages,
    #         async_callback,
    #         model_name_or_path=DEFAULT_MISTRAL_MODELS["mistral-7b-instruct"]["name"],
    #         max_length=200,
    #         temperature=0.7
    #     )
    #     
    #     # Wait for the chat to complete
    #     print("Waiting for response...")
    #     time.sleep(10)  # Adjust the sleep time as needed
    # 
    # except Exception as e:
    #     print(f"Error setting up async chat: {e}")


def quantized_model_example():
    """Example of using a quantized Mistral model."""
    print("\n=== Using a Quantized Mistral Model ===")
    print("Note: This example will not actually use a quantized model unless you uncomment the code.")
    print("You need to have bitsandbytes installed to use quantized models.")
    
    # Uncomment to actually use a quantized model
    # prompt = "What are the benefits of quantization in machine learning?"
    # print(f"Prompt: {prompt}")
    # 
    # try:
    #     # Generate text with a 4-bit quantized model
    #     print("\nGenerating with 4-bit quantization:")
    #     generated_texts = generate_text_with_mistral(
    #         prompt,
    #         max_length=100,
    #         temperature=0.7,
    #         quantization="4bit"
    #     )
    #     
    #     # Print generated text
    #     for text in generated_texts:
    #         print(text)
    # 
    # except Exception as e:
    #     print(f"Error generating text with quantized model: {e}")


def format_chat_prompt_example():
    """Example of formatting a chat prompt for Mistral models."""
    print("\n=== Formatting Chat Prompt for Mistral ===")
    
    # Create messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
        {"role": "user", "content": "What can you help me with?"}
    ]
    
    # Format prompt for standard Mistral
    print("Formatted prompt for standard Mistral:")
    prompt_standard = format_chat_prompt(messages, "mistralai/Mistral-7B-Instruct-v0.1")
    print(prompt_standard)
    
    # Format prompt for Mixtral
    print("\nFormatted prompt for Mixtral:")
    prompt_mixtral = format_chat_prompt(messages, "mistralai/Mixtral-8x7B-Instruct-v0.1")
    print(prompt_mixtral)


def main():
    """Run all examples."""
    print("=== Mistral Support Examples ===")
    
    # Check dependencies
    if not check_dependencies_example():
        print("\nCannot run examples because Mistral is not available.")
        return
    
    # Run examples
    list_models_example()
    download_model_example()
    generate_text_example()
    streaming_generation_example()
    async_generation_example()
    chat_example()
    async_chat_example()
    quantized_model_example()
    format_chat_prompt_example()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
