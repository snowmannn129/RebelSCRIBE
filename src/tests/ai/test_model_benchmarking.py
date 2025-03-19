#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the model_benchmarking module.

This module contains tests for the model benchmarking functionality,
including benchmark creation, running benchmarks, and comparing models.
"""

import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, ANY
import datetime

from src.ai.model_benchmarking import (
    ModelBenchmark, BenchmarkMetric, BenchmarkResult,
    BenchmarkRegistry, ModelBenchmarkError, ModelNotSupportedError,
    run_benchmark, compare_models, get_benchmark_results,
    create_standard_benchmarks, evaluate_model_quality,
    generate_benchmark_report
)
from src.ai.model_registry import ModelRegistry, ModelInfo, ModelType, ModelSource


class TestModelBenchmark(unittest.TestCase):
    """Tests for the ModelBenchmark class."""
    
    def test_model_benchmark_creation(self):
        """Test creating a ModelBenchmark instance."""
        benchmark = ModelBenchmark(
            model_id="test-model",
            prompt="Test prompt",
            max_tokens=50,
            num_runs=2,
            temperature=0.8,
            top_p=0.95,
            tags=["test", "unit-test"],
            description="Test benchmark"
        )
        
        self.assertEqual(benchmark.model_id, "test-model")
        self.assertEqual(benchmark.prompt, "Test prompt")
        self.assertEqual(benchmark.max_tokens, 50)
        self.assertEqual(benchmark.num_runs, 2)
        self.assertEqual(benchmark.temperature, 0.8)
        self.assertEqual(benchmark.top_p, 0.95)
        self.assertEqual(benchmark.tags, ["test", "unit-test"])
        self.assertEqual(benchmark.description, "Test benchmark")
    
    def test_model_benchmark_to_dict(self):
        """Test converting a ModelBenchmark to a dictionary."""
        benchmark = ModelBenchmark(
            model_id="test-model",
            prompt="Test prompt",
            metrics=[BenchmarkMetric.LOAD_TIME, BenchmarkMetric.GENERATION_TIME]
        )
        
        data = benchmark.to_dict()
        
        self.assertEqual(data["model_id"], "test-model")
        self.assertEqual(data["prompt"], "Test prompt")
        self.assertEqual(data["metrics"], ["LOAD_TIME", "GENERATION_TIME"])
    
    def test_model_benchmark_from_dict(self):
        """Test creating a ModelBenchmark from a dictionary."""
        data = {
            "model_id": "test-model",
            "prompt": "Test prompt",
            "max_tokens": 50,
            "num_runs": 2,
            "temperature": 0.8,
            "top_p": 0.95,
            "metrics": ["LOAD_TIME", "GENERATION_TIME"],
            "tags": ["test", "unit-test"],
            "description": "Test benchmark"
        }
        
        benchmark = ModelBenchmark.from_dict(data)
        
        self.assertEqual(benchmark.model_id, "test-model")
        self.assertEqual(benchmark.prompt, "Test prompt")
        self.assertEqual(benchmark.max_tokens, 50)
        self.assertEqual(benchmark.num_runs, 2)
        self.assertEqual(benchmark.temperature, 0.8)
        self.assertEqual(benchmark.top_p, 0.95)
        self.assertEqual(benchmark.metrics, [BenchmarkMetric.LOAD_TIME, BenchmarkMetric.GENERATION_TIME])
        self.assertEqual(benchmark.tags, ["test", "unit-test"])
        self.assertEqual(benchmark.description, "Test benchmark")


class TestBenchmarkResult(unittest.TestCase):
    """Tests for the BenchmarkResult class."""
    
    def test_benchmark_result_creation(self):
        """Test creating a BenchmarkResult instance."""
        result = BenchmarkResult(
            benchmark_id="test-benchmark",
            model_id="test-model",
            model_name="Test Model",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2,
            load_time_seconds=1.5,
            generation_times_seconds=[2.0, 2.2],
            avg_generation_time=2.1,
            tokens_generated=[100, 110],
            avg_tokens_per_second=50.0,
            peak_memory_mb=1024.0,
            generated_texts=["Generated text 1", "Generated text 2"],
            tags=["test", "unit-test"],
            metadata={"test_key": "test_value"}
        )
        
        self.assertEqual(result.benchmark_id, "test-benchmark")
        self.assertEqual(result.model_id, "test-model")
        self.assertEqual(result.model_name, "Test Model")
        self.assertEqual(result.model_type, "LLAMA")
        self.assertEqual(result.timestamp, "2025-03-12T12:00:00")
        self.assertEqual(result.prompt, "Test prompt")
        self.assertEqual(result.max_tokens, 50)
        self.assertEqual(result.temperature, 0.8)
        self.assertEqual(result.top_p, 0.95)
        self.assertEqual(result.num_runs, 2)
        self.assertEqual(result.load_time_seconds, 1.5)
        self.assertEqual(result.generation_times_seconds, [2.0, 2.2])
        self.assertEqual(result.avg_generation_time, 2.1)
        self.assertEqual(result.tokens_generated, [100, 110])
        self.assertEqual(result.avg_tokens_per_second, 50.0)
        self.assertEqual(result.peak_memory_mb, 1024.0)
        self.assertEqual(result.generated_texts, ["Generated text 1", "Generated text 2"])
        self.assertEqual(result.tags, ["test", "unit-test"])
        self.assertEqual(result.metadata, {"test_key": "test_value"})
    
    def test_benchmark_result_to_dict(self):
        """Test converting a BenchmarkResult to a dictionary."""
        result = BenchmarkResult(
            benchmark_id="test-benchmark",
            model_id="test-model",
            model_name="Test Model",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        data = result.to_dict()
        
        self.assertEqual(data["benchmark_id"], "test-benchmark")
        self.assertEqual(data["model_id"], "test-model")
        self.assertEqual(data["model_name"], "Test Model")
        self.assertEqual(data["model_type"], "LLAMA")
    
    def test_benchmark_result_from_dict(self):
        """Test creating a BenchmarkResult from a dictionary."""
        data = {
            "benchmark_id": "test-benchmark",
            "model_id": "test-model",
            "model_name": "Test Model",
            "model_type": "LLAMA",
            "timestamp": "2025-03-12T12:00:00",
            "prompt": "Test prompt",
            "max_tokens": 50,
            "temperature": 0.8,
            "top_p": 0.95,
            "num_runs": 2,
            "load_time_seconds": 1.5,
            "generation_times_seconds": [2.0, 2.2],
            "avg_generation_time": 2.1,
            "tokens_generated": [100, 110],
            "avg_tokens_per_second": 50.0,
            "peak_memory_mb": 1024.0,
            "generated_texts": ["Generated text 1", "Generated text 2"],
            "tags": ["test", "unit-test"],
            "metadata": {"test_key": "test_value"}
        }
        
        result = BenchmarkResult.from_dict(data)
        
        self.assertEqual(result.benchmark_id, "test-benchmark")
        self.assertEqual(result.model_id, "test-model")
        self.assertEqual(result.model_name, "Test Model")
        self.assertEqual(result.model_type, "LLAMA")
        self.assertEqual(result.timestamp, "2025-03-12T12:00:00")
        self.assertEqual(result.prompt, "Test prompt")
        self.assertEqual(result.max_tokens, 50)
        self.assertEqual(result.temperature, 0.8)
        self.assertEqual(result.top_p, 0.95)
        self.assertEqual(result.num_runs, 2)
        self.assertEqual(result.load_time_seconds, 1.5)
        self.assertEqual(result.generation_times_seconds, [2.0, 2.2])
        self.assertEqual(result.avg_generation_time, 2.1)
        self.assertEqual(result.tokens_generated, [100, 110])
        self.assertEqual(result.avg_tokens_per_second, 50.0)
        self.assertEqual(result.peak_memory_mb, 1024.0)
        self.assertEqual(result.generated_texts, ["Generated text 1", "Generated text 2"])
        self.assertEqual(result.tags, ["test", "unit-test"])
        self.assertEqual(result.metadata, {"test_key": "test_value"})


class TestBenchmarkRegistry(unittest.TestCase):
    """Tests for the BenchmarkRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for the registry file
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Patch the _get_registry_file_path method to use a temporary file
        self.registry_file_patcher = patch(
            'src.ai.model_benchmarking.BenchmarkRegistry._get_registry_file_path',
            return_value=os.path.join(self.temp_dir.name, "benchmark_registry.json")
        )
        self.registry_file_patcher.start()
        
        # Reset the singleton instance
        BenchmarkRegistry._instance = None
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patcher
        self.registry_file_patcher.stop()
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        
        # Reset the singleton instance
        BenchmarkRegistry._instance = None
    
    def test_singleton_pattern(self):
        """Test that BenchmarkRegistry follows the singleton pattern."""
        registry1 = BenchmarkRegistry.get_instance()
        registry2 = BenchmarkRegistry.get_instance()
        
        self.assertIs(registry1, registry2)
        
        # Ensure direct instantiation raises an error
        with self.assertRaises(RuntimeError):
            BenchmarkRegistry()
    
    def test_register_benchmark(self):
        """Test registering a benchmark."""
        registry = BenchmarkRegistry.get_instance()
        
        benchmark = ModelBenchmark(
            model_id="test-model",
            prompt="Test prompt"
        )
        
        benchmark_id = registry.register_benchmark(benchmark)
        
        self.assertIsNotNone(benchmark_id)
        self.assertTrue(benchmark_id.startswith("benchmark_"))
        
        # Verify the benchmark was registered
        registered_benchmark = registry.get_benchmark(benchmark_id)
        self.assertEqual(registered_benchmark.model_id, "test-model")
        self.assertEqual(registered_benchmark.prompt, "Test prompt")
    
    def test_register_result(self):
        """Test registering a benchmark result."""
        registry = BenchmarkRegistry.get_instance()
        
        result = BenchmarkResult(
            benchmark_id="test-benchmark",
            model_id="test-model",
            model_name="Test Model",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        result_id = registry.register_result(result)
        
        self.assertIsNotNone(result_id)
        self.assertTrue(result_id.startswith("result_"))
        
        # Verify the result was registered
        registered_result = registry.get_result(result_id)
        self.assertEqual(registered_result.model_id, "test-model")
        self.assertEqual(registered_result.model_name, "Test Model")
    
    def test_get_results_for_model(self):
        """Test getting results for a specific model."""
        registry = BenchmarkRegistry.get_instance()
        
        # Register results for two different models
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        result2 = BenchmarkResult(
            benchmark_id="test-benchmark-2",
            model_id="model-2",
            model_name="Model 2",
            model_type="MISTRAL",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        result3 = BenchmarkResult(
            benchmark_id="test-benchmark-3",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T13:00:00",
            prompt="Another test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        registry.register_result(result1)
        registry.register_result(result2)
        registry.register_result(result3)
        
        # Get results for model-1
        model1_results = registry.get_results_for_model("model-1")
        
        self.assertEqual(len(model1_results), 2)
        self.assertEqual(model1_results[0][1].model_id, "model-1")
        self.assertEqual(model1_results[1][1].model_id, "model-1")
        
        # Get results for model-2
        model2_results = registry.get_results_for_model("model-2")
        
        self.assertEqual(len(model2_results), 1)
        self.assertEqual(model2_results[0][1].model_id, "model-2")
    
    def test_get_latest_result_for_model(self):
        """Test getting the latest result for a specific model."""
        registry = BenchmarkRegistry.get_instance()
        
        # Register results for the same model with different timestamps
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        result2 = BenchmarkResult(
            benchmark_id="test-benchmark-2",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T13:00:00",
            prompt="Another test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            num_runs=2
        )
        
        registry.register_result(result1)
        registry.register_result(result2)
        
        # Get the latest result for model-1
        latest_result = registry.get_latest_result_for_model("model-1")
        
        self.assertIsNotNone(latest_result)
        self.assertEqual(latest_result[1].model_id, "model-1")
        self.assertEqual(latest_result[1].timestamp, "2025-03-12T13:00:00")
        self.assertEqual(latest_result[1].prompt, "Another test prompt")


@patch('src.ai.model_benchmarking.ModelRegistry')
class TestRunBenchmark(unittest.TestCase):
    """Tests for the run_benchmark function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model info
        self.model_info = MagicMock()
        self.model_info.name = "Test Model"
        self.model_info.model_type = ModelType.LLAMA
        self.model_info.source = ModelSource.LOCAL
        self.model_info.format = MagicMock()
        self.model_info.format.name = "PYTORCH"
        self.model_info.quantization = "4bit"
        self.model_info.parameters = 7000000000
        
        # Create a mock model
        self.model = MagicMock()
        
        # Create a benchmark
        self.benchmark = ModelBenchmark(
            model_id="test-model",
            prompt="Test prompt",
            max_tokens=50,
            num_runs=2
        )
        
        # Reset the BenchmarkRegistry singleton
        BenchmarkRegistry._instance = None
        
        # Patch the BenchmarkRegistry._get_registry_file_path method
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry_file_patcher = patch(
            'src.ai.model_benchmarking.BenchmarkRegistry._get_registry_file_path',
            return_value=os.path.join(self.temp_dir.name, "benchmark_registry.json")
        )
        self.registry_file_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patcher
        self.registry_file_patcher.stop()
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        
        # Reset the singleton instance
        BenchmarkRegistry._instance = None
    
    @patch('src.ai.model_benchmarking._get_model_loader_and_generator')
    @patch('src.ai.model_benchmarking.track_model_usage')
    @patch('src.ai.model_benchmarking.tracemalloc')
    @patch('src.ai.model_benchmarking._measure_memory_usage')
    @patch('src.ai.model_benchmarking.time')
    def test_run_benchmark_success(self, mock_time, mock_measure_memory, mock_tracemalloc, 
                                  mock_track_usage, mock_get_loader_generator, mock_model_registry):
        """Test running a benchmark successfully."""
        # Set up mocks
        mock_model_registry.get_instance.return_value.get_model_info.return_value = self.model_info
        
        mock_loader = MagicMock(return_value=self.model)
        mock_generator = MagicMock(return_value="Generated text")
        mock_get_loader_generator.return_value = (mock_loader, mock_generator)
        
        mock_time.time.side_effect = [0, 1, 2, 3, 4, 5]  # Load time: 1s, Generation times: 1s, 1s
        mock_measure_memory.side_effect = [100, 200]  # Initial: 100MB, Final: 200MB
        mock_tracemalloc.get_traced_memory.return_value = (50 * 1024 * 1024, 150 * 1024 * 1024)
        
        # Run the benchmark
        result = run_benchmark(self.benchmark)
        
        # Verify the result
        self.assertEqual(result.model_id, "test-model")
        self.assertEqual(result.model_name, "Test Model")
        self.assertEqual(result.model_type, "LLAMA")
        self.assertEqual(result.prompt, "Test prompt")
        self.assertEqual(result.max_tokens, 50)
        self.assertEqual(result.num_runs, 2)
        self.assertEqual(result.load_time_seconds, 1)
        self.assertEqual(result.generation_times_seconds, [1, 1])
        self.assertEqual(result.avg_generation_time, 1)
        self.assertEqual(result.generated_texts, ["Generated text", "Generated text"])
        self.assertEqual(result.tokens_generated, [1, 1])  # One word in "Generated text"
        self.assertAlmostEqual(result.avg_tokens_per_second, 1)
        self.assertEqual(result.peak_memory_mb, 150)
        
        # Verify the model loader and generator were called correctly
        mock_loader.assert_called_once_with("test-model")
        self.assertEqual(mock_generator.call_count, 2)
        mock_generator.assert_called_with(
            model=self.model,
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9
        )
        
        # Verify model usage was tracked
        mock_track_usage.assert_called_once_with(
            model_id="test-model",
            usage_type="benchmark",
            metadata=ANY
        )
    
    @patch('src.ai.model_benchmarking._get_model_loader_and_generator')
    def test_run_benchmark_model_not_found(self, mock_get_loader_generator, mock_model_registry):
        """Test running a benchmark with a model that doesn't exist."""
        # Set up mocks
        mock_model_registry.get_instance.return_value.get_model_info.return_value = None
        
        # Run the benchmark
        result = run_benchmark(self.benchmark)
        
        # Verify the result
        self.assertEqual(result.model_id, "test-model")
        self.assertIsNotNone(result.error)
        self.assertIn("not found", result.error)
        
        # Verify the model loader and generator were not called
        mock_get_loader_generator.assert_not_called()
    
    @patch('src.ai.model_benchmarking._get_model_loader_and_generator')
    def test_run_benchmark_model_not_supported(self, mock_get_loader_generator, mock_model_registry):
        """Test running a benchmark with a model type that's not supported."""
        # Set up mocks
        mock_model_registry.get_instance.return_value.get_model_info.return_value = self.model_info
        mock_get_loader_generator.side_effect = ModelNotSupportedError("Model type not supported")
        
        # Run the benchmark
        result = run_benchmark(self.benchmark)
        
        # Verify the result
        self.assertEqual(result.model_id, "test-model")
        self.assertIsNotNone(result.error)
        self.assertIn("not supported", result.error)


@patch('src.ai.model_benchmarking.ModelRegistry')
@patch('src.ai.model_benchmarking.run_benchmark')
class TestCompareModels(unittest.TestCase):
    """Tests for the compare_models function."""
    
    def test_compare_models_success(self, mock_run_benchmark, mock_model_registry):
        """Test comparing models successfully."""
        # Set up mocks
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            avg_generation_time=1.0,
            avg_tokens_per_second=50.0,
            peak_memory_mb=1024.0
        )
        
        result2 = BenchmarkResult(
            benchmark_id="test-benchmark-2",
            model_id="model-2",
            model_name="Model 2",
            model_type="MISTRAL",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            avg_generation_time=0.8,
            avg_tokens_per_second=60.0,
            peak_memory_mb=800.0
        )
        
        mock_run_benchmark.side_effect = [result1, result2]
        
        # Compare models
        results = compare_models(
            model_ids=["model-1", "model-2"],
            prompt="Test prompt",
            max_tokens=50,
            num_runs=2
        )
        
        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results["model-1"], result1)
        self.assertEqual(results["model-2"], result2)
        
        # Verify run_benchmark was called correctly
        self.assertEqual(mock_run_benchmark.call_count, 2)
        mock_run_benchmark.assert_any_call(ANY)
        
        # Verify the benchmark parameters
        benchmark1 = mock_run_benchmark.call_args_list[0][0][0]
        self.assertEqual(benchmark1.model_id, "model-1")
        self.assertEqual(benchmark1.prompt, "Test prompt")
        self.assertEqual(benchmark1.max_tokens, 50)
        self.assertEqual(benchmark1.num_runs, 2)
        self.assertEqual(benchmark1.tags, ["comparison"])
        
        benchmark2 = mock_run_benchmark.call_args_list[1][0][0]
        self.assertEqual(benchmark2.model_id, "model-2")
        self.assertEqual(benchmark2.prompt, "Test prompt")
        self.assertEqual(benchmark2.max_tokens, 50)
        self.assertEqual(benchmark2.num_runs, 2)
        self.assertEqual(benchmark2.tags, ["comparison"])
    
    def test_compare_models_error(self, mock_run_benchmark, mock_model_registry):
        """Test comparing models with an error."""
        # Set up mocks
        mock_run_benchmark.side_effect = Exception("Test error")
        
        # Compare models
        results = compare_models(
            model_ids=["model-1", "model-2"],
            prompt="Test prompt",
            max_tokens=50,
            num_runs=2
        )
        
        # Verify the results
        self.assertEqual(len(results), 0)


@patch('src.ai.model_benchmarking.BenchmarkRegistry')
class TestGetBenchmarkResults(unittest.TestCase):
    """Tests for the get_benchmark_results function."""
    
    def test_get_all_benchmark_results(self, mock_benchmark_registry):
        """Test getting all benchmark results."""
        # Set up mocks
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2
        )
        
        result2 = BenchmarkResult(
            benchmark_id="test-benchmark-2",
            model_id="model-2",
            model_name="Model 2",
            model_type="MISTRAL",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2
        )
        
        mock_benchmark_registry.get_instance.return_value.get_all_results.return_value = [
            ("result-1", result1),
            ("result-2", result2)
        ]
        
        # Get all benchmark results
        results = get_benchmark_results()
        
        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], result1)
        self.assertEqual(results[1], result2)
    
    def test_get_benchmark_results_for_model(self, mock_benchmark_registry):
        """Test getting benchmark results for a specific model."""
        # Set up mocks
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2
        )
        
        mock_benchmark_registry.get_instance.return_value.get_results_for_model.return_value = [
            ("result-1", result1)
        ]
        
        # Get benchmark results for model-1
        results = get_benchmark_results("model-1")
        
        # Verify the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], result1)
        
        # Verify get_results_for_model was called correctly
        mock_benchmark_registry.get_instance.return_value.get_results_for_model.assert_called_once_with("model-1")


@patch('src.ai.model_benchmarking.ModelRegistry')
@patch('src.ai.model_benchmarking.BenchmarkRegistry')
class TestCreateStandardBenchmarks(unittest.TestCase):
    """Tests for the create_standard_benchmarks function."""
    
    def test_create_standard_benchmarks(self, mock_benchmark_registry, mock_model_registry):
        """Test creating standard benchmarks."""
        # Set up mocks
        model1 = MagicMock()
        model1.id = "model-1"
        
        model2 = MagicMock()
        model2.id = "model-2"
        
        mock_model_registry.get_instance.return_value.get_all_models.return_value = [model1, model2]
        mock_benchmark_registry.get_instance.return_value.register_benchmark.side_effect = [
            f"benchmark-{i}" for i in range(10)  # 2 models * 5 standard prompts
        ]
        
        # Create standard benchmarks
        benchmark_ids = create_standard_benchmarks()
        
        # Verify the results
        self.assertEqual(len(benchmark_ids), 10)  # 2 models * 5 standard prompts
        
        # Verify register_benchmark was called correctly
        self.assertEqual(mock_benchmark_registry.get_instance.return_value.register_benchmark.call_count, 10)
        
        # Verify the benchmark parameters for the first call
        benchmark = mock_benchmark_registry.get_instance.return_value.register_benchmark.call_args_list[0][0][0]
        self.assertEqual(benchmark.model_id, "model-1")
        self.assertIn(benchmark.prompt, [
            "Write a short story about a robot learning to paint.",
            "Write a dialogue between two characters discussing the ethics of AI.",
            "Summarize the following text: The development of artificial intelligence has accelerated in recent years, with breakthroughs in natural language processing, computer vision, and reinforcement learning. These advances have led to applications in healthcare, finance, transportation, and many other fields. However, they also raise important questions about privacy, bias, job displacement, and the long-term implications of increasingly autonomous systems.",
            "What are the main challenges in developing sustainable energy sources?",
            "Write a Python function that calculates the Fibonacci sequence up to n terms."
        ])
        self.assertEqual(benchmark.max_tokens, 100)
        self.assertEqual(benchmark.num_runs, 3)
        self.assertIn("standard", benchmark.tags)


@patch('src.ai.model_benchmarking.ModelRegistry')
@patch('src.ai.model_benchmarking._get_model_loader_and_generator')
class TestEvaluateModelQuality(unittest.TestCase):
    """Tests for the evaluate_model_quality function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model info
        self.model_info = MagicMock()
        self.model_info.name = "Test Model"
        self.model_info.model_type = ModelType.LLAMA
        
        # Create a mock model
        self.model = MagicMock()
    
    def test_evaluate_model_quality_success(self, mock_get_loader_generator, mock_model_registry):
        """Test evaluating model quality successfully."""
        # Set up mocks
        mock_model_registry.get_instance.return_value.get_model_info.return_value = self.model_info
        
        mock_loader = MagicMock(return_value=self.model)
        mock_generator = MagicMock(return_value="Generated text with some words to test quality metrics.")
        mock_get_loader_generator.return_value = (mock_loader, mock_generator)
        
        # Evaluate model quality
        metrics = evaluate_model_quality(
            model_id="test-model",
            prompts=["Test prompt"]
        )
        
        # Verify the metrics
        self.assertIn("coherence", metrics)
        self.assertIn("relevance", metrics)
        self.assertIn("fluency", metrics)
        self.assertIn("diversity", metrics)
        self.assertIn("overall", metrics)
        
        # Verify the model loader and generator were called correctly
        mock_loader.assert_called_once_with("test-model")
        mock_generator.assert_called_with(
            model=self.model,
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            top_p=0.9
        )
    
    def test_evaluate_model_quality_model_not_found(self, mock_get_loader_generator, mock_model_registry):
        """Test evaluating model quality with a model that doesn't exist."""
        # Set up mocks
        mock_model_registry.get_instance.return_value.get_model_info.return_value = None
        
        # Evaluate model quality
        metrics = evaluate_model_quality(
            model_id="test-model",
            prompts=["Test prompt"]
        )
        
        # Verify the metrics
        self.assertEqual(metrics["coherence"], 0.0)
        self.assertEqual(metrics["relevance"], 0.0)
        self.assertEqual(metrics["fluency"], 0.0)
        self.assertEqual(metrics["diversity"], 0.0)
        self.assertEqual(metrics["overall"], 0.0)
        self.assertIn("error", metrics)
        
        # Verify the model loader and generator were not called
        mock_get_loader_generator.assert_not_called()
    
    def test_evaluate_model_quality_with_reference_model(self, mock_get_loader_generator, mock_model_registry):
        """Test evaluating model quality with a reference model."""
        # Set up mocks
        mock_model_registry.get_instance.return_value.get_model_info.side_effect = [
            self.model_info,  # First call for the model being evaluated
            self.model_info   # Second call for the reference model
        ]
        
        mock_loader = MagicMock(return_value=self.model)
        mock_generator = MagicMock(return_value="Generated text with some words to test quality metrics.")
        mock_get_loader_generator.return_value = (mock_loader, mock_generator)
        
        # Evaluate model quality
        metrics = evaluate_model_quality(
            model_id="test-model",
            reference_model_id="reference-model",
            prompts=["Test prompt"]
        )
        
        # Verify the metrics
        self.assertIn("coherence", metrics)
        self.assertIn("relevance", metrics)
        self.assertIn("fluency", metrics)
        self.assertIn("diversity", metrics)
        self.assertIn("overall", metrics)
        
        # Verify the model loader and generator were called correctly
        self.assertEqual(mock_loader.call_count, 2)
        mock_loader.assert_any_call("test-model")
        mock_loader.assert_any_call("reference-model")
        
        self.assertEqual(mock_generator.call_count, 2)
        mock_generator.assert_any_call(
            model=self.model,
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            top_p=0.9
        )


@patch('src.ai.model_benchmarking.BenchmarkRegistry')
@patch('src.ai.model_benchmarking.ModelRegistry')
class TestGenerateBenchmarkReport(unittest.TestCase):
    """Tests for the generate_benchmark_report function."""
    
    def test_generate_benchmark_report_all_models(self, mock_model_registry, mock_benchmark_registry):
        """Test generating a benchmark report for all models."""
        # Set up mocks
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            load_time_seconds=1.0,
            avg_generation_time=2.0,
            avg_tokens_per_second=50.0,
            peak_memory_mb=1024.0
        )
        
        result2 = BenchmarkResult(
            benchmark_id="test-benchmark-2",
            model_id="model-2",
            model_name="Model 2",
            model_type="MISTRAL",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            load_time_seconds=0.8,
            avg_generation_time=1.5,
            avg_tokens_per_second=60.0,
            peak_memory_mb=800.0
        )
        
        mock_benchmark_registry.get_instance.return_value.get_all_results.return_value = [
            ("result-1", result1),
            ("result-2", result2)
        ]
        
        model_info1 = MagicMock()
        model_info1.name = "Model 1"
        model_info1.model_type = ModelType.LLAMA
        
        model_info2 = MagicMock()
        model_info2.name = "Model 2"
        model_info2.model_type = ModelType.MISTRAL
        
        mock_model_registry.get_instance.return_value.get_model_info.side_effect = [
            model_info1,
            model_info2
        ]
        
        # Generate benchmark report
        report = generate_benchmark_report()
        
        # Verify the report
        self.assertEqual(report["num_models"], 2)
        self.assertEqual(report["num_results"], 2)
        self.assertIn("model-1", report["models"])
        self.assertIn("model-2", report["models"])
        
        # Verify model-1 report
        model1_report = report["models"]["model-1"]
        self.assertEqual(model1_report["name"], "Model 1")
        self.assertEqual(model1_report["type"], "LLAMA")
        self.assertEqual(model1_report["num_results"], 1)
        self.assertEqual(model1_report["avg_load_time_seconds"], 1.0)
        self.assertEqual(model1_report["avg_generation_time_seconds"], 2.0)
        self.assertEqual(model1_report["avg_tokens_per_second"], 50.0)
        self.assertEqual(model1_report["avg_peak_memory_mb"], 1024.0)
        
        # Verify model-2 report
        model2_report = report["models"]["model-2"]
        self.assertEqual(model2_report["name"], "Model 2")
        self.assertEqual(model2_report["type"], "MISTRAL")
        self.assertEqual(model2_report["num_results"], 1)
        self.assertEqual(model2_report["avg_load_time_seconds"], 0.8)
        self.assertEqual(model2_report["avg_generation_time_seconds"], 1.5)
        self.assertEqual(model2_report["avg_tokens_per_second"], 60.0)
        self.assertEqual(model2_report["avg_peak_memory_mb"], 800.0)
    
    def test_generate_benchmark_report_specific_model(self, mock_model_registry, mock_benchmark_registry):
        """Test generating a benchmark report for a specific model."""
        # Set up mocks
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt 1",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            load_time_seconds=1.0,
            avg_generation_time=2.0,
            avg_tokens_per_second=50.0,
            peak_memory_mb=1024.0
        )
        
        result2 = BenchmarkResult(
            benchmark_id="test-benchmark-2",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T13:00:00",
            prompt="Test prompt 2",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            load_time_seconds=1.2,
            avg_generation_time=2.2,
            avg_tokens_per_second=45.0,
            peak_memory_mb=1100.0
        )
        
        mock_benchmark_registry.get_instance.return_value.get_results_for_model.return_value = [
            ("result-1", result1),
            ("result-2", result2)
        ]
        
        model_info = MagicMock()
        model_info.name = "Model 1"
        model_info.model_type = ModelType.LLAMA
        
        mock_model_registry.get_instance.return_value.get_model_info.return_value = model_info
        
        # Generate benchmark report
        report = generate_benchmark_report(model_id="model-1")
        
        # Verify the report
        self.assertEqual(report["num_models"], 1)
        self.assertEqual(report["num_results"], 2)
        self.assertIn("model-1", report["models"])
        
        # Verify model-1 report
        model1_report = report["models"]["model-1"]
        self.assertEqual(model1_report["name"], "Model 1")
        self.assertEqual(model1_report["type"], "LLAMA")
        self.assertEqual(model1_report["num_results"], 2)
        self.assertEqual(model1_report["avg_load_time_seconds"], 1.1)  # Average of 1.0 and 1.2
        self.assertEqual(model1_report["avg_generation_time_seconds"], 2.1)  # Average of 2.0 and 2.2
        self.assertEqual(model1_report["avg_tokens_per_second"], 47.5)  # Average of 50.0 and 45.0
        self.assertEqual(model1_report["avg_peak_memory_mb"], 1062.0)  # Average of 1024.0 and 1100.0
    
    def test_generate_benchmark_report_specific_benchmarks(self, mock_model_registry, mock_benchmark_registry):
        """Test generating a benchmark report for specific benchmark IDs."""
        # Set up mocks
        result1 = BenchmarkResult(
            benchmark_id="test-benchmark-1",
            model_id="model-1",
            model_name="Model 1",
            model_type="LLAMA",
            timestamp="2025-03-12T12:00:00",
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            num_runs=2,
            load_time_seconds=1.0,
            avg_generation_time=2.0,
            avg_tokens_per_second=50.0,
            peak_memory_mb=1024.0
        )
        
        mock_benchmark_registry.get_instance.return_value.get_result.return_value = result1
        
        model_info = MagicMock()
        model_info.name = "Model 1"
        model_info.model_type = ModelType.LLAMA
        
        mock_model_registry.get_instance.return_value.get_model_info.return_value = model_info
        
        # Generate benchmark report
        report = generate_benchmark_report(benchmark_ids=["test-benchmark-1"])
        
        # Verify the report
        self.assertEqual(report["num_models"], 1)
        self.assertEqual(report["num_results"], 1)
        self.assertIn("model-1", report["models"])
        
        # Verify model-1 report
        model1_report = report["models"]["model-1"]
        self.assertEqual(model1_report["name"], "Model 1")
        self.assertEqual(model1_report["type"], "LLAMA")
        self.assertEqual(model1_report["num_results"], 1)
        self.assertEqual(model1_report["avg_load_time_seconds"], 1.0)
        self.assertEqual(model1_report["avg_generation_time_seconds"], 2.0)
        self.assertEqual(model1_report["avg_tokens_per_second"], 50.0)
        self.assertEqual(model1_report["avg_peak_memory_mb"], 1024.0)


if __name__ == "__main__":
    unittest.main()
