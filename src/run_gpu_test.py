#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU Acceleration Test Script for RebelSCRIBE.

This script tests the GPU acceleration functionality by:
1. Detecting available GPU hardware
2. Printing GPU information
3. Running a simple benchmark if a model is available
"""

import os
import sys
import argparse
import time
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the GPU acceleration module
from ai import gpu_acceleration
from utils.logging_utils import get_logger

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
    logger.info("=== GPU Information ===")
    
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


def run_benchmark(model_name: str, prompt: str, max_length: int = 50):
    """
    Run a simple benchmark using the specified model.
    
    Args:
        model_name: The name of the model to use.
        prompt: The prompt to generate text from.
        max_length: The maximum length of the generated text.
    """
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Cannot run benchmark: required dependencies are not available.")
        return
    
    logger.info(f"=== Running Benchmark with {model_name} ===")
    logger.info(f"Prompt: {prompt}")
    
    try:
        # Get the optimal configuration for the model
        # Estimate model size based on name (very rough estimate)
        model_size_gb = 0.5  # Default for small models
        if "large" in model_name.lower() or "7b" in model_name.lower():
            model_size_gb = 7.0
        elif "medium" in model_name.lower() or "3b" in model_name.lower():
            model_size_gb = 3.0
        
        config = gpu_acceleration.get_transformers_config(model_size_gb)
        logger.info(f"Using configuration: {config}")
        
        # Load the tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load the model with the optimal configuration
        logger.info("Loading model...")
        start_time = time.time()
        model = AutoModelForCausalLM.from_pretrained(model_name, **config)
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")
        
        # Optimize the model for inference
        logger.info("Optimizing model for inference...")
        model = gpu_acceleration.optimize_for_inference(model)
        
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
        return None


def main():
    """Run the GPU acceleration test."""
    parser = argparse.ArgumentParser(description="Test GPU acceleration in RebelSCRIBE")
    parser.add_argument("--model", type=str, default="gpt2", 
                        help="Model to use for benchmark (default: gpt2)")
    parser.add_argument("--prompt", type=str, 
                        default="Once upon a time in a land far away,",
                        help="Prompt for text generation")
    parser.add_argument("--max-length", type=int, default=50,
                        help="Maximum length of generated text")
    parser.add_argument("--info-only", action="store_true",
                        help="Only print GPU information, don't run benchmark")
    
    args = parser.parse_args()
    
    logger.info("=== RebelSCRIBE GPU Acceleration Test ===")
    
    # Print GPU information
    print_gpu_info()
    
    if args.info_only:
        logger.info("Info-only mode, skipping benchmark.")
        return
    
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Required dependencies not available. Install with: pip install torch transformers")
        return
    
    # Run benchmark
    run_benchmark(args.model, args.prompt, args.max_length)


if __name__ == "__main__":
    main()
