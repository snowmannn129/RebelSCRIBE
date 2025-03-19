#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the adapter_support module.

This example demonstrates how to use the AdapterManager class to create,
save, load, and fine-tune models with LoRA and QLoRA adapters.
"""

import os
import logging
from pathlib import Path

from src.ai.adapter_support import AdapterManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def example_create_lora_adapter():
    """Example of creating a LoRA adapter for a model."""
    logger.info("Example: Creating a LoRA adapter")
    
    # Initialize the adapter manager
    adapter_manager = AdapterManager()
    
    # Create a LoRA adapter for a small model (for demonstration purposes)
    base_model_name = "gpt2"  # Using a small model for quick demonstration
    adapter_name = "my-lora-adapter"
    
    try:
        # Create the adapter
        model, tokenizer = adapter_manager.create_lora_adapter(
            base_model_name=base_model_name,
            adapter_name=adapter_name,
            r=8,  # Rank of the update matrices
            lora_alpha=16,  # Alpha parameter for LoRA scaling
            lora_dropout=0.05,  # Dropout probability for LoRA layers
            # Target modules will be automatically inferred
        )
        
        logger.info(f"Successfully created LoRA adapter '{adapter_name}' for model '{base_model_name}'")
        
        # Example of generating text with the adapted model
        input_text = "Once upon a time"
        inputs = tokenizer(input_text, return_tensors="pt")
        
        # Generate text
        outputs = model.generate(
            inputs.input_ids,
            max_length=50,
            num_return_sequences=1,
            temperature=0.7,
        )
        
        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Generated text: {generated_text}")
        
        return model, tokenizer, adapter_name
    
    except Exception as e:
        logger.error(f"Error creating LoRA adapter: {e}")
        return None, None, None

def example_save_and_load_adapter(model, adapter_name):
    """Example of saving and loading a LoRA adapter."""
    logger.info("Example: Saving and loading a LoRA adapter")
    
    # Initialize the adapter manager
    adapter_manager = AdapterManager()
    
    # Create a temporary directory for the adapter
    output_dir = os.path.join("temp", "adapters", adapter_name)
    
    try:
        # Save the adapter
        saved_path = adapter_manager.save_adapter(
            model=model,
            adapter_name=adapter_name,
            output_dir=output_dir,
        )
        
        logger.info(f"Saved adapter to {saved_path}")
        
        # Load the adapter
        base_model_name = "gpt2"  # Same base model
        loaded_model, loaded_tokenizer = adapter_manager.load_adapter(
            base_model_name=base_model_name,
            adapter_path=saved_path,
            adapter_name=adapter_name,
        )
        
        logger.info(f"Successfully loaded adapter from {saved_path}")
        
        return loaded_model, loaded_tokenizer
    
    except Exception as e:
        logger.error(f"Error saving/loading adapter: {e}")
        return None, None

def example_create_qlora_adapter():
    """Example of creating a QLoRA (Quantized LoRA) adapter."""
    logger.info("Example: Creating a QLoRA adapter")
    
    # Initialize the adapter manager
    adapter_manager = AdapterManager()
    
    # Create a QLoRA adapter for a small model (for demonstration purposes)
    base_model_name = "gpt2"  # Using a small model for quick demonstration
    adapter_name = "my-qlora-adapter"
    
    try:
        # Create the QLoRA adapter with 4-bit quantization
        model, tokenizer = adapter_manager.create_qlora_adapter(
            base_model_name=base_model_name,
            adapter_name=adapter_name,
            quantization_bits=4,  # 4-bit quantization
            r=8,  # Rank of the update matrices
            lora_alpha=16,  # Alpha parameter for LoRA scaling
            lora_dropout=0.05,  # Dropout probability for LoRA layers
        )
        
        logger.info(f"Successfully created QLoRA adapter '{adapter_name}' for model '{base_model_name}'")
        
        return model, tokenizer, adapter_name
    
    except Exception as e:
        logger.error(f"Error creating QLoRA adapter: {e}")
        return None, None, None

def example_create_prefix_tuning_adapter():
    """Example of creating a Prefix Tuning adapter."""
    logger.info("Example: Creating a Prefix Tuning adapter")
    
    # Initialize the adapter manager
    adapter_manager = AdapterManager()
    
    # Create a Prefix Tuning adapter for a small model (for demonstration purposes)
    base_model_name = "gpt2"  # Using a small model for quick demonstration
    adapter_name = "my-prefix-tuning-adapter"
    
    try:
        # Create the Prefix Tuning adapter
        model, tokenizer = adapter_manager.create_prefix_tuning_adapter(
            base_model_name=base_model_name,
            adapter_name=adapter_name,
            num_virtual_tokens=20,  # Number of virtual tokens to add as prefix
            prefix_projection=False,  # Whether to use a projection matrix
        )
        
        logger.info(f"Successfully created Prefix Tuning adapter '{adapter_name}' for model '{base_model_name}'")
        
        # Example of generating text with the adapted model
        input_text = "Once upon a time"
        inputs = tokenizer(input_text, return_tensors="pt")
        
        # Generate text
        outputs = model.generate(
            inputs.input_ids,
            max_length=50,
            num_return_sequences=1,
            temperature=0.7,
        )
        
        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Generated text: {generated_text}")
        
        return model, tokenizer, adapter_name
    
    except Exception as e:
        logger.error(f"Error creating Prefix Tuning adapter: {e}")
        return None, None, None

def example_fine_tune_with_adapter(model, tokenizer):
    """Example of fine-tuning a model with an adapter."""
    logger.info("Example: Fine-tuning with an adapter")
    
    # Initialize the adapter manager
    adapter_manager = AdapterManager()
    
    # Create a simple dataset for demonstration
    texts = [
        "Once upon a time, there was a brave knight who lived in a castle.",
        "The knight went on a quest to slay a dragon and save the princess.",
        "After a long journey, the knight found the dragon's cave.",
        "The knight fought bravely and defeated the dragon.",
        "The princess was grateful and they lived happily ever after.",
    ]
    
    try:
        # Prepare the dataset
        dataset = adapter_manager.prepare_dataset(
            texts=texts,
            tokenizer=tokenizer,
            max_length=128,
        )
        
        logger.info(f"Prepared dataset with {len(texts)} samples")
        
        # Fine-tune the model
        output_dir = os.path.join("temp", "fine-tuned")
        fine_tuned_model = adapter_manager.fine_tune(
            model=model,
            tokenizer=tokenizer,
            dataset=dataset,
            output_dir=output_dir,
            # Using default training arguments
        )
        
        logger.info(f"Successfully fine-tuned model and saved to {output_dir}")
        
        return fine_tuned_model
    
    except Exception as e:
        logger.error(f"Error fine-tuning with adapter: {e}")
        return None

def example_merge_adapter(model, adapter_name):
    """Example of merging an adapter with its base model."""
    logger.info("Example: Merging adapter with base model")
    
    # Initialize the adapter manager
    adapter_manager = AdapterManager()
    
    try:
        # Merge the adapter with the base model
        merged_model = adapter_manager.merge_adapter(
            model=model,
            adapter_name=adapter_name,
        )
        
        logger.info("Successfully merged adapter with base model")
        
        return merged_model
    
    except Exception as e:
        logger.error(f"Error merging adapter: {e}")
        return None

def run_all_examples():
    """Run all examples."""
    logger.info("Running all adapter support examples")
    
    # Create directories if they don't exist
    os.makedirs(os.path.join("temp", "adapters"), exist_ok=True)
    os.makedirs(os.path.join("temp", "fine-tuned"), exist_ok=True)
    
    # Example 1: Create a LoRA adapter
    model, tokenizer, adapter_name = example_create_lora_adapter()
    if model is None:
        logger.warning("Skipping remaining examples due to error in creating LoRA adapter")
        return
    
    # Example 2: Save and load the adapter
    loaded_model, loaded_tokenizer = example_save_and_load_adapter(model, adapter_name)
    if loaded_model is None:
        logger.warning("Skipping remaining examples due to error in saving/loading adapter")
        return
    
    # Example 3: Create a QLoRA adapter
    qlora_model, qlora_tokenizer, qlora_adapter_name = example_create_qlora_adapter()
    
    # Example 4: Create a Prefix Tuning adapter
    prefix_model, prefix_tokenizer, prefix_adapter_name = example_create_prefix_tuning_adapter()
    
    # Example 5: Fine-tune with the adapter
    if loaded_model is not None:
        fine_tuned_model = example_fine_tune_with_adapter(loaded_model, loaded_tokenizer)
    
    # Example 6: Merge the adapter with the base model
    if fine_tuned_model is not None:
        merged_model = example_merge_adapter(fine_tuned_model, adapter_name)
    
    logger.info("Completed all adapter support examples")

if __name__ == "__main__":
    run_all_examples()
