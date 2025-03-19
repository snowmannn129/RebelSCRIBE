#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the benchmark_visualization module.

This module contains tests for the visualization capabilities for AI model benchmark results,
including plot generation, HTML report creation, and visualization export.
"""

import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, ANY
import datetime
import base64
from io import BytesIO

# Import the module to test
from src.ai.benchmark_visualization import (
    check_visualization_dependencies, _prepare_benchmark_data,
    plot_model_comparison, plot_benchmark_history, plot_metric_correlation,
    plot_model_radar_chart, export_visualization, generate_benchmark_report_html,
    _get_color_for_model_type, _fig_to_base64
)
from src.ai.model_benchmarking import (
    BenchmarkResult, ModelBenchmark, BenchmarkRegistry
)


class TestVisualizationDependencies(unittest.TestCase):
    """Tests for the visualization dependency checking."""
    
    @patch('src.ai.benchmark_visualization.MATPLOTLIB_AVAILABLE', True)
    @patch('src.ai.benchmark_visualization.SEABORN_AVAILABLE', True)
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', True)
    def test_all_dependencies_available(self):
        """Test when all dependencies are available."""
        self.assertTrue(check_visualization_dependencies())
    
    @patch('src.ai.benchmark_visualization.MATPLOTLIB_AVAILABLE', False)
    @patch('src.ai.benchmark_visualization.SEABORN_AVAILABLE', True)
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', True)
    def test_matplotlib_missing(self):
        """Test when matplotlib is missing."""
        self.assertFalse(check_visualization_dependencies())
    
    @patch('src.ai.benchmark_visualization.MATPLOTLIB_AVAILABLE', True)
    @patch('src.ai.benchmark_visualization.SEABORN_AVAILABLE', False)
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', True)
    def test_seaborn_missing(self):
        """Test when seaborn is missing."""
        self.assertFalse(check_visualization_dependencies())
    
    @patch('src.ai.benchmark_visualization.MATPLOTLIB_AVAILABLE', True)
    @patch('src.ai.benchmark_visualization.SEABORN_AVAILABLE', True)
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', False)
    def test_pandas_missing(self):
        """Test when pandas is missing."""
        self.assertFalse(check_visualization_dependencies())


class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions in the benchmark_visualization module."""
    
    def test_get_color_for_model_type(self):
        """Test getting colors for different model types."""
        # Test known model types
        self.assertEqual(_get_color_for_model_type("LLAMA"), "#3498db")
        self.assertEqual(_get_color_for_model_type("MISTRAL"), "#2ecc71")
        self.assertEqual(_get_color_for_model_type("PHI"), "#9b59b6")
        
        # Test unknown model type
        self.assertEqual(_get_color_for_model_type("UNKNOWN_MODEL"), "#7f8c8d")
    
    @patch('src.ai.benchmark_visualization.BytesIO')
    @patch('src.ai.benchmark_visualization.base64.b64encode')
    def test_fig_to_base64(self, mock_b64encode, mock_bytesio):
        """Test converting a figure to base64."""
        # Setup mocks
        mock_fig = MagicMock()
        mock_buf = MagicMock()
        mock_bytesio.return_value = mock_buf
        mock_b64encode.return_value.decode.return_value = "base64_encoded_string"
        
        # Call the function
        result = _fig_to_base64(mock_fig)
        
        # Verify the result
        self.assertEqual(result, "base64_encoded_string")
        mock_fig.savefig.assert_called_once_with(mock_buf, format="png", bbox_inches="tight")
        mock_buf.seek.assert_called_once_with(0)
        mock_b64encode.assert_called_once()


@patch('src.ai.benchmark_visualization.pd')
class TestPrepareData(unittest.TestCase):
    """Tests for the _prepare_benchmark_data function."""
    
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', True)
    def test_prepare_benchmark_data(self, mock_pd):
        """Test preparing benchmark data for visualization."""
        # Create mock results
        results = [
            BenchmarkResult(
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
                generation_times_seconds=[2.0, 2.2],
                avg_generation_time=2.1,
                tokens_generated=[100, 110],
                avg_tokens_per_second=50.0,
                peak_memory_mb=1024.0,
                generated_texts=["Generated text 1", "Generated text 2"]
            ),
            BenchmarkResult(
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
                generation_times_seconds=[1.8, 2.0],
                avg_generation_time=1.9,
                tokens_generated=[120, 130],
                avg_tokens_per_second=65.0,
                peak_memory_mb=800.0,
                generated_texts=["Generated text 3", "Generated text 4"]
            )
        ]
        
        # Mock DataFrame
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df
        
        # Call the function
        df = _prepare_benchmark_data(results)
        
        # Verify the result
        self.assertEqual(df, mock_df)
        mock_pd.DataFrame.assert_called_once()
        
        # Verify the data passed to DataFrame
        data = mock_pd.DataFrame.call_args[0][0]
        self.assertEqual(len(data), 2)
        
        # Check first result data
        self.assertEqual(data[0]["model_id"], "model-1")
        self.assertEqual(data[0]["model_name"], "Model 1")
        self.assertEqual(data[0]["model_type"], "LLAMA")
        self.assertEqual(data[0]["load_time_seconds"], 1.0)
        self.assertEqual(data[0]["avg_generation_time"], 2.1)
        self.assertEqual(data[0]["avg_tokens_per_second"], 50.0)
        self.assertEqual(data[0]["peak_memory_mb"], 1024.0)
        
        # Check second result data
        self.assertEqual(data[1]["model_id"], "model-2")
        self.assertEqual(data[1]["model_name"], "Model 2")
        self.assertEqual(data[1]["model_type"], "MISTRAL")
        self.assertEqual(data[1]["load_time_seconds"], 0.8)
        self.assertEqual(data[1]["avg_generation_time"], 1.9)
        self.assertEqual(data[1]["avg_tokens_per_second"], 65.0)
        self.assertEqual(data[1]["peak_memory_mb"], 800.0)
    
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', False)
    def test_prepare_benchmark_data_no_pandas(self, mock_pd):
        """Test preparing benchmark data when pandas is not available."""
        with self.assertRaises(ImportError):
            _prepare_benchmark_data([])
    
    @patch('src.ai.benchmark_visualization.PANDAS_AVAILABLE', True)
    def test_prepare_benchmark_data_with_errors(self, mock_pd):
        """Test preparing benchmark data with error results."""
        # Create mock results with one error result
        results = [
            BenchmarkResult(
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
                generation_times_seconds=[2.0, 2.2],
                avg_generation_time=2.1,
                tokens_generated=[100, 110],
                avg_tokens_per_second=50.0,
                peak_memory_mb=1024.0,
                generated_texts=["Generated text 1", "Generated text 2"]
            ),
            BenchmarkResult(
                benchmark_id="test-benchmark-error",
                model_id="model-error",
                model_name="Error Model",
                model_type="UNKNOWN",
                timestamp="2025-03-12T12:00:00",
                prompt="Test prompt",
                max_tokens=50,
                temperature=0.7,
                top_p=0.9,
                num_runs=2,
                error="Model not found"
            )
        ]
        
        # Mock DataFrame
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df
        
        # Call the function
        df = _prepare_benchmark_data(results)
        
        # Verify the result
        self.assertEqual(df, mock_df)
        mock_pd.DataFrame.assert_called_once()
        
        # Verify the data passed to DataFrame
        data = mock_pd.DataFrame.call_args[0][0]
        self.assertEqual(len(data), 1)  # Only one result should be included (the non-error one)
        
        # Check the data
        self.assertEqual(data[0]["model_id"], "model-1")
        self.assertEqual(data[0]["model_name"], "Model 1")


@patch('src.ai.benchmark_visualization.check_visualization_dependencies', return_value=True)
@patch('src.ai.benchmark_visualization._prepare_benchmark_data')
@patch('src.ai.benchmark_visualization.plt')
@patch('src.ai.benchmark_visualization.sns')
@patch('src.ai.benchmark_visualization.PLOTLY_AVAILABLE', False)
class TestPlotModelComparison(unittest.TestCase):
    """Tests for the plot_model_comparison function."""
    
    def test_plot_model_comparison_static(self, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a static model comparison plot."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "model_type", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_model_performance = MagicMock()
        mock_df.groupby.return_value.__getitem__.return_value.mean.return_value.reset_index.return_value = mock_model_performance
        mock_model_performance.sort_values.return_value = mock_model_performance
        mock_model_performance.__getitem__.side_effect = lambda x: MagicMock() if x in ["model_name", "model_type"] else MagicMock()
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        mock_bars = MagicMock()
        mock_ax.bar.return_value = mock_bars
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function with interactive=False
        fig = plot_model_comparison(results, metric="avg_tokens_per_second", interactive=False)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_check_deps.assert_called_once()
        mock_prepare_data.assert_called_once_with(results, calculate_additional_metrics=True)
        mock_df.groupby.assert_called_once_with(["model_name", "model_type"])
        mock_model_performance.sort_values.assert_called_once_with(by="avg_tokens_per_second", ascending=False)
        mock_plt.subplots.assert_called_once()
        mock_ax.bar.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_ax.set_xlabel.assert_called_once()
        mock_ax.set_ylabel.assert_called_once()
        mock_plt.xticks.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
    
    @patch('src.ai.benchmark_visualization.px', new_callable=MagicMock)
    def test_plot_model_comparison_interactive(self, mock_px, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating an interactive model comparison plot."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "model_type", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_model_performance = MagicMock()
        mock_df.groupby.return_value.__getitem__.return_value.mean.return_value.reset_index.return_value = mock_model_performance
        
        mock_fig = MagicMock()
        mock_px.bar.return_value = mock_fig
        
        # Create mock results
        results = [MagicMock()]
        
        # Temporarily patch PLOTLY_AVAILABLE to True
        with patch('src.ai.benchmark_visualization.PLOTLY_AVAILABLE', True):
            # Call the function with interactive=True
            fig = plot_model_comparison(results, metric="avg_tokens_per_second", interactive=True)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_prepare_data.assert_called_once_with(results, calculate_additional_metrics=True)
        mock_df.groupby.assert_called_once_with(["model_name", "model_type"])
        mock_px.bar.assert_called_once()
        mock_fig.update_layout.assert_called_once()
        mock_fig.update_traces.assert_called_once()
    
    def test_plot_model_comparison_invalid_metric(self, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a model comparison plot with an invalid metric."""
        with self.assertRaises(ValueError):
            plot_model_comparison([], metric="invalid_metric")
    
    def test_plot_model_comparison_dependencies_not_available(self, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a model comparison plot when dependencies are not available."""
        mock_check_deps.return_value = False
        
        with self.assertRaises(ImportError):
            plot_model_comparison([], interactive=False)
    
    @patch('src.ai.benchmark_visualization.logger')
    def test_plot_model_comparison_interactive_fallback(self, mock_logger, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test fallback to static plot when interactive requested but dependencies not available."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "model_type", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_model_performance = MagicMock()
        mock_df.groupby.return_value.__getitem__.return_value.mean.return_value.reset_index.return_value = mock_model_performance
        mock_model_performance.sort_values.return_value = mock_model_performance
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Force check_visualization_dependencies to return False for interactive
        mock_check_deps.side_effect = lambda include_interactive=False: not include_interactive
        
        # Create mock results
        results = [MagicMock()]
        
        # Temporarily patch PLOTLY_AVAILABLE to True
        with patch('src.ai.benchmark_visualization.PLOTLY_AVAILABLE', True):
            # Call the function with interactive=True
            fig = plot_model_comparison(results, metric="avg_tokens_per_second", interactive=True)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_logger.warning.assert_called_once()
        mock_prepare_data.assert_called_once()


@patch('src.ai.benchmark_visualization.check_visualization_dependencies', return_value=True)
@patch('src.ai.benchmark_visualization._prepare_benchmark_data')
@patch('src.ai.benchmark_visualization.plt')
@patch('src.ai.benchmark_visualization.sns')
@patch('src.ai.benchmark_visualization.mdates')
@patch('src.ai.benchmark_visualization.PLOTLY_AVAILABLE', False)
class TestPlotBenchmarkHistory(unittest.TestCase):
    """Tests for the plot_benchmark_history function."""
    
    def test_plot_benchmark_history_static(self, mock_mdates, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a static benchmark history plot."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "timestamp", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Mock groupby result
        mock_groups = [("Model 1", MagicMock()), ("Model 2", MagicMock())]
        mock_df.groupby.return_value = mock_groups
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function with interactive=False
        fig = plot_benchmark_history(results, metric="avg_tokens_per_second", interactive=False)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_check_deps.assert_called_once()
        mock_prepare_data.assert_called_once_with(results, calculate_additional_metrics=True)
        mock_df.groupby.assert_called_once_with("model_name")
        mock_plt.subplots.assert_called_once()
        mock_ax.xaxis.set_major_formatter.assert_called_once()
        mock_ax.xaxis.set_major_locator.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_ax.set_xlabel.assert_called_once()
        mock_ax.set_ylabel.assert_called_once()
        mock_ax.legend.assert_called_once()
        mock_plt.xticks.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
    
    @patch('src.ai.benchmark_visualization.px', new_callable=MagicMock)
    def test_plot_benchmark_history_interactive(self, mock_px, mock_mdates, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating an interactive benchmark history plot."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "timestamp", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_fig = MagicMock()
        mock_px.line.return_value = mock_fig
        
        # Create mock results
        results = [MagicMock()]
        
        # Temporarily patch PLOTLY_AVAILABLE to True
        with patch('src.ai.benchmark_visualization.PLOTLY_AVAILABLE', True):
            # Call the function with interactive=True
            fig = plot_benchmark_history(results, metric="avg_tokens_per_second", interactive=True)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_prepare_data.assert_called_once_with(results, calculate_additional_metrics=True)
        mock_px.line.assert_called_once()
        mock_fig.update_layout.assert_called_once()
        mock_fig.update_xaxes.assert_called_once()
    
    def test_plot_benchmark_history_with_model_id(self, mock_mdates, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a benchmark history plot for a specific model."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "timestamp", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_filtered_df = MagicMock()
        mock_filtered_df.columns = ["model_id", "model_name", "timestamp", "avg_tokens_per_second"]
        mock_df.__getitem__.return_value.__eq__.return_value = MagicMock()
        mock_df.__getitem__.return_value.__eq__.return_value.__getitem__.return_value = mock_filtered_df
        mock_filtered_df.empty = False
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Mock groupby result
        mock_groups = [("Model 1", MagicMock())]
        mock_filtered_df.groupby.return_value = mock_groups
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function
        fig = plot_benchmark_history(results, model_id="model-1", metric="avg_tokens_per_second", interactive=False)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_check_deps.assert_called_once()
        mock_prepare_data.assert_called_once_with(results, calculate_additional_metrics=True)
        mock_df.__getitem__.assert_called_with("model_id")
        mock_filtered_df.groupby.assert_called_once_with("model_name")
        mock_plt.subplots.assert_called_once()
        mock_ax.xaxis.set_major_formatter.assert_called_once()
        mock_ax.xaxis.set_major_locator.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_ax.set_xlabel.assert_called_once()
        mock_ax.set_ylabel.assert_called_once()
        mock_ax.legend.assert_called_once()
        mock_plt.xticks.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
    
    def test_plot_benchmark_history_with_days(self, mock_mdates, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a benchmark history plot with a days filter."""
        # Setup mocks
        mock_df = MagicMock()
        # Make sure the DataFrame has the required column
        mock_df.columns = ["model_id", "model_name", "timestamp", "avg_tokens_per_second"]
        mock_prepare_data.return_value = mock_df
        
        mock_filtered_df = MagicMock()
        mock_filtered_df.columns = ["model_id", "model_name", "timestamp", "avg_tokens_per_second"]
        mock_df.__getitem__.return_value.__ge__.return_value = mock_filtered_df
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Mock groupby result
        mock_groups = [("Model 1", MagicMock())]
        mock_filtered_df.groupby.return_value = mock_groups
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function
        fig = plot_benchmark_history(results, metric="avg_tokens_per_second", days=30, interactive=False)
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_check_deps.assert_called_once()
        mock_prepare_data.assert_called_once_with(results, calculate_additional_metrics=True)
        mock_df.__getitem__.assert_called_with("timestamp")
        mock_filtered_df.groupby.assert_called_once_with("model_name")
        mock_plt.subplots.assert_called_once()
        mock_ax.xaxis.set_major_formatter.assert_called_once()
        mock_ax.xaxis.set_major_locator.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_ax.set_xlabel.assert_called_once()
        mock_ax.set_ylabel.assert_called_once()
        mock_ax.legend.assert_called_once()
        mock_plt.xticks.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
    
    def test_plot_benchmark_history_metric_not_available(self, mock_mdates, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a benchmark history plot with a metric that is not available."""
        # Setup mocks
        mock_df = MagicMock()
        mock_prepare_data.return_value = mock_df
        
        # Set up the DataFrame to not have the requested metric
        mock_df.columns = ["model_id", "model_name", "timestamp"]
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function with a metric that doesn't exist
        with self.assertRaises(ValueError):
            plot_benchmark_history(results, metric="perplexity", interactive=False)


@patch('src.ai.benchmark_visualization.check_visualization_dependencies', return_value=True)
@patch('src.ai.benchmark_visualization._prepare_benchmark_data')
@patch('src.ai.benchmark_visualization.plt')
@patch('src.ai.benchmark_visualization.sns')
class TestPlotMetricCorrelation(unittest.TestCase):
    """Tests for the plot_metric_correlation function."""
    
    def test_plot_metric_correlation(self, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a metric correlation plot."""
        # Setup mocks
        mock_df = MagicMock()
        mock_prepare_data.return_value = mock_df
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function
        fig = plot_metric_correlation(
            results,
            x_metric="avg_generation_time",
            y_metric="avg_tokens_per_second"
        )
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_check_deps.assert_called_once()
        mock_prepare_data.assert_called_once_with(results)
        mock_plt.subplots.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_ax.set_xlabel.assert_called_once()
        mock_ax.set_ylabel.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
    
    def test_plot_metric_correlation_with_seaborn(self, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a metric correlation plot with seaborn."""
        # Setup mocks
        mock_df = MagicMock()
        mock_prepare_data.return_value = mock_df
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Set seaborn available
        mock_sns.regplot = MagicMock()
        mock_sns.scatterplot = MagicMock()
        
        # Create mock results
        results = [MagicMock()]
        
        # Call the function
        fig = plot_metric_correlation(
            results,
            x_metric="avg_generation_time",
            y_metric="avg_tokens_per_second"
        )
        
        # Verify the result
        self.assertEqual(fig, mock_fig)
        mock_check_deps.assert_called_once()
        mock_prepare_data.assert_called_once_with(results)
        mock_plt.subplots.assert_called_once()
        mock_sns.set_style.assert_called_once_with("whitegrid")
        mock_sns.regplot.assert_called_once()
        mock_sns.scatterplot.assert_called_once()
        mock_plt.legend.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_ax.set_xlabel.assert_called_once()
        mock_ax.set_ylabel.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
    
    def test_plot_metric_correlation_invalid_metrics(self, mock_sns, mock_plt, mock_prepare_data, mock_check_deps):
        """Test creating a metric correlation plot with invalid metrics."""
        # Test invalid x_metric
        with self.assertRaises(ValueError):
            plot_metric_correlation([], x_metric="invalid_metric", y_metric="avg_tokens_per_second")
        
        # Test invalid y_metric
        with self.assertRaises(ValueError):
            plot_metric_correlation([], x_metric="avg_generation_time", y_metric="invalid_metric")


@patch('src.ai.benchmark_visualization.check_visualization_dependencies', return_value=True)
@patch('src.ai.benchmark_visualization._prepare_benchmark_data')
@patch('src.ai.benchmark_visualization.plt')
@patch('src
