#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the llama_support module.

This module demonstrates how to use the Llama model support functionality
in RebelSCRIBE, including checking dependencies, loading models, and generating text.
"""

import os
import sys
import time
from typing import List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.ai.llama_support import (
    check_llama_dependencies, is_llama_available, get_available_llama_models,
    download_llama_model, load_llama_model, generate_text_with_llama,
    async_generate_text_with_llama, DEFAULT_LLAMA_MODELS
)
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def check_dependencies_example():
    """Example of checking Llama dependencies."""
    print("\n=== Checking Llama Dependencies ===")
    
    # Check all dependencies
    deps = check_llama_dependencies()
    print(f"Dependencies: {deps}")
    
    # Check if Llama is available
    available = is_llama_available()
    print(f"Llama available: {available}")
    
    if not available:
        print("Llama models are not available. Please install the required dependencies:")
        print("  pip install torch transformers bitsandbytes accelerate")
        return False
    
    return True


def list_models_example():
    """Example of listing available Llama models."""
    print("\n=== Listing Available Llama Models ===")
    
    # Get available models
    models = get_available_llama_models()
    
    if not models:
        print("No Llama models found.")
        print("Default models that can be downloaded:")
        for key, model in DEFAULT_LLAMA_MODELS.items():
            print(f"  - {key}: {model['name']} ({model['description']})")
    else:
        print(f"Found {len(models)} Llama models:")
        for model in models:
            print(f"  - {model['name']}")
            print(f"    Description: {model.get('description', 'N/A')}")
            print(f"    Path: {model.get('path', 'N/A')}")
            print(f"    Quantized: {model.get('quantized', False)}")
            print()


def download_model_example():
    """Example of downloading a Llama model."""
    print("\n=== Downloading a Llama Model ===")
    print("Note: This example will not actually download the model unless you uncomment the code.")
    print("Downloading Llama models requires authentication with the Hugging Face Hub.")
    print("You need to run `huggingface-cli login` before downloading Llama models.")
    
    # Uncomment to actually download a model
    # model_name = DEFAULT_LLAMA_MODELS["llama2-7b"]["name"]
    # print(f"Downloading model: {model_name}")
    # model_path = download_llama_model(model_name)
    # if model_path:
    #     print(f"Model downloaded to: {model_path}")
    # else:
    #     print("Failed to download model.")


def generate_text_example():
    """Example of generating text with a Llama model."""
    print("\n=== Generating Text with Llama ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Llama model downloaded to generate text.")
    
    # Uncomment to actually generate text
    # prompt = "Once upon a time in a land far away,"
    # print(f"Prompt: {prompt}")
    # 
    # try:
    #     # Generate text
    #     generated_texts = generate_text_with_llama(
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
    """Example of streaming text generation with a Llama model."""
    print("\n=== Streaming Text Generation with Llama ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Llama model downloaded to generate text.")
    
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
    #     generate_text_with_llama(
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
    """Example of asynchronous text generation with a Llama model."""
    print("\n=== Asynchronous Text Generation with Llama ===")
    print("Note: This example will not actually generate text unless you uncomment the code.")
    print("You need to have a Llama model downloaded to generate text.")
    
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
    #     async_generate_text_with_llama(
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
    """Example of using a quantized Llama model."""
    print("\n=== Using a Quantized Llama Model ===")
    print("Note: This example will not actually use a quantized model unless you uncomment the code.")
    print("You need to have bitsandbytes installed to use quantized models.")
    
    # Uncomment to actually use a quantized model
    # prompt = "What are the benefits of quantization in machine learning?"
    # print(f"Prompt: {prompt}")
    # 
    # try:
    #     # Generate text with a 4-bit quantized model
    #     print("\nGenerating with 4-bit quantization:")
    #     generated_texts = generate_text_with_llama(
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


def main():
    """Run all examples."""
    print("=== Llama Support Examples ===")
    
    # Check dependencies
    if not check_dependencies_example():
        print("\nCannot run examples because Llama is not available.")
        return
    
    # Run examples
    list_models_example()
    download_model_example()
    generate_text_example()
    streaming_generation_example()
    async_generation_example()
    quantized_model_example()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
