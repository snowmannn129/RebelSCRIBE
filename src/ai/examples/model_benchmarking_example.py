#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the model_benchmarking module.

This script demonstrates how to use the model_benchmarking module to benchmark
AI models, compare their performance, and generate benchmark reports.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.ai.model_benchmarking import (
    ModelBenchmark, BenchmarkMetric, BenchmarkResult,
    run_benchmark, compare_models, get_benchmark_results,
    create_standard_benchmarks, evaluate_model_quality,
    generate_benchmark_report
)
from src.ai.model_registry import (
    ModelRegistry, ModelInfo, ModelType, ModelSource,
    discover_models, get_model_info
)
from src.utils.logging_utils import get_logger

# Set up logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)


def example_discover_models():
    """Example of discovering models before benchmarking."""
    print("\n=== Discovering Models ===")
    
    # Get the model registry
    registry = ModelRegistry.get_instance()
    
    # Discover models from all sources
    models = registry.discover_models(force_refresh=True)
    
    print(f"Discovered {len(models)} models:")
    for i, model in enumerate(models[:5], 1):  # Show first 5 models
        print(f"{i}. {model.name} ({model.id})")
    
    if len(models) > 5:
        print(f"... and {len(models) - 5} more")
    
    return models


def example_run_benchmark(model_id: str):
    """
    Example of running a benchmark for a single model.
    
    Args:
        model_id: The ID of the model to benchmark.
    """
    print(f"\n=== Benchmarking Model: {model_id} ===")
    
    # Create a benchmark
    benchmark = ModelBenchmark(
        model_id=model_id,
        prompt="Write a short story about a robot learning to paint.",
        max_tokens=100,
        num_runs=2,  # Use a small number for the example
        tags=["example", "creative-writing"],
        description="Example benchmark for creative writing"
    )
    
    # Run the benchmark
    try:
        result = run_benchmark(benchmark)
        
        # Print the results
        print(f"Model: {result.model_name}")
        print(f"Load time: {result.load_time_seconds:.2f} seconds")
        print(f"Average generation time: {result.avg_generation_time:.2f} seconds")
        print(f"Average tokens per second: {result.avg_tokens_per_second:.2f}")
        print(f"Peak memory usage: {result.peak_memory_mb:.2f} MB")
        print("\nGenerated text sample:")
        print(f"{result.generated_texts[0][:200]}...")  # Show first 200 chars
    
    except Exception as e:
        print(f"Error benchmarking model: {e}")


def example_compare_models(model_ids: List[str]):
    """
    Example of comparing multiple models.
    
    Args:
        model_ids: The IDs of the models to compare.
    """
    print(f"\n=== Comparing Models: {', '.join(model_ids)} ===")
    
    # Compare models
    try:
        results = compare_models(
            model_ids=model_ids,
            prompt="Explain the concept of artificial intelligence to a high school student.",
            max_tokens=150,
            num_runs=2  # Use a small number for the example
        )
        
        # Print the results
        print("Comparison Results:")
        for model_id, result in results.items():
            print(f"\nModel: {result.model_name} ({model_id})")
            print(f"Load time: {result.load_time_seconds:.2f} seconds")
            print(f"Average generation time: {result.avg_generation_time:.2f} seconds")
            print(f"Average tokens per second: {result.avg_tokens_per_second:.2f}")
            print(f"Peak memory usage: {result.peak_memory_mb:.2f} MB")
    
    except Exception as e:
        print(f"Error comparing models: {e}")


def example_create_standard_benchmarks():
    """Example of creating standard benchmarks for all models."""
    print("\n=== Creating Standard Benchmarks ===")
    
    try:
        # Create standard benchmarks
        benchmark_ids = create_standard_benchmarks()
        
        print(f"Created {len(benchmark_ids)} standard benchmarks")
        print("Benchmark IDs:")
        for i, benchmark_id in enumerate(benchmark_ids[:5], 1):  # Show first 5
            print(f"{i}. {benchmark_id}")
        
        if len(benchmark_ids) > 5:
            print(f"... and {len(benchmark_ids) - 5} more")
    
    except Exception as e:
        print(f"Error creating standard benchmarks: {e}")


def example_evaluate_model_quality(model_id: str, reference_model_id: Optional[str] = None):
    """
    Example of evaluating model quality.
    
    Args:
        model_id: The ID of the model to evaluate.
        reference_model_id: Optional ID of a reference model to compare against.
    """
    print(f"\n=== Evaluating Model Quality: {model_id} ===")
    
    try:
        # Define prompts for evaluation
        prompts = [
            "Write a short story about a robot learning to paint.",
            "Explain the concept of quantum computing to a high school student.",
            "Summarize the key events of World War II in a few paragraphs."
        ]
        
        # Evaluate model quality
        metrics = evaluate_model_quality(
            model_id=model_id,
            reference_model_id=reference_model_id,
            prompts=prompts,
            max_tokens=100
        )
        
        # Print the metrics
        print("Quality Metrics:")
        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")
    
    except Exception as e:
        print(f"Error evaluating model quality: {e}")


def example_generate_benchmark_report():
    """Example of generating a benchmark report."""
    print("\n=== Generating Benchmark Report ===")
    
    try:
        # Generate benchmark report
        report = generate_benchmark_report()
        
        # Print report summary
        print(f"Report generated at: {report['timestamp']}")
        print(f"Number of models: {report['num_models']}")
        print(f"Number of results: {report['num_results']}")
        
        # Print model summaries
        for model_id, model_data in report["models"].items():
            print(f"\nModel: {model_data['name']} ({model_id})")
            print(f"Type: {model_data['type']}")
            print(f"Number of results: {model_data['num_results']}")
            print(f"Average load time: {model_data['avg_load_time_seconds']:.2f} seconds")
            print(f"Average generation time: {model_data['avg_generation_time_seconds']:.2f} seconds")
            print(f"Average tokens per second: {model_data['avg_tokens_per_second']:.2f}")
            print(f"Average peak memory usage: {model_data['avg_peak_memory_mb']:.2f} MB")
    
    except Exception as e:
        print(f"Error generating benchmark report: {e}")


def main():
    """Main function to run the examples."""
    print("Model Benchmarking Examples")
    print("==========================")
    
    # Discover models
    models = example_discover_models()
    
    # If no models were discovered, create a mock model for demonstration
    if not models:
        print("\nNo models discovered. Creating a mock model for demonstration purposes.")
        registry = ModelRegistry.get_instance()
        mock_model = ModelInfo(
            id="mock-model",
            name="Mock Model",
            version="1.0",
            source=ModelSource.LOCAL,
            model_type=ModelType.LLAMA,
            path="/path/to/mock/model",
            description="A mock model for demonstration purposes"
        )
        registry.register_model(mock_model)
        models = [mock_model]
    
    # Run benchmark for the first model
    example_run_benchmark(models[0].id)
    
    # Compare models if there are at least 2
    if len(models) >= 2:
        example_compare_models([models[0].id, models[1].id])
    
    # Create standard benchmarks
    example_create_standard_benchmarks()
    
    # Evaluate model quality
    example_evaluate_model_quality(models[0].id)
    
    # Generate benchmark report
    example_generate_benchmark_report()


if __name__ == "__main__":
    main()
