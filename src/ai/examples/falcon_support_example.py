#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the falcon_support module.

This script demonstrates how to use the Falcon model support functionality
in RebelSCRIBE, including model loading, text generation, and chat completion.
"""

import os
import sys
import asyncio
import logging
from typing import Optional

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the falcon_support module
from src.ai.falcon_support import (
    is_falcon_available, check_dependencies, get_available_models,
    load_model, unload_model, clear_model_cache, optimize_model,
    generate_text, generate_text_streaming, chat_completion, chat_completion_streaming,
    FalconModelNotAvailableError, FalconModelLoadError, FalconInferenceError
)


async def check_availability():
    """Check if Falcon models are available."""
    logger.info("Checking Falcon availability...")
    
    # Check if Falcon models are available
    available = is_falcon_available()
    logger.info(f"Falcon models available: {available}")
    
    # Check dependencies
    dependencies = check_dependencies()
    logger.info(f"Dependencies: {dependencies}")
    
    # Get available models
    if available:
        models = get_available_models()
        logger.info(f"Available models: {len(models)}")
        for model in models:
            logger.info(f"  - {model['name']}: {model['description']}")
    
    return available


async def basic_text_generation(model_name: str = "tiiuae/falcon-7b-instruct"):
    """
    Demonstrate basic text generation with a Falcon model.
    
    Args:
        model_name (str): The name or path of the model to use.
    """
    logger.info(f"Basic text generation with {model_name}...")
    
    # Generate text
    prompt = "Write a short story about a robot who discovers emotions."
    try:
        response = await generate_text(
            prompt=prompt,
            model_name_or_path=model_name,
            max_length=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        logger.info(f"Prompt: {prompt}")
        logger.info(f"Response: {response}")
    
    except (FalconModelNotAvailableError, FalconModelLoadError, FalconInferenceError) as e:
        logger.error(f"Error generating text: {e}")


async def streaming_text_generation(model_name: str = "tiiuae/falcon-7b-instruct"):
    """
    Demonstrate streaming text generation with a Falcon model.
    
    Args:
        model_name (str): The name or path of the model to use.
    """
    logger.info(f"Streaming text generation with {model_name}...")
    
    # Define callback function
    def callback(text_chunk: str, error: Optional[str]):
        if error:
            logger.error(f"Streaming error: {error}")
        else:
            print(text_chunk, end="", flush=True)
    
    # Generate text with streaming
    prompt = "Write a short poem about the changing seasons."
    try:
        print(f"Prompt: {prompt}\nResponse: ", end="", flush=True)
        
        await generate_text_streaming(
            prompt=prompt,
            callback=callback,
            model_name_or_path=model_name,
            max_length=256,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        print("\n")  # Add newline after streaming is complete
    
    except (FalconModelNotAvailableError, FalconModelLoadError, FalconInferenceError) as e:
        logger.error(f"Error generating streaming text: {e}")


async def chat_completion_example(model_name: str = "tiiuae/falcon-7b-instruct"):
    """
    Demonstrate chat completion with a Falcon model.
    
    Args:
        model_name (str): The name or path of the model to use.
    """
    logger.info(f"Chat completion with {model_name}...")
    
    # Create messages
    messages = [
        {"role": "system", "content": "You are a helpful writing assistant for a novelist."},
        {"role": "user", "content": "I'm writing a mystery novel and I'm stuck on how to introduce a plot twist."},
        {"role": "assistant", "content": "Plot twists work best when they're both surprising and inevitable. Consider what clues you've already planted that could lead to an unexpected revelation."},
        {"role": "user", "content": "Can you give me an example of a good plot twist for a murder mystery?"}
    ]
    
    try:
        # Generate chat completion
        response = await chat_completion(
            messages=messages,
            model_name_or_path=model_name,
            max_length=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        # Print the conversation and response
        logger.info("Chat conversation:")
        for message in messages:
            logger.info(f"{message['role'].capitalize()}: {message['content']}")
        
        logger.info(f"Assistant: {response}")
    
    except (FalconModelNotAvailableError, FalconModelLoadError, FalconInferenceError) as e:
        logger.error(f"Error generating chat completion: {e}")


async def streaming_chat_completion_example(model_name: str = "tiiuae/falcon-7b-instruct"):
    """
    Demonstrate streaming chat completion with a Falcon model.
    
    Args:
        model_name (str): The name or path of the model to use.
    """
    logger.info(f"Streaming chat completion with {model_name}...")
    
    # Create messages
    messages = [
        {"role": "system", "content": "You are a helpful writing assistant for a novelist."},
        {"role": "user", "content": "I'm writing a fantasy novel. Can you help me create a magic system?"}
    ]
    
    # Define callback function
    def callback(text_chunk: str, error: Optional[str]):
        if error:
            logger.error(f"Streaming error: {error}")
        else:
            print(text_chunk, end="", flush=True)
    
    try:
        # Print the conversation
        logger.info("Chat conversation:")
        for message in messages:
            logger.info(f"{message['role'].capitalize()}: {message['content']}")
        
        print("Assistant: ", end="", flush=True)
        
        # Generate streaming chat completion
        await chat_completion_streaming(
            messages=messages,
            callback=callback,
            model_name_or_path=model_name,
            max_length=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        print("\n")  # Add newline after streaming is complete
    
    except (FalconModelNotAvailableError, FalconModelLoadError, FalconInferenceError) as e:
        logger.error(f"Error generating streaming chat completion: {e}")


async def model_optimization_example(model_name: str = "tiiuae/falcon-7b-instruct"):
    """
    Demonstrate model optimization for a Falcon model.
    
    Args:
        model_name (str): The name or path of the model to use.
    """
    logger.info(f"Model optimization for {model_name}...")
    
    try:
        # Create output directory
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "optimized_falcon")
        
        # Optimize model
        optimized_path = await optimize_model(
            model_name_or_path=model_name,
            output_dir=output_dir,
            quantization="4bit"
        )
        
        if optimized_path:
            logger.info(f"Model optimized and saved to: {optimized_path}")
        else:
            logger.warning("Model optimization failed.")
    
    except (FalconModelNotAvailableError, FalconModelLoadError) as e:
        logger.error(f"Error optimizing model: {e}")


async def cleanup():
    """Clean up resources."""
    logger.info("Cleaning up...")
    
    # Clear model cache
    await clear_model_cache()
    logger.info("Model cache cleared.")


async def main():
    """Main function to run the examples."""
    logger.info("Starting Falcon support examples...")
    
    # Check if Falcon models are available
    available = await check_availability()
    if not available:
        logger.error("Falcon models are not available. Please install the required dependencies.")
        return
    
    # Run examples
    await basic_text_generation()
    await streaming_text_generation()
    await chat_completion_example()
    await streaming_chat_completion_example()
    
    # Model optimization is resource-intensive, so it's commented out by default
    # Uncomment to run the optimization example
    # await model_optimization_example()
    
    # Clean up
    await cleanup()
    
    logger.info("Falcon support examples completed.")


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
