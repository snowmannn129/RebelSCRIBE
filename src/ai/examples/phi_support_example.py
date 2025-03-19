#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the phi_support module.

This module demonstrates how to use the Microsoft Phi model support functionality
in RebelSCRIBE, including checking dependencies, loading models, and generating text.
"""

import os
import sys
import time
from typing import List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.ai.phi_support import (
    check_phi_dependencies, is_phi_available, get_available_phi_models,
    download_phi_model, load_phi_model, generate_text_with_phi,
    async_generate_text_with_phi, format_chat_prompt, chat_with_phi,
    async_chat_with_phi, DEFAULT_PHI_MODELS
)
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def check_dependencies_example():
    """Example of checking Phi dependencies."""
    print("\n=== Checking Phi Dependencies ===")
    
    # Check all dependencies
    deps = check_phi_dependencies()
    print(f"Dependencies: {deps}")
    
    # Check if Phi is available
    available = is_phi_available()
    print(f"Phi available: {available}")
    
    if not available:
        print("Phi models are not available. Please install the required dependencies:")
        print("  pip install torch transformers bitsandbytes accelerate")
        return False
    
    return True


def list_models_example():
    """Example of listing available Phi models."""
    print("\n=== Listing Available Phi Models ===")
    
    # Get available models
    models = get_available_phi_models()
    
    if not models:
        print("No Phi models found.")
        print("Default models that can be downloaded:")
        for key, model in DEFAULT_PHI_MODELS.items():
            print(f"  - {key}: {model['name']} ({model['description']})")
    else:
        print(f"Found {len(models)} Phi models:")
        for model in models:
            print(f"  - {model['name']}")
            print(f"    Description: {model.get('description', 'N/A')}")
            print(f"    Path: {model.get('path', 'N/A')}")
            print(f"    Quantized: {model.get('quantized', False)}")
            print()


def download_model_example():
    """Example of downloading a Phi model."""
    print("\n=== Downloading a Phi Model ===")
    print("Note: This example will not actually download the model unless you uncomment the code.")
    
    # Uncomment to actually download a model
    # model_name = DEFAULT_PHI_MODELS["phi-2"]["name"]
    # print(f"Downloading model: {model_name}")
    # model_path = download_phi_model(model_name)
    # if model_path:
    #     print(f"Model downloaded to: {model_path}")
    # else:
    #     print("Failed to download model.")


def generate_text_example():
    """Example of generating text with a Phi model."""
    print("\n=== Generating Text with Phi ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Phi model downloaded to generate text.")
    
    # Uncomment to actually generate text
    # prompt = "Once upon a time in a land far away,"
    # print(f"Prompt: {prompt}")
    # 
    # try:
    #     # Generate text
    #     generated_texts = generate_text_with_phi(
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
    """Example of streaming text generation with a Phi model."""
    print("\n=== Streaming Text Generation with Phi ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Phi model downloaded to generate text.")
    
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
    #     generate_text_with_phi(
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
    """Example of asynchronous text generation with a Phi model."""
    print("\n=== Asynchronous Text Generation with Phi ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Phi model downloaded to generate text.")
    
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
    #     async_generate_text_with_phi(
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


def quantized_model_example():
    """Example of using a quantized Phi model."""
    print("\n=== Using a Quantized Phi Model ===")
    print("Note: This example will not actually use a quantized model unless you uncomment the code.")
    print("You need to have bitsandbytes installed to use quantized models.")
    
    # Uncomment to actually use a quantized model
    # prompt = "What are the benefits of quantization in machine learning?"
    # print(f"Prompt: {prompt}")
    # 
    # try:
    #     # Generate text with a 4-bit quantized model
    #     print("\nGenerating with 4-bit quantization:")
    #     generated_texts = generate_text_with_phi(
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


def chat_example():
    """Example of using Phi models for chat."""
    print("\n=== Chat with Phi ===")
    print("Note: This example will not actually generate chat responses unless you uncomment the code.")
    print("You need to have a Phi model downloaded to use chat functionality.")
    
    # Uncomment to actually use chat functionality
    # # Create messages for Phi-2
    # messages_phi2 = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Hello, can you help me with writing a short poem?"}
    # ]
    # 
    # # Create messages for Phi-3
    # messages_phi3 = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Hello, can you help me with writing a short poem?"}
    # ]
    # 
    # try:
    #     # Chat with Phi-2
    #     print("\nChatting with Phi-2:")
    #     response_phi2 = chat_with_phi(
    #         messages_phi2,
    #         model_name_or_path="microsoft/phi-2",
    #         max_length=100,
    #         temperature=0.7
    #     )
    #     print(f"Phi-2 response: {response_phi2}")
    #     
    #     # Chat with Phi-3
    #     print("\nChatting with Phi-3:")
    #     response_phi3 = chat_with_phi(
    #         messages_phi3,
    #         model_name_or_path="microsoft/Phi-3-mini-4k-instruct",
    #         max_length=100,
    #         temperature=0.7
    #     )
    #     print(f"Phi-3 response: {response_phi3}")
    # 
    # except Exception as e:
    #     print(f"Error in chat: {e}")


def async_chat_example():
    """Example of asynchronous chat with a Phi model."""
    print("\n=== Asynchronous Chat with Phi ===")
    print("Note: This example will not actually generate chat responses unless you uncomment the code.")
    print("You need to have a Phi model downloaded to use chat functionality.")
    
    # Uncomment to actually use async chat functionality
    # # Create messages
    # messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Hello, can you help me with writing a short poem?"}
    # ]
    # 
    # # Define a callback function for async chat
    # def async_callback(result: Optional[str], error: Optional[str]):
    #     if error:
    #         print(f"\nError: {error}")
    #     else:
    #         print("\nPhi response:")
    #         print(result)
    # 
    # try:
    #     # Chat asynchronously
    #     print("Chatting asynchronously...")
    #     async_chat_with_phi(
    #         messages,
    #         async_callback,
    #         model_name_or_path="microsoft/Phi-3-mini-4k-instruct",
    #         max_length=100,
    #         temperature=0.7
    #     )
    #     
    #     # Wait for the chat to complete
    #     print("Waiting for response...")
    #     time.sleep(10)  # Adjust the sleep time as needed
    # 
    # except Exception as e:
    #     print(f"Error setting up async chat: {e}")


def main():
    """Run all examples."""
    print("=== Phi Support Examples ===")
    
    # Check dependencies
    if not check_dependencies_example():
        print("\nCannot run examples because Phi is not available.")
        return
    
    # Run examples
    list_models_example()
    download_model_example()
    generate_text_example()
    streaming_generation_example()
    async_generation_example()
    quantized_model_example()
    chat_example()
    async_chat_example()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
