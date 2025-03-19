#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the GPU acceleration module.

This example demonstrates how to use the GPU acceleration module to:
1. Detect available GPU hardware
2. Configure models for optimal performance
3. Load and run models with GPU acceleration
"""

import os
import logging
import time
from typing import Dict, Any

# Import the GPU acceleration module
from src.ai import gpu_acceleration
from src.utils.logging_utils import get_logger

# Set up logging
logger = get_logger(__name__)

# Try to import optional dependencies
try:
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    logger.warning("Required dependencies not available. Install with: pip install torch transformers")


def print_gpu_info():
    """Print information about available GPU hardware."""
    logger.info("Checking for available GPU hardware...")
    
    # Get GPU information
    gpu_info = gpu_acceleration.get_gpu_info()
    
    logger.info(f"GPU Type: {gpu_info['type']}")
    logger.info(f"GPU Count: {gpu_info['count']}")
    
    if gpu_info['count'] > 0:
        logger.info(f"GPU Memory (MB): {gpu_info['memory']}")
    
    logger.info(f"CUDA Available: {gpu_info['cuda_available']}")
    logger.info(f"ROCm Available: {gpu_info['rocm_available']}")
    logger.info(f"MPS Available: {gpu_info['mps_available']}")
    
    # Check if GPU acceleration is available
    if gpu_acceleration.is_gpu_available():
        logger.info("GPU acceleration is available!")
    else:
        logger.info("GPU acceleration is not available. Using CPU.")


def load_model_with_gpu_acceleration(model_name: str, model_size_gb: float) -> Dict[str, Any]:
    """
    Load a model with GPU acceleration.
    
    Args:
        model_name: The name of the model to load.
        model_size_gb: The approximate size of the model in GB.
        
    Returns:
        Dict[str, Any]: A dictionary containing the loaded model and tokenizer.
    """
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Cannot load model: required dependencies are not available.")
        return {}
    
    logger.info(f"Loading model {model_name} with GPU acceleration...")
    
    # Get the optimal configuration for the model
    config = gpu_acceleration.get_transformers_config(model_size_gb)
    
    logger.info(f"Using configuration: {config}")
    
    try:
        # Load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load the model with the optimal configuration
        model = AutoModelForCausalLM.from_pretrained(model_name, **config)
        
        # Optimize the model for inference
        model = gpu_acceleration.optimize_for_inference(model)
        
        logger.info(f"Model {model_name} loaded successfully with GPU acceleration")
        
        return {
            "model": model,
            "tokenizer": tokenizer
        }
    
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return {}


def run_inference_benchmark(model_dict: Dict[str, Any], prompt: str, max_length: int = 100) -> Dict[str, Any]:
    """
    Run an inference benchmark with the loaded model.
    
    Args:
        model_dict: A dictionary containing the model and tokenizer.
        prompt: The prompt to generate text from.
        max_length: The maximum length of the generated text.
        
    Returns:
        Dict[str, Any]: Benchmark results.
    """
    if not model_dict or "model" not in model_dict or "tokenizer" not in model_dict:
        logger.error("Cannot run benchmark: model not loaded.")
        return {}
    
    model = model_dict["model"]
    tokenizer = model_dict["tokenizer"]
    
    logger.info(f"Running inference benchmark with prompt: {prompt}")
    
    try:
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(model.device)
        
        # Warm-up run
        logger.info("Performing warm-up run...")
        with torch.no_grad():
            _ = model.generate(
                input_ids,
                max_length=20,
                num_return_sequences=1
            )
        
        # Benchmark run
        logger.info("Starting benchmark run...")
        start_time = time.time()
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_length=max_length,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                top_k=50
            )
        
        end_time = time.time()
        
        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Calculate metrics
        inference_time = end_time - start_time
        tokens_generated = len(outputs[0]) - len(input_ids[0])
        tokens_per_second = tokens_generated / inference_time
        
        logger.info(f"Generated {tokens_generated} tokens in {inference_time:.2f} seconds")
        logger.info(f"Tokens per second: {tokens_per_second:.2f}")
        logger.info(f"Generated text: {generated_text}")
        
        return {
            "inference_time": inference_time,
            "tokens_generated": tokens_generated,
            "tokens_per_second": tokens_per_second,
            "generated_text": generated_text
        }
    
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        return {}


def compare_gpu_vs_cpu(model_name: str, model_size_gb: float, prompt: str, max_length: int = 100) -> None:
    """
    Compare inference performance between GPU and CPU.
    
    Args:
        model_name: The name of the model to load.
        model_size_gb: The approximate size of the model in GB.
        prompt: The prompt to generate text from.
        max_length: The maximum length of the generated text.
    """
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Cannot run comparison: required dependencies are not available.")
        return
    
    logger.info(f"Comparing GPU vs CPU performance for model {model_name}")
    
    # GPU run
    logger.info("=== GPU Run ===")
    gpu_model = load_model_with_gpu_acceleration(model_name, model_size_gb)
    gpu_results = run_inference_benchmark(gpu_model, prompt, max_length)
    
    # CPU run
    logger.info("=== CPU Run ===")
    # Force CPU by setting device_map to "cpu"
    try:
        logger.info("Loading model on CPU...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="cpu")
        
        cpu_model = {
            "model": model,
            "tokenizer": tokenizer
        }
        
        cpu_results = run_inference_benchmark(cpu_model, prompt, max_length)
        
        # Compare results
        if gpu_results and cpu_results:
            speedup = cpu_results["inference_time"] / gpu_results["inference_time"]
            logger.info("=== Comparison ===")
            logger.info(f"GPU: {gpu_results['tokens_per_second']:.2f} tokens/sec")
            logger.info(f"CPU: {cpu_results['tokens_per_second']:.2f} tokens/sec")
            logger.info(f"Speedup: {speedup:.2f}x")
    
    except Exception as e:
        logger.error(f"Error in CPU comparison: {e}")


def main():
    """Run the GPU acceleration example."""
    logger.info("=== GPU Acceleration Example ===")
    
    # Print GPU information
    print_gpu_info()
    
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Required dependencies not available. Install with: pip install torch transformers")
        return
    
    # Example: Load and run a small model
    model_name = "gpt2"  # A small model that should work on most GPUs
    model_size_gb = 0.5  # Approximate size of GPT-2 small
    
    # Load the model with GPU acceleration
    model_dict = load_model_with_gpu_acceleration(model_name, model_size_gb)
    
    if model_dict:
        # Run inference benchmark
        prompt = "Once upon a time in a land far away,"
        benchmark_results = run_inference_benchmark(model_dict, prompt)
        
        if benchmark_results:
            logger.info("Benchmark completed successfully!")
        
        # Compare GPU vs CPU (only if you have time - this can be slow)
        # compare_gpu_vs_cpu(model_name, model_size_gb, prompt)


if __name__ == "__main__":
    main()
