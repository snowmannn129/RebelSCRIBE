#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the benchmark_visualization module.

This script demonstrates how to use the benchmark_visualization module to create
visualizations and reports for AI model benchmark results.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.ai.benchmark_visualization import (
    plot_model_comparison, plot_benchmark_history, plot_metric_correlation,
    plot_model_radar_chart, export_visualization, generate_benchmark_report_html,
    check_visualization_dependencies
)
from src.ai.model_benchmarking import (
    get_benchmark_results, compare_models, ModelBenchmark, run_benchmark
)
from src.utils.logging_utils import get_logger

# Set up logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)


def example_check_dependencies():
    """Example of checking visualization dependencies."""
    print("\n=== Checking Visualization Dependencies ===")
    
    if check_visualization_dependencies():
        print("All required visualization dependencies are available.")
    else:
        print("Some visualization dependencies are missing.")
        print("Please install the required dependencies:")
        print("  pip install matplotlib seaborn pandas")


def example_plot_model_comparison(results):
    """
    Example of creating a model comparison plot.
    
    Args:
        results: List of benchmark results.
    """
    print("\n=== Creating Model Comparison Plot ===")
    
    try:
        # Create a static model comparison plot for tokens per second
        fig = plot_model_comparison(
            results=results,
            metric="avg_tokens_per_second",
            title="Model Comparison: Average Tokens per Second",
            sort_ascending=False,
            interactive=False
        )
        
        # Save the plot
        output_path = "model_comparison_tps.png"
        export_visualization(fig, output_path)
        print(f"Static model comparison plot saved to {output_path}")
        
        # Create a model comparison plot for generation time
        fig = plot_model_comparison(
            results=results,
            metric="avg_generation_time",
            title="Model Comparison: Average Generation Time",
            sort_ascending=True,  # Lower is better for generation time
            interactive=False
        )
        
        # Save the plot
        output_path = "model_comparison_time.png"
        export_visualization(fig, output_path)
        print(f"Static model comparison plot saved to {output_path}")
        
        # Check if Plotly is available for interactive plots
        try:
            import plotly
            
            # Create an interactive model comparison plot
            fig = plot_model_comparison(
                results=results,
                metric="avg_tokens_per_second",
                title="Interactive Model Comparison: Average Tokens per Second",
                sort_ascending=False,
                interactive=True
            )
            
            # Save the interactive plot as HTML
            output_path = "interactive_model_comparison.html"
            fig.write_html(output_path)
            print(f"Interactive model comparison plot saved to {output_path}")
            print("Open this file in a web browser to interact with the visualization.")
            
        except ImportError:
            print("Plotly is not available. Skipping interactive visualization example.")
    
    except Exception as e:
        print(f"Error creating model comparison plot: {e}")


def example_plot_benchmark_history(results):
    """
    Example of creating a benchmark history plot.
    
    Args:
        results: List of benchmark results.
    """
    print("\n=== Creating Benchmark History Plot ===")
    
    try:
        # Create a static benchmark history plot for all models
        fig = plot_benchmark_history(
            results=results,
            metric="avg_tokens_per_second",
            title="Benchmark History: Average Tokens per Second",
            days=30,  # Last 30 days
            interactive=False
        )
        
        # Save the plot
        output_path = "benchmark_history.png"
        export_visualization(fig, output_path)
        print(f"Static benchmark history plot saved to {output_path}")
        
        # If we have results for a specific model, create a history plot for it
        if results and hasattr(results[0], 'model_id'):
            model_id = results[0].model_id
            
            try:
                fig = plot_benchmark_history(
                    results=results,
                    model_id=model_id,
                    metric="avg_tokens_per_second",
                    title=f"Benchmark History for {model_id}: Average Tokens per Second",
                    interactive=False
                )
                
                # Save the plot
                output_path = f"benchmark_history_{model_id}.png"
                export_visualization(fig, output_path)
                print(f"Model-specific benchmark history plot saved to {output_path}")
                
                # Check if Plotly is available for interactive plots
                try:
                    import plotly
                    
                    # Create an interactive benchmark history plot
                    fig = plot_benchmark_history(
                        results=results,
                        model_id=model_id,
                        metric="avg_tokens_per_second",
                        title=f"Interactive Benchmark History for {model_id}",
                        interactive=True
                    )
                    
                    # Save the interactive plot as HTML
                    output_path = f"interactive_benchmark_history_{model_id}.html"
                    fig.write_html(output_path)
                    print(f"Interactive benchmark history plot saved to {output_path}")
                    print("Open this file in a web browser to interact with the visualization.")
                    
                except ImportError:
                    print("Plotly is not available. Skipping interactive visualization example.")
            
            except ValueError as e:
                print(f"Could not create model-specific history plot: {e}")
    
    except Exception as e:
        print(f"Error creating benchmark history plot: {e}")


def example_plot_metric_correlation(results):
    """
    Example of creating a metric correlation plot.
    
    Args:
        results: List of benchmark results.
    """
    print("\n=== Creating Metric Correlation Plot ===")
    
    try:
        # Create a correlation plot between generation time and tokens per second
        fig = plot_metric_correlation(
            results=results,
            x_metric="avg_generation_time",
            y_metric="avg_tokens_per_second",
            title="Correlation: Generation Time vs Tokens per Second"
        )
        
        # Save the plot
        output_path = "metric_correlation.png"
        export_visualization(fig, output_path)
        print(f"Metric correlation plot saved to {output_path}")
        
        # Create a correlation plot between memory usage and tokens per second
        fig = plot_metric_correlation(
            results=results,
            x_metric="peak_memory_mb",
            y_metric="avg_tokens_per_second",
            title="Correlation: Memory Usage vs Tokens per Second"
        )
        
        # Save the plot
        output_path = "memory_correlation.png"
        export_visualization(fig, output_path)
        print(f"Memory correlation plot saved to {output_path}")
        
        # Demonstrate additional metrics if available
        try:
            # Prepare data with additional metrics
            df = _prepare_benchmark_data(results, calculate_additional_metrics=True)
            
            # Check if perplexity is available
            if "perplexity" in df.columns and not df["perplexity"].isna().all():
                fig = plot_metric_correlation(
                    results=results,
                    x_metric="perplexity",
                    y_metric="avg_tokens_per_second",
                    title="Correlation: Perplexity vs Tokens per Second"
                )
                
                # Save the plot
                output_path = "perplexity_correlation.png"
                export_visualization(fig, output_path)
                print(f"Perplexity correlation plot saved to {output_path}")
            else:
                print("Perplexity data not available in the benchmark results.")
            
            # Check if BLEU score is available
            if "bleu_score" in df.columns and not df["bleu_score"].isna().all():
                fig = plot_metric_correlation(
                    results=results,
                    x_metric="bleu_score",
                    y_metric="avg_generation_time",
                    title="Correlation: BLEU Score vs Generation Time"
                )
                
                # Save the plot
                output_path = "bleu_correlation.png"
                export_visualization(fig, output_path)
                print(f"BLEU score correlation plot saved to {output_path}")
            else:
                print("BLEU score data not available in the benchmark results.")
                
        except Exception as e:
            print(f"Error creating additional metric correlation plots: {e}")
    
    except Exception as e:
        print(f"Error creating metric correlation plot: {e}")


def example_plot_radar_chart(results):
    """
    Example of creating a radar chart for model comparison.
    
    Args:
        results: List of benchmark results.
    """
    print("\n=== Creating Radar Chart ===")
    
    try:
        # Get unique model IDs
        model_ids = list(set(result.model_id for result in results if hasattr(result, 'model_id')))
        
        if len(model_ids) < 2:
            print("Need at least 2 models for a radar chart comparison.")
            return
        
        # Limit to 5 models for readability
        model_ids = model_ids[:5]
        
        # Create a radar chart
        fig = plot_model_radar_chart(
            results=results,
            model_ids=model_ids,
            title="Model Comparison Radar Chart"
        )
        
        # Save the plot
        output_path = "radar_chart.png"
        export_visualization(fig, output_path)
        print(f"Radar chart saved to {output_path}")
    
    except Exception as e:
        print(f"Error creating radar chart: {e}")


def example_generate_html_report(results):
    """
    Example of generating an HTML benchmark report.
    
    Args:
        results: List of benchmark results.
    """
    print("\n=== Generating HTML Report ===")
    
    try:
        # Generate HTML report
        html_report = generate_benchmark_report_html(
            results=results,
            include_plots=True
        )
        
        # Save the report
        output_path = "benchmark_report.html"
        with open(output_path, "w") as f:
            f.write(html_report)
        
        print(f"HTML report saved to {output_path}")
        print(f"Open this file in a web browser to view the report.")
    
    except Exception as e:
        print(f"Error generating HTML report: {e}")


def example_run_new_benchmark_and_visualize():
    """Example of running a new benchmark and visualizing the results."""
    print("\n=== Running New Benchmark and Visualizing Results ===")
    
    try:
        # Get available models
        from src.ai.model_registry import ModelRegistry
        registry = ModelRegistry.get_instance()
        models = registry.get_all_models()
        
        if not models:
            print("No models available for benchmarking.")
            return
        
        print(f"Found {len(models)} models. Using the first one for demonstration.")
        model = models[0]
        
        # Create a benchmark
        benchmark = ModelBenchmark(
            model_id=model.id,
            prompt="Write a short story about a robot learning to paint.",
            max_tokens=100,
            num_runs=2,  # Use a small number for the example
            tags=["example", "visualization"]
        )
        
        # Run the benchmark
        print(f"Running benchmark for model {model.id}...")
        result = run_benchmark(benchmark)
        
        print("Benchmark completed.")
        print(f"Average generation time: {result.avg_generation_time:.2f} seconds")
        print(f"Average tokens per second: {result.avg_tokens_per_second:.2f}")
        
        # Create a visualization
        fig = plot_model_comparison(
            results=[result],
            metric="avg_tokens_per_second",
            title=f"Benchmark Result for {model.id}"
        )
        
        # Save the plot
        output_path = "new_benchmark_result.png"
        export_visualization(fig, output_path)
        print(f"Benchmark result visualization saved to {output_path}")
    
    except Exception as e:
        print(f"Error running and visualizing benchmark: {e}")


def example_check_interactive_dependencies():
    """Example of checking interactive visualization dependencies."""
    print("\n=== Checking Interactive Visualization Dependencies ===")
    
    if check_visualization_dependencies(include_interactive=True):
        print("All required visualization dependencies including interactive ones are available.")
    else:
        print("Some visualization dependencies are missing.")
        print("For interactive visualizations, please install:")
        print("  pip install plotly")
        print("For additional metrics, please install:")
        print("  pip install nltk")


def main():
    """Main function to run the examples."""
    print("Benchmark Visualization Examples")
    print("===============================")
    
    # Check dependencies
    example_check_dependencies()
    example_check_interactive_dependencies()
    
    # Get benchmark results
    results = get_benchmark_results()
    
    if not results:
        print("\nNo benchmark results found. Running example with mock data...")
        # Create mock results for demonstration
        from datetime import datetime, timedelta
        from src.ai.model_benchmarking import BenchmarkResult
        
        # Create mock results for different models
        mock_results = []
        model_types = ["LLAMA", "MISTRAL", "PHI", "FALCON", "MPT"]
        
        for i, model_type in enumerate(model_types):
            # Create results with different timestamps for history plot
            for j in range(5):
                timestamp = (datetime.now() - timedelta(days=j*3)).isoformat()
                
                # Values vary by model type and time
                tps_base = 50 - i * 5  # Tokens per second decreases by model index
                tps_variation = j * 2  # Increases over time
                
                # Create mock token logprobs for perplexity calculation
                token_logprobs = [-1.5 - (i * 0.1) - (j * 0.05)] * 100
                
                # Create mock reference text for BLEU score calculation
                reference_text = "This is a reference text for BLEU score calculation."
                
                mock_results.append(
                    BenchmarkResult(
                        benchmark_id=f"benchmark_{i}_{j}",
                        model_id=f"model-{model_type.lower()}",
                        model_name=f"{model_type} Model",
                        model_type=model_type,
                        timestamp=timestamp,
                        prompt="This is a mock prompt for testing visualization.",
                        max_tokens=100,
                        temperature=0.7,
                        top_p=0.9,
                        num_runs=3,
                        load_time_seconds=1.0 + i * 0.2,
                        generation_times_seconds=[2.0 - j * 0.1] * 3,
                        avg_generation_time=2.0 - j * 0.1,
                        tokens_generated=[100] * 3,
                        avg_tokens_per_second=tps_base + tps_variation,
                        peak_memory_mb=1000 - i * 100,
                        generated_texts=["This is a mock generated text for testing visualization."] * 3,
                        token_logprobs=token_logprobs,
                        reference_text=reference_text
                    )
                )
        
        results = mock_results
        print(f"Created {len(results)} mock benchmark results for demonstration.")
    else:
        print(f"\nFound {len(results)} benchmark results.")
    
    # Run examples
    example_plot_model_comparison(results)
    example_plot_benchmark_history(results)
    example_plot_metric_correlation(results)
    example_plot_radar_chart(results)
    example_generate_html_report(results)
    
    # Uncomment to run a new benchmark (may take time)
    # example_run_new_benchmark_and_visualize()
    
    print("\nAll examples completed.")
    print("Check the current directory for generated visualizations and reports.")


if __name__ == "__main__":
    main()
