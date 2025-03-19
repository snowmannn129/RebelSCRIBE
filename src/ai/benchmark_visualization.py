#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark Visualization for RebelSCRIBE.

This module provides visualization capabilities for AI model benchmark results,
allowing users to generate plots, charts, and visual reports to compare model
performance and analyze benchmark data.

Example usage:
    ```python
    from src.ai.benchmark_visualization import (
        plot_model_comparison, generate_benchmark_report_html,
        plot_benchmark_history, export_visualization
    )
    from src.ai.model_benchmarking import get_benchmark_results
    
    # Get benchmark results
    results = get_benchmark_results()
    
    # Plot model comparison
    fig = plot_model_comparison(results, metric="avg_tokens_per_second")
    
    # Save the plot
    export_visualization(fig, "model_comparison.png")
    
    # Generate HTML report
    html_report = generate_benchmark_report_html(results)
    with open("benchmark_report.html", "w") as f:
        f.write(html_report)
    ```
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import base64
from io import BytesIO

# Import visualization libraries
try:
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from src.utils.logging_utils import get_logger
from src.ai.model_benchmarking import (
    BenchmarkResult, get_benchmark_results, generate_benchmark_report
)

logger = get_logger(__name__)


def check_visualization_dependencies(include_interactive: bool = False) -> bool:
    """
    Check if the required visualization dependencies are available.
    
    Args:
        include_interactive: Whether to check for interactive visualization dependencies.
        
    Returns:
        bool: True if all required dependencies are available, False otherwise.
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib is not available. Install it with 'pip install matplotlib'")
        return False
    
    if not SEABORN_AVAILABLE:
        logger.warning("Seaborn is not available. Install it with 'pip install seaborn'")
        return False
    
    if not PANDAS_AVAILABLE:
        logger.warning("Pandas is not available. Install it with 'pip install pandas'")
        return False
    
    if include_interactive and not PLOTLY_AVAILABLE:
        logger.warning("Plotly is not available. Install it with 'pip install plotly'")
        return False
    
    return True


def _prepare_benchmark_data(results: List[BenchmarkResult], calculate_additional_metrics: bool = False) -> pd.DataFrame:
    """
    Prepare benchmark data for visualization.
    
    Args:
        results: List of benchmark results.
        calculate_additional_metrics: Whether to calculate additional metrics like perplexity and BLEU score.
        
    Returns:
        pd.DataFrame: DataFrame containing the benchmark data.
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas is required for data preparation")
    
    # Extract relevant data from benchmark results
    data = []
    for result in results:
        # Skip results with errors
        if result.error:
            continue
        
        # Convert timestamp to datetime
        try:
            timestamp = datetime.datetime.fromisoformat(result.timestamp)
        except (ValueError, TypeError):
            timestamp = datetime.datetime.now()
        
        # Create base result data
        result_data = {
            "model_id": result.model_id,
            "model_name": result.model_name,
            "model_type": result.model_type,
            "timestamp": timestamp,
            "load_time_seconds": result.load_time_seconds,
            "avg_generation_time": result.avg_generation_time,
            "avg_tokens_per_second": result.avg_tokens_per_second,
            "peak_memory_mb": result.peak_memory_mb,
            "prompt_length": len(result.prompt.split()),
            "max_tokens": result.max_tokens,
            "num_runs": result.num_runs,
            "benchmark_id": result.benchmark_id
        }
        
        # Calculate additional metrics if requested
        if calculate_additional_metrics:
            # Calculate perplexity (approximation based on token probabilities)
            # Lower perplexity is better - indicates more confident predictions
            if hasattr(result, 'token_logprobs') and result.token_logprobs:
                avg_logprob = sum(result.token_logprobs) / len(result.token_logprobs)
                perplexity = 2 ** (-avg_logprob)
                result_data["perplexity"] = perplexity
            else:
                # Use a placeholder value if token logprobs are not available
                result_data["perplexity"] = None
            
            # Calculate BLEU score if reference text is available
            if NLTK_AVAILABLE and hasattr(result, 'reference_text') and result.reference_text and result.generated_texts:
                try:
                    # Use the first generated text for BLEU calculation
                    reference = [result.reference_text.split()]
                    candidate = result.generated_texts[0].split()
                    
                    # Use smoothing to handle cases where there are no n-gram overlaps
                    smoothing = SmoothingFunction().method1
                    bleu_score = sentence_bleu(reference, candidate, smoothing_function=smoothing)
                    result_data["bleu_score"] = bleu_score
                except Exception as e:
                    logger.debug(f"Error calculating BLEU score: {e}")
                    result_data["bleu_score"] = None
            else:
                result_data["bleu_score"] = None
            
            # Calculate response length ratio (generated text length / prompt length)
            if result.generated_texts:
                avg_response_length = sum(len(text.split()) for text in result.generated_texts) / len(result.generated_texts)
                prompt_length = len(result.prompt.split())
                if prompt_length > 0:
                    result_data["response_length_ratio"] = avg_response_length / prompt_length
                else:
                    result_data["response_length_ratio"] = None
            else:
                result_data["response_length_ratio"] = None
        
        # Add result data
        data.append(result_data)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


def plot_model_comparison(
    results: List[BenchmarkResult],
    metric: str = "avg_tokens_per_second",
    top_n: Optional[int] = None,
    figsize: Tuple[int, int] = (10, 6),
    title: Optional[str] = None,
    sort_ascending: bool = False,
    interactive: bool = False
) -> Union[Figure, Any]:
    """
    Plot a comparison of model performance based on a specific metric.
    
    Args:
        results: List of benchmark results.
        metric: The metric to compare (e.g., "avg_tokens_per_second", "avg_generation_time").
        top_n: Optional number of top models to include.
        figsize: Figure size as (width, height) in inches.
        title: Optional custom title for the plot.
        sort_ascending: Whether to sort in ascending order (default is descending).
        interactive: Whether to create an interactive plot using Plotly.
        
    Returns:
        Union[Figure, Any]: The matplotlib figure object or Plotly figure object.
        
    Raises:
        ImportError: If required visualization dependencies are not available.
        ValueError: If the specified metric is not valid.
    """
    if interactive and not PLOTLY_AVAILABLE:
        logger.warning("Plotly is not available. Falling back to static visualization.")
        interactive = False
    
    if not interactive and not check_visualization_dependencies():
        raise ImportError("Required visualization dependencies are not available")
    
    # Valid metrics
    valid_metrics = {
        "avg_tokens_per_second": "Average Tokens per Second",
        "avg_generation_time": "Average Generation Time (s)",
        "load_time_seconds": "Model Load Time (s)",
        "peak_memory_mb": "Peak Memory Usage (MB)",
        "perplexity": "Perplexity (lower is better)",
        "bleu_score": "BLEU Score (higher is better)",
        "response_length_ratio": "Response Length Ratio"
    }
    
    if metric not in valid_metrics:
        raise ValueError(f"Invalid metric: {metric}. Valid metrics are: {list(valid_metrics.keys())}")
    
    # Prepare data
    df = _prepare_benchmark_data(results, calculate_additional_metrics=True)
    
    # Skip if the metric is not available in the data
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' is not available in the benchmark results")
    
    # Group by model and calculate mean of the metric
    model_performance = df.groupby(["model_name", "model_type"])[metric].mean().reset_index()
    
    # Sort by the metric
    model_performance = model_performance.sort_values(by=metric, ascending=sort_ascending)
    
    # Limit to top N models if specified
    if top_n is not None and top_n > 0:
        model_performance = model_performance.head(top_n)
    
    # Set the title
    if not title:
        title = f"Model Comparison: {valid_metrics[metric]}"
    
    if interactive and PLOTLY_AVAILABLE:
        # Create interactive plot with Plotly
        fig = px.bar(
            model_performance,
            x="model_name",
            y=metric,
            color="model_type",
            title=title,
            labels={
                "model_name": "Model",
                metric: valid_metrics[metric],
                "model_type": "Model Type"
            },
            height=figsize[1] * 100,
            width=figsize[0] * 100,
            text=metric
        )
        
        # Update layout
        fig.update_layout(
            title_font_size=20,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            legend_title_font_size=14,
            xaxis_tickangle=-45
        )
        
        # Format text on bars
        fig.update_traces(
            texttemplate='%{text:.2f}',
            textposition='outside'
        )
        
        return fig
    else:
        # Create static plot with Matplotlib
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set style
        if SEABORN_AVAILABLE:
            sns.set_style("whitegrid")
            palette = sns.color_palette("viridis", len(model_performance))
        else:
            palette = None
        
        # Create bar plot
        bars = ax.bar(
            model_performance["model_name"],
            model_performance[metric],
            color=palette
        )
        
        # Add model type as text on bars
        for i, (_, row) in enumerate(model_performance.iterrows()):
            ax.text(
                i,
                row[metric] / 2,
                row["model_type"],
                ha="center",
                va="center",
                color="white",
                fontweight="bold"
            )
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height * 1.01,
                f"{height:.2f}",
                ha="center",
                va="bottom",
                fontsize=9
            )
        
        # Set title and labels
        ax.set_title(title, fontsize=14, pad=20)
        ax.set_xlabel("Model", fontsize=12, labelpad=10)
        ax.set_ylabel(valid_metrics[metric], fontsize=12, labelpad=10)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha="right")
        
        # Adjust layout
        plt.tight_layout()
        
        return fig


def plot_benchmark_history(
    results: List[BenchmarkResult],
    model_id: Optional[str] = None,
    metric: str = "avg_tokens_per_second",
    figsize: Tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    days: Optional[int] = None,
    interactive: bool = False
) -> Union[Figure, Any]:
    """
    Plot the history of benchmark results over time for a specific model or all models.
    
    Args:
        results: List of benchmark results.
        model_id: Optional model ID to filter results.
        metric: The metric to plot (e.g., "avg_tokens_per_second", "avg_generation_time").
        figsize: Figure size as (width, height) in inches.
        title: Optional custom title for the plot.
        days: Optional number of days to include in the history.
        interactive: Whether to create an interactive plot using Plotly.
        
    Returns:
        Union[Figure, Any]: The matplotlib figure object or Plotly figure object.
        
    Raises:
        ImportError: If required visualization dependencies are not available.
        ValueError: If the specified metric is not valid.
    """
    if interactive and not PLOTLY_AVAILABLE:
        logger.warning("Plotly is not available. Falling back to static visualization.")
        interactive = False
    
    if not interactive and not check_visualization_dependencies():
        raise ImportError("Required visualization dependencies are not available")
    
    # Valid metrics
    valid_metrics = {
        "avg_tokens_per_second": "Average Tokens per Second",
        "avg_generation_time": "Average Generation Time (s)",
        "load_time_seconds": "Model Load Time (s)",
        "peak_memory_mb": "Peak Memory Usage (MB)",
        "perplexity": "Perplexity (lower is better)",
        "bleu_score": "BLEU Score (higher is better)",
        "response_length_ratio": "Response Length Ratio"
    }
    
    if metric not in valid_metrics:
        raise ValueError(f"Invalid metric: {metric}. Valid metrics are: {list(valid_metrics.keys())}")
    
    # Prepare data
    df = _prepare_benchmark_data(results, calculate_additional_metrics=True)
    
    # Skip if the metric is not available in the data
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' is not available in the benchmark results")
    
    # Filter by model if specified
    if model_id:
        df = df[df["model_id"] == model_id]
        if df.empty:
            raise ValueError(f"No benchmark results found for model: {model_id}")
    
    # Filter by date range if specified
    if days:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        df = df[df["timestamp"] >= cutoff_date]
    
    # Sort by timestamp
    df = df.sort_values(by="timestamp")
    
    # Set the title
    if not title:
        if model_id:
            model_name = df["model_name"].iloc[0] if not df.empty else model_id
            title = f"Benchmark History for {model_name}: {valid_metrics[metric]}"
        else:
            title = f"Benchmark History: {valid_metrics[metric]}"
    
    if interactive and PLOTLY_AVAILABLE:
        # Create interactive plot with Plotly
        fig = px.line(
            df,
            x="timestamp",
            y=metric,
            color="model_name",
            markers=True,
            title=title,
            labels={
                "timestamp": "Date",
                metric: valid_metrics[metric],
                "model_name": "Model"
            },
            height=figsize[1] * 100,
            width=figsize[0] * 100,
            hover_data=["model_type", "benchmark_id"]
        )
        
        # Update layout
        fig.update_layout(
            title_font_size=20,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            legend_title_font_size=14,
            hovermode="closest"
        )
        
        # Format x-axis as dates
        fig.update_xaxes(
            tickformat="%Y-%m-%d",
            tickangle=-45
        )
        
        return fig
    else:
        # Create static plot with Matplotlib
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set style
        if SEABORN_AVAILABLE:
            sns.set_style("whitegrid")
        
        # Group by model and plot lines
        for name, group in df.groupby("model_name"):
            ax.plot(
                group["timestamp"],
                group[metric],
                marker="o",
                linestyle="-",
                label=name
            )
        
        # Format x-axis as dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Set title and labels
        ax.set_title(title, fontsize=14, pad=20)
        ax.set_xlabel("Date", fontsize=12, labelpad=10)
        ax.set_ylabel(valid_metrics[metric], fontsize=12, labelpad=10)
        
        # Add legend
        ax.legend(loc="best")
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha="right")
        
        # Adjust layout
        plt.tight_layout()
        
        return fig


def plot_metric_correlation(
    results: List[BenchmarkResult],
    x_metric: str = "avg_generation_time",
    y_metric: str = "avg_tokens_per_second",
    figsize: Tuple[int, int] = (10, 8),
    title: Optional[str] = None
) -> Figure:
    """
    Plot the correlation between two metrics across all benchmark results.
    
    Args:
        results: List of benchmark results.
        x_metric: The metric for the x-axis.
        y_metric: The metric for the y-axis.
        figsize: Figure size as (width, height) in inches.
        title: Optional custom title for the plot.
        
    Returns:
        Figure: The matplotlib figure object.
        
    Raises:
        ImportError: If required visualization dependencies are not available.
        ValueError: If the specified metrics are not valid.
    """
    if not check_visualization_dependencies():
        raise ImportError("Required visualization dependencies are not available")
    
    # Valid metrics
    valid_metrics = {
        "avg_tokens_per_second": "Average Tokens per Second",
        "avg_generation_time": "Average Generation Time (s)",
        "load_time_seconds": "Model Load Time (s)",
        "peak_memory_mb": "Peak Memory Usage (MB)",
        "prompt_length": "Prompt Length (tokens)",
        "max_tokens": "Max Tokens"
    }
    
    if x_metric not in valid_metrics:
        raise ValueError(f"Invalid x_metric: {x_metric}. Valid metrics are: {list(valid_metrics.keys())}")
    
    if y_metric not in valid_metrics:
        raise ValueError(f"Invalid y_metric: {y_metric}. Valid metrics are: {list(valid_metrics.keys())}")
    
    # Prepare data
    df = _prepare_benchmark_data(results)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set style
    if SEABORN_AVAILABLE:
        sns.set_style("whitegrid")
        # Create scatter plot with regression line
        sns.regplot(
            x=x_metric,
            y=y_metric,
            data=df,
            scatter_kws={"alpha": 0.5},
            ax=ax
        )
        
        # Add color by model type
        scatter = sns.scatterplot(
            x=x_metric,
            y=y_metric,
            hue="model_type",
            data=df,
            ax=ax
        )
        
        # Move legend outside the plot
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    else:
        # Create simple scatter plot
        scatter = ax.scatter(
            df[x_metric],
            df[y_metric],
            alpha=0.5
        )
    
    # Set title and labels
    if title:
        ax.set_title(title, fontsize=14, pad=20)
    else:
        ax.set_title(f"Correlation: {valid_metrics[x_metric]} vs {valid_metrics[y_metric]}", fontsize=14, pad=20)
    
    ax.set_xlabel(valid_metrics[x_metric], fontsize=12, labelpad=10)
    ax.set_ylabel(valid_metrics[y_metric], fontsize=12, labelpad=10)
    
    # Add model names as tooltips (only works in interactive environments)
    try:
        for i, row in df.iterrows():
            ax.annotate(
                row["model_name"],
                (row[x_metric], row[y_metric]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                alpha=0.7
            )
    except Exception as e:
        logger.debug(f"Could not add annotations: {e}")
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def _get_color_for_model_type(model_type: str) -> str:
    """
    Get a color for a model type.
    
    Args:
        model_type: The model type.
        
    Returns:
        str: A CSS color string.
    """
    color_map = {
        "LLAMA": "#3498db",    # Blue
        "MISTRAL": "#2ecc71",  # Green
        "PHI": "#9b59b6",      # Purple
        "FALCON": "#e74c3c",   # Red
        "MPT": "#f39c12",      # Orange
        "GGUF": "#1abc9c",     # Turquoise
        "AWQ": "#d35400",      # Pumpkin
        "UNKNOWN": "#7f8c8d"   # Gray
    }
    
    return color_map.get(model_type, "#7f8c8d")


def _fig_to_base64(fig: Figure) -> str:
    """
    Convert a matplotlib figure to a base64-encoded string.
    
    Args:
        fig: The matplotlib figure.
        
    Returns:
        str: The base64-encoded string.
    """
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    return img_str


def plot_model_radar_chart(
    results: List[BenchmarkResult],
    model_ids: List[str],
    figsize: Tuple[int, int] = (10, 10),
    title: Optional[str] = None
) -> Figure:
    """
    Create a radar chart comparing multiple models across different metrics.
    
    Args:
        results: List of benchmark results.
        model_ids: List of model IDs to include in the comparison.
        figsize: Figure size as (width, height) in inches.
        title: Optional custom title for the plot.
        
    Returns:
        Figure: The matplotlib figure object.
        
    Raises:
        ImportError: If required visualization dependencies are not available.
        ValueError: If no results are found for the specified models.
    """
    if not check_visualization_dependencies():
        raise ImportError("Required visualization dependencies are not available")
    
    if not NUMPY_AVAILABLE:
        raise ImportError("NumPy is required for radar charts")
    
    # Prepare data
    df = _prepare_benchmark_data(results)
    
    # Filter by model IDs
    df = df[df["model_id"].isin(model_ids)]
    if df.empty:
        raise ValueError(f"No benchmark results found for the specified models: {model_ids}")
    
    # Group by model and calculate mean of metrics
    model_metrics = df.groupby("model_name").agg({
        "avg_tokens_per_second": "mean",
        "avg_generation_time": "mean",
        "load_time_seconds": "mean",
        "peak_memory_mb": "mean"
    }).reset_index()
    
    # Normalize metrics to 0-1 scale for radar chart
    metrics = ["avg_tokens_per_second", "avg_generation_time", "load_time_seconds", "peak_memory_mb"]
    
    # For generation time and load time, lower is better, so invert the normalization
    for metric in metrics:
        if metric in ["avg_generation_time", "load_time_seconds", "peak_memory_mb"]:
            max_val = model_metrics[metric].max()
            min_val = model_metrics[metric].min()
            if max_val > min_val:
                model_metrics[f"{metric}_norm"] = 1 - ((model_metrics[metric] - min_val) / (max_val - min_val))
            else:
                model_metrics[f"{metric}_norm"] = 1.0
        else:
            max_val = model_metrics[metric].max()
            min_val = model_metrics[metric].min()
            if max_val > min_val:
                model_metrics[f"{metric}_norm"] = (model_metrics[metric] - min_val) / (max_val - min_val)
            else:
                model_metrics[f"{metric}_norm"] = 1.0
    
    # Metrics for radar chart
    radar_metrics = [
        "avg_tokens_per_second_norm",
        "avg_generation_time_norm",
        "load_time_seconds_norm",
        "peak_memory_mb_norm"
    ]
    
    # Labels for radar chart
    labels = [
        "Tokens per Second",
        "Generation Speed",
        "Load Speed",
        "Memory Efficiency"
    ]
    
    # Number of metrics
    num_metrics = len(radar_metrics)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
    
    # Set style
    if SEABORN_AVAILABLE:
        sns.set_style("whitegrid")
        palette = sns.color_palette("viridis", len(model_metrics))
    else:
        palette = None
    
    # Compute angle for each metric
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    
    # Close the polygon
    angles += angles[:1]
    
    # Add labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    
    # Draw radar chart for each model
    for i, (_, row) in enumerate(model_metrics.iterrows()):
        values = [row[metric] for metric in radar_metrics]
        values += values[:1]  # Close the polygon
        
        color = palette[i] if palette else None
        
        ax.plot(angles, values, linewidth=2, label=row["model_name"], color=color)
        ax.fill(angles, values, alpha=0.1, color=color)
    
    # Set y-axis limits
    ax.set_ylim(0, 1)
    
    # Add legend
    ax.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))
    
    # Set title
    if title:
        ax.set_title(title, fontsize=14, pad=20)
    else:
        ax.set_title("Model Comparison Radar Chart", fontsize=14, pad=20)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def export_visualization(
    fig: Figure,
    filename: str,
    dpi: int = 300,
    format: Optional[str] = None,
    transparent: bool = False
) -> str:
    """
    Export a visualization to a file.
    
    Args:
        fig: The matplotlib figure object.
        filename: The filename to save the visualization to.
        dpi: The resolution in dots per inch.
        format: The file format (e.g., "png", "pdf", "svg").
        transparent: Whether to use a transparent background.
        
    Returns:
        str: The path to the saved file.
        
    Raises:
        ImportError: If matplotlib is not available.
        ValueError: If the file format is not supported.
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for exporting visualizations")
    
    # Get directory from filename
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save the figure
    fig.savefig(
        filename,
        dpi=dpi,
        format=format,
        bbox_inches="tight",
        transparent=transparent
    )
    
    logger.info(f"Visualization exported to {filename}")
    return filename


def generate_benchmark_report_html(
    results: List[BenchmarkResult],
    include_plots: bool = True,
    model_ids: Optional[List[str]] = None
) -> str:
    """
    Generate an HTML report of benchmark results with visualizations.
    
    Args:
        results: List of benchmark results.
        include_plots: Whether to include plots in the report.
        model_ids: Optional list of model IDs to include in the report.
        
    Returns:
        str: The HTML report as a string.
        
    Raises:
        ImportError: If required dependencies are not available.
    """
    # Filter results by model IDs if specified
    if model_ids:
        results = [r for r in results if r.model_id in model_ids]
    
    # Generate benchmark report data
    report_data = generate_benchmark_report(
        model_id=model_ids[0] if model_ids and len(model_ids) == 1 else None
    )
    
    # Start building HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Model Benchmark Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            .summary {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
            .model-card {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .model-header {{
                display: flex;
                justify-content: space-between;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            .model-name {{
                font-size: 1.4em;
                font-weight: bold;
                color: #2c3e50;
            }}
            .model-type {{
                background-color: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 0.9em;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .metric {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }}
            .metric-value {{
                font-size: 1.8em;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px 0;
            }}
            .metric-label {{
                font-size: 0.9em;
                color: #7f8c8d;
            }}
            .plots {{
                margin-top: 30px;
            }}
            .plot {{
                margin-bottom: 30px;
                text-align: center;
            }}
            .plot img {{
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #7f8c8d;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AI Model Benchmark Report</h1>
            <p>Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Number of models: {report_data["num_models"]}</p>
            <p>Number of benchmark results: {report_data["num_results"]}</p>
        </div>
    """
    
    # Add model cards
    html += "<h2>Model Performance</h2>"
    
    for model_id, model_data in report_data["models"].items():
        model_type_class = model_data["type"].lower()
        
        html += f"""
        <div class="model-card">
            <div class="model-header">
                <div class="model-name">{model_data["name"]}</div>
                <div class="model-type" style="background-color: {_get_color_for_model_type(model_data["type"])}">{model_data["type"]}</div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Average Tokens per Second</div>
                    <div class="metric-value">{model_data["avg_tokens_per_second"]:.2f}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Average Generation Time</div>
                    <div class="metric-value">{model_data["avg_generation_time_seconds"]:.2f}s</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Average Load Time</div>
                    <div class="metric-value">{model_data["avg_load_time_seconds"]:.2f}s</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Peak Memory Usage</div>
                    <div class="metric-value">{model_data["avg_peak_memory_mb"]:.2f} MB</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Number of Results</div>
                    <div class="metric-value">{model_data["num_results"]}</div>
                </div>
            </div>
        </div>
        """
    
    # Add plots if requested
    if include_plots and check_visualization_dependencies():
        html += """
        <div class="plots">
            <h2>Visualizations</h2>
        """
        
        try:
            # Model comparison plot
            fig = plot_model_comparison(results, metric="avg_tokens_per_second")
            plot_img = _fig_to_base64(fig)
            html += f"""
            <div class="plot">
                <h3>Model Comparison: Average Tokens per Second</h3>
                <img src="data:image/png;base64,{plot_img}" alt="Model Comparison">
            </div>
            """
            plt.close(fig)
            
            # Generation time comparison
            fig = plot_model_comparison(results, metric="avg_generation_time", sort_ascending=True)
            plot_img = _fig_to_base64(fig)
            html += f"""
            <div class="plot">
                <h3>Model Comparison: Average Generation Time</h3>
                <img src="data:image/png;base64,{plot_img}" alt="Generation Time Comparison">
            </div>
            """
            plt.close(fig)
            
            # Memory usage comparison
            fig = plot_model_comparison(results, metric="peak_memory_mb")
            plot_img = _fig_to_base64(fig)
            html += f"""
            <div class="plot">
                <h3>Model Comparison: Peak Memory Usage</h3>
                <img src="data:image/png;base64,{plot_img}" alt="Memory Usage Comparison">
            </div>
            """
            plt.close(fig)
            
            # Correlation plot
            fig = plot_metric_correlation(results, x_metric="avg_generation_time", y_metric="avg_tokens_per_second")
            plot_img = _fig_to_base64(fig)
            html += f"""
            <div class="plot">
                <h3>Correlation: Generation Time vs Tokens per Second</h3>
                <img src="data:image/png;base64,{plot_img}" alt="Metric Correlation">
            </div>
            """
            plt.close(fig)
            
            # If we have at least 2 models, add radar chart
            model_ids_list = list(report_data["models"].keys())
            if len(model_ids_list) >= 2:
                try:
                    fig = plot_model_radar_chart(results, model_ids_list[:5])  # Limit to 5 models for readability
                    plot_img = _fig_to_base64(fig)
                    html += f"""
                    <div class="plot">
                        <h3>Model Comparison: Radar Chart</h3>
                        <img src="data:image/png;base64,{plot_img}" alt="Model Radar Chart">
                    </div>
                    """
                    plt.close(fig)
                except Exception as e:
                    logger.warning(f"Could not generate radar chart: {e}")
        except Exception as e:
            logger.error(f"Error generating plots for HTML report: {e}")
        
        html += "</div>"  # Close plots div
    
    # Add footer
    html += """
        <div class="footer">
            <p>Generated by RebelSCRIBE Benchmark Visualization</p>
        </div>
    </body>
    </html>
    """
    
    return html


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Visualization Tool")
    parser.add_argument("--model", type=str, help="Model ID to visualize")
    parser.add_argument("--metric", type=str, default="avg_tokens_per_second", 
                        choices=["avg_tokens_per_second", "avg_generation_time", "load_time_seconds", "peak_memory_mb"],
                        help="Metric to visualize")
    parser.add_argument("--output", type=str, help="Output file for visualization")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--report-output", type=str, default="benchmark_report.html", help="Output file for HTML report")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_visualization_dependencies():
        print("Required visualization dependencies are not available.")
        print("Please install matplotlib, seaborn, and pandas.")
        sys.exit(1)
    
    # Get benchmark results
    results = get_benchmark_results(args.model)
    
    if not results:
        print("No benchmark results found.")
        sys.exit(1)
    
    print(f"Found {len(results)} benchmark results.")
    
    if args.report:
        print(f"Generating HTML report to {args.report_output}...")
        html_report = generate_benchmark_report_html(results)
        with open(args.report_output, "w") as f:
            f.write(html_report)
        print(f"HTML report saved to {args.report_output}")
    
    if args.output:
        print(f"Generating visualization of {args.metric} to {args.output}...")
        fig = plot_model_comparison(results, metric=args.metric)
        export_visualization(fig, args.output)
        print(f"Visualization saved to {args.output}")
