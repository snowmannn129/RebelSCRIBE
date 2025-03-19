"""
Example usage of the AWQ support module.

This example demonstrates how to use the AWQ support module to load and use
AWQ quantized models for text generation and chat completion.

AWQ (Activation-aware Weight Quantization) is an advanced quantization method
that analyzes activation patterns to preserve the most important weights,
resulting in better quality at the same bit-width compared to other methods.

Requirements:
- autoawq package: pip install autoawq
- A GPU with CUDA support
- An AWQ quantized model (can be downloaded from Hugging Face)
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ai.awq_support import get_awq_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_awq_availability():
    """Check if AWQ support is available."""
    manager = get_awq_manager()
    if manager.is_available():
        logger.info("AWQ support is available.")
    else:
        logger.warning("AWQ support is not available. Please install the required dependencies.")
        logger.warning("You need to install autoawq: pip install autoawq")
        logger.warning("You also need a CUDA-capable GPU.")
        return False
    return True


def basic_text_generation():
    """Demonstrate basic text generation with an AWQ quantized model."""
    logger.info("=== Basic Text Generation ===")
    
    # Get the AWQ manager
    manager = get_awq_manager()
    
    # Model path - this should be a path to an AWQ quantized model
    # You can download AWQ quantized models from Hugging Face
    # For example: https://huggingface.co/TheBloke/Llama-2-7B-AWQ
    model_path = "path/to/your/awq/model"
    
    try:
        # Load the model
        logger.info(f"Loading model from {model_path}")
        model, tokenizer = manager.load_model(model_path)
        
        # Generate text
        prompt = "Once upon a time in a land far away,"
        logger.info(f"Generating text with prompt: {prompt}")
        
        output = manager.generate_text(
            model_path,  # Use the model path as the model ID
            prompt,
            max_new_tokens=100,
            temperature=0.7,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.1
        )
        
        logger.info(f"Generated text: {output}")
        
        # Unload the model to free up memory
        manager.unload_model(model_path)
        
    except Exception as e:
        logger.error(f"Error in basic text generation: {str(e)}")


async def async_text_generation():
    """Demonstrate asynchronous text generation with an AWQ quantized model."""
    logger.info("=== Asynchronous Text Generation ===")
    
    # Get the AWQ manager
    manager = get_awq_manager()
    
    # Model path
    model_path = "path/to/your/awq/model"
    
    try:
        # Load the model
        logger.info(f"Loading model from {model_path}")
        model, tokenizer = manager.load_model(model_path)
        
        # Generate text asynchronously
        prompt = "Write a short story about a robot who dreams of becoming human."
        logger.info(f"Generating text asynchronously with prompt: {prompt}")
        
        output = await manager.generate_text_async(
            model_path,
            prompt,
            max_new_tokens=200,
            temperature=0.8,
            top_p=0.92,
            top_k=40,
            repetition_penalty=1.05
        )
        
        logger.info(f"Generated text: {output}")
        
        # Unload the model
        manager.unload_model(model_path)
        
    except Exception as e:
        logger.error(f"Error in asynchronous text generation: {str(e)}")


def streaming_text_generation():
    """Demonstrate streaming text generation with an AWQ quantized model."""
    logger.info("=== Streaming Text Generation ===")
    
    # Get the AWQ manager
    manager = get_awq_manager()
    
    # Model path
    model_path = "path/to/your/awq/model"
    
    try:
        # Load the model
        logger.info(f"Loading model from {model_path}")
        model, tokenizer = manager.load_model(model_path)
        
        # Define a callback function to process streamed tokens
        def process_token(token):
            print(token, end="", flush=True)
        
        # Generate text with streaming
        prompt = "Explain the concept of quantum computing in simple terms."
        logger.info(f"Generating text with streaming using prompt: {prompt}")
        print("\nGenerated text: ", end="", flush=True)
        
        streamer = manager.generate_text_stream(
            model_path,
            prompt,
            max_new_tokens=150,
            temperature=0.7,
            callback=process_token
        )
        
        # Iterate through the streamer to get the generated text
        # Note: This is not necessary if you're using the callback
        # but it's shown here for demonstration purposes
        full_text = ""
        for text in streamer:
            full_text += text
        
        print("\n")  # Add a newline after the generated text
        
        # Unload the model
        manager.unload_model(model_path)
        
    except Exception as e:
        logger.error(f"Error in streaming text generation: {str(e)}")


def chat_completion():
    """Demonstrate chat completion with an AWQ quantized model."""
    logger.info("=== Chat Completion ===")
    
    # Get the AWQ manager
    manager = get_awq_manager()
    
    # Model path
    model_path = "path/to/your/awq/model"
    
    try:
        # Load the model
        logger.info(f"Loading model from {model_path}")
        model, tokenizer = manager.load_model(model_path)
        
        # Create a chat conversation
        messages = [
            {"role": "system", "content": "You are a helpful, concise assistant."},
            {"role": "user", "content": "What are the main benefits of AWQ quantization?"},
        ]
        
        logger.info("Generating chat completion")
        
        # Generate a chat completion
        response = manager.chat_completion(
            model_path,
            messages,
            max_new_tokens=200,
            temperature=0.7,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.1
        )
        
        logger.info(f"Assistant: {response}")
        
        # Continue the conversation
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": "How does it compare to other quantization methods?"})
        
        logger.info("Generating follow-up response")
        
        # Generate another response
        response = manager.chat_completion(
            model_path,
            messages,
            max_new_tokens=200,
            temperature=0.7,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.1
        )
        
        logger.info(f"Assistant: {response}")
        
        # Unload the model
        manager.unload_model(model_path)
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")


def main():
    """Run the example."""
    # Check if AWQ support is available
    if not check_awq_availability():
        return
    
    # Run the examples
    basic_text_generation()
    
    # Run the async example
    asyncio.run(async_text_generation())
    
    streaming_text_generation()
    
    chat_completion()
    
    # Close the AWQ manager to release resources
    manager = get_awq_manager()
    manager.close()
    logger.info("AWQ manager closed")


if __name__ == "__main__":
    main()
