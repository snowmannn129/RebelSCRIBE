#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Training Visualization Dialog

This module implements a dialog for visualizing model training progress and results.
It provides real-time monitoring of training metrics and visualization of results.
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QProgressBar, QRadioButton, QButtonGroup, QScrollArea,
    QSplitter, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QThread, pyqtSlot, QTimer, QObject
from PyQt6.QtGui import QFont, QIcon, QPixmap

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.training_monitor import TrainingMonitor, TrainingMetrics
from src.ai.progress_callbacks import ProgressCallback

logger = get_logger(__name__)
config = ConfigManager()


class MatplotlibCanvas(FigureCanvas):
    """Matplotlib canvas for embedding plots in PyQt widgets."""
    
    def __init__(self, figure=None, parent=None, width=5, height=4, dpi=100):
        """
        Initialize the canvas.
        
        Args:
            figure: The matplotlib figure to display.
            parent: The parent widget.
            width: The width of the figure in inches.
            height: The height of the figure in inches.
            dpi: The resolution of the figure in dots per inch.
        """
        if figure is None:
            self.figure = Figure(figsize=(width, height), dpi=dpi)
            self.axes = self.figure.add_subplot(111)
        else:
            self.figure = figure
            self.axes = self.figure.axes[0] if self.figure.axes else self.figure.add_subplot(111)
        
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()
    
    def update_figure(self, figure):
        """
        Update the displayed figure.
        
        Args:
            figure: The new matplotlib figure to display.
        """
        self.figure = figure
        self.axes = self.figure.axes[0] if self.figure.axes else self.figure.add_subplot(111)
        self.draw()


class TrainingProgressCallback(QObject):
    """Callback for updating the UI during training."""
    
    # Define signals for UI updates
    training_started = pyqtSignal(str, str, str, int, int)
    training_ended = pyqtSignal(str, str, str, float)
    step_completed = pyqtSignal(int, float, float, object, float, float)
    epoch_completed = pyqtSignal(int, object, object, object, object, float, float)
    progress_updated = pyqtSignal(float, float)
    
    def __init__(self):
        """Initialize the callback."""
        super().__init__()
    
    def __call__(self, progress_info: 'ProgressInfo') -> None:
        """
        Called when progress is updated.
        
        Args:
            progress_info: The progress information.
        """
        # This method makes the class callable, conforming to the ProgressCallback type
        # We don't need to implement anything here as we're using signals for UI updates
        pass
    
    def on_training_start(self, adapter_name: str, base_model: str, adapter_type: str,
                         total_epochs: int, total_steps: int):
        """
        Called when training starts.
        
        Args:
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            total_epochs: Total number of epochs for training.
            total_steps: Total number of steps for training.
        """
        self.training_started.emit(adapter_name, base_model, adapter_type, total_epochs, total_steps)
    
    def on_training_end(self, adapter_name: str, base_model: str, adapter_type: str,
                       elapsed_time: float):
        """
        Called when training ends.
        
        Args:
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            elapsed_time: Total training time in seconds.
        """
        self.training_ended.emit(adapter_name, base_model, adapter_type, elapsed_time)
    
    def on_step_complete(self, step: int, loss: float, learning_rate: float,
                        perplexity: Optional[float], progress: float,
                        estimated_time_remaining: float):
        """
        Called when a training step is completed.
        
        Args:
            step: Current step number.
            loss: Training loss for the step.
            learning_rate: Learning rate for the step.
            perplexity: Perplexity for the step (optional).
            progress: Overall progress as a percentage.
            estimated_time_remaining: Estimated time remaining in seconds.
        """
        self.step_completed.emit(step, loss, learning_rate, perplexity, progress, estimated_time_remaining)
    
    def on_epoch_complete(self, epoch: int, eval_loss: Optional[float],
                         eval_perplexity: Optional[float], bleu_score: Optional[float],
                         rouge_scores: Optional[Dict[str, float]], progress: float,
                         estimated_time_remaining: float):
        """
        Called when a training epoch is completed.
        
        Args:
            epoch: Current epoch number.
            eval_loss: Evaluation loss for the epoch (optional).
            eval_perplexity: Evaluation perplexity for the epoch (optional).
            bleu_score: BLEU score for the epoch (optional).
            rouge_scores: ROUGE scores for the epoch (optional).
            progress: Epoch progress as a percentage.
            estimated_time_remaining: Estimated time remaining in seconds.
        """
        self.epoch_completed.emit(epoch, eval_loss, eval_perplexity, bleu_score, rouge_scores,
                                 progress, estimated_time_remaining)
    
    def on_progress_update(self, progress: float, estimated_time_remaining: float):
        """
        Called periodically to update progress.
        
        Args:
            progress: Overall progress as a percentage.
            estimated_time_remaining: Estimated time remaining in seconds.
        """
        self.progress_updated.emit(progress, estimated_time_remaining)


class TrainingVisualizationDialog(QDialog):
    """
    Training visualization dialog for RebelSCRIBE.
    
    This dialog allows users to visualize model training progress and results:
    - Real-time monitoring of training metrics
    - Visualization of training results
    - Saving and exporting training results
    """
    
    def __init__(self, parent=None, training_monitor=None):
        """
        Initialize the training visualization dialog.
        
        Args:
            parent: The parent widget.
            training_monitor: The training monitor instance.
        """
        super().__init__(parent)
        
        self.training_monitor = training_monitor or TrainingMonitor()
        
        # Create progress callback
        self.progress_callback = TrainingProgressCallback()
        self.training_monitor.set_callback(self.progress_callback)
        
        # Initialize UI components
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Set up visualization update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_visualizations)
        
        # Set dark mode based on application theme
        self._set_dark_mode_from_theme()
        
        logger.info("Training visualization dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing training visualization dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Training Visualization")
        self.setMinimumSize(800, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create training info group
        self.training_info_group = QGroupBox("Training Information")
        training_info_layout = QFormLayout(self.training_info_group)
        
        self.adapter_name_label = QLabel("Not started")
        training_info_layout.addRow("Adapter:", self.adapter_name_label)
        
        self.base_model_label = QLabel("Not started")
        training_info_layout.addRow("Base Model:", self.base_model_label)
        
        self.adapter_type_label = QLabel("Not started")
        training_info_layout.addRow("Adapter Type:", self.adapter_type_label)
        
        self.main_layout.addWidget(self.training_info_group)
        
        # Create progress group
        self.progress_group = QGroupBox("Training Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # Progress info layout
        progress_info_layout = QHBoxLayout()
        
        self.step_label = QLabel("Step: 0/0")
        progress_info_layout.addWidget(self.step_label)
        
        self.epoch_label = QLabel("Epoch: 0/0")
        progress_info_layout.addWidget(self.epoch_label)
        
        self.loss_label = QLabel("Loss: N/A")
        progress_info_layout.addWidget(self.loss_label)
        
        self.time_label = QLabel("Time Remaining: N/A")
        progress_info_layout.addWidget(self.time_label)
        
        progress_layout.addLayout(progress_info_layout)
        
        self.main_layout.addWidget(self.progress_group)
        
        # Create tab widget for visualizations
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self._create_loss_tab()
        self._create_perplexity_tab()
        self._create_learning_rate_tab()
        self._create_metrics_tab()
        self._create_progress_tab()
        self._create_summary_tab()
        
        self.main_layout.addWidget(self.tab_widget)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Start/stop button
        self.start_stop_button = QPushButton("Start Training")
        self.start_stop_button.setEnabled(False)  # Disabled until training is configured
        button_layout.addWidget(self.start_stop_button)
        
        # Save results button
        self.save_results_button = QPushButton("Save Results")
        self.save_results_button.setEnabled(False)  # Disabled until training is completed
        button_layout.addWidget(self.save_results_button)
        
        # Export report button
        self.export_report_button = QPushButton("Export Report")
        self.export_report_button.setEnabled(False)  # Disabled until training is completed
        button_layout.addWidget(self.export_report_button)
        
        # Close button
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.close_button)
        
        self.main_layout.addLayout(button_layout)
        
        logger.debug("Training visualization dialog UI components initialized")
    
    def _create_loss_tab(self):
        """Create the loss visualization tab."""
        self.loss_tab = QWidget()
        self.tab_widget.addTab(self.loss_tab, "Loss")
        
        # Create layout
        layout = QVBoxLayout(self.loss_tab)
        
        # Create canvas for loss plot
        self.loss_canvas = MatplotlibCanvas(parent=self.loss_tab)
        layout.addWidget(self.loss_canvas)
    
    def _create_perplexity_tab(self):
        """Create the perplexity visualization tab."""
        self.perplexity_tab = QWidget()
        self.tab_widget.addTab(self.perplexity_tab, "Perplexity")
        
        # Create layout
        layout = QVBoxLayout(self.perplexity_tab)
        
        # Create canvas for perplexity plot
        self.perplexity_canvas = MatplotlibCanvas(parent=self.perplexity_tab)
        layout.addWidget(self.perplexity_canvas)
    
    def _create_learning_rate_tab(self):
        """Create the learning rate visualization tab."""
        self.learning_rate_tab = QWidget()
        self.tab_widget.addTab(self.learning_rate_tab, "Learning Rate")
        
        # Create layout
        layout = QVBoxLayout(self.learning_rate_tab)
        
        # Create canvas for learning rate plot
        self.learning_rate_canvas = MatplotlibCanvas(parent=self.learning_rate_tab)
        layout.addWidget(self.learning_rate_canvas)
    
    def _create_metrics_tab(self):
        """Create the metrics visualization tab."""
        self.metrics_tab = QWidget()
        self.tab_widget.addTab(self.metrics_tab, "Metrics")
        
        # Create layout
        layout = QVBoxLayout(self.metrics_tab)
        
        # Create canvas for metrics plot
        self.metrics_canvas = MatplotlibCanvas(parent=self.metrics_tab)
        layout.addWidget(self.metrics_canvas)
    
    def _create_progress_tab(self):
        """Create the progress visualization tab."""
        self.progress_tab = QWidget()
        self.tab_widget.addTab(self.progress_tab, "Progress")
        
        # Create layout
        layout = QVBoxLayout(self.progress_tab)
        
        # Create canvas for progress plot
        self.progress_canvas = MatplotlibCanvas(parent=self.progress_tab)
        layout.addWidget(self.progress_canvas)
    
    def _create_summary_tab(self):
        """Create the summary visualization tab."""
        self.summary_tab = QWidget()
        self.tab_widget.addTab(self.summary_tab, "Summary")
        
        # Create layout
        layout = QVBoxLayout(self.summary_tab)
        
        # Create canvas for summary plot
        self.summary_canvas = MatplotlibCanvas(parent=self.summary_tab)
        layout.addWidget(self.summary_canvas)
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button signals
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        self.save_results_button.clicked.connect(self._on_save_results_clicked)
        self.export_report_button.clicked.connect(self._on_export_report_clicked)
        self.close_button.clicked.connect(self.close)
        
        # Connect progress callback signals
        self.progress_callback.training_started.connect(self._on_training_started)
        self.progress_callback.training_ended.connect(self._on_training_ended)
        self.progress_callback.step_completed.connect(self._on_step_completed)
        self.progress_callback.epoch_completed.connect(self._on_epoch_completed)
        self.progress_callback.progress_updated.connect(self._on_progress_updated)
        
        logger.debug("Signals connected")
    
    def _set_dark_mode_from_theme(self):
        """Set dark mode based on application theme."""
        # Get theme from config
        theme = config.get_config().get("theme", {})
        dark_mode = theme.get("dark_mode", False)
        
        # Set dark mode for training monitor
        self.training_monitor.set_dark_mode(dark_mode)
    
    def set_training_config(self, adapter_name: str, base_model: str, adapter_type: str,
                           total_epochs: int, total_steps: int, parameters: Dict[str, Any],
                           dataset_info: Dict[str, Any]):
        """
        Set the training configuration.
        
        Args:
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            total_epochs: Total number of epochs for training.
            total_steps: Total number of steps for training.
            parameters: Training parameters.
            dataset_info: Information about the dataset.
        """
        logger.info(f"Setting training configuration for {adapter_name} on {base_model}")
        
        # Update UI
        self.adapter_name_label.setText(adapter_name)
        self.base_model_label.setText(base_model)
        self.adapter_type_label.setText(adapter_type)
        
        self.step_label.setText(f"Step: 0/{total_steps}")
        self.epoch_label.setText(f"Epoch: 0/{total_epochs}")
        
        # Enable start button
        self.start_stop_button.setEnabled(True)
        self.start_stop_button.setText("Start Training")
        
        # Store configuration
        self.adapter_name = adapter_name
        self.base_model = base_model
        self.adapter_type = adapter_type
        self.total_epochs = total_epochs
        self.total_steps = total_steps
        self.parameters = parameters
        self.dataset_info = dataset_info
    
    def load_training_results(self, metrics_file: str):
        """
        Load training results from a metrics file.
        
        Args:
            metrics_file: Path to the metrics file.
        """
        logger.info(f"Loading training results from {metrics_file}")
        
        try:
            # Load results
            results = self.training_monitor.load_results(metrics_file)
            
            # Update UI
            metrics = results["metrics"]
            self.adapter_name_label.setText(metrics.adapter_name)
            self.base_model_label.setText(metrics.base_model)
            self.adapter_type_label.setText(metrics.adapter_type)
            
            self.step_label.setText(f"Step: {metrics.steps_completed}/{metrics.total_steps}")
            self.epoch_label.setText(f"Epoch: {metrics.epochs_completed}/{metrics.total_epochs}")
            
            if metrics.train_loss:
                self.loss_label.setText(f"Loss: {metrics.train_loss[-1]:.4f}")
            
            elapsed_time = metrics.get_elapsed_time()
            self.time_label.setText(f"Time: {elapsed_time:.1f}s")
            
            # Set progress bar
            _, overall_progress = metrics.get_progress()
            self.progress_bar.setValue(int(overall_progress))
            
            # Update visualizations
            self._update_visualizations()
            
            # Enable save and export buttons
            self.save_results_button.setEnabled(True)
            self.export_report_button.setEnabled(True)
            
            # Show success message
            QMessageBox.information(
                self,
                "Training Results Loaded",
                f"Successfully loaded training results for {metrics.adapter_name} on {metrics.base_model}."
            )
        
        except Exception as e:
            logger.error(f"Error loading training results: {str(e)}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load training results: {str(e)}"
            )
    
    def _on_start_stop_clicked(self):
        """Handle start/stop button clicked."""
        if self.start_stop_button.text() == "Start Training":
            self._start_training()
        else:
            self._stop_training()
    
    def _start_training(self):
        """Start training."""
        logger.info("Starting training")
        
        # Update UI
        self.start_stop_button.setText("Stop Training")
        self.save_results_button.setEnabled(False)
        self.export_report_button.setEnabled(False)
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Start visualization update timer
        self.update_timer.start(2000)  # Update every 2 seconds
        
        # Start training
        self.training_monitor.start_training(
            total_epochs=self.total_epochs,
            total_steps=self.total_steps,
            adapter_name=self.adapter_name,
            base_model=self.base_model,
            adapter_type=self.adapter_type,
            parameters=self.parameters,
            dataset_info=self.dataset_info
        )
        
        # TODO: Start actual training in a separate thread
        # For now, we'll simulate training with random data
        self._simulate_training()
    
    def _stop_training(self):
        """Stop training."""
        logger.info("Stopping training")
        
        # Update UI
        self.start_stop_button.setText("Start Training")
        
        # Stop visualization update timer
        self.update_timer.stop()
        
        # End training
        self.training_monitor.end_training()
        
        # Enable save and export buttons
        self.save_results_button.setEnabled(True)
        self.export_report_button.setEnabled(True)
        
        # TODO: Stop actual training thread
        # For now, we'll stop the simulation
        if hasattr(self, "_simulation_thread") and self._simulation_thread is not None:
            self._simulation_thread.join()
            self._simulation_thread = None
    
    def _on_save_results_clicked(self):
        """Handle save results button clicked."""
        logger.info("Saving training results")
        
        # Show directory dialog
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )
        
        if dir_path:
            try:
                # Save results
                result_files = self.training_monitor.save_results(dir_path)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Results Saved",
                    f"Training results saved to {dir_path}"
                )
            except Exception as e:
                logger.error(f"Error saving training results: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to save training results: {str(e)}"
                )
    
    def _on_export_report_clicked(self):
        """Handle export report button clicked."""
        logger.info("Exporting training report")
        
        # Show directory dialog
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )
        
        if dir_path:
            try:
                # Get current visualizations
                visualizations = self.training_monitor.get_current_visualizations()
                
                # Save visualizations to temporary directory
                import tempfile
                temp_dir = tempfile.mkdtemp()
                
                visualization_files = {}
                for name, fig in visualizations.items():
                    file_path = os.path.join(temp_dir, f"{name}.png")
                    fig.savefig(file_path, dpi=300, bbox_inches='tight')
                    visualization_files[name] = file_path
                
                # Create HTML report
                report_file = self.training_monitor.visualizer.create_html_report(
                    self.training_monitor.metrics, visualization_files, dir_path
                )
                
                # Clean up temporary directory
                import shutil
                shutil.rmtree(temp_dir)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Report Exported",
                    f"Training report exported to {report_file}"
                )
            except Exception as e:
                logger.error(f"Error exporting training report: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to export training report: {str(e)}"
                )
    
    def _update_visualizations(self):
        """Update visualizations."""
        logger.debug("Updating visualizations")
        
        try:
            # Get current visualizations
            visualizations = self.training_monitor.get_current_visualizations()
            
            # Update canvases
            if "loss_plot" in visualizations:
                self.loss_canvas.update_figure(visualizations["loss_plot"])
            
            if "perplexity_plot" in visualizations:
                self.perplexity_canvas.update_figure(visualizations["perplexity_plot"])
            
            if "learning_rate_plot" in visualizations:
                self.learning_rate_canvas.update_figure(visualizations["learning_rate_plot"])
            
            if "bleu_rouge_plot" in visualizations:
                self.metrics_canvas.update_figure(visualizations["bleu_rouge_plot"])
            
            if "progress_plot" in visualizations:
                self.progress_canvas.update_figure(visualizations["progress_plot"])
            
            if "summary_plot" in visualizations:
                self.summary_canvas.update_figure(visualizations["summary_plot"])
        
        except Exception as e:
            logger.error(f"Error updating visualizations: {str(e)}")
    
    def _on_training_started(self, adapter_name: str, base_model: str, adapter_type: str,
                            total_epochs: int, total_steps: int):
        """
        Handle training started.
        
        Args:
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            total_epochs: Total number of epochs for training.
            total_steps: Total number of steps for training.
        """
        logger.info(f"Training started for {adapter_name} on {base_model}")
        
        # Update UI
        self.adapter_name_label.setText(adapter_name)
        self.base_model_label.setText(base_model)
        self.adapter_type_label.setText(adapter_type)
        
        self.step_label.setText(f"Step: 0/{total_steps}")
        self.epoch_label.setText(f"Epoch: 0/{total_epochs}")
        
        self.start_stop_button.setText("Stop Training")
    
    def _on_training_ended(self, adapter_name: str, base_model: str, adapter_type: str,
                          elapsed_time: float):
        """
        Handle training ended.
        
        Args:
            adapter_name: Name of the adapter being trained.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            elapsed_time: Total training time in seconds.
        """
        logger.info(f"Training ended for {adapter_name} on {base_model}")
        
        # Update UI
        self.time_label.setText(f"Time: {elapsed_time:.1f}s")
        
        self.start_stop_button.setText("Start Training")
        self.save_results_button.setEnabled(True)
        self.export_report_button.setEnabled(True)
        
        # Stop visualization update timer
        self.update_timer.stop()
        
        # Update visualizations one last time
        self._update_visualizations()
    
    def _on_step_completed(self, step: int, loss: float, learning_rate: float,
                          perplexity: Optional[float], progress: float,
                          estimated_time_remaining: float):
        """
        Handle step completed.
        
        Args:
            step: Current step number.
            loss: Training loss for the step.
            learning_rate: Learning rate for the step.
            perplexity: Perplexity for the step (optional).
            progress: Overall progress as a percentage.
            estimated_time_remaining: Estimated time remaining in seconds.
        """
        # Update UI
        self.step_label.setText(f"Step: {step}/{self.total_steps}")
        self.loss_label.setText(f"Loss: {loss:.4f}")
        
        if estimated_time_remaining > 0:
            self.time_label.setText(f"Time Remaining: {estimated_time_remaining:.1f}s")
        
        self.progress_bar.setValue(int(progress))
    
    def _on_epoch_completed(self, epoch: int, eval_loss: Optional[float],
                           eval_perplexity: Optional[float], bleu_score: Optional[float],
                           rouge_scores: Optional[Dict[str, float]], progress: float,
                           estimated_time_remaining: float):
        """
        Handle epoch completed.
        
        Args:
            epoch: Current epoch number.
            eval_loss: Evaluation loss for the epoch (optional).
            eval_perplexity: Evaluation perplexity for the epoch (optional).
            bleu_score: BLEU score for the epoch (optional).
            rouge_scores: ROUGE scores for the epoch (optional).
            progress: Epoch progress as a percentage.
            estimated_time_remaining: Estimated time remaining in seconds.
        """
        # Update UI
        self.epoch_label.setText(f"Epoch: {epoch}/{self.total_epochs}")
        
        if eval_loss is not None:
            self.loss_label.setText(f"Loss: {eval_loss:.4f} (eval)")
    
    def _on_progress_updated(self, progress: float, estimated_time_remaining: float):
        """
        Handle progress updated.
        
        Args:
            progress: Overall progress as a percentage.
            estimated_time_remaining: Estimated time remaining in seconds.
        """
        # Update UI
        self.progress_bar.setValue(int(progress))
        
        if estimated_time_remaining > 0:
            self.time_label.setText(f"Time Remaining: {estimated_time_remaining:.1f}s")
    
    def _simulate_training(self):
        """Simulate training with random data."""
        import random
        import numpy as np
        import threading
        
        def simulate():
            # Simulate training steps
            for step in range(1, self.total_steps + 1):
                # Check if training was stopped
                if not hasattr(self, "_simulation_thread") or self._simulation_thread is None:
                    break
                
                # Simulate loss (decreasing over time with some noise)
                loss = 2.0 * np.exp(-step / (self.total_steps / 3)) + 0.5 + random.uniform(-0.1, 0.1)
                
                # Simulate learning rate (decreasing over time)
                learning_rate = 0.001 * np.exp(-step / (self.total_steps / 2))
                
                # Simulate perplexity (decreasing over time with some noise)
                perplexity = np.exp(loss)
                
                # Update step metrics
                self.training_monitor.update_step(
                    step=step,
                    loss=loss,
                    learning_rate=learning_rate,
                    perplexity=perplexity
                )
                
                # Simulate epoch completion
                if step % (self.total_steps // self.total_epochs) == 0:
                    epoch = step // (self.total_steps // self.total_epochs)
                    
                    # Simulate evaluation metrics
                    eval_loss = loss * 1.1 + random.uniform(-0.05, 0.05)
                    eval_perplexity = np.exp(eval_loss)
                    
                    # Simulate BLEU score (increasing over time with some noise)
                    bleu_score = 0.3 + 0.5 * (epoch / self.total_epochs) + random.uniform(-0.05, 0.05)
                    bleu_score = max(0.0, min(1.0, bleu_score))  # Clamp to [0, 1]
                    
                    # Simulate ROUGE scores (increasing over time with some noise)
                    rouge_scores = {
                        "rouge1": 0.4 + 0.4 * (epoch / self.total_epochs) + random.uniform(-0.05, 0.05),
                        "rouge2": 0.3 + 0.4 * (epoch / self.total_epochs) + random.uniform(-0.05, 0.05),
                        "rougeL": 0.35 + 0.4 * (epoch / self.total_epochs) + random.uniform(-0.05, 0.05)
                    }
                    
                    # Clamp ROUGE scores to [0, 1]
                    for key in rouge_scores:
                        rouge_scores[key] = max(0.0, min(1.0, rouge_scores[key]))
                    
                    # Update epoch metrics
                    self.training_monitor.update_epoch(
                        epoch=epoch,
                        eval_loss=eval_loss,
                        eval_perplexity=eval_perplexity,
                        bleu_score=bleu_score,
                        rouge_scores=rouge_scores
                    )
                
                # Sleep to simulate training time
                time.sleep(0.01)
            
            # End training
            self.training_monitor.end_training()
            
            # Update UI
            self.start_stop_button.setText("Start Training")
            self.save_results_button.setEnabled(True)
            self.export_report_button.setEnabled(True)
            
            # Stop visualization update timer
            self.update_timer.stop()
            
            # Update visualizations one last time
            self._update_visualizations()
        
        # Start simulation thread
        self._simulation_thread = threading.Thread(target=simulate)
        self._simulation_thread.daemon = True
        self._simulation_thread.start()
