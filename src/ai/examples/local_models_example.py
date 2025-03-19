#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example script demonstrating how to use the local_models module.

This script shows how to:
1. Check if local models are available
2. Download and load models
3. Generate text, summarize text, and correct grammar
4. Use asynchronous inference
5. Fine-tune a model
"""

import os
import sys
import time
import logging
from typing import List, Optional

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ai.local_models import (
    check_dependencies, is_local_models_available, get_models_directory,
    get_available_models, download_model, load_model, unload_model,
    clear_model_cache, optimize_model, quantize_model,
    generate_text, summarize_text, correct_grammar,
    start_inference_thread, stop_inference_thread,
    async_generate_text, async_summarize_text, async_correct_grammar,
    fine_tune_model, ModelNotAvailableError, ModelLoadError, InferenceError
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_availability():
    """Check if local models are available."""
    logger.info("Checking dependencies...")
    deps = check_dependencies()
    for dep, available in deps.items():
        logger.info(f"  {dep}: {'Available' if available else 'Not available'}")
    
    available = is_local_models_available()
    logger.info(f"Local models functionality is {'available' if available else 'not available'}")
    
    if not available:
        logger.info("To use local models, install the required dependencies:")
        logger.info("  pip install torch transformers")
        logger.info("For optimized inference, also install:")
        logger.info("  pip install onnxruntime optimum")
        return False
    
    return True


def list_available_models():
    """List available local models."""
    logger.info("Models directory: " + get_models_directory())
    
    models = get_available_models()
    if not models:
        logger.info("No models available. Use download_model() to download a model.")
        return
    
    logger.info(f"Found {len(models)} models:")
    for i, model in enumerate(models):
        logger.info(f"  {i+1}. {model['name']} ({model['task']})")
        logger.info(f"     Path: {model['path']}")
        logger.info(f"     Description: {model['description']}")
        if model.get('quantized'):
            logger.info(f"     Quantized: Yes")
        if model.get('optimized'):
            logger.info(f"     Optimized: Yes (level: {model.get('optimization_level', 'unknown')})")
        if model.get('fine_tuned'):
            logger.info(f"     Fine-tuned: Yes (on {model.get('training_examples', 'unknown')} examples)")


def download_example_model():
    """Download an example model."""
    logger.info("Downloading a small model (GPT-2)...")
    model_path = download_model("gpt2", "text-generation")
    
    if model_path:
        logger.info(f"Model downloaded to: {model_path}")
        return model_path
    else:
        logger.error("Failed to download model")
        return None


def generate_text_example(model_path: Optional[str] = None):
    """Generate text using a local model."""
    try:
        logger.info("Generating text...")
        prompt = "Once upon a time in a land far away,"
        
        # Generate text
        generated_texts = generate_text(
            prompt=prompt,
            model_name_or_path=model_path,
            max_length=100,
            temperature=0.7,
            num_return_sequences=3
        )
        
        logger.info(f"Generated {len(generated_texts)} text sequences:")
        for i, text in enumerate(generated_texts):
            logger.info(f"  {i+1}. {text}")
        
        return True
    
    except (ModelNotAvailableError, ModelLoadError, InferenceError) as e:
        logger.error(f"Error generating text: {e}")
        return False


def summarize_text_example(model_path: Optional[str] = None):
    """Summarize text using a local model."""
    try:
        logger.info("Summarizing text...")
        text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, 
        as opposed to natural intelligence displayed by animals including humans. 
        AI research has been defined as the field of study of intelligent agents, 
        which refers to any system that perceives its environment and takes actions 
        that maximize its chance of achieving its goals.
        
        The term "artificial intelligence" had previously been used to describe 
        machines that mimic and display "human" cognitive skills that are associated 
        with the human mind, such as "learning" and "problem-solving". This definition 
        has since been rejected by major AI researchers who now describe AI in terms 
        of rationality and acting rationally, which does not limit how intelligence 
        can be articulated.
        
        AI applications include advanced web search engines, recommendation systems, 
        understanding human speech, self-driving cars, automated decision-making, and 
        competing at the highest level in strategic game systems. As machines become 
        increasingly capable, tasks considered to require "intelligence" are often 
        removed from the definition of AI, a phenomenon known as the AI effect.
        """
        
        # Summarize text
        summary = summarize_text(
            text=text,
            model_name_or_path=model_path,
            max_length=100,
            min_length=30
        )
        
        logger.info(f"Summary: {summary}")
        
        return True
    
    except (ModelNotAvailableError, ModelLoadError, InferenceError) as e:
        logger.error(f"Error summarizing text: {e}")
        return False


def correct_grammar_example(model_path: Optional[str] = None):
    """Correct grammar using a local model."""
    try:
        logger.info("Correcting grammar...")
        text = "I has went to the store yesterday and buyed some milk."
        
        # Correct grammar
        corrected = correct_grammar(
            text=text,
            model_name_or_path=model_path
        )
        
        logger.info(f"Original: {text}")
        logger.info(f"Corrected: {corrected}")
        
        return True
    
    except (ModelNotAvailableError, ModelLoadError, InferenceError) as e:
        logger.error(f"Error correcting grammar: {e}")
        return False


def async_inference_example():
    """Demonstrate asynchronous inference."""
    logger.info("Starting asynchronous inference...")
    
    # Start the inference thread
    start_inference_thread()
    
    # Define callback functions
    def text_callback(result: List[str], error: Optional[str]):
        if error:
            logger.error(f"Async text generation error: {error}")
        else:
            logger.info(f"Async text generation result: {result[0][:100]}...")
    
    def summary_callback(result: str, error: Optional[str]):
        if error:
            logger.error(f"Async summarization error: {error}")
        else:
            logger.info(f"Async summarization result: {result}")
    
    # Submit async tasks
    async_generate_text(
        prompt="The future of artificial intelligence is",
        callback=text_callback,
        max_length=100
    )
    
    async_summarize_text(
        text="Artificial intelligence (AI) is intelligence demonstrated by machines. "
             "AI applications include advanced web search engines, recommendation systems, "
             "understanding human speech, self-driving cars, and automated decision-making.",
        callback=summary_callback,
        max_length=50
    )
    
    # Wait for tasks to complete
    logger.info("Waiting for async tasks to complete...")
    time.sleep(10)
    
    # Stop the inference thread
    stop_inference_thread()
    
    logger.info("Async inference example completed")


def fine_tuning_example(model_path: Optional[str] = None):
    """Demonstrate model fine-tuning."""
    logger.info("Fine-tuning a model...")
    
    # Create training data
    training_data = [
        {
            "prompt": "What is artificial intelligence?",
            "completion": "Artificial intelligence is intelligence demonstrated by machines."
        },
        {
            "prompt": "What are AI applications?",
            "completion": "AI applications include web search, recommendation systems, speech recognition, and self-driving cars."
        },
        {
            "prompt": "What is machine learning?",
            "completion": "Machine learning is a subset of AI that enables systems to learn from data without explicit programming."
        },
        {
            "prompt": "What is deep learning?",
            "completion": "Deep learning is a subset of machine learning using neural networks with multiple layers."
        },
        {
            "prompt": "What is natural language processing?",
            "completion": "Natural language processing is a field of AI that enables computers to understand and generate human language."
        }
    ]
    
    # Create output directory
    output_dir = os.path.join(get_models_directory(), "fine_tuned_example")
    
    try:
        # Fine-tune the model
        fine_tuned_path = fine_tune_model(
            model_name_or_path=model_path or "gpt2",
            training_data=training_data,
            output_dir=output_dir,
            num_train_epochs=1,
            batch_size=2
        )
        
        if fine_tuned_path:
            logger.info(f"Model fine-tuned successfully and saved to: {fine_tuned_path}")
            
            # Test the fine-tuned model
            logger.info("Testing the fine-tuned model...")
            generated_texts = generate_text(
                prompt="What is artificial intelligence?",
                model_name_or_path=fine_tuned_path,
                max_length=50
            )
            
            logger.info(f"Generated response: {generated_texts[0]}")
            
            return True
        else:
            logger.error("Fine-tuning failed")
            return False
    
    except (ModelNotAvailableError, ModelLoadError, InferenceError) as e:
        logger.error(f"Error fine-tuning model: {e}")
        return False


def main():
    """Run the example script."""
    logger.info("Local Models Example Script")
    logger.info("==========================")
    
    # Check if local models are available
    if not check_availability():
        return
    
    # List available models
    list_available_models()
    
    # Download a model if needed
    models = get_available_models()
    if not models:
        model_path = download_example_model()
    else:
        model_path = models[0]["path"]
    
    # Generate text
    generate_text_example(model_path)
    
    # Summarize text
    summarize_text_example(model_path)
    
    # Correct grammar
    correct_grammar_example(model_path)
    
    # Async inference
    async_inference_example()
    
    # Fine-tuning (optional, can be slow)
    # fine_tuning_example(model_path)
    
    logger.info("Example script completed")


if __name__ == "__main__":
    main()
