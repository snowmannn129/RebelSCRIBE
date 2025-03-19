#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the model registry module.

This example demonstrates how to use the model registry module to discover, track,
and manage AI models from multiple sources.

Note: This example requires the huggingface_hub and requests packages to be installed.
You can install them with: pip install huggingface_hub requests
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.ai.model_registry import (
    ModelRegistry, ModelSource, ModelInfo, ModelType, ModelFormat,
    get_model_registry, discover_models, get_model_info, register_model,
    unregister_model, search_models, check_for_updates, track_model_usage,
    get_model_usage_stats
)
from src.utils.logging_utils import get_logger, configure_logging

# Configure logging
configure_logging()
logger = get_logger(__name__)


def check_dependencies():
    """Check if required dependencies are available."""
    print("\n=== Checking Dependencies ===")
    
    try:
        import huggingface_hub
        print("huggingface_hub is available")
    except ImportError:
        print("huggingface_hub is not available. Install with: pip install huggingface_hub")
    
    try:
        import requests
        print("requests is available")
    except ImportError:
        print("requests is not available. Install with: pip install requests")


def register_custom_model_example():
    """Example of registering a custom model."""
    print("\n=== Registering a Custom Model ===")
    
    # Get the model registry
    registry = get_model_registry()
    
    # Create a custom model
    custom_model = ModelInfo(
        id="custom-llama-7b",
        name="Custom Llama 7B",
        version="1.0",
        source=ModelSource.CUSTOM,
        model_type=ModelType.LLAMA,
        path="/path/to/custom/model.gguf",
        description="A custom fine-tuned Llama model",
        format=ModelFormat.GGUF,
        size_bytes=4_000_000_000,
        parameters=7_000_000_000,
        quantization="Q4_K_M",
        tags=["llama", "7b", "custom", "fine-tuned"],
        metadata={
            "fine_tuned_on": "custom dataset",
            "base_model": "llama-2-7b"
        }
    )
    
    # Register the model
    registry.register_model(custom_model)
    print(f"Registered custom model: {custom_model.name}")
    
    # Get the model information
    model_info = registry.get_model_info("custom-llama-7b")
    print(f"Model ID: {model_info.id}")
    print(f"Model Name: {model_info.name}")
    print(f"Model Version: {model_info.version}")
    print(f"Model Type: {model_info.model_type.name}")
    print(f"Model Format: {model_info.format.name}")
    print(f"Model Size: {model_info.size_bytes / (1024 * 1024 * 1024):.2f} GB")
    print(f"Model Parameters: {model_info.parameters / 1_000_000_000:.1f} billion")
    print(f"Model Tags: {', '.join(model_info.tags)}")


def discover_models_example():
    """Example of discovering models from different sources."""
    print("\n=== Discovering Models ===")
    
    # Get the model registry
    registry = get_model_registry()
    
    # Define a progress callback
    def progress_callback(progress_info):
        print(f"Discovery progress: {progress_info.progress:.1%} - {progress_info.message}")
    
    # Discover models from local storage only
    print("\nDiscovering models from local storage...")
    local_models = registry.discover_models(
        sources=[ModelSource.LOCAL],
        force_refresh=True,
        progress_callback=progress_callback
    )
    
    print(f"Discovered {len(local_models)} models from local storage")
    
    # Try to discover models from HuggingFace
    try:
        print("\nDiscovering models from HuggingFace...")
        hf_models = registry.discover_models(
            sources=[ModelSource.HUGGINGFACE],
            force_refresh=True,
            progress_callback=progress_callback
        )
        
        print(f"Discovered {len(hf_models)} models from HuggingFace")
    except Exception as e:
        print(f"Error discovering models from HuggingFace: {e}")
    
    # Get all registered models
    all_models = registry.get_all_models()
    print(f"\nTotal registered models: {len(all_models)}")
    
    # Print model counts by type
    model_types = {}
    for model in all_models:
        type_name = model.model_type.name
        if type_name not in model_types:
            model_types[type_name] = 0
        model_types[type_name] += 1
    
    print("\nModels by type:")
    for type_name, count in model_types.items():
        print(f"  {type_name}: {count}")
    
    # Print model counts by source
    model_sources = {}
    for model in all_models:
        source_name = model.source.name
        if source_name not in model_sources:
            model_sources[source_name] = 0
        model_sources[source_name] += 1
    
    print("\nModels by source:")
    for source_name, count in model_sources.items():
        print(f"  {source_name}: {count}")


def search_models_example():
    """Example of searching for models."""
    print("\n=== Searching for Models ===")
    
    # Get the model registry
    registry = get_model_registry()
    
    # Search for Llama models
    print("\nSearching for Llama models...")
    llama_models = registry.search_models("llama")
    print(f"Found {len(llama_models)} Llama models")
    
    # Print the first 5 models
    for i, model in enumerate(llama_models[:5]):
        print(f"{i+1}. {model.name} ({model.id})")
        print(f"   Source: {model.source.name}")
        print(f"   Type: {model.model_type.name}")
        print(f"   Format: {model.format.name}")
        if model.parameters:
            print(f"   Parameters: {model.parameters / 1_000_000_000:.1f} billion")
        if model.quantization:
            print(f"   Quantization: {model.quantization}")
        print()
    
    # Search for 7B models
    print("\nSearching for 7B models...")
    models_7b = registry.search_models("7b")
    print(f"Found {len(models_7b)} 7B models")
    
    # Search for GGUF format models
    print("\nSearching for GGUF format models...")
    gguf_models = [m for m in registry.get_all_models() if m.format == ModelFormat.GGUF]
    print(f"Found {len(gguf_models)} GGUF models")
    
    # Search for local Llama models
    print("\nSearching for local Llama models...")
    local_llama_models = registry.search_models(
        "llama",
        model_type=ModelType.LLAMA,
        source=ModelSource.LOCAL
    )
    print(f"Found {len(local_llama_models)} local Llama models")


def track_model_usage_example():
    """Example of tracking model usage."""
    print("\n=== Tracking Model Usage ===")
    
    # Get the model registry
    registry = get_model_registry()
    
    # Get a model to track
    all_models = registry.get_all_models()
    if not all_models:
        print("No models available for tracking")
        return
    
    model = all_models[0]
    print(f"Tracking usage for model: {model.name} ({model.id})")
    
    # Track inference usage
    registry.track_model_usage(
        model.id,
        "inference",
        {
            "tokens": 1000,
            "prompt_tokens": 200,
            "completion_tokens": 800,
            "duration_ms": 1500
        }
    )
    print("Tracked inference usage")
    
    # Track fine-tuning usage
    registry.track_model_usage(
        model.id,
        "fine-tuning",
        {
            "epochs": 3,
            "batch_size": 8,
            "learning_rate": 2e-5,
            "duration_ms": 60000
        }
    )
    print("Tracked fine-tuning usage")
    
    # Get usage statistics
    stats = registry.get_model_usage_stats(model.id)
    print(f"\nUsage statistics for {model.name}:")
    print(f"Total usage: {stats['total_usage']}")
    print("Usage types:")
    for usage_type, count in stats["models"][model.id]["usage_types"].items():
        print(f"  {usage_type}: {count}")


def check_for_updates_example():
    """Example of checking for model updates."""
    print("\n=== Checking for Model Updates ===")
    
    # Get the model registry
    registry = get_model_registry()
    
    # Define a progress callback
    def progress_callback(progress_info):
        print(f"Update check progress: {progress_info.progress:.1%} - {progress_info.message}")
    
    # Check for updates
    updates = registry.check_for_updates(progress_callback)
    
    if updates:
        print(f"Found {len(updates)} model updates:")
        for model_id, model in updates.items():
            print(f"  {model.name} ({model_id}): {model.version}")
    else:
        print("No model updates found")


def share_model_example():
    """Example of sharing a model."""
    print("\n=== Sharing a Model ===")
    
    # Get the model registry
    registry = get_model_registry()
    
    # Get a local model to share
    local_models = registry.get_models_by_source(ModelSource.LOCAL)
    if not local_models:
        print("No local models available for sharing")
        return
    
    model = local_models[0]
    print(f"Sharing model: {model.name} ({model.id})")
    
    # Create a temporary destination path
    import tempfile
    dest_dir = tempfile.mkdtemp()
    dest_path = os.path.join(dest_dir, os.path.basename(model.path or "model.bin"))
    
    # Share the model
    if model.path:
        print(f"Model path: {model.path}")
        print(f"Destination path: {dest_path}")
        
        # This would actually copy the file, but we'll just simulate it
        print("Simulating model sharing (not actually copying the file)")
        # result = registry.share_model(model.id, dest_path)
        result = True
        
        if result:
            print(f"Model shared successfully to {dest_path}")
        else:
            print("Failed to share model")
    else:
        print("Model does not have a local path")


def main():
    """Run the model registry examples."""
    print("=== Model Registry Examples ===")
    
    # Check dependencies
    check_dependencies()
    
    # Register a custom model
    register_custom_model_example()
    
    # Discover models
    discover_models_example()
    
    # Search for models
    search_models_example()
    
    # Track model usage
    track_model_usage_example()
    
    # Check for updates
    check_for_updates_example()
    
    # Share a model
    share_model_example()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
