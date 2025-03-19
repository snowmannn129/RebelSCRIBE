#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Benchmarking for RebelSCRIBE.

This module provides functionality for benchmarking AI models to compare their
performance in terms of speed, memory usage, and quality of generated text.
It supports benchmarking models from different sources and with different configurations.

Example usage:
    ```python
    from src.ai.model_benchmarking import (
        ModelBenchmark, BenchmarkMetric, BenchmarkResult,
        run_benchmark, compare_models, get_benchmark_results
    )
    
    # Create a benchmark for a specific model
    benchmark = ModelBenchmark(
        model_id="llama-2-7b",
        prompt="Write a short story about a robot learning to paint.",
        max_tokens=100,
        num_runs=3
    )
    
    # Run the benchmark
    result = run_benchmark(benchmark)
    print(f"Average generation time: {result.avg_generation_time:.2f} seconds")
    print(f"Average tokens per second: {result.avg_tokens_per_second:.2f}")
    print(f"Peak memory usage: {result.peak_memory_mb:.2f} MB")
    
    # Compare multiple models
    models_to_compare = ["llama-2-7b", "mistral-7b", "phi-2"]
    comparison = compare_models(
        model_ids=models_to_compare,
        prompt="Write a short story about a robot learning to paint.",
        max_tokens=100,
        num_runs=3
    )
    
    # Get all benchmark results
    all_results = get_benchmark_results()
    ```
"""

import os
import json
import time
import logging
import threading
import psutil
import gc
import statistics
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
import datetime
import tracemalloc

from src.utils.logging_utils import get_logger
from src.utils.file_utils import ensure_directory
from src.ai.progress_callbacks import (
    OperationType, ProgressStatus, ProgressInfo, ProgressCallback,
    create_operation, start_operation, update_progress,
    complete_operation, fail_operation
)
from src.ai.model_registry import (
    ModelRegistry, ModelInfo, ModelType, ModelSource,
    get_model_info, track_model_usage
)

# Import model support modules
try:
    from src.ai.llama_support import load_llama_model, generate_text as generate_llama_text
    LLAMA_SUPPORT_AVAILABLE = True
except ImportError:
    LLAMA_SUPPORT_AVAILABLE = False

try:
    from src.ai.mistral_support import load_mistral_model, generate_text as generate_mistral_text
    MISTRAL_SUPPORT_AVAILABLE = True
except ImportError:
    MISTRAL_SUPPORT_AVAILABLE = False

try:
    from src.ai.phi_support import load_phi_model, generate_text as generate_phi_text
    PHI_SUPPORT_AVAILABLE = True
except ImportError:
    PHI_SUPPORT_AVAILABLE = False

try:
    from src.ai.falcon_support import load_falcon_model, generate_text as generate_falcon_text
    FALCON_SUPPORT_AVAILABLE = True
except ImportError:
    FALCON_SUPPORT_AVAILABLE = False

try:
    from src.ai.mpt_support import load_mpt_model, generate_text as generate_mpt_text
    MPT_SUPPORT_AVAILABLE = True
except ImportError:
    MPT_SUPPORT_AVAILABLE = False

try:
    from src.ai.gguf_support import load_gguf_model, generate_text as generate_gguf_text
    GGUF_SUPPORT_AVAILABLE = True
except ImportError:
    GGUF_SUPPORT_AVAILABLE = False

try:
    from src.ai.awq_support import load_awq_model, generate_text as generate_awq_text
    AWQ_SUPPORT_AVAILABLE = True
except ImportError:
    AWQ_SUPPORT_AVAILABLE = False

logger = get_logger(__name__)


class BenchmarkMetric(Enum):
    """Enum representing the metrics to benchmark."""
    LOAD_TIME = auto()
    GENERATION_TIME = auto()
    TOKENS_PER_SECOND = auto()
    MEMORY_USAGE = auto()
    QUALITY = auto()


@dataclass
class ModelBenchmark:
    """Class for defining a model benchmark."""
    model_id: str
    prompt: str
    max_tokens: int = 100
    num_runs: int = 3
    temperature: float = 0.7
    top_p: float = 0.9
    metrics: List[BenchmarkMetric] = field(default_factory=lambda: list(BenchmarkMetric))
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the benchmark to a dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["metrics"] = [metric.name for metric in self.metrics]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelBenchmark':
        """Create a ModelBenchmark instance from a dictionary."""
        # Convert string metrics back to enum values
        metrics_str = data.pop("metrics", [])
        metrics = [BenchmarkMetric[metric_str] for metric_str in metrics_str]
        
        return cls(
            metrics=metrics,
            **data
        )


@dataclass
class BenchmarkResult:
    """Class for storing benchmark results."""
    benchmark_id: str
    model_id: str
    model_name: str
    model_type: str
    timestamp: str
    prompt: str
    max_tokens: int
    temperature: float
    top_p: float
    num_runs: int
    
    # Performance metrics
    load_time_seconds: Optional[float] = None
    generation_times_seconds: List[float] = field(default_factory=list)
    avg_generation_time: Optional[float] = None
    tokens_generated: List[int] = field(default_factory=list)
    avg_tokens_per_second: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    
    # Quality metrics
    generated_texts: List[str] = field(default_factory=list)
    quality_scores: Optional[Dict[str, float]] = None
    
    # Additional information
    error: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """Create a BenchmarkResult instance from a dictionary."""
        return cls(**data)


class ModelBenchmarkError(Exception):
    """Base exception for model benchmark errors."""
    pass


class ModelNotSupportedError(ModelBenchmarkError):
    """Exception raised when a model is not supported for benchmarking."""
    pass


class BenchmarkRegistry:
    """
    Singleton class for managing model benchmarks and results.
    
    This class provides functionality for storing, retrieving, and managing
    benchmark definitions and results.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'BenchmarkRegistry':
        """Get the singleton instance of the BenchmarkRegistry."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        """Initialize the benchmark registry."""
        # Ensure this is only called once
        if BenchmarkRegistry._instance is not None:
            raise RuntimeError("Use BenchmarkRegistry.get_instance() to get the singleton instance")
        
        # Initialize registry data
        self._benchmarks: Dict[str, ModelBenchmark] = {}
        self._results: Dict[str, BenchmarkResult] = {}
        self._registry_file = self._get_registry_file_path()
        
        # Load existing registry data
        self._load_registry()
    
    def _get_registry_file_path(self) -> str:
        """Get the path to the registry file."""
        # Get the registry directory
        registry_dir = os.environ.get(
            "REBELSCRIBE_BENCHMARK_DIR", 
            os.path.join(os.path.expanduser("~"), ".rebelscribe", "benchmarks")
        )
        
        # Ensure the directory exists
        ensure_directory(registry_dir)
        
        # Return the path to the registry file
        return os.path.join(registry_dir, "benchmark_registry.json")
    
    def _load_registry(self) -> None:
        """Load the registry data from the registry file."""
        if not os.path.exists(self._registry_file):
            logger.info(f"Registry file not found at {self._registry_file}, creating new registry")
            return
        
        try:
            with open(self._registry_file, "r") as f:
                data = json.load(f)
            
            # Convert dictionaries to ModelBenchmark objects
            for benchmark_id, benchmark_data in data.get("benchmarks", {}).items():
                self._benchmarks[benchmark_id] = ModelBenchmark.from_dict(benchmark_data)
            
            # Convert dictionaries to BenchmarkResult objects
            for result_id, result_data in data.get("results", {}).items():
                self._results[result_id] = BenchmarkResult.from_dict(result_data)
            
            logger.info(f"Loaded {len(self._benchmarks)} benchmarks and {len(self._results)} results from registry")
        
        except Exception as e:
            logger.error(f"Error loading registry: {e}", exc_info=True)
            # Create a backup of the corrupted file
            if os.path.exists(self._registry_file):
                backup_path = f"{self._registry_file}.bak.{int(time.time())}"
                try:
                    import shutil
                    shutil.copy2(self._registry_file, backup_path)
                    logger.info(f"Created backup of corrupted registry at {backup_path}")
                except Exception as backup_error:
                    logger.error(f"Error creating backup: {backup_error}")
    
    def _save_registry(self) -> None:
        """Save the registry data to the registry file."""
        try:
            # Convert ModelBenchmark objects to dictionaries
            benchmarks_dict = {benchmark_id: benchmark.to_dict() for benchmark_id, benchmark in self._benchmarks.items()}
            
            # Convert BenchmarkResult objects to dictionaries
            results_dict = {result_id: result.to_dict() for result_id, result in self._results.items()}
            
            # Create the data to save
            data = {
                "benchmarks": benchmarks_dict,
                "results": results_dict,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Save to file
            with open(self._registry_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self._benchmarks)} benchmarks and {len(self._results)} results to registry")
        
        except Exception as e:
            logger.error(f"Error saving registry: {e}", exc_info=True)
    
    def register_benchmark(self, benchmark: ModelBenchmark) -> str:
        """
        Register a benchmark in the registry.
        
        Args:
            benchmark: The benchmark to register.
            
        Returns:
            str: The ID of the registered benchmark.
        """
        with self._lock:
            # Generate a unique ID for the benchmark
            benchmark_id = f"benchmark_{int(time.time())}_{hash(benchmark.model_id + benchmark.prompt) % 10000:04d}"
            
            # Register the benchmark
            self._benchmarks[benchmark_id] = benchmark
            self._save_registry()
            
            logger.info(f"Registered benchmark: {benchmark_id}")
            return benchmark_id
    
    def get_benchmark(self, benchmark_id: str) -> Optional[ModelBenchmark]:
        """
        Get a benchmark by ID.
        
        Args:
            benchmark_id: The ID of the benchmark to get.
            
        Returns:
            Optional[ModelBenchmark]: The benchmark, or None if not found.
        """
        return self._benchmarks.get(benchmark_id)
    
    def get_all_benchmarks(self) -> List[Tuple[str, ModelBenchmark]]:
        """
        Get all registered benchmarks.
        
        Returns:
            List[Tuple[str, ModelBenchmark]]: A list of (benchmark_id, benchmark) tuples.
        """
        return list(self._benchmarks.items())
    
    def register_result(self, result: BenchmarkResult) -> str:
        """
        Register a benchmark result in the registry.
        
        Args:
            result: The benchmark result to register.
            
        Returns:
            str: The ID of the registered result.
        """
        with self._lock:
            # Generate a unique ID for the result
            result_id = f"result_{int(time.time())}_{hash(result.model_id + result.prompt) % 10000:04d}"
            
            # Register the result
            self._results[result_id] = result
            self._save_registry()
            
            logger.info(f"Registered benchmark result: {result_id}")
            return result_id
    
    def get_result(self, result_id: str) -> Optional[BenchmarkResult]:
        """
        Get a benchmark result by ID.
        
        Args:
            result_id: The ID of the result to get.
            
        Returns:
            Optional[BenchmarkResult]: The result, or None if not found.
        """
        return self._results.get(result_id)
    
    def get_all_results(self) -> List[Tuple[str, BenchmarkResult]]:
        """
        Get all registered benchmark results.
        
        Returns:
            List[Tuple[str, BenchmarkResult]]: A list of (result_id, result) tuples.
        """
        return list(self._results.items())
    
    def get_results_for_model(self, model_id: str) -> List[Tuple[str, BenchmarkResult]]:
        """
        Get all benchmark results for a specific model.
        
        Args:
            model_id: The ID of the model to get results for.
            
        Returns:
            List[Tuple[str, BenchmarkResult]]: A list of (result_id, result) tuples.
        """
        return [(result_id, result) for result_id, result in self._results.items() if result.model_id == model_id]
    
    def get_latest_result_for_model(self, model_id: str) -> Optional[Tuple[str, BenchmarkResult]]:
        """
        Get the latest benchmark result for a specific model.
        
        Args:
            model_id: The ID of the model to get the latest result for.
            
        Returns:
            Optional[Tuple[str, BenchmarkResult]]: The (result_id, result) tuple, or None if not found.
        """
        results = self.get_results_for_model(model_id)
        if not results:
            return None
        
        # Sort by timestamp (newest first)
        sorted_results = sorted(results, key=lambda x: x[1].timestamp, reverse=True)
        return sorted_results[0]


def _get_model_loader_and_generator(model_type: ModelType) -> Tuple[Callable, Callable]:
    """
    Get the appropriate model loader and text generator functions for a model type.
    
    Args:
        model_type: The type of model.
        
    Returns:
        Tuple[Callable, Callable]: A tuple of (loader_function, generator_function).
        
    Raises:
        ModelNotSupportedError: If the model type is not supported.
    """
    if model_type == ModelType.LLAMA:
        if not LLAMA_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("Llama support is not available")
        return load_llama_model, generate_llama_text
    
    elif model_type == ModelType.MISTRAL:
        if not MISTRAL_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("Mistral support is not available")
        return load_mistral_model, generate_mistral_text
    
    elif model_type == ModelType.PHI:
        if not PHI_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("Phi support is not available")
        return load_phi_model, generate_phi_text
    
    elif model_type == ModelType.FALCON:
        if not FALCON_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("Falcon support is not available")
        return load_falcon_model, generate_falcon_text
    
    elif model_type == ModelType.MPT:
        if not MPT_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("MPT support is not available")
        return load_mpt_model, generate_mpt_text
    
    elif model_type == ModelType.GGUF:
        if not GGUF_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("GGUF support is not available")
        return load_gguf_model, generate_gguf_text
    
    elif model_type == ModelType.AWQ:
        if not AWQ_SUPPORT_AVAILABLE:
            raise ModelNotSupportedError("AWQ support is not available")
        return load_awq_model, generate_awq_text
    
    else:
        raise ModelNotSupportedError(f"Model type {model_type} is not supported for benchmarking")


def _measure_memory_usage() -> float:
    """
    Measure the current memory usage of the process.
    
    Returns:
        float: The memory usage in megabytes.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 * 1024)  # Convert to MB


def run_benchmark(benchmark: ModelBenchmark,
                 progress_callback: Optional[ProgressCallback] = None) -> BenchmarkResult:
    """
    Run a benchmark for a model.
    
    Args:
        benchmark: The benchmark to run.
        progress_callback: Optional callback for tracking progress.
        
    Returns:
        BenchmarkResult: The benchmark result.
        
    Raises:
        ModelNotSupportedError: If the model is not supported for benchmarking.
    """
    # Create operation for tracking progress
    operation_id, progress_info = create_operation(
        OperationType.BENCHMARK, 
        operation_id=f"benchmark_{benchmark.model_id}",
        callback=progress_callback
    )
    
    try:
        # Start the operation
        start_operation(operation_id, f"Benchmarking model {benchmark.model_id}")
        
        # Get model information
        model_registry = ModelRegistry.get_instance()
        model_info = model_registry.get_model_info(benchmark.model_id)
        
        if not model_info:
            raise ModelNotSupportedError(f"Model {benchmark.model_id} not found in registry")
        
        # Get the appropriate model loader and generator
        model_loader, text_generator = _get_model_loader_and_generator(model_info.model_type)
        
        # Create benchmark result
        result = BenchmarkResult(
            benchmark_id=f"benchmark_{int(time.time())}_{hash(benchmark.model_id + benchmark.prompt) % 10000:04d}",
            model_id=benchmark.model_id,
            model_name=model_info.name,
            model_type=model_info.model_type.name,
            timestamp=datetime.datetime.now().isoformat(),
            prompt=benchmark.prompt,
            max_tokens=benchmark.max_tokens,
            temperature=benchmark.temperature,
            top_p=benchmark.top_p,
            num_runs=benchmark.num_runs,
            tags=benchmark.tags.copy(),
            metadata={
                "model_source": model_info.source.name,
                "model_format": model_info.format.name if hasattr(model_info, "format") else "UNKNOWN",
                "model_quantization": model_info.quantization,
                "model_parameters": model_info.parameters,
                "benchmark_description": benchmark.description,
            }
        )
        
        # Measure load time
        update_progress(operation_id, 0.1, "Loading model")
        
        # Start memory tracking
        tracemalloc.start()
        initial_memory = _measure_memory_usage()
        
        # Load the model
        load_start_time = time.time()
        model = model_loader(benchmark.model_id)
        load_end_time = time.time()
        
        # Record load time
        result.load_time_seconds = load_end_time - load_start_time
        
        # Run the benchmark multiple times
        for run in range(benchmark.num_runs):
            update_progress(
                operation_id,
                0.2 + (0.7 * run / benchmark.num_runs),
                f"Running benchmark {run + 1}/{benchmark.num_runs}"
            )
            
            # Clear GPU cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            # Force garbage collection
            gc.collect()
            
            # Generate text
            generation_start_time = time.time()
            generated_text = text_generator(
                model=model,
                prompt=benchmark.prompt,
                max_tokens=benchmark.max_tokens,
                temperature=benchmark.temperature,
                top_p=benchmark.top_p
            )
            generation_end_time = time.time()
            
            # Record generation time
            generation_time = generation_end_time - generation_start_time
            result.generation_times_seconds.append(generation_time)
            
            # Record generated text
            result.generated_texts.append(generated_text)
            
            # Estimate tokens generated (approximate)
            tokens_generated = len(generated_text.split())
            result.tokens_generated.append(tokens_generated)
        
        # Calculate average generation time
        result.avg_generation_time = statistics.mean(result.generation_times_seconds)
        
        # Calculate average tokens per second
        tokens_per_second = [
            tokens / time for tokens, time in zip(result.tokens_generated, result.generation_times_seconds)
        ]
        result.avg_tokens_per_second = statistics.mean(tokens_per_second)
        
        # Measure peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        final_memory = _measure_memory_usage()
        result.peak_memory_mb = max(final_memory - initial_memory, peak / (1024 * 1024))
        
        # Track model usage
        track_model_usage(
            model_id=benchmark.model_id,
            usage_type="benchmark",
            metadata={
                "prompt_length": len(benchmark.prompt.split()),
                "max_tokens": benchmark.max_tokens,
                "avg_generation_time": result.avg_generation_time,
                "avg_tokens_per_second": result.avg_tokens_per_second,
                "peak_memory_mb": result.peak_memory_mb,
            }
        )
        
        # Register the result
        registry = BenchmarkRegistry.get_instance()
        registry.register_benchmark(benchmark)
        registry.register_result(result)
        
        # Complete the operation
        complete_operation(
            operation_id,
            result,
            f"Benchmark completed for {benchmark.model_id}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error benchmarking model {benchmark.model_id}: {e}", exc_info=True)
        
        # Create error result
        error_result = BenchmarkResult(
            benchmark_id=f"benchmark_{int(time.time())}_{hash(benchmark.model_id + benchmark.prompt) % 10000:04d}",
            model_id=benchmark.model_id,
            model_name=get_model_info(benchmark.model_id).name if get_model_info(benchmark.model_id) else "Unknown",
            model_type=get_model_info(benchmark.model_id).model_type.name if get_model_info(benchmark.model_id) else "UNKNOWN",
            timestamp=datetime.datetime.now().isoformat(),
            prompt=benchmark.prompt,
            max_tokens=benchmark.max_tokens,
            temperature=benchmark.temperature,
            top_p=benchmark.top_p,
            num_runs=benchmark.num_runs,
            error=str(e),
            tags=benchmark.tags.copy(),
        )
        
        # Register the error result
        registry = BenchmarkRegistry.get_instance()
        registry.register_benchmark(benchmark)
        registry.register_result(error_result)
        
        # Fail the operation
        fail_operation(operation_id, str(e), f"Failed to benchmark model {benchmark.model_id}")
        
        return error_result


def compare_models(model_ids: List[str],
                  prompt: str,
                  max_tokens: int = 100,
                  num_runs: int = 3,
                  temperature: float = 0.7,
                  top_p: float = 0.9,
                  progress_callback: Optional[ProgressCallback] = None) -> Dict[str, BenchmarkResult]:
    """
    Compare multiple models using the same benchmark parameters.
    
    Args:
        model_ids: The IDs of the models to compare.
        prompt: The prompt to use for the benchmark.
        max_tokens: The maximum number of tokens to generate.
        num_runs: The number of times to run the benchmark.
        temperature: The temperature to use for generation.
        top_p: The top-p value to use for generation.
        progress_callback: Optional callback for tracking progress.
        
    Returns:
        Dict[str, BenchmarkResult]: A dictionary mapping model IDs to benchmark results.
    """
    # Create operation for tracking progress
    operation_id, progress_info = create_operation(
        OperationType.BENCHMARK, 
        operation_id=f"compare_models",
        callback=progress_callback
    )
    
    try:
        # Start the operation
        start_operation(operation_id, f"Comparing {len(model_ids)} models")
        
        # Initialize results
        results = {}
        
        # Benchmark each model
        for i, model_id in enumerate(model_ids):
            update_progress(
                operation_id,
                i / len(model_ids),
                f"Benchmarking model {model_id} ({i + 1}/{len(model_ids)})"
            )
            
            # Create benchmark
            benchmark = ModelBenchmark(
                model_id=model_id,
                prompt=prompt,
                max_tokens=max_tokens,
                num_runs=num_runs,
                temperature=temperature,
                top_p=top_p,
                tags=["comparison"],
                description=f"Comparison benchmark with {len(model_ids)} models"
            )
            
            # Run benchmark
            result = run_benchmark(benchmark)
            
            # Add to results
            results[model_id] = result
        
        # Complete the operation
        complete_operation(
            operation_id,
            results,
            f"Comparison completed for {len(model_ids)} models"
        )
        
        return results
    
    except Exception as e:
        logger.error(f"Error comparing models: {e}", exc_info=True)
        fail_operation(operation_id, str(e), "Failed to compare models")
        return {}


def get_benchmark_results(model_id: Optional[str] = None) -> List[BenchmarkResult]:
    """
    Get benchmark results.
    
    Args:
        model_id: Optional ID of a specific model to get results for.
        
    Returns:
        List[BenchmarkResult]: A list of benchmark results.
    """
    registry = BenchmarkRegistry.get_instance()
    
    if model_id:
        return [result for _, result in registry.get_results_for_model(model_id)]
    else:
        return [result for _, result in registry.get_all_results()]


def get_benchmark_registry() -> BenchmarkRegistry:
    """
    Get the singleton instance of the BenchmarkRegistry.
    
    Returns:
        BenchmarkRegistry: The benchmark registry instance.
    """
    return BenchmarkRegistry.get_instance()


def create_standard_benchmarks() -> List[str]:
    """
    Create a set of standard benchmarks for common use cases.
    
    Returns:
        List[str]: A list of benchmark IDs.
    """
    registry = BenchmarkRegistry.get_instance()
    model_registry = ModelRegistry.get_instance()
    
    # Define standard prompts
    standard_prompts = {
        "creative_writing": "Write a short story about a robot learning to paint.",
        "dialogue": "Write a dialogue between two characters discussing the ethics of AI.",
        "summarization": "Summarize the following text: The development of artificial intelligence has accelerated in recent years, with breakthroughs in natural language processing, computer vision, and reinforcement learning. These advances have led to applications in healthcare, finance, transportation, and many other fields. However, they also raise important questions about privacy, bias, job displacement, and the long-term implications of increasingly autonomous systems.",
        "question_answering": "What are the main challenges in developing sustainable energy sources?",
        "code_generation": "Write a Python function that calculates the Fibonacci sequence up to n terms."
    }
    
    # Get available models
    available_models = model_registry.get_all_models()
    
    # Create benchmarks
    benchmark_ids = []
    
    for model in available_models:
        for prompt_name, prompt in standard_prompts.items():
            # Create benchmark
            benchmark = ModelBenchmark(
                model_id=model.id,
                prompt=prompt,
                max_tokens=100,
                num_runs=3,
                tags=[prompt_name, "standard"],
                description=f"Standard {prompt_name} benchmark"
            )
            
            # Register the benchmark
            benchmark_id = registry.register_benchmark(benchmark)
            benchmark_ids.append(benchmark_id)
    
    logger.info(f"Created {len(benchmark_ids)} standard benchmarks")
    return benchmark_ids


def evaluate_model_quality(model_id: str, 
                          reference_model_id: Optional[str] = None,
                          prompts: Optional[List[str]] = None,
                          max_tokens: int = 100,
                          progress_callback: Optional[ProgressCallback] = None) -> Dict[str, float]:
    """
    Evaluate the quality of a model's output compared to a reference model.
    
    Args:
        model_id: The ID of the model to evaluate.
        reference_model_id: Optional ID of a reference model to compare against.
        prompts: Optional list of prompts to use for evaluation.
        max_tokens: The maximum number of tokens to generate.
        progress_callback: Optional callback for tracking progress.
        
    Returns:
        Dict[str, float]: A dictionary of quality metrics.
    """
    # Create operation for tracking progress
    operation_id, progress_info = create_operation(
        OperationType.EVALUATION, 
        operation_id=f"evaluate_{model_id}",
        callback=progress_callback
    )
    
    try:
        # Start the operation
        start_operation(operation_id, f"Evaluating model {model_id}")
        
        # Use default prompts if none provided
        if not prompts:
            prompts = [
                "Write a short story about a robot learning to paint.",
                "Explain the concept of quantum computing to a high school student.",
                "Summarize the key events of World War II in a few paragraphs.",
                "Write a poem about the changing seasons.",
                "Describe the process of photosynthesis in plants."
            ]
        
        # Get model information
        model_registry = ModelRegistry.get_instance()
        model_info = model_registry.get_model_info(model_id)
        
        if not model_info:
            raise ModelNotSupportedError(f"Model {model_id} not found in registry")
        
        # Get reference model if provided
        reference_model_info = None
        if reference_model_id:
            reference_model_info = model_registry.get_model_info(reference_model_id)
            if not reference_model_info:
                raise ModelNotSupportedError(f"Reference model {reference_model_id} not found in registry")
        
        # Initialize metrics
        metrics = {
            "coherence": 0.0,
            "relevance": 0.0,
            "fluency": 0.0,
            "diversity": 0.0,
            "overall": 0.0
        }
        
        # Generate text with the model
        update_progress(operation_id, 0.1, "Generating text with model")
        
        # Get the appropriate model loader and generator
        model_loader, text_generator = _get_model_loader_and_generator(model_info.model_type)
        
        # Load the model
        model = model_loader(model_id)
        
        # Generate text for each prompt
        model_outputs = []
        for i, prompt in enumerate(prompts):
            update_progress(
                operation_id,
                0.1 + (0.4 * i / len(prompts)),
                f"Generating text for prompt {i + 1}/{len(prompts)}"
            )
            
            # Generate text
            generated_text = text_generator(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9
            )
            
            model_outputs.append(generated_text)
        
        # If reference model provided, generate text with it
        reference_outputs = []
        if reference_model_info:
            update_progress(operation_id, 0.5, "Generating text with reference model")
            
            # Get the appropriate model loader and generator
            ref_model_loader, ref_text_generator = _get_model_loader_and_generator(reference_model_info.model_type)
            
            # Load the reference model
            reference_model = ref_model_loader(reference_model_id)
            
            # Generate text for each prompt
            for i, prompt in enumerate(prompts):
                update_progress(
                    operation_id,
                    0.5 + (0.4 * i / len(prompts)),
                    f"Generating text with reference model for prompt {i + 1}/{len(prompts)}"
                )
                
                # Generate text
                generated_text = ref_text_generator(
                    model=reference_model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    top_p=0.9
                )
                
                reference_outputs.append(generated_text)
        
        # Evaluate quality metrics
        update_progress(operation_id, 0.9, "Evaluating quality metrics")
        
        # Simple heuristic evaluation (in a real implementation, this would use more sophisticated methods)
        for i, (prompt, output) in enumerate(zip(prompts, model_outputs)):
            # Coherence: measure how well the text flows
            coherence_score = min(1.0, 0.5 + (len(output.split()) / 200))
            
            # Relevance: measure how relevant the output is to the prompt
            prompt_words = set(prompt.lower().split())
            output_words = set(output.lower().split())
            common_words = prompt_words.intersection(output_words)
            relevance_score = min(1.0, len(common_words) / len(prompt_words))
            
            # Fluency: measure grammatical correctness (simplified)
            sentences = output.split('.')
            avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
            fluency_score = min(1.0, 0.5 + (avg_sentence_length / 20))
            
            # Diversity: measure vocabulary diversity
            unique_words = len(set(output.lower().split()))
            total_words = len(output.split())
            diversity_score = min(1.0, unique_words / max(1, total_words))
            
            # Update metrics
            metrics["coherence"] += coherence_score / len(prompts)
            metrics["relevance"] += relevance_score / len(prompts)
            metrics["fluency"] += fluency_score / len(prompts)
            metrics["diversity"] += diversity_score / len(prompts)
        
        # Calculate overall score
        metrics["overall"] = (
            metrics["coherence"] + 
            metrics["relevance"] + 
            metrics["fluency"] + 
            metrics["diversity"]
        ) / 4
        
        # Complete the operation
        complete_operation(
            operation_id,
            metrics,
            f"Evaluation completed for {model_id}"
        )
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error evaluating model {model_id}: {e}", exc_info=True)
        fail_operation(operation_id, str(e), f"Failed to evaluate model {model_id}")
        return {
            "coherence": 0.0,
            "relevance": 0.0,
            "fluency": 0.0,
            "diversity": 0.0,
            "overall": 0.0,
            "error": str(e)
        }


def generate_benchmark_report(model_id: Optional[str] = None,
                             benchmark_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate a report of benchmark results.
    
    Args:
        model_id: Optional ID of a specific model to generate a report for.
        benchmark_ids: Optional list of benchmark IDs to include in the report.
        
    Returns:
        Dict[str, Any]: A dictionary containing the report data.
    """
    registry = BenchmarkRegistry.get_instance()
    
    # Get results
    if benchmark_ids:
        results = [registry.get_result(benchmark_id) for benchmark_id in benchmark_ids if registry.get_result(benchmark_id)]
    elif model_id:
        results = [result for _, result in registry.get_results_for_model(model_id)]
    else:
        results = [result for _, result in registry.get_all_results()]
    
    # Group results by model
    results_by_model = {}
    for result in results:
        if result.model_id not in results_by_model:
            results_by_model[result.model_id] = []
        results_by_model[result.model_id].append(result)
    
    # Generate report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "num_models": len(results_by_model),
        "num_results": len(results),
        "models": {}
    }
    
    # Process each model
    for model_id, model_results in results_by_model.items():
        # Get model info
        model_registry = ModelRegistry.get_instance()
        model_info = model_registry.get_model_info(model_id)
        
        # Calculate average metrics
        avg_load_time = statistics.mean([r.load_time_seconds for r in model_results if r.load_time_seconds is not None])
        avg_generation_time = statistics.mean([r.avg_generation_time for r in model_results if r.avg_generation_time is not None])
        avg_tokens_per_second = statistics.mean([r.avg_tokens_per_second for r in model_results if r.avg_tokens_per_second is not None])
        avg_peak_memory = statistics.mean([r.peak_memory_mb for r in model_results if r.peak_memory_mb is not None])
        
        # Add to report
        report["models"][model_id] = {
            "name": model_info.name if model_info else "Unknown",
            "type": model_info.model_type.name if model_info else "UNKNOWN",
            "num_results": len(model_results),
            "avg_load_time_seconds": avg_load_time,
            "avg_generation_time_seconds": avg_generation_time,
            "avg_tokens_per_second": avg_tokens_per_second,
            "avg_peak_memory_mb": avg_peak_memory,
            "results": [result.benchmark_id for result in model_results]
        }
    
    return report


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Benchmarking Tool")
    parser.add_argument("--model", type=str, help="Model ID to benchmark")
    parser.add_argument("--prompt", type=str, help="Prompt to use for benchmarking")
    parser.add_argument("--max-tokens", type=int, default=100, help="Maximum tokens to generate")
    parser.add_argument("--num-runs", type=int, default=3, help="Number of benchmark runs")
    parser.add_argument("--compare", type=str, nargs="+", help="Model IDs to compare")
    parser.add_argument("--create-standard", action="store_true", help="Create standard benchmarks")
    parser.add_argument("--report", action="store_true", help="Generate benchmark report")
    
    args = parser.parse_args()
    
    if args.create_standard:
        print("Creating standard benchmarks...")
        benchmark_ids = create_standard_benchmarks()
        print(f"Created {len(benchmark_ids)} standard benchmarks")
    
    elif args.compare:
        print(f"Comparing models: {', '.join(args.compare)}")
        results = compare_models(
            model_ids=args.compare,
            prompt=args.prompt or "Write a short story about a robot learning to paint.",
            max_tokens=args.max_tokens,
            num_runs=args.num_runs
        )
        
        # Print results
        for model_id, result in results.items():
            print(f"\nModel: {result.model_name} ({model_id})")
            print(f"Average generation time: {result.avg_generation_time:.2f} seconds")
            print(f"Average tokens per second: {result.avg_tokens_per_second:.2f}")
            print(f"Peak memory usage: {result.peak_memory_mb:.2f} MB")
    
    elif args.model:
        print(f"Benchmarking model: {args.model}")
        benchmark = ModelBenchmark(
            model_id=args.model,
            prompt=args.prompt or "Write a short story about a robot learning to paint.",
            max_tokens=args.max_tokens,
            num_runs=args.num_runs
        )
        
        result = run_benchmark(benchmark)
        
        # Print results
        print(f"\nModel: {result.model_name} ({args.model})")
        print(f"Load time: {result.load_time_seconds:.2f} seconds")
        print(f"Average generation time: {result.avg_generation_time:.2f} seconds")
        print(f"Average tokens per second: {result.avg_tokens_per_second:.2f}")
        print(f"Peak memory usage: {result.peak_memory_mb:.2f} MB")
    
    elif args.report:
        print("Generating benchmark report...")
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
    
    else:
        print("No action specified. Use --help for usage information.")
