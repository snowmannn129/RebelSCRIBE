#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Training Monitoring and Visualization

This module provides tools for monitoring and visualizing model training progress.
It supports tracking metrics, generating visualizations, and providing callbacks
for UI integration.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import threading
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap

from src.utils.logging_utils import get_logger
from src.ai.progress_callbacks import ProgressCallback

logger = get_logger(__name__)


class TrainingMetrics:
    """
    Class for tracking and storing training metrics.
    
    This class provides methods for recording training metrics such as loss,
    learning rate, and evaluation metrics, and for retrieving the metrics
    for visualization.
    """
    
    def __init__(self):
        """Initialize the training metrics."""
        logger.info("Initializing training metrics")
        
        # Training metrics
        self.train_loss: List[float] = []
        self.train_perplexity: List[float] = []
        self.eval_loss: List[float] = []
        self.eval_perplexity: List[float] = []
        self.learning_rate: List[float] = []
        
        # Additional metrics
        self.bleu_scores: List[float] = []
        self.rouge_scores: Dict[str, List[float]] = {
            "rouge1": [],
            "rouge2": [],
            "rougeL": []
        }
        
        # Training progress
        self.epochs_completed: int = 0
        self.steps_completed: int = 0
        self.total_epochs: int = 0
        self.total_steps: int = 0
        
        # Timing information
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.epoch_times: List[float] = []
        self.step_times: List[float] = []
        
        # Training parameters
        self.parameters: Dict[str, Any] = {}
        
        # Metadata
        self.adapter_name: str = ""
        self.base_model: str = ""
        self.adapter_type: str = ""
        self.dataset_info: Dict[str, Any] = {}
    
    def start_training(self, total_epochs: int, total_steps: int, 
                      adapter_name: str, base_model: str, adapter_type: str,
                      parameters: Dict[str, Any], dataset_info: Dict[str, Any]):
        """
        Start tracking training progress.
        
        Args:
            total_epochs: Total number of epochs for training.
            total_steps: Total number of steps for training.
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            parameters: Training parameters.
            dataset_info: Information about the dataset.
        """
        logger.info(f"Starting training tracking for {adapter_name} on {base_model}")
        
        self.total_epochs = total_epochs
        self.total_steps = total_steps
        self.adapter_name = adapter_name
        self.base_model = base_model
        self.adapter_type = adapter_type
        self.parameters = parameters
        self.dataset_info = dataset_info
        
        self.start_time = time.time()
        
        # Reset metrics
        self.train_loss = []
        self.train_perplexity = []
        self.eval_loss = []
        self.eval_perplexity = []
        self.learning_rate = []
        self.bleu_scores = []
        self.rouge_scores = {
            "rouge1": [],
            "rouge2": [],
            "rougeL": []
        }
        self.epochs_completed = 0
        self.steps_completed = 0
        self.epoch_times = []
        self.step_times = []
    
    def end_training(self):
        """End tracking training progress."""
        logger.info(f"Ending training tracking for {self.adapter_name}")
        
        self.end_time = time.time()
    
    def update_step(self, step: int, loss: float, learning_rate: float, 
                   perplexity: Optional[float] = None):
        """
        Update metrics for a training step.
        
        Args:
            step: Current step number.
            loss: Training loss for the step.
            learning_rate: Learning rate for the step.
            perplexity: Perplexity for the step (optional).
        """
        self.steps_completed = step
        self.train_loss.append(loss)
        self.learning_rate.append(learning_rate)
        
        if perplexity is not None:
            self.train_perplexity.append(perplexity)
        
        # Record step time
        if self.start_time is not None:
            self.step_times.append(time.time() - self.start_time)
    
    def update_epoch(self, epoch: int, eval_loss: Optional[float] = None,
                    eval_perplexity: Optional[float] = None,
                    bleu_score: Optional[float] = None,
                    rouge_scores: Optional[Dict[str, float]] = None):
        """
        Update metrics for a training epoch.
        
        Args:
            epoch: Current epoch number.
            eval_loss: Evaluation loss for the epoch (optional).
            eval_perplexity: Evaluation perplexity for the epoch (optional).
            bleu_score: BLEU score for the epoch (optional).
            rouge_scores: ROUGE scores for the epoch (optional).
        """
        self.epochs_completed = epoch
        
        if eval_loss is not None:
            self.eval_loss.append(eval_loss)
        
        if eval_perplexity is not None:
            self.eval_perplexity.append(eval_perplexity)
        
        if bleu_score is not None:
            self.bleu_scores.append(bleu_score)
        
        if rouge_scores is not None:
            for key, value in rouge_scores.items():
                if key in self.rouge_scores:
                    self.rouge_scores[key].append(value)
        
        # Record epoch time
        if self.start_time is not None:
            self.epoch_times.append(time.time() - self.start_time)
    
    def get_progress(self) -> Tuple[float, float]:
        """
        Get the current training progress.
        
        Returns:
            A tuple of (epoch_progress, overall_progress) as percentages.
        """
        if self.total_epochs == 0:
            epoch_progress = 0.0
        else:
            epoch_progress = (self.epochs_completed / self.total_epochs) * 100.0
        
        if self.total_steps == 0:
            overall_progress = 0.0
        else:
            overall_progress = (self.steps_completed / self.total_steps) * 100.0
        
        return epoch_progress, overall_progress
    
    def get_estimated_time_remaining(self) -> float:
        """
        Get the estimated time remaining for training.
        
        Returns:
            Estimated time remaining in seconds.
        """
        if self.start_time is None or self.steps_completed == 0:
            return 0.0
        
        elapsed_time = time.time() - self.start_time
        steps_per_second = self.steps_completed / elapsed_time
        
        if steps_per_second == 0:
            return 0.0
        
        remaining_steps = self.total_steps - self.steps_completed
        estimated_time_remaining = remaining_steps / steps_per_second
        
        return estimated_time_remaining
    
    def get_elapsed_time(self) -> float:
        """
        Get the elapsed training time.
        
        Returns:
            Elapsed time in seconds.
        """
        if self.start_time is None:
            return 0.0
        
        if self.end_time is not None:
            return self.end_time - self.start_time
        
        return time.time() - self.start_time
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the training metrics.
        
        Returns:
            A dictionary containing the training metrics summary.
        """
        summary = {
            "adapter_name": self.adapter_name,
            "base_model": self.base_model,
            "adapter_type": self.adapter_type,
            "epochs_completed": self.epochs_completed,
            "total_epochs": self.total_epochs,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "elapsed_time": self.get_elapsed_time(),
            "parameters": self.parameters,
            "dataset_info": self.dataset_info
        }
        
        # Add metrics if available
        if self.train_loss:
            summary["final_train_loss"] = self.train_loss[-1]
            summary["min_train_loss"] = min(self.train_loss)
            summary["avg_train_loss"] = sum(self.train_loss) / len(self.train_loss)
        
        if self.eval_loss:
            summary["final_eval_loss"] = self.eval_loss[-1]
            summary["min_eval_loss"] = min(self.eval_loss)
            summary["avg_eval_loss"] = sum(self.eval_loss) / len(self.eval_loss)
        
        if self.train_perplexity:
            summary["final_train_perplexity"] = self.train_perplexity[-1]
            summary["min_train_perplexity"] = min(self.train_perplexity)
            summary["avg_train_perplexity"] = sum(self.train_perplexity) / len(self.train_perplexity)
        
        if self.eval_perplexity:
            summary["final_eval_perplexity"] = self.eval_perplexity[-1]
            summary["min_eval_perplexity"] = min(self.eval_perplexity)
            summary["avg_eval_perplexity"] = sum(self.eval_perplexity) / len(self.eval_perplexity)
        
        if self.bleu_scores:
            summary["final_bleu_score"] = self.bleu_scores[-1]
            summary["max_bleu_score"] = max(self.bleu_scores)
            summary["avg_bleu_score"] = sum(self.bleu_scores) / len(self.bleu_scores)
        
        for key, values in self.rouge_scores.items():
            if values:
                summary[f"final_{key}"] = values[-1]
                summary[f"max_{key}"] = max(values)
                summary[f"avg_{key}"] = sum(values) / len(values)
        
        return summary
    
    def save_metrics(self, output_dir: str) -> str:
        """
        Save the training metrics to a file.
        
        Args:
            output_dir: Directory to save the metrics to.
            
        Returns:
            Path to the saved metrics file.
        """
        logger.info(f"Saving training metrics to {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create metrics dictionary
        metrics = {
            "adapter_name": self.adapter_name,
            "base_model": self.base_model,
            "adapter_type": self.adapter_type,
            "epochs_completed": self.epochs_completed,
            "total_epochs": self.total_epochs,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "elapsed_time": self.get_elapsed_time(),
            "parameters": self.parameters,
            "dataset_info": self.dataset_info,
            "train_loss": self.train_loss,
            "train_perplexity": self.train_perplexity,
            "eval_loss": self.eval_loss,
            "eval_perplexity": self.eval_perplexity,
            "learning_rate": self.learning_rate,
            "bleu_scores": self.bleu_scores,
            "rouge_scores": self.rouge_scores,
            "epoch_times": self.epoch_times,
            "step_times": self.step_times
        }
        
        # Save metrics to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = os.path.join(output_dir, f"training_metrics_{timestamp}.json")
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            # Convert numpy values to Python types for JSON serialization
            def convert_to_python_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            json.dump(metrics, f, indent=2, default=convert_to_python_types)
        
        logger.info(f"Training metrics saved to {metrics_file}")
        
        return metrics_file
    
    @classmethod
    def load_metrics(cls, metrics_file: str) -> 'TrainingMetrics':
        """
        Load training metrics from a file.
        
        Args:
            metrics_file: Path to the metrics file.
            
        Returns:
            A TrainingMetrics object with the loaded metrics.
            
        Raises:
            FileNotFoundError: If the metrics file does not exist.
            ValueError: If the metrics file is invalid.
        """
        logger.info(f"Loading training metrics from {metrics_file}")
        
        if not os.path.exists(metrics_file):
            logger.error(f"Metrics file not found: {metrics_file}")
            raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
        
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics_data = json.load(f)
            
            metrics = cls()
            
            # Load metadata
            metrics.adapter_name = metrics_data.get("adapter_name", "")
            metrics.base_model = metrics_data.get("base_model", "")
            metrics.adapter_type = metrics_data.get("adapter_type", "")
            metrics.epochs_completed = metrics_data.get("epochs_completed", 0)
            metrics.total_epochs = metrics_data.get("total_epochs", 0)
            metrics.steps_completed = metrics_data.get("steps_completed", 0)
            metrics.total_steps = metrics_data.get("total_steps", 0)
            metrics.parameters = metrics_data.get("parameters", {})
            metrics.dataset_info = metrics_data.get("dataset_info", {})
            
            # Load metrics
            metrics.train_loss = metrics_data.get("train_loss", [])
            metrics.train_perplexity = metrics_data.get("train_perplexity", [])
            metrics.eval_loss = metrics_data.get("eval_loss", [])
            metrics.eval_perplexity = metrics_data.get("eval_perplexity", [])
            metrics.learning_rate = metrics_data.get("learning_rate", [])
            metrics.bleu_scores = metrics_data.get("bleu_scores", [])
            metrics.rouge_scores = metrics_data.get("rouge_scores", {
                "rouge1": [],
                "rouge2": [],
                "rougeL": []
            })
            metrics.epoch_times = metrics_data.get("epoch_times", [])
            metrics.step_times = metrics_data.get("step_times", [])
            
            # Set start and end times based on elapsed time
            elapsed_time = metrics_data.get("elapsed_time", 0.0)
            if elapsed_time > 0:
                metrics.start_time = time.time() - elapsed_time
                metrics.end_time = time.time()
            
            logger.info(f"Training metrics loaded successfully from {metrics_file}")
            
            return metrics
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid metrics file: {str(e)}")
            raise ValueError(f"Invalid metrics file: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading metrics: {str(e)}")
            raise ValueError(f"Error loading metrics: {str(e)}")


class TrainingVisualizer:
    """
    Class for visualizing training metrics.
    
    This class provides methods for generating visualizations of training
    metrics such as loss curves, learning rate schedules, and evaluation
    metrics.
    """
    
    def __init__(self, dark_mode: bool = False):
        """
        Initialize the training visualizer.
        
        Args:
            dark_mode: Whether to use dark mode for visualizations.
        """
        logger.info("Initializing training visualizer")
        
        self.dark_mode = dark_mode
        self._setup_style()
    
    def _setup_style(self):
        """Set up the visualization style."""
        if self.dark_mode:
            plt.style.use('dark_background')
            self.text_color = 'white'
            self.grid_color = '#555555'
            self.figure_facecolor = '#2D2D2D'
            self.axes_facecolor = '#383838'
            self.primary_color = '#1F77B4'
            self.secondary_color = '#FF7F0E'
            self.tertiary_color = '#2CA02C'
            self.quaternary_color = '#D62728'
        else:
            plt.style.use('default')
            self.text_color = 'black'
            self.grid_color = '#CCCCCC'
            self.figure_facecolor = 'white'
            self.axes_facecolor = '#F8F8F8'
            self.primary_color = '#1F77B4'
            self.secondary_color = '#FF7F0E'
            self.tertiary_color = '#2CA02C'
            self.quaternary_color = '#D62728'
    
    def set_dark_mode(self, dark_mode: bool):
        """
        Set dark mode for visualizations.
        
        Args:
            dark_mode: Whether to use dark mode.
        """
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            self._setup_style()
    
    def create_loss_plot(self, metrics: TrainingMetrics, 
                        figsize: Tuple[int, int] = (10, 6)) -> Figure:
        """
        Create a plot of training and evaluation loss.
        
        Args:
            metrics: Training metrics to visualize.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            A matplotlib Figure object.
        """
        logger.debug("Creating loss plot")
        
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.figure_facecolor)
        ax.set_facecolor(self.axes_facecolor)
        
        # Plot training loss
        if metrics.train_loss:
            train_steps = list(range(1, len(metrics.train_loss) + 1))
            ax.plot(train_steps, metrics.train_loss, label='Training Loss',
                   color=self.primary_color, linewidth=2)
        
        # Plot evaluation loss
        if metrics.eval_loss:
            # Calculate steps at which evaluation was performed
            eval_steps = []
            if metrics.total_steps > 0 and metrics.total_epochs > 0:
                steps_per_epoch = metrics.total_steps // metrics.total_epochs
                eval_steps = [(i + 1) * steps_per_epoch for i in range(len(metrics.eval_loss))]
            else:
                # Fallback if total_steps or total_epochs is not set
                eval_steps = [i * (len(metrics.train_loss) // len(metrics.eval_loss)) 
                             for i in range(1, len(metrics.eval_loss) + 1)]
            
            ax.plot(eval_steps, metrics.eval_loss, label='Evaluation Loss',
                   color=self.secondary_color, linewidth=2, marker='o')
        
        # Set labels and title
        ax.set_xlabel('Steps', color=self.text_color)
        ax.set_ylabel('Loss', color=self.text_color)
        ax.set_title(f'Training and Evaluation Loss - {metrics.adapter_name}',
                    color=self.text_color)
        
        # Set grid
        ax.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        
        # Set legend
        ax.legend(facecolor=self.axes_facecolor, edgecolor=self.grid_color,
                 labelcolor=self.text_color)
        
        # Set tick colors
        ax.tick_params(colors=self.text_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.grid_color)
        
        fig.tight_layout()
        
        return fig
    
    def create_perplexity_plot(self, metrics: TrainingMetrics,
                              figsize: Tuple[int, int] = (10, 6)) -> Optional[Figure]:
        """
        Create a plot of training and evaluation perplexity.
        
        Args:
            metrics: Training metrics to visualize.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            A matplotlib Figure object, or None if no perplexity data is available.
        """
        logger.debug("Creating perplexity plot")
        
        # Check if perplexity data is available
        if not metrics.train_perplexity and not metrics.eval_perplexity:
            logger.warning("No perplexity data available for visualization")
            return None
        
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.figure_facecolor)
        ax.set_facecolor(self.axes_facecolor)
        
        # Plot training perplexity
        if metrics.train_perplexity:
            train_steps = list(range(1, len(metrics.train_perplexity) + 1))
            ax.plot(train_steps, metrics.train_perplexity, label='Training Perplexity',
                   color=self.primary_color, linewidth=2)
        
        # Plot evaluation perplexity
        if metrics.eval_perplexity:
            # Calculate steps at which evaluation was performed
            eval_steps = []
            if metrics.total_steps > 0 and metrics.total_epochs > 0:
                steps_per_epoch = metrics.total_steps // metrics.total_epochs
                eval_steps = [(i + 1) * steps_per_epoch for i in range(len(metrics.eval_perplexity))]
            else:
                # Fallback if total_steps or total_epochs is not set
                eval_steps = [i * (len(metrics.train_perplexity) // len(metrics.eval_perplexity)) 
                             for i in range(1, len(metrics.eval_perplexity) + 1)]
            
            ax.plot(eval_steps, metrics.eval_perplexity, label='Evaluation Perplexity',
                   color=self.secondary_color, linewidth=2, marker='o')
        
        # Set labels and title
        ax.set_xlabel('Steps', color=self.text_color)
        ax.set_ylabel('Perplexity', color=self.text_color)
        ax.set_title(f'Training and Evaluation Perplexity - {metrics.adapter_name}',
                    color=self.text_color)
        
        # Set grid
        ax.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        
        # Set legend
        ax.legend(facecolor=self.axes_facecolor, edgecolor=self.grid_color,
                 labelcolor=self.text_color)
        
        # Set tick colors
        ax.tick_params(colors=self.text_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.grid_color)
        
        # Use log scale for perplexity
        ax.set_yscale('log')
        
        fig.tight_layout()
        
        return fig
    
    def create_learning_rate_plot(self, metrics: TrainingMetrics,
                                 figsize: Tuple[int, int] = (10, 6)) -> Optional[Figure]:
        """
        Create a plot of the learning rate schedule.
        
        Args:
            metrics: Training metrics to visualize.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            A matplotlib Figure object, or None if no learning rate data is available.
        """
        logger.debug("Creating learning rate plot")
        
        # Check if learning rate data is available
        if not metrics.learning_rate:
            logger.warning("No learning rate data available for visualization")
            return None
        
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.figure_facecolor)
        ax.set_facecolor(self.axes_facecolor)
        
        # Plot learning rate
        steps = list(range(1, len(metrics.learning_rate) + 1))
        ax.plot(steps, metrics.learning_rate, color=self.tertiary_color, linewidth=2)
        
        # Set labels and title
        ax.set_xlabel('Steps', color=self.text_color)
        ax.set_ylabel('Learning Rate', color=self.text_color)
        ax.set_title(f'Learning Rate Schedule - {metrics.adapter_name}',
                    color=self.text_color)
        
        # Set grid
        ax.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        
        # Set tick colors
        ax.tick_params(colors=self.text_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.grid_color)
        
        # Use scientific notation for y-axis
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        
        fig.tight_layout()
        
        return fig
    
    def create_bleu_rouge_plot(self, metrics: TrainingMetrics,
                              figsize: Tuple[int, int] = (10, 6)) -> Optional[Figure]:
        """
        Create a plot of BLEU and ROUGE scores.
        
        Args:
            metrics: Training metrics to visualize.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            A matplotlib Figure object, or None if no BLEU or ROUGE data is available.
        """
        logger.debug("Creating BLEU and ROUGE plot")
        
        # Check if BLEU or ROUGE data is available
        has_bleu = bool(metrics.bleu_scores)
        has_rouge = any(bool(values) for values in metrics.rouge_scores.values())
        
        if not has_bleu and not has_rouge:
            logger.warning("No BLEU or ROUGE data available for visualization")
            return None
        
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.figure_facecolor)
        ax.set_facecolor(self.axes_facecolor)
        
        # Plot BLEU scores
        if has_bleu:
            epochs = list(range(1, len(metrics.bleu_scores) + 1))
            ax.plot(epochs, metrics.bleu_scores, label='BLEU Score',
                   color=self.primary_color, linewidth=2, marker='o')
        
        # Plot ROUGE scores
        colors = [self.secondary_color, self.tertiary_color, self.quaternary_color]
        for i, (key, values) in enumerate(metrics.rouge_scores.items()):
            if values:
                epochs = list(range(1, len(values) + 1))
                ax.plot(epochs, values, label=f'{key.upper()} Score',
                       color=colors[i % len(colors)], linewidth=2, marker='s')
        
        # Set labels and title
        ax.set_xlabel('Epochs', color=self.text_color)
        ax.set_ylabel('Score', color=self.text_color)
        ax.set_title(f'BLEU and ROUGE Scores - {metrics.adapter_name}',
                    color=self.text_color)
        
        # Set grid
        ax.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        
        # Set legend
        ax.legend(facecolor=self.axes_facecolor, edgecolor=self.grid_color,
                 labelcolor=self.text_color)
        
        # Set tick colors
        ax.tick_params(colors=self.text_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.grid_color)
        
        # Set y-axis limits
        ax.set_ylim(0, 1.0)
        
        fig.tight_layout()
        
        return fig
    
    def create_training_progress_plot(self, metrics: TrainingMetrics,
                                     figsize: Tuple[int, int] = (10, 6)) -> Figure:
        """
        Create a plot of training progress over time.
        
        Args:
            metrics: Training metrics to visualize.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            A matplotlib Figure object.
        """
        logger.debug("Creating training progress plot")
        
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.figure_facecolor)
        ax.set_facecolor(self.axes_facecolor)
        
        # Plot steps completed over time
        if metrics.step_times:
            ax.plot(metrics.step_times, list(range(1, len(metrics.step_times) + 1)),
                   color=self.primary_color, linewidth=2, label='Steps')
        
        # Plot epochs completed over time
        if metrics.epoch_times:
            # Normalize epoch times to the same scale as step times
            if metrics.total_steps > 0 and metrics.total_epochs > 0:
                steps_per_epoch = metrics.total_steps // metrics.total_epochs
                normalized_epochs = [epoch * steps_per_epoch for epoch in range(1, len(metrics.epoch_times) + 1)]
                ax.plot(metrics.epoch_times, normalized_epochs,
                       color=self.secondary_color, linewidth=2, marker='o', label='Epochs')
            else:
                ax.plot(metrics.epoch_times, list(range(1, len(metrics.epoch_times) + 1)),
                       color=self.secondary_color, linewidth=2, marker='o', label='Epochs')
        
        # Set labels and title
        ax.set_xlabel('Time (seconds)', color=self.text_color)
        ax.set_ylabel('Progress', color=self.text_color)
        ax.set_title(f'Training Progress - {metrics.adapter_name}',
                    color=self.text_color)
        
        # Set grid
        ax.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        
        # Set legend
        ax.legend(facecolor=self.axes_facecolor, edgecolor=self.grid_color,
                 labelcolor=self.text_color)
        
        # Set tick colors
        ax.tick_params(colors=self.text_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.grid_color)
        
        fig.tight_layout()
        
        return fig
    
    def create_metrics_summary_plot(self, metrics: TrainingMetrics,
                                   figsize: Tuple[int, int] = (10, 6)) -> Figure:
        """
        Create a summary plot of training metrics.
        
        Args:
            metrics: Training metrics to visualize.
            figsize: Figure size (width, height) in inches.
            
        Returns:
            A matplotlib Figure object.
        """
        logger.debug("Creating metrics summary plot")
        
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.figure_facecolor)
        ax.set_facecolor(self.axes_facecolor)
        
        # Get metrics summary
        summary = metrics.get_metrics_summary()
        
        # Create a bar chart of key metrics
        metrics_to_plot = []
        values_to_plot = []
        
        # Add loss metrics
        if "min_train_loss" in summary:
            metrics_to_plot.append("Min Train Loss")
            values_to_plot.append(summary["min_train_loss"])
        
        if "min_eval_loss" in summary:
            metrics_to_plot.append("Min Eval Loss")
            values_to_plot.append(summary["min_eval_loss"])
        
        # Add perplexity metrics
        if "min_train_perplexity" in summary:
            metrics_to_plot.append("Min Train PPL")
            values_to_plot.append(summary["min_train_perplexity"])
        
        if "min_eval_perplexity" in summary:
            metrics_to_plot.append("Min Eval PPL")
            values_to_plot.append(summary["min_eval_perplexity"])
        
        # Add BLEU and ROUGE metrics
        if "max_bleu_score" in summary:
            metrics_to_plot.append("Max BLEU")
            values_to_plot.append(summary["max_bleu_score"])
        
        for key in ["rouge1", "rouge2", "rougeL"]:
            if f"max_{key}" in summary:
                metrics_to_plot.append(f"Max {key.upper()}")
                values_to_plot.append(summary[f"max_{key}"])
        
        # Plot the metrics
        if metrics_to_plot and values_to_plot:
            # Use different colors for different metric types
            colors = []
            for metric in metrics_to_plot:
                if "Loss" in metric:
                    colors.append(self.primary_color)
                elif "PPL" in metric:
                    colors.append(self.secondary_color)
                elif "BLEU" in metric:
                    colors.append(self.tertiary_color)
                else:
                    colors.append(self.quaternary_color)
            
            ax.bar(metrics_to_plot, values_to_plot, color=colors)
            
            # Set labels and title
            ax.set_xlabel('Metric', color=self.text_color)
            ax.set_ylabel('Value', color=self.text_color)
            ax.set_title(f'Training Metrics Summary - {metrics.adapter_name}',
                        color=self.text_color)
            
            # Set tick colors
            ax.tick_params(colors=self.text_color)
            for spine in ax.spines.values():
                spine.set_edgecolor(self.grid_color)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
        else:
            # If no metrics to plot, show a message
            ax.text(0.5, 0.5, "No metrics available for summary",
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, color=self.text_color, fontsize=12)
        
        fig.tight_layout()
        
        return fig
    
    def save_visualizations(self, metrics: TrainingMetrics, output_dir: str) -> Dict[str, str]:
        """
        Save all visualizations to files.
        
        Args:
            metrics: Training metrics to visualize.
            output_dir: Directory to save the visualizations to.
            
        Returns:
            A dictionary mapping visualization names to file paths.
        """
        logger.info(f"Saving visualizations to {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Dictionary to store file paths
        visualization_files = {}
        
        # Save loss plot
        loss_plot = self.create_loss_plot(metrics)
        loss_plot_path = os.path.join(output_dir, f"loss_plot_{timestamp}.png")
        loss_plot.savefig(loss_plot_path, dpi=300, bbox_inches='tight')
        plt.close(loss_plot)
        visualization_files["loss_plot"] = loss_plot_path
        
        # Save perplexity plot if available
        perplexity_plot = self.create_perplexity_plot(metrics)
        if perplexity_plot is not None:
            perplexity_plot_path = os.path.join(output_dir, f"perplexity_plot_{timestamp}.png")
            perplexity_plot.savefig(perplexity_plot_path, dpi=300, bbox_inches='tight')
            plt.close(perplexity_plot)
            visualization_files["perplexity_plot"] = perplexity_plot_path
        
        # Save learning rate plot if available
        learning_rate_plot = self.create_learning_rate_plot(metrics)
        if learning_rate_plot is not None:
            learning_rate_plot_path = os.path.join(output_dir, f"learning_rate_plot_{timestamp}.png")
            learning_rate_plot.savefig(learning_rate_plot_path, dpi=300, bbox_inches='tight')
            plt.close(learning_rate_plot)
            visualization_files["learning_rate_plot"] = learning_rate_plot_path
        
        # Save BLEU and ROUGE plot if available
        bleu_rouge_plot = self.create_bleu_rouge_plot(metrics)
        if bleu_rouge_plot is not None:
            bleu_rouge_plot_path = os.path.join(output_dir, f"bleu_rouge_plot_{timestamp}.png")
            bleu_rouge_plot.savefig(bleu_rouge_plot_path, dpi=300, bbox_inches='tight')
            plt.close(bleu_rouge_plot)
            visualization_files["bleu_rouge_plot"] = bleu_rouge_plot_path
        
        # Save training progress plot
        progress_plot = self.create_training_progress_plot(metrics)
        progress_plot_path = os.path.join(output_dir, f"progress_plot_{timestamp}.png")
        progress_plot.savefig(progress_plot_path, dpi=300, bbox_inches='tight')
        plt.close(progress_plot)
        visualization_files["progress_plot"] = progress_plot_path
        
        # Save metrics summary plot
        summary_plot = self.create_metrics_summary_plot(metrics)
        summary_plot_path = os.path.join(output_dir, f"summary_plot_{timestamp}.png")
        summary_plot.savefig(summary_plot_path, dpi=300, bbox_inches='tight')
        plt.close(summary_plot)
        visualization_files["summary_plot"] = summary_plot_path
        
        logger.info(f"Saved {len(visualization_files)} visualizations to {output_dir}")
        
        return visualization_files
    
    def create_html_report(self, metrics: TrainingMetrics, visualization_files: Dict[str, str],
                          output_dir: str) -> str:
        """
        Create an HTML report of the training results.
        
        Args:
            metrics: Training metrics to include in the report.
            visualization_files: Dictionary mapping visualization names to file paths.
            output_dir: Directory to save the report to.
            
        Returns:
            Path to the saved HTML report.
        """
        logger.info(f"Creating HTML report in {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get metrics summary
        summary = metrics.get_metrics_summary()
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Training Report - {metrics.adapter_name}</title>
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
                .container {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                }}
                .metrics-container {{
                    flex: 1;
                    min-width: 300px;
                }}
                .visualization-container {{
                    flex: 2;
                    min-width: 600px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .visualization {{
                    margin-bottom: 30px;
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <h1>Training Report - {metrics.adapter_name}</h1>
            <p>
                <strong>Base Model:</strong> {metrics.base_model}<br>
                <strong>Adapter Type:</strong> {metrics.adapter_type}<br>
                <strong>Training Completed:</strong> {datetime.fromtimestamp(metrics.end_time or time.time()).strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Training Duration:</strong> {metrics.get_elapsed_time():.2f} seconds
            </p>
            
            <div class="container">
                <div class="metrics-container">
                    <h2>Training Parameters</h2>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
        """
        
        # Add training parameters
        for key, value in metrics.parameters.items():
            html_content += f"""
                        <tr>
                            <td>{key}</td>
                            <td>{value}</td>
                        </tr>
            """
        
        html_content += f"""
                    </table>
                    
                    <h2>Dataset Information</h2>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
        """
        
        # Add dataset information
        for key, value in metrics.dataset_info.items():
            html_content += f"""
                        <tr>
                            <td>{key}</td>
                            <td>{value}</td>
                        </tr>
            """
        
        html_content += f"""
                    </table>
                    
                    <h2>Training Metrics</h2>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
        """
        
        # Add training metrics
        metrics_to_include = [
            ("Epochs Completed", metrics.epochs_completed),
            ("Total Epochs", metrics.total_epochs),
            ("Steps Completed", metrics.steps_completed),
            ("Total Steps", metrics.total_steps)
        ]
        
        # Add additional metrics from summary
        for key, value in summary.items():
            if key not in ["adapter_name", "base_model", "adapter_type", "epochs_completed", 
                          "total_epochs", "steps_completed", "total_steps", "elapsed_time",
                          "parameters", "dataset_info"]:
                metrics_to_include.append((key, value))
        
        for name, value in metrics_to_include:
            # Format the name for display
            display_name = name.replace("_", " ").title()
            
            # Format the value based on type
            if isinstance(value, float):
                display_value = f"{value:.4f}"
            else:
                display_value = str(value)
            
            html_content += f"""
                        <tr>
                            <td>{display_name}</td>
                            <td>{display_value}</td>
                        </tr>
            """
        
        html_content += f"""
                    </table>
                </div>
                
                <div class="visualization-container">
                    <h2>Visualizations</h2>
        """
        
        # Add visualizations
        visualization_titles = {
            "loss_plot": "Training and Evaluation Loss",
            "perplexity_plot": "Training and Evaluation Perplexity",
            "learning_rate_plot": "Learning Rate Schedule",
            "bleu_rouge_plot": "BLEU and ROUGE Scores",
            "progress_plot": "Training Progress",
            "summary_plot": "Metrics Summary"
        }
        
        for name, path in visualization_files.items():
            if os.path.exists(path):
                # Get the filename from the path
                filename = os.path.basename(path)
                
                # Get the title for the visualization
                title = visualization_titles.get(name, name.replace("_", " ").title())
                
                html_content += f"""
                    <div class="visualization">
                        <h3>{title}</h3>
                        <img src="{filename}" alt="{title}">
                    </div>
                """
        
        html_content += f"""
                </div>
            </div>
            
            <div class="footer">
                <p>Generated by RebelSCRIBE Training Monitor on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        # Save HTML report
        report_path = os.path.join(output_dir, f"training_report_{timestamp}.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy visualization files to the output directory
        for name, path in visualization_files.items():
            if os.path.exists(path):
                # Get the filename from the path
                filename = os.path.basename(path)
                
                # Copy the file to the output directory
                try:
                    import shutil
                    shutil.copy2(path, os.path.join(output_dir, filename))
                except (PermissionError, OSError) as e:
                    # If we can't copy the file, log a warning but continue
                    logger.warning(f"Could not copy visualization file {path}: {str(e)}")
        
        logger.info(f"HTML report saved to {report_path}")
        
        return report_path


class TrainingMonitor:
    """
    Class for monitoring and visualizing model training.
    
    This class provides methods for tracking training progress, visualizing
    training metrics, and generating reports. It also provides callbacks for
    updating the UI during training.
    """
    
    def __init__(self, callback: Optional[ProgressCallback] = None):
        """
        Initialize the training monitor.
        
        Args:
            callback: Callback for updating the UI during training.
        """
        logger.info("Initializing training monitor")
        
        self.metrics = TrainingMetrics()
        self.visualizer = TrainingVisualizer()
        self.callback = callback
        
        self._training_thread = None
        self._stop_event = threading.Event()
    
    def set_callback(self, callback: ProgressCallback):
        """
        Set the progress callback.
        
        Args:
            callback: Callback for updating the UI during training.
        """
        self.callback = callback
    
    def set_dark_mode(self, dark_mode: bool):
        """
        Set dark mode for visualizations.
        
        Args:
            dark_mode: Whether to use dark mode.
        """
        self.visualizer.set_dark_mode(dark_mode)
    
    def start_training(self, total_epochs: int, total_steps: int, 
                      adapter_name: str, base_model: str, adapter_type: str,
                      parameters: Dict[str, Any], dataset_info: Dict[str, Any]):
        """
        Start tracking training progress.
        
        Args:
            total_epochs: Total number of epochs for training.
            total_steps: Total number of steps for training.
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            parameters: Training parameters.
            dataset_info: Information about the dataset.
        """
        logger.info(f"Starting training monitoring for {adapter_name} on {base_model}")
        
        # Reset stop event
        self._stop_event.clear()
        
        # Start tracking metrics
        self.metrics.start_training(
            total_epochs=total_epochs,
            total_steps=total_steps,
            adapter_name=adapter_name,
            base_model=base_model,
            adapter_type=adapter_type,
            parameters=parameters,
            dataset_info=dataset_info
        )
        
        # Start progress update thread
        self._start_progress_update_thread()
        
        # Notify callback
        if self.callback:
            self.callback.on_training_start(
                adapter_name=adapter_name,
                base_model=base_model,
                adapter_type=adapter_type,
                total_epochs=total_epochs,
                total_steps=total_steps
            )
    
    def end_training(self):
        """End tracking training progress."""
        logger.info(f"Ending training monitoring for {self.metrics.adapter_name}")
        
        # Stop progress update thread
        self._stop_event.set()
        if self._training_thread is not None:
            self._training_thread.join()
            self._training_thread = None
        
        # End tracking metrics
        self.metrics.end_training()
        
        # Notify callback
        if self.callback:
            self.callback.on_training_end(
                adapter_name=self.metrics.adapter_name,
                base_model=self.metrics.base_model,
                adapter_type=self.metrics.adapter_type,
                elapsed_time=self.metrics.get_elapsed_time()
            )
    
    def update_step(self, step: int, loss: float, learning_rate: float, 
                   perplexity: Optional[float] = None):
        """
        Update metrics for a training step.
        
        Args:
            step: Current step number.
            loss: Training loss for the step.
            learning_rate: Learning rate for the step.
            perplexity: Perplexity for the step (optional).
        """
        # Update metrics
        self.metrics.update_step(
            step=step,
            loss=loss,
            learning_rate=learning_rate,
            perplexity=perplexity
        )
        
        # Notify callback
        if self.callback:
            epoch_progress, overall_progress = self.metrics.get_progress()
            estimated_time = self.metrics.get_estimated_time_remaining()
            
            self.callback.on_step_complete(
                step=step,
                loss=loss,
                learning_rate=learning_rate,
                perplexity=perplexity,
                progress=overall_progress,
                estimated_time_remaining=estimated_time
            )
    
    def update_epoch(self, epoch: int, eval_loss: Optional[float] = None,
                    eval_perplexity: Optional[float] = None,
                    bleu_score: Optional[float] = None,
                    rouge_scores: Optional[Dict[str, float]] = None):
        """
        Update metrics for a training epoch.
        
        Args:
            epoch: Current epoch number.
            eval_loss: Evaluation loss for the epoch (optional).
            eval_perplexity: Evaluation perplexity for the epoch (optional).
            bleu_score: BLEU score for the epoch (optional).
            rouge_scores: ROUGE scores for the epoch (optional).
        """
        # Update metrics
        self.metrics.update_epoch(
            epoch=epoch,
            eval_loss=eval_loss,
            eval_perplexity=eval_perplexity,
            bleu_score=bleu_score,
            rouge_scores=rouge_scores
        )
        
        # Notify callback
        if self.callback:
            epoch_progress, overall_progress = self.metrics.get_progress()
            estimated_time = self.metrics.get_estimated_time_remaining()
            
            self.callback.on_epoch_complete(
                epoch=epoch,
                eval_loss=eval_loss,
                eval_perplexity=eval_perplexity,
                bleu_score=bleu_score,
                rouge_scores=rouge_scores,
                progress=epoch_progress,
                estimated_time_remaining=estimated_time
            )
    
    def _start_progress_update_thread(self):
        """Start a thread to periodically update progress."""
        if self._training_thread is not None:
            return
        
        def update_progress():
            while not self._stop_event.is_set():
                if self.callback:
                    epoch_progress, overall_progress = self.metrics.get_progress()
                    estimated_time = self.metrics.get_estimated_time_remaining()
                    
                    self.callback.on_progress_update(
                        progress=overall_progress,
                        estimated_time_remaining=estimated_time
                    )
                
                # Sleep for a short time
                time.sleep(0.5)
        
        self._training_thread = threading.Thread(target=update_progress)
        self._training_thread.daemon = True
        self._training_thread.start()
    
    def get_current_visualizations(self) -> Dict[str, Figure]:
        """
        Get the current visualizations.
        
        Returns:
            A dictionary mapping visualization names to matplotlib Figure objects.
        """
        visualizations = {}
        
        # Add loss plot
        visualizations["loss_plot"] = self.visualizer.create_loss_plot(self.metrics)
        
        # Add perplexity plot if available
        perplexity_plot = self.visualizer.create_perplexity_plot(self.metrics)
        if perplexity_plot is not None:
            visualizations["perplexity_plot"] = perplexity_plot
        
        # Add learning rate plot if available
        learning_rate_plot = self.visualizer.create_learning_rate_plot(self.metrics)
        if learning_rate_plot is not None:
            visualizations["learning_rate_plot"] = learning_rate_plot
        
        # Add BLEU and ROUGE plot if available
        bleu_rouge_plot = self.visualizer.create_bleu_rouge_plot(self.metrics)
        if bleu_rouge_plot is not None:
            visualizations["bleu_rouge_plot"] = bleu_rouge_plot
        
        # Add training progress plot
        visualizations["progress_plot"] = self.visualizer.create_training_progress_plot(self.metrics)
        
        # Add metrics summary plot
        visualizations["summary_plot"] = self.visualizer.create_metrics_summary_plot(self.metrics)
        
        return visualizations
    
    def save_results(self, output_dir: str) -> Dict[str, str]:
        """
        Save training results to files.
        
        Args:
            output_dir: Directory to save the results to.
            
        Returns:
            A dictionary mapping result types to file paths.
        """
        logger.info(f"Saving training results to {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create subdirectories
        metrics_dir = os.path.join(output_dir, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        visualizations_dir = os.path.join(output_dir, "visualizations")
        os.makedirs(visualizations_dir, exist_ok=True)
        
        reports_dir = os.path.join(output_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Save metrics
        metrics_file = self.metrics.save_metrics(metrics_dir)
        
        # Save visualizations
        visualization_files = self.visualizer.save_visualizations(self.metrics, visualizations_dir)
        
        # Create HTML report
        report_file = self.visualizer.create_html_report(
            self.metrics, visualization_files, reports_dir
        )
        
        # Return file paths
        result_files = {
            "metrics": metrics_file,
            "report": report_file
        }
        result_files.update({f"visualization_{k}": v for k, v in visualization_files.items()})
        
        return result_files
    
    def load_results(self, metrics_file: str) -> Dict[str, Any]:
        """
        Load training results from a metrics file.
        
        Args:
            metrics_file: Path to the metrics file.
            
        Returns:
            A dictionary containing the loaded results.
        """
        logger.info(f"Loading training results from {metrics_file}")
        
        # Load metrics
        self.metrics = TrainingMetrics.load_metrics(metrics_file)
        
        # Get visualizations
        visualizations = self.get_current_visualizations()
        
        # Return results
        return {
            "metrics": self.metrics,
            "visualizations": visualizations,
            "summary": self.metrics.get_metrics_summary()
        }
