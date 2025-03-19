#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Model Benchmark Dialog

This module implements a dialog for benchmarking AI models and visualizing results.
"""

import os
import sys
import tempfile
import webbrowser
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QProgressBar, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.model_registry import (
    ModelRegistry, ModelInfo, ModelType, ModelSource,
    discover_models, get_model_info
)
from src.ai.model_benchmarking import (
    ModelBenchmark, BenchmarkMetric, BenchmarkResult,
    run_benchmark, compare_models, get_benchmark_results,
    create_standard_benchmarks, evaluate_model_quality,
    generate_benchmark_report
)
from src.ai.benchmark_visualization import (
    plot_model_comparison, plot_benchmark_history, plot_metric_correlation,
    plot_model_radar_chart, export_visualization, generate_benchmark_report_html,
    check_visualization_dependencies, _prepare_benchmark_data
)
from src.ai.progress_callbacks import (
    ProgressInfo, ProgressCallback, ProgressStatus
)

logger = get_logger(__name__)
config = ConfigManager()


class BenchmarkThread(QThread):
    """Thread for running benchmarks in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the benchmark is complete
    benchmark_complete = pyqtSignal(BenchmarkResult)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, benchmark: ModelBenchmark):
        """
        Initialize the benchmark thread.
        
        Args:
            benchmark: The benchmark to run.
        """
        super().__init__()
        self.benchmark = benchmark
    
    def run(self):
        """Run the benchmark."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the benchmark
            result = run_benchmark(self.benchmark, progress_callback)
            
            # Emit the result
            self.benchmark_complete.emit(result)
        
        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            self.error_occurred.emit(str(e))


class ComparisonThread(QThread):
    """Thread for running model comparisons in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the comparison is complete
    comparison_complete = pyqtSignal(dict)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_ids: List[str], prompt: str, max_tokens: int, num_runs: int):
        """
        Initialize the comparison thread.
        
        Args:
            model_ids: The IDs of the models to compare.
            prompt: The prompt to use for the benchmark.
            max_tokens: The maximum number of tokens to generate.
            num_runs: The number of times to run the benchmark.
        """
        super().__init__()
        self.model_ids = model_ids
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.num_runs = num_runs
    
    def run(self):
        """Run the comparison."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the comparison
            results = compare_models(
                model_ids=self.model_ids,
                prompt=self.prompt,
                max_tokens=self.max_tokens,
                num_runs=self.num_runs,
                progress_callback=progress_callback
            )
            
            # Emit the results
            self.comparison_complete.emit(results)
        
        except Exception as e:
            logger.error(f"Error running comparison: {e}")
            self.error_occurred.emit(str(e))


class BenchmarkDialog(QDialog):
    """
    Model benchmark dialog for RebelSCRIBE.
    
    This dialog allows users to:
    - Run benchmarks on selected models
    - View benchmark results
    - Compare model performance
    - Generate and view benchmark reports
    """
    
    def __init__(self, parent=None):
        """
        Initialize the benchmark dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        # Load models
        self._load_models()
        
        # Load benchmark results
        self._load_benchmark_results()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Benchmark dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing benchmark dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Model Benchmarking")
        self.setMinimumSize(800, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_run_benchmark_tab()
        self._create_results_tab()
        self._create_comparison_tab()
        self._create_reports_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Benchmark dialog UI components initialized")
    
    def _create_run_benchmark_tab(self):
        """Create the run benchmark tab."""
        logger.debug("Creating run benchmark tab")
        
        # Create tab widget
        self.run_benchmark_tab = QWidget()
        self.tab_widget.addTab(self.run_benchmark_tab, "Run Benchmark")
        
        # Create layout
        layout = QVBoxLayout(self.run_benchmark_tab)
        
        # Create form layout for benchmark settings
        form_layout = QFormLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        form_layout.addRow("Model:", self.model_combo)
        
        # Prompt input
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter a prompt for the benchmark")
        self.prompt_edit.setText("Write a short story about a robot learning to paint.")
        form_layout.addRow("Prompt:", self.prompt_edit)
        
        # Reference text for BLEU score calculation
        self.reference_text_edit = QTextEdit()
        self.reference_text_edit.setPlaceholderText("Enter a reference text for BLEU score calculation (optional)")
        self.reference_text_edit.setMaximumHeight(80)
        form_layout.addRow("Reference Text:", self.reference_text_edit)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(10, 2000)
        self.max_tokens_spin.setValue(100)
        form_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Number of runs
        self.num_runs_spin = QSpinBox()
        self.num_runs_spin.setRange(1, 10)
        self.num_runs_spin.setValue(3)
        form_layout.addRow("Number of Runs:", self.num_runs_spin)
        
        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setValue(0.7)
        self.temperature_spin.setSingleStep(0.1)
        form_layout.addRow("Temperature:", self.temperature_spin)
        
        # Top-p
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setValue(0.9)
        self.top_p_spin.setSingleStep(0.1)
        form_layout.addRow("Top-p:", self.top_p_spin)
        
        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        # Save token logprobs for perplexity calculation
        self.save_logprobs_check = QCheckBox()
        self.save_logprobs_check.setChecked(True)
        advanced_layout.addRow("Save Token Logprobs:", self.save_logprobs_check)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas")
        advanced_layout.addRow("Tags:", self.tags_edit)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Enter a description for the benchmark")
        advanced_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Add run button
        self.run_benchmark_button = QPushButton("Run Benchmark")
        layout.addWidget(self.run_benchmark_button)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Add progress label
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Add result group
        self.result_group = QGroupBox("Benchmark Result")
        result_layout = QVBoxLayout(self.result_group)
        
        # Create a form layout for the result
        result_form = QFormLayout()
        
        self.result_model_label = QLabel()
        result_form.addRow("Model:", self.result_model_label)
        
        self.result_load_time_label = QLabel()
        result_form.addRow("Load Time:", self.result_load_time_label)
        
        self.result_generation_time_label = QLabel()
        result_form.addRow("Generation Time:", self.result_generation_time_label)
        
        self.result_tokens_per_second_label = QLabel()
        result_form.addRow("Tokens per Second:", self.result_tokens_per_second_label)
        
        self.result_memory_label = QLabel()
        result_form.addRow("Memory Usage:", self.result_memory_label)
        
        result_layout.addLayout(result_form)
        
        # Add generated text
        result_layout.addWidget(QLabel("Generated Text Sample:"))
        
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        result_layout.addWidget(self.result_text_edit)
        
        # Hide the result group initially
        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Run benchmark tab created")
    
    def _create_results_tab(self):
        """Create the results tab."""
        logger.debug("Creating results tab")
        
        # Create tab widget
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Create layout
        layout = QVBoxLayout(self.results_tab)
        
        # Create a splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create a list widget for results
        self.results_list = QListWidget()
        splitter.addWidget(self.results_list)
        
        # Create a widget for result details
        result_details_widget = QWidget()
        result_details_layout = QVBoxLayout(result_details_widget)
        
        # Create a form layout for the result details
        result_details_form = QFormLayout()
        
        self.result_details_model_label = QLabel()
        result_details_form.addRow("Model:", self.result_details_model_label)
        
        self.result_details_timestamp_label = QLabel()
        result_details_form.addRow("Timestamp:", self.result_details_timestamp_label)
        
        self.result_details_load_time_label = QLabel()
        result_details_form.addRow("Load Time:", self.result_details_load_time_label)
        
        self.result_details_generation_time_label = QLabel()
        result_details_form.addRow("Generation Time:", self.result_details_generation_time_label)
        
        self.result_details_tokens_per_second_label = QLabel()
        result_details_form.addRow("Tokens per Second:", self.result_details_tokens_per_second_label)
        
        self.result_details_memory_label = QLabel()
        result_details_form.addRow("Memory Usage:", self.result_details_memory_label)
        
        self.result_details_prompt_label = QLabel()
        self.result_details_prompt_label.setWordWrap(True)
        result_details_form.addRow("Prompt:", self.result_details_prompt_label)
        
        self.result_details_tags_label = QLabel()
        result_details_form.addRow("Tags:", self.result_details_tags_label)
        
        result_details_layout.addLayout(result_details_form)
        
        # Add generated text
        result_details_layout.addWidget(QLabel("Generated Text:"))
        
        self.result_details_text_edit = QTextEdit()
        self.result_details_text_edit.setReadOnly(True)
        result_details_layout.addWidget(self.result_details_text_edit)
        
        # Add visualization buttons
        visualization_layout = QVBoxLayout()
        
        # Add metric selection
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.result_metric_combo = QComboBox()
        self.result_metric_combo.addItems([
            "Tokens per Second", 
            "Generation Time", 
            "Memory Usage", 
            "Perplexity", 
            "BLEU Score",
            "Response Length Ratio"
        ])
        metric_layout.addWidget(self.result_metric_combo)
        
        # Add interactive checkbox
        self.result_interactive_check = QCheckBox("Interactive")
        self.result_interactive_check.setChecked(True)
        metric_layout.addWidget(self.result_interactive_check)
        
        visualization_layout.addLayout(metric_layout)
        
        # Add visualization buttons
        buttons_layout = QHBoxLayout()
        
        self.visualize_history_button = QPushButton("Visualize History")
        buttons_layout.addWidget(self.visualize_history_button)
        
        self.visualize_correlation_button = QPushButton("Visualize Correlation")
        buttons_layout.addWidget(self.visualize_correlation_button)
        
        visualization_layout.addLayout(buttons_layout)
        
        result_details_layout.addLayout(visualization_layout)
        
        # Add the result details widget to the splitter
        splitter.addWidget(result_details_widget)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([200, 600])
        
        # Add refresh button
        self.refresh_results_button = QPushButton("Refresh Results")
        layout.addWidget(self.refresh_results_button)
        
        logger.debug("Results tab created")
    
    def _create_comparison_tab(self):
        """Create the comparison tab."""
        logger.debug("Creating comparison tab")
        
        # Create tab widget
        self.comparison_tab = QWidget()
        self.tab_widget.addTab(self.comparison_tab, "Comparison")
        
        # Create layout
        layout = QVBoxLayout(self.comparison_tab)
        
        # Create form layout for comparison settings
        form_layout = QFormLayout()
        
        # Model selection
        self.comparison_models_list = QListWidget()
        self.comparison_models_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        form_layout.addRow("Models:", self.comparison_models_list)
        
        # Prompt input
        self.comparison_prompt_edit = QTextEdit()
        self.comparison_prompt_edit.setPlaceholderText("Enter a prompt for the comparison")
        self.comparison_prompt_edit.setText("Explain the concept of artificial intelligence to a high school student.")
        form_layout.addRow("Prompt:", self.comparison_prompt_edit)
        
        # Max tokens
        self.comparison_max_tokens_spin = QSpinBox()
        self.comparison_max_tokens_spin.setRange(10, 2000)
        self.comparison_max_tokens_spin.setValue(150)
        form_layout.addRow("Max Tokens:", self.comparison_max_tokens_spin)
        
        # Number of runs
        self.comparison_num_runs_spin = QSpinBox()
        self.comparison_num_runs_spin.setRange(1, 10)
        self.comparison_num_runs_spin.setValue(2)
        form_layout.addRow("Number of Runs:", self.comparison_num_runs_spin)
        
        layout.addLayout(form_layout)
        
        # Add run comparison button
        self.run_comparison_button = QPushButton("Run Comparison")
        layout.addWidget(self.run_comparison_button)
        
        # Add progress bar
        self.comparison_progress_bar = QProgressBar()
        self.comparison_progress_bar.setRange(0, 100)
        self.comparison_progress_bar.setValue(0)
        self.comparison_progress_bar.setVisible(False)
        layout.addWidget(self.comparison_progress_bar)
        
        # Add progress label
        self.comparison_progress_label = QLabel()
        self.comparison_progress_label.setVisible(False)
        layout.addWidget(self.comparison_progress_label)
        
        # Add visualization group
        self.visualization_group = QGroupBox("Visualization")
        visualization_layout = QVBoxLayout(self.visualization_group)
        
        # Add visualization options
        visualization_options_layout = QHBoxLayout()
        
        # Add metric selection
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.comparison_metric_combo = QComboBox()
        self.comparison_metric_combo.addItems([
            "Tokens per Second", 
            "Generation Time", 
            "Memory Usage", 
            "Perplexity", 
            "BLEU Score",
            "Response Length Ratio"
        ])
        metric_layout.addWidget(self.comparison_metric_combo)
        
        # Add interactive checkbox
        self.comparison_interactive_check = QCheckBox("Interactive")
        self.comparison_interactive_check.setChecked(True)
        metric_layout.addWidget(self.comparison_interactive_check)
        
        visualization_options_layout.addLayout(metric_layout)
        visualization_layout.addLayout(visualization_options_layout)
        
        # Add visualization buttons
        visualization_buttons_layout = QHBoxLayout()
        
        self.visualize_comparison_bar_button = QPushButton("Bar Chart")
        visualization_buttons_layout.addWidget(self.visualize_comparison_bar_button)
        
        self.visualize_comparison_radar_button = QPushButton("Radar Chart")
        visualization_buttons_layout.addWidget(self.visualize_comparison_radar_button)
        
        self.visualize_comparison_correlation_button = QPushButton("Correlation")
        visualization_buttons_layout.addWidget(self.visualize_comparison_correlation_button)
        
        visualization_layout.addLayout(visualization_buttons_layout)
        
        # Add visualization label
        self.visualization_label = QLabel("Run a comparison to generate visualizations.")
        self.visualization_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visualization_layout.addWidget(self.visualization_label)
        
        # Add visualization image label
        self.visualization_image_label = QLabel()
        self.visualization_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visualization_image_label.setMinimumHeight(300)
        
        # Create a scroll area for the visualization image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.visualization_image_label)
        visualization_layout.addWidget(scroll_area)
        
        # Add save visualization button
        self.save_visualization_button = QPushButton("Save Visualization")
        self.save_visualization_button.setEnabled(False)
        visualization_layout.addWidget(self.save_visualization_button)
        
        # Hide the visualization group initially
        self.visualization_group.setVisible(False)
        layout.addWidget(self.visualization_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Comparison tab created")
    
    def _create_reports_tab(self):
        """Create the reports tab."""
        logger.debug("Creating reports tab")
        
        # Create tab widget
        self.reports_tab = QWidget()
        self.tab_widget.addTab(self.reports_tab, "Reports")
        
        # Create layout
        layout = QVBoxLayout(self.reports_tab)
        
        # Create form layout for report settings
        form_layout = QFormLayout()
        
        # Model selection
        self.report_model_combo = QComboBox()
        self.report_model_combo.addItem("All Models")
        form_layout.addRow("Model:", self.report_model_combo)
        
        # Include plots
        self.report_include_plots_check = QCheckBox()
        self.report_include_plots_check.setChecked(True)
        form_layout.addRow("Include Plots:", self.report_include_plots_check)
        
        layout.addLayout(form_layout)
        
        # Add generate report button
        self.generate_report_button = QPushButton("Generate Report")
        layout.addWidget(self.generate_report_button)
        
        # Add progress bar
        self.report_progress_bar = QProgressBar()
        self.report_progress_bar.setRange(0, 100)
        self.report_progress_bar.setValue(0)
        self.report_progress_bar.setVisible(False)
        layout.addWidget(self.report_progress_bar)
        
        # Add progress label
        self.report_progress_label = QLabel()
        self.report_progress_label.setVisible(False)
        layout.addWidget(self.report_progress_label)
        
        # Add report preview
        self.report_preview_group = QGroupBox("Report Preview")
        report_preview_layout = QVBoxLayout(self.report_preview_group)
        
        self.report_preview_text = QTextEdit()
        self.report_preview_text.setReadOnly(True)
        report_preview_layout.addWidget(self.report_preview_text)
        
        # Add open in browser button
        self.open_report_button = QPushButton("Open in Browser")
        self.open_report_button.setEnabled(False)
        report_preview_layout.addWidget(self.open_report_button)
        
        # Hide the report preview group initially
        self.report_preview_group.setVisible(False)
        layout.addWidget(self.report_preview_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Reports tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.rejected.connect(self.reject)
        
        # Connect run benchmark tab signals
        self.run_benchmark_button.clicked.connect(self._on_run_benchmark)
        
        # Connect results tab signals
        self.results_list.currentItemChanged.connect(self._on_result_selected)
        self.refresh_results_button.clicked.connect(self._load_benchmark_results)
        self.visualize_history_button.clicked.connect(self._visualize_result_history)
        self.visualize_correlation_button.clicked.connect(self._visualize_result_correlation)
        
        # Connect comparison tab signals
        self.run_comparison_button.clicked.connect(self._on_run_comparison)
        self.visualize_comparison_bar_button.clicked.connect(self._visualize_comparison_bar)
        self.visualize_comparison_radar_button.clicked.connect(self._visualize_comparison_radar)
        # Remove the correlation button connection as it's not implemented yet
        self.save_visualization_button.clicked.connect(self._on_save_visualization)
        
        # Connect reports tab signals
        self.generate_report_button.clicked.connect(self._on_generate_report)
        self.open_report_button.clicked.connect(self._on_open_report)
        
        logger.debug("Signals connected")
    
    def _load_models(self):
        """Load available models."""
        logger.debug("Loading available models")
        
        try:
            # Get the model registry
            registry = ModelRegistry.get_instance()
            
            # Discover models
            models = registry.get_all_models()
            
            if not models:
                # Try to discover models
                models = registry.discover_models()
            
            # Add models to combo boxes
            for model in models:
                self.model_combo.addItem(f"{model.name} ({model.id})", model.id)
                self.report_model_combo.addItem(f"{model.name} ({model.id})", model.id)
                
                # Add to comparison models list
                item = QListWidgetItem(f"{model.name} ({model.id})")
                item.setData(Qt.ItemDataRole.UserRole, model.id)
                self.comparison_models_list.addItem(item)
            
            logger.debug(f"Loaded {len(models)} models")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load models: {e}")
    
    def _load_benchmark_results(self):
        """Load benchmark results."""
        logger.debug("Loading benchmark results")
        
        try:
            # Clear the results list
            self.results_list.clear()
            
            # Get benchmark results
            results = get_benchmark_results()
            
            # Add results to the list
            for result in results:
                item = QListWidgetItem(f"{result.model_name} - {result.timestamp}")
                item.setData(Qt.ItemDataRole.UserRole, result)
                self.results_list.addItem(item)
            
            logger.debug(f"Loaded {len(results)} benchmark results")
        except Exception as e:
            logger.error(f"Error loading benchmark results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load benchmark results: {e}")
    
    def _on_run_benchmark(self):
        """Handle run benchmark button clicked."""
        logger.debug("Run benchmark button clicked")
        
        try:
            # Get selected model
            model_id = self.model_combo.currentData()
            
            if not model_id:
                QMessageBox.warning(self, "Error", "Please select a model.")
                return
            
            # Get benchmark parameters
            prompt = self.prompt_edit.toPlainText()
            reference_text = self.reference_text_edit.toPlainText()
            max_tokens = self.max_tokens_spin.value()
            num_runs = self.num_runs_spin.value()
            temperature = self.temperature_spin.value()
            top_p = self.top_p_spin.value()
            save_logprobs = self.save_logprobs_check.isChecked()
            tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
            description = self.description_edit.text()
            
            # Create benchmark
            benchmark = ModelBenchmark(
                model_id=model_id,
                prompt=prompt,
                max_tokens=max_tokens,
                num_runs=num_runs,
                temperature=temperature,
                top_p=top_p,
                tags=tags,
                description=description,
                save_logprobs=save_logprobs,
                reference_text=reference_text if reference_text else None
            )
            
            # Show progress bar
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.progress_label.setText("Initializing benchmark...")
            self.progress_label.setVisible(True)
            
            # Disable run button
            self.run_benchmark_button.setEnabled(False)
            
            # Create and start benchmark thread
            self.benchmark_thread = BenchmarkThread(benchmark)
            self.benchmark_thread.progress_updated.connect(self._on_benchmark_progress)
            self.benchmark_thread.benchmark_complete.connect(self._on_benchmark_complete)
            self.benchmark_thread.error_occurred.connect(self._on_benchmark_error)
            self.benchmark_thread.start()
            
            logger.debug(f"Started benchmark for model {model_id}")
        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run benchmark: {e}")
            
            # Hide progress bar
            self.progress_bar.setVisible(False)
            self.progress_label.setVisible(False)
            
            # Enable run button
            self.run_benchmark_button.setEnabled(True)
    
    def _on_benchmark_progress(self, progress_info: ProgressInfo):
        """
        Handle benchmark progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.progress_label.setText(progress_info.message)
    
    def _on_benchmark_complete(self, result: BenchmarkResult):
        """
        Handle benchmark completion.
        
        Args:
            result: The benchmark result.
        """
        logger.debug(f"Benchmark completed for model {result.model_id}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Enable run button
        self.run_benchmark_button.setEnabled(True)
        
        # Show result
        self.result_model_label.setText(f"{result.model_name} ({result.model_id})")
        self.result_load_time_label.setText(f"{result.load_time_seconds:.2f} seconds")
        self.result_generation_time_label.setText(f"{result.avg_generation_time:.2f} seconds")
        self.result_tokens_per_second_label.setText(f"{result.avg_tokens_per_second:.2f}")
        self.result_memory_label.setText(f"{result.peak_memory_mb:.2f} MB")
        
        # Show generated text
        if result.generated_texts:
            self.result_text_edit.setText(result.generated_texts[0])
        
        # Show result group
        self.result_group.setVisible(True)
        
        # Reload benchmark results
        self._load_benchmark_results()
    
    def _on_benchmark_error(self, error: str):
        """
        Handle benchmark error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Benchmark error: {error}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Enable run button
        self.run_benchmark_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Benchmark Error", f"Error running benchmark: {error}")
    
    def _on_result_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handle result selection changed.
        
        Args:
            current: The current selected item.
            previous: The previously selected item.
        """
        if not current:
            return
        
        # Get the result
        result = current.data(Qt.ItemDataRole.UserRole)
        
        # Show result details
        self.result_details_model_label.setText(f"{result.model_name} ({result.model_id})")
        self.result_details_timestamp_label.setText(result.timestamp)
        self.result_details_load_time_label.setText(f"{result.load_time_seconds:.2f} seconds")
        self.result_details_generation_time_label.setText(f"{result.avg_generation_time:.2f} seconds")
        self.result_details_tokens_per_second_label.setText(f"{result.avg_tokens_per_second:.2f}")
        self.result_details_memory_label.setText(f"{result.peak_memory_mb:.2f} MB")
        self.result_details_prompt_label.setText(result.prompt)
        self.result_details_tags_label.setText(", ".join(result.tags) if result.tags else "")
        
        # Show generated text
        if result.generated_texts:
            self.result_details_text_edit.setText(result.generated_texts[0])
        else:
            self.result_details_text_edit.setText("")
    
    def _get_metric_from_combo(self, combo_box: QComboBox) -> str:
        """
        Get the metric name from a combo box selection.
        
        Args:
            combo_box: The combo box with the metric selection.
            
        Returns:
            str: The metric name.
        """
        metric_map = {
            "Tokens per Second": "avg_tokens_per_second",
            "Generation Time": "avg_generation_time",
            "Memory Usage": "peak_memory_mb",
            "Perplexity": "perplexity",
            "BLEU Score": "bleu_score",
            "Response Length Ratio": "response_length_ratio"
        }
        
        return metric_map.get(combo_box.currentText(), "avg_tokens_per_second")
    
    def _visualize_result_history(self):
        """Visualize a result history."""
        logger.debug("Visualizing result history")
        
        try:
            # Check if visualization dependencies are available
            interactive = self.result_interactive_check.isChecked()
            if interactive and not check_visualization_dependencies(include_interactive=True):
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Interactive visualization dependencies are not available. Please install plotly."
                )
                interactive = False
            elif not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Get the selected result
            current_item = self.results_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Error", "Please select a result to visualize.")
                return
            
            result = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Get all results for the same model
            all_results = get_benchmark_results(result.model_id)
            
            # Get the selected metric
            metric = self._get_metric_from_combo(self.result_metric_combo)
            
            # Create a temporary file for the visualization
            suffix = ".html" if interactive else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"{self.result_metric_combo.currentText()}: {result.model_name}"
            
            try:
                fig = plot_benchmark_history(
                    all_results, 
                    result.model_id, 
                    metric, 
                    title=title,
                    interactive=interactive
                )
                
                # Save the visualization
                if interactive:
                    fig.write_html(temp_path)
                else:
                    export_visualization(fig, temp_path)
                
                # Show the visualization
                os.startfile(temp_path)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing result history: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize result history: {e}")
    
    def _visualize_result_correlation(self):
        """Visualize a result correlation."""
        logger.debug("Visualizing result correlation")
        
        try:
            # Check if visualization dependencies are available
            if not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Get the selected result
            current_item = self.results_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Error", "Please select a result to visualize.")
                return
            
            result = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Get all results for the same model
            all_results = get_benchmark_results(result.model_id)
            
            # Get the selected metric
            y_metric = self._get_metric_from_combo(self.result_metric_combo)
            
            # Create a temporary file for the visualization
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"Correlation: Generation Time vs {self.result_metric_combo.currentText()}"
            
            try:
                # Check if we have enough data points
                if len(all_results) < 3:
                    QMessageBox.warning(
                        self, 
                        "Insufficient Data", 
                        "Need at least 3 benchmark results for correlation analysis."
                    )
                    return
                
                # Create the correlation plot
                fig = plot_metric_correlation(
                    all_results,
                    x_metric="avg_generation_time",
                    y_metric=y_metric,
                    title=title
                )
                
                # Save the visualization
                export_visualization(fig, temp_path)
                
                # Show the visualization
                os.startfile(temp_path)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing result correlation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize result correlation: {e}")
    
    def _on_run_comparison(self):
        """Handle run comparison button clicked."""
        logger.debug("Run comparison button clicked")
        
        try:
            # Get selected models
            selected_items = self.comparison_models_list.selectedItems()
            
            if not selected_items or len(selected_items) < 2:
                QMessageBox.warning(self, "Error", "Please select at least two models to compare.")
                return
            
            # Get model IDs
            model_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            
            # Get comparison parameters
            prompt = self.comparison_prompt_edit.toPlainText()
            max_tokens = self.comparison_max_tokens_spin.value()
            num_runs = self.comparison_num_runs_spin.value()
            
            # Show progress bar
            self.comparison_progress_bar.setValue(0)
            self.comparison_progress_bar.setVisible(True)
            self.comparison_progress_label.setText("Initializing comparison...")
            self.comparison_progress_label.setVisible(True)
            
            # Disable run button
            self.run_comparison_button.setEnabled(False)
            
            # Create and start comparison thread
            self.comparison_thread = ComparisonThread(model_ids, prompt, max_tokens, num_runs)
            self.comparison_thread.progress_updated.connect(self._on_comparison_progress)
            self.comparison_thread.comparison_complete.connect(self._on_comparison_complete)
            self.comparison_thread.error_occurred.connect(self._on_comparison_error)
            self.comparison_thread.start()
            
            logger.debug(f"Started comparison for models: {', '.join(model_ids)}")
        except Exception as e:
            logger.error(f"Error running comparison: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run comparison: {e}")
            
            # Hide progress bar
            self.comparison_progress_bar.setVisible(False)
            self.comparison_progress_label.setVisible(False)
            
            # Enable run button
            self.run_comparison_button.setEnabled(True)
    
    def _on_comparison_progress(self, progress_info: ProgressInfo):
        """
        Handle comparison progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.comparison_progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.comparison_progress_label.setText(progress_info.message)
    
    def _on_comparison_complete(self, results: Dict[str, BenchmarkResult]):
        """
        Handle comparison completion.
        
        Args:
            results: The comparison results.
        """
        logger.debug(f"Comparison completed for {len(results)} models")
        
        # Hide progress bar
        self.comparison_progress_bar.setVisible(False)
        self.comparison_progress_label.setVisible(False)
        
        # Enable run button
        self.run_comparison_button.setEnabled(True)
        
        # Store the results
        self.comparison_results = results
        
        # Show visualization group
        self.visualization_group.setVisible(True)
        
        # Update visualization label
        self.visualization_label.setText(f"Comparison completed for {len(results)} models. Select a visualization type.")
        
        # Visualize tokens per second by default
        self._visualize_comparison("avg_tokens_per_second")
    
    def _on_comparison_error(self, error: str):
        """
        Handle comparison error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Comparison error: {error}")
        
        # Hide progress bar
        self.comparison_progress_bar.setVisible(False)
        self.comparison_progress_label.setVisible(False)
        
        # Enable run button
        self.run_comparison_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Comparison Error", f"Error running comparison: {error}")
    
    def _visualize_comparison_bar(self):
        """Visualize a comparison using a bar chart."""
        logger.debug("Visualizing comparison with bar chart")
        
        try:
            # Check if visualization dependencies are available
            interactive = self.comparison_interactive_check.isChecked()
            if interactive and not check_visualization_dependencies(include_interactive=True):
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Interactive visualization dependencies are not available. Please install plotly."
                )
                interactive = False
            elif not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Check if comparison results are available
            if not hasattr(self, "comparison_results") or not self.comparison_results:
                QMessageBox.warning(self, "Error", "No comparison results available. Run a comparison first.")
                return
            
            # Get the selected metric
            metric = self._get_metric_from_combo(self.comparison_metric_combo)
            
            # Create a temporary file for the visualization
            suffix = ".html" if interactive else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"Model Comparison: {self.comparison_metric_combo.currentText()}"
            
            # Sort ascending for metrics where lower is better
            sort_ascending = metric in ["avg_generation_time", "load_time_seconds", "peak_memory_mb", "perplexity"]
            
            try:
                # Create the visualization
                fig = plot_model_comparison(
                    list(self.comparison_results.values()), 
                    metric, 
                    title=title, 
                    sort_ascending=sort_ascending,
                    interactive=interactive
                )
                
                # Save the visualization
                if interactive:
                    # Save as HTML for interactive visualization
                    fig.write_html(temp_path)
                    
                    # Open in browser
                    os.startfile(temp_path)
                    
                    # Create a static version for display in the UI
                    static_temp_path = temp_path.replace(".html", ".png")
                    static_fig = plot_model_comparison(
                        list(self.comparison_results.values()), 
                        metric, 
                        title=title, 
                        sort_ascending=sort_ascending,
                        interactive=False
                    )
                    export_visualization(static_fig, static_temp_path)
                    
                    # Load the static visualization for display
                    pixmap = QPixmap(static_temp_path)
                    self.visualization_image_label.setPixmap(pixmap)
                    
                    # Store both paths
                    self.current_visualization_path = temp_path
                    self.current_static_visualization_path = static_temp_path
                else:
                    # Save and display static visualization
                    export_visualization(fig, temp_path)
                    pixmap = QPixmap(temp_path)
                    self.visualization_image_label.setPixmap(pixmap)
                    self.current_visualization_path = temp_path
                
                # Enable save button
                self.save_visualization_button.setEnabled(True)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing comparison: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize comparison: {e}")
    
    def _visualize_comparison_radar(self):
        """Visualize a comparison using a radar chart."""
        logger.debug("Visualizing comparison with radar chart")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Model Benchmark Dialog

This module implements a dialog for benchmarking AI models and visualizing results.
"""

import os
import sys
import tempfile
import webbrowser
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QProgressBar, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.model_registry import (
    ModelRegistry, ModelInfo, ModelType, ModelSource,
    discover_models, get_model_info
)
from src.ai.model_benchmarking import (
    ModelBenchmark, BenchmarkMetric, BenchmarkResult,
    run_benchmark, compare_models, get_benchmark_results,
    create_standard_benchmarks, evaluate_model_quality,
    generate_benchmark_report
)
from src.ai.benchmark_visualization import (
    plot_model_comparison, plot_benchmark_history, plot_metric_correlation,
    plot_model_radar_chart, export_visualization, generate_benchmark_report_html,
    check_visualization_dependencies, _prepare_benchmark_data
)
from src.ai.progress_callbacks import (
    ProgressInfo, ProgressCallback, ProgressStatus
)

logger = get_logger(__name__)
config = ConfigManager()


class BenchmarkThread(QThread):
    """Thread for running benchmarks in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the benchmark is complete
    benchmark_complete = pyqtSignal(BenchmarkResult)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, benchmark: ModelBenchmark):
        """
        Initialize the benchmark thread.
        
        Args:
            benchmark: The benchmark to run.
        """
        super().__init__()
        self.benchmark = benchmark
    
    def run(self):
        """Run the benchmark."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the benchmark
            result = run_benchmark(self.benchmark, progress_callback)
            
            # Emit the result
            self.benchmark_complete.emit(result)
        
        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            self.error_occurred.emit(str(e))


class ComparisonThread(QThread):
    """Thread for running model comparisons in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the comparison is complete
    comparison_complete = pyqtSignal(dict)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_ids: List[str], prompt: str, max_tokens: int, num_runs: int):
        """
        Initialize the comparison thread.
        
        Args:
            model_ids: The IDs of the models to compare.
            prompt: The prompt to use for the benchmark.
            max_tokens: The maximum number of tokens to generate.
            num_runs: The number of times to run the benchmark.
        """
        super().__init__()
        self.model_ids = model_ids
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.num_runs = num_runs
    
    def run(self):
        """Run the comparison."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the comparison
            results = compare_models(
                model_ids=self.model_ids,
                prompt=self.prompt,
                max_tokens=self.max_tokens,
                num_runs=self.num_runs,
                progress_callback=progress_callback
            )
            
            # Emit the results
            self.comparison_complete.emit(results)
        
        except Exception as e:
            logger.error(f"Error running comparison: {e}")
            self.error_occurred.emit(str(e))


class BenchmarkDialog(QDialog):
    """
    Model benchmark dialog for RebelSCRIBE.
    
    This dialog allows users to:
    - Run benchmarks on selected models
    - View benchmark results
    - Compare model performance
    - Generate and view benchmark reports
    """
    
    def __init__(self, parent=None):
        """
        Initialize the benchmark dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        # Load models
        self._load_models()
        
        # Load benchmark results
        self._load_benchmark_results()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Benchmark dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing benchmark dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Model Benchmarking")
        self.setMinimumSize(800, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_run_benchmark_tab()
        self._create_results_tab()
        self._create_comparison_tab()
        self._create_reports_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Benchmark dialog UI components initialized")
    
    def _create_run_benchmark_tab(self):
        """Create the run benchmark tab."""
        logger.debug("Creating run benchmark tab")
        
        # Create tab widget
        self.run_benchmark_tab = QWidget()
        self.tab_widget.addTab(self.run_benchmark_tab, "Run Benchmark")
        
        # Create layout
        layout = QVBoxLayout(self.run_benchmark_tab)
        
        # Create form layout for benchmark settings
        form_layout = QFormLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        form_layout.addRow("Model:", self.model_combo)
        
        # Prompt input
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter a prompt for the benchmark")
        self.prompt_edit.setText("Write a short story about a robot learning to paint.")
        form_layout.addRow("Prompt:", self.prompt_edit)
        
        # Reference text for BLEU score calculation
        self.reference_text_edit = QTextEdit()
        self.reference_text_edit.setPlaceholderText("Enter a reference text for BLEU score calculation (optional)")
        self.reference_text_edit.setMaximumHeight(80)
        form_layout.addRow("Reference Text:", self.reference_text_edit)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(10, 2000)
        self.max_tokens_spin.setValue(100)
        form_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Number of runs
        self.num_runs_spin = QSpinBox()
        self.num_runs_spin.setRange(1, 10)
        self.num_runs_spin.setValue(3)
        form_layout.addRow("Number of Runs:", self.num_runs_spin)
        
        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setValue(0.7)
        self.temperature_spin.setSingleStep(0.1)
        form_layout.addRow("Temperature:", self.temperature_spin)
        
        # Top-p
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setValue(0.9)
        self.top_p_spin.setSingleStep(0.1)
        form_layout.addRow("Top-p:", self.top_p_spin)
        
        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        # Save token logprobs for perplexity calculation
        self.save_logprobs_check = QCheckBox()
        self.save_logprobs_check.setChecked(True)
        advanced_layout.addRow("Save Token Logprobs:", self.save_logprobs_check)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas")
        advanced_layout.addRow("Tags:", self.tags_edit)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Enter a description for the benchmark")
        advanced_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Add run button
        self.run_benchmark_button = QPushButton("Run Benchmark")
        layout.addWidget(self.run_benchmark_button)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Add progress label
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Add result group
        self.result_group = QGroupBox("Benchmark Result")
        result_layout = QVBoxLayout(self.result_group)
        
        # Create a form layout for the result
        result_form = QFormLayout()
        
        self.result_model_label = QLabel()
        result_form.addRow("Model:", self.result_model_label)
        
        self.result_load_time_label = QLabel()
        result_form.addRow("Load Time:", self.result_load_time_label)
        
        self.result_generation_time_label = QLabel()
        result_form.addRow("Generation Time:", self.result_generation_time_label)
        
        self.result_tokens_per_second_label = QLabel()
        result_form.addRow("Tokens per Second:", self.result_tokens_per_second_label)
        
        self.result_memory_label = QLabel()
        result_form.addRow("Memory Usage:", self.result_memory_label)
        
        result_layout.addLayout(result_form)
        
        # Add generated text
        result_layout.addWidget(QLabel("Generated Text Sample:"))
        
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        result_layout.addWidget(self.result_text_edit)
        
        # Hide the result group initially
        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Run benchmark tab created")
    
    def _create_results_tab(self):
        """Create the results tab."""
        logger.debug("Creating results tab")
        
        # Create tab widget
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Create layout
        layout = QVBoxLayout(self.results_tab)
        
        # Create a splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create a list widget for results
        self.results_list = QListWidget()
        splitter.addWidget(self.results_list)
        
        # Create a widget for result details
        result_details_widget = QWidget()
        result_details_layout = QVBoxLayout(result_details_widget)
        
        # Create a form layout for the result details
        result_details_form = QFormLayout()
        
        self.result_details_model_label = QLabel()
        result_details_form.addRow("Model:", self.result_details_model_label)
        
        self.result_details_timestamp_label = QLabel()
        result_details_form.addRow("Timestamp:", self.result_details_timestamp_label)
        
        self.result_details_load_time_label = QLabel()
        result_details_form.addRow("Load Time:", self.result_details_load_time_label)
        
        self.result_details_generation_time_label = QLabel()
        result_details_form.addRow("Generation Time:", self.result_details_generation_time_label)
        
        self.result_details_tokens_per_second_label = QLabel()
        result_details_form.addRow("Tokens per Second:", self.result_details_tokens_per_second_label)
        
        self.result_details_memory_label = QLabel()
        result_details_form.addRow("Memory Usage:", self.result_details_memory_label)
        
        self.result_details_prompt_label = QLabel()
        self.result_details_prompt_label.setWordWrap(True)
        result_details_form.addRow("Prompt:", self.result_details_prompt_label)
        
        self.result_details_tags_label = QLabel()
        result_details_form.addRow("Tags:", self.result_details_tags_label)
        
        result_details_layout.addLayout(result_details_form)
        
        # Add generated text
        result_details_layout.addWidget(QLabel("Generated Text:"))
        
        self.result_details_text_edit = QTextEdit()
        self.result_details_text_edit.setReadOnly(True)
        result_details_layout.addWidget(self.result_details_text_edit)
        
        # Add visualization buttons
        visualization_layout = QVBoxLayout()
        
        # Add metric selection
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.result_metric_combo = QComboBox()
        self.result_metric_combo.addItems([
            "Tokens per Second", 
            "Generation Time", 
            "Memory Usage", 
            "Perplexity", 
            "BLEU Score",
            "Response Length Ratio"
        ])
        metric_layout.addWidget(self.result_metric_combo)
        
        # Add interactive checkbox
        self.result_interactive_check = QCheckBox("Interactive")
        self.result_interactive_check.setChecked(True)
        metric_layout.addWidget(self.result_interactive_check)
        
        visualization_layout.addLayout(metric_layout)
        
        # Add visualization buttons
        buttons_layout = QHBoxLayout()
        
        self.visualize_history_button = QPushButton("Visualize History")
        buttons_layout.addWidget(self.visualize_history_button)
        
        self.visualize_correlation_button = QPushButton("Visualize Correlation")
        buttons_layout.addWidget(self.visualize_correlation_button)
        
        visualization_layout.addLayout(buttons_layout)
        
        result_details_layout.addLayout(visualization_layout)
        
        # Add the result details widget to the splitter
        splitter.addWidget(result_details_widget)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([200, 600])
        
        # Add refresh button
        self.refresh_results_button = QPushButton("Refresh Results")
        layout.addWidget(self.refresh_results_button)
        
        logger.debug("Results tab created")
    
    def _create_comparison_tab(self):
        """Create the comparison tab."""
        logger.debug("Creating comparison tab")
        
        # Create tab widget
        self.comparison_tab = QWidget()
        self.tab_widget.addTab(self.comparison_tab, "Comparison")
        
        # Create layout
        layout = QVBoxLayout(self.comparison_tab)
        
        # Create form layout for comparison settings
        form_layout = QFormLayout()
        
        # Model selection
        self.comparison_models_list = QListWidget()
        self.comparison_models_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        form_layout.addRow("Models:", self.comparison_models_list)
        
        # Prompt input
        self.comparison_prompt_edit = QTextEdit()
        self.comparison_prompt_edit.setPlaceholderText("Enter a prompt for the comparison")
        self.comparison_prompt_edit.setText("Explain the concept of artificial intelligence to a high school student.")
        form_layout.addRow("Prompt:", self.comparison_prompt_edit)
        
        # Max tokens
        self.comparison_max_tokens_spin = QSpinBox()
        self.comparison_max_tokens_spin.setRange(10, 2000)
        self.comparison_max_tokens_spin.setValue(150)
        form_layout.addRow("Max Tokens:", self.comparison_max_tokens_spin)
        
        # Number of runs
        self.comparison_num_runs_spin = QSpinBox()
        self.comparison_num_runs_spin.setRange(1, 10)
        self.comparison_num_runs_spin.setValue(2)
        form_layout.addRow("Number of Runs:", self.comparison_num_runs_spin)
        
        layout.addLayout(form_layout)
        
        # Add run comparison button
        self.run_comparison_button = QPushButton("Run Comparison")
        layout.addWidget(self.run_comparison_button)
        
        # Add progress bar
        self.comparison_progress_bar = QProgressBar()
        self.comparison_progress_bar.setRange(0, 100)
        self.comparison_progress_bar.setValue(0)
        self.comparison_progress_bar.setVisible(False)
        layout.addWidget(self.comparison_progress_bar)
        
        # Add progress label
        self.comparison_progress_label = QLabel()
        self.comparison_progress_label.setVisible(False)
        layout.addWidget(self.comparison_progress_label)
        
        # Add visualization group
        self.visualization_group = QGroupBox("Visualization")
        visualization_layout = QVBoxLayout(self.visualization_group)
        
        # Add visualization options
        visualization_options_layout = QHBoxLayout()
        
        # Add metric selection
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.comparison_metric_combo = QComboBox()
        self.comparison_metric_combo.addItems([
            "Tokens per Second", 
            "Generation Time", 
            "Memory Usage", 
            "Perplexity", 
            "BLEU Score",
            "Response Length Ratio"
        ])
        metric_layout.addWidget(self.comparison_metric_combo)
        
        # Add interactive checkbox
        self.comparison_interactive_check = QCheckBox("Interactive")
        self.comparison_interactive_check.setChecked(True)
        metric_layout.addWidget(self.comparison_interactive_check)
        
        visualization_options_layout.addLayout(metric_layout)
        visualization_layout.addLayout(visualization_options_layout)
        
        # Add visualization buttons
        visualization_buttons_layout = QHBoxLayout()
        
        self.visualize_comparison_bar_button = QPushButton("Bar Chart")
        visualization_buttons_layout.addWidget(self.visualize_comparison_bar_button)
        
        self.visualize_comparison_radar_button = QPushButton("Radar Chart")
        visualization_buttons_layout.addWidget(self.visualize_comparison_radar_button)
        
        self.visualize_comparison_correlation_button = QPushButton("Correlation")
        visualization_buttons_layout.addWidget(self.visualize_comparison_correlation_button)
        
        visualization_layout.addLayout(visualization_buttons_layout)
        
        # Add visualization label
        self.visualization_label = QLabel("Run a comparison to generate visualizations.")
        self.visualization_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visualization_layout.addWidget(self.visualization_label)
        
        # Add visualization image label
        self.visualization_image_label = QLabel()
        self.visualization_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visualization_image_label.setMinimumHeight(300)
        
        # Create a scroll area for the visualization image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.visualization_image_label)
        visualization_layout.addWidget(scroll_area)
        
        # Add save visualization button
        self.save_visualization_button = QPushButton("Save Visualization")
        self.save_visualization_button.setEnabled(False)
        visualization_layout.addWidget(self.save_visualization_button)
        
        # Hide the visualization group initially
        self.visualization_group.setVisible(False)
        layout.addWidget(self.visualization_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Comparison tab created")
    
    def _create_reports_tab(self):
        """Create the reports tab."""
        logger.debug("Creating reports tab")
        
        # Create tab widget
        self.reports_tab = QWidget()
        self.tab_widget.addTab(self.reports_tab, "Reports")
        
        # Create layout
        layout = QVBoxLayout(self.reports_tab)
        
        # Create form layout for report settings
        form_layout = QFormLayout()
        
        # Model selection
        self.report_model_combo = QComboBox()
        self.report_model_combo.addItem("All Models")
        form_layout.addRow("Model:", self.report_model_combo)
        
        # Include plots
        self.report_include_plots_check = QCheckBox()
        self.report_include_plots_check.setChecked(True)
        form_layout.addRow("Include Plots:", self.report_include_plots_check)
        
        layout.addLayout(form_layout)
        
        # Add generate report button
        self.generate_report_button = QPushButton("Generate Report")
        layout.addWidget(self.generate_report_button)
        
        # Add progress bar
        self.report_progress_bar = QProgressBar()
        self.report_progress_bar.setRange(0, 100)
        self.report_progress_bar.setValue(0)
        self.report_progress_bar.setVisible(False)
        layout.addWidget(self.report_progress_bar)
        
        # Add progress label
        self.report_progress_label = QLabel()
        self.report_progress_label.setVisible(False)
        layout.addWidget(self.report_progress_label)
        
        # Add report preview
        self.report_preview_group = QGroupBox("Report Preview")
        report_preview_layout = QVBoxLayout(self.report_preview_group)
        
        self.report_preview_text = QTextEdit()
        self.report_preview_text.setReadOnly(True)
        report_preview_layout.addWidget(self.report_preview_text)
        
        # Add open in browser button
        self.open_report_button = QPushButton("Open in Browser")
        self.open_report_button.setEnabled(False)
        report_preview_layout.addWidget(self.open_report_button)
        
        # Hide the report preview group initially
        self.report_preview_group.setVisible(False)
        layout.addWidget(self.report_preview_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Reports tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.rejected.connect(self.reject)
        
        # Connect run benchmark tab signals
        self.run_benchmark_button.clicked.connect(self._on_run_benchmark)
        
        # Connect results tab signals
        self.results_list.currentItemChanged.connect(self._on_result_selected)
        self.refresh_results_button.clicked.connect(self._load_benchmark_results)
        self.visualize_history_button.clicked.connect(self._visualize_result_history)
        self.visualize_correlation_button.clicked.connect(self._visualize_result_correlation)
        
        # Connect comparison tab signals
        self.run_comparison_button.clicked.connect(self._on_run_comparison)
        self.visualize_comparison_bar_button.clicked.connect(self._visualize_comparison_bar)
        self.visualize_comparison_radar_button.clicked.connect(self._visualize_comparison_radar)
        # Remove the correlation button connection as it's not implemented yet
        self.save_visualization_button.clicked.connect(self._on_save_visualization)
        
        # Connect reports tab signals
        self.generate_report_button.clicked.connect(self._on_generate_report)
        self.open_report_button.clicked.connect(self._on_open_report)
        
        logger.debug("Signals connected")
    
    def _load_models(self):
        """Load available models."""
        logger.debug("Loading available models")
        
        try:
            # Get the model registry
            registry = ModelRegistry.get_instance()
            
            # Discover models
            models = registry.get_all_models()
            
            if not models:
                # Try to discover models
                models = registry.discover_models()
            
            # Add models to combo boxes
            for model in models:
                self.model_combo.addItem(f"{model.name} ({model.id})", model.id)
                self.report_model_combo.addItem(f"{model.name} ({model.id})", model.id)
                
                # Add to comparison models list
                item = QListWidgetItem(f"{model.name} ({model.id})")
                item.setData(Qt.ItemDataRole.UserRole, model.id)
                self.comparison_models_list.addItem(item)
            
            logger.debug(f"Loaded {len(models)} models")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load models: {e}")
    
    def _load_benchmark_results(self):
        """Load benchmark results."""
        logger.debug("Loading benchmark results")
        
        try:
            # Clear the results list
            self.results_list.clear()
            
            # Get benchmark results
            results = get_benchmark_results()
            
            # Add results to the list
            for result in results:
                item = QListWidgetItem(f"{result.model_name} - {result.timestamp}")
                item.setData(Qt.ItemDataRole.UserRole, result)
                self.results_list.addItem(item)
            
            logger.debug(f"Loaded {len(results)} benchmark results")
        except Exception as e:
            logger.error(f"Error loading benchmark results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load benchmark results: {e}")
    
    def _on_run_benchmark(self):
        """Handle run benchmark button clicked."""
        logger.debug("Run benchmark button clicked")
        
        try:
            # Get selected model
            model_id = self.model_combo.currentData()
            
            if not model_id:
                QMessageBox.warning(self, "Error", "Please select a model.")
                return
            
            # Get benchmark parameters
            prompt = self.prompt_edit.toPlainText()
            reference_text = self.reference_text_edit.toPlainText()
            max_tokens = self.max_tokens_spin.value()
            num_runs = self.num_runs_spin.value()
            temperature = self.temperature_spin.value()
            top_p = self.top_p_spin.value()
            save_logprobs = self.save_logprobs_check.isChecked()
            tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
            description = self.description_edit.text()
            
            # Create benchmark
            benchmark = ModelBenchmark(
                model_id=model_id,
                prompt=prompt,
                max_tokens=max_tokens,
                num_runs=num_runs,
                temperature=temperature,
                top_p=top_p,
                tags=tags,
                description=description,
                save_logprobs=save_logprobs,
                reference_text=reference_text if reference_text else None
            )
            
            # Show progress bar
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.progress_label.setText("Initializing benchmark...")
            self.progress_label.setVisible(True)
            
            # Disable run button
            self.run_benchmark_button.setEnabled(False)
            
            # Create and start benchmark thread
            self.benchmark_thread = BenchmarkThread(benchmark)
            self.benchmark_thread.progress_updated.connect(self._on_benchmark_progress)
            self.benchmark_thread.benchmark_complete.connect(self._on_benchmark_complete)
            self.benchmark_thread.error_occurred.connect(self._on_benchmark_error)
            self.benchmark_thread.start()
            
            logger.debug(f"Started benchmark for model {model_id}")
        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run benchmark: {e}")
            
            # Hide progress bar
            self.progress_bar.setVisible(False)
            self.progress_label.setVisible(False)
            
            # Enable run button
            self.run_benchmark_button.setEnabled(True)
    
    def _on_benchmark_progress(self, progress_info: ProgressInfo):
        """
        Handle benchmark progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.progress_label.setText(progress_info.message)
    
    def _on_benchmark_complete(self, result: BenchmarkResult):
        """
        Handle benchmark completion.
        
        Args:
            result: The benchmark result.
        """
        logger.debug(f"Benchmark completed for model {result.model_id}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Enable run button
        self.run_benchmark_button.setEnabled(True)
        
        # Show result
        self.result_model_label.setText(f"{result.model_name} ({result.model_id})")
        self.result_load_time_label.setText(f"{result.load_time_seconds:.2f} seconds")
        self.result_generation_time_label.setText(f"{result.avg_generation_time:.2f} seconds")
        self.result_tokens_per_second_label.setText(f"{result.avg_tokens_per_second:.2f}")
        self.result_memory_label.setText(f"{result.peak_memory_mb:.2f} MB")
        
        # Show generated text
        if result.generated_texts:
            self.result_text_edit.setText(result.generated_texts[0])
        
        # Show result group
        self.result_group.setVisible(True)
        
        # Reload benchmark results
        self._load_benchmark_results()
    
    def _on_benchmark_error(self, error: str):
        """
        Handle benchmark error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Benchmark error: {error}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Enable run button
        self.run_benchmark_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Benchmark Error", f"Error running benchmark: {error}")
    
    def _on_result_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handle result selection changed.
        
        Args:
            current: The current selected item.
            previous: The previously selected item.
        """
        if not current:
            return
        
        # Get the result
        result = current.data(Qt.ItemDataRole.UserRole)
        
        # Show result details
        self.result_details_model_label.setText(f"{result.model_name} ({result.model_id})")
        self.result_details_timestamp_label.setText(result.timestamp)
        self.result_details_load_time_label.setText(f"{result.load_time_seconds:.2f} seconds")
        self.result_details_generation_time_label.setText(f"{result.avg_generation_time:.2f} seconds")
        self.result_details_tokens_per_second_label.setText(f"{result.avg_tokens_per_second:.2f}")
        self.result_details_memory_label.setText(f"{result.peak_memory_mb:.2f} MB")
        self.result_details_prompt_label.setText(result.prompt)
        self.result_details_tags_label.setText(", ".join(result.tags) if result.tags else "")
        
        # Show generated text
        if result.generated_texts:
            self.result_details_text_edit.setText(result.generated_texts[0])
        else:
            self.result_details_text_edit.setText("")
    
    def _get_metric_from_combo(self, combo_box: QComboBox) -> str:
        """
        Get the metric name from a combo box selection.
        
        Args:
            combo_box: The combo box with the metric selection.
            
        Returns:
            str: The metric name.
        """
        metric_map = {
            "Tokens per Second": "avg_tokens_per_second",
            "Generation Time": "avg_generation_time",
            "Memory Usage": "peak_memory_mb",
            "Perplexity": "perplexity",
            "BLEU Score": "bleu_score",
            "Response Length Ratio": "response_length_ratio"
        }
        
        return metric_map.get(combo_box.currentText(), "avg_tokens_per_second")
    
    def _visualize_result_history(self):
        """Visualize a result history."""
        logger.debug("Visualizing result history")
        
        try:
            # Check if visualization dependencies are available
            interactive = self.result_interactive_check.isChecked()
            if interactive and not check_visualization_dependencies(include_interactive=True):
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Interactive visualization dependencies are not available. Please install plotly."
                )
                interactive = False
            elif not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Get the selected result
            current_item = self.results_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Error", "Please select a result to visualize.")
                return
            
            result = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Get all results for the same model
            all_results = get_benchmark_results(result.model_id)
            
            # Get the selected metric
            metric = self._get_metric_from_combo(self.result_metric_combo)
            
            # Create a temporary file for the visualization
            suffix = ".html" if interactive else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"{self.result_metric_combo.currentText()}: {result.model_name}"
            
            try:
                fig = plot_benchmark_history(
                    all_results, 
                    result.model_id, 
                    metric, 
                    title=title,
                    interactive=interactive
                )
                
                # Save the visualization
                if interactive:
                    fig.write_html(temp_path)
                else:
                    export_visualization(fig, temp_path)
                
                # Show the visualization
                os.startfile(temp_path)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing result history: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize result history: {e}")
    
    def _visualize_result_correlation(self):
        """Visualize a result correlation."""
        logger.debug("Visualizing result correlation")
        
        try:
            # Check if visualization dependencies are available
            if not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Get the selected result
            current_item = self.results_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Error", "Please select a result to visualize.")
                return
            
            result = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Get all results for the same model
            all_results = get_benchmark_results(result.model_id)
            
            # Get the selected metric
            y_metric = self._get_metric_from_combo(self.result_metric_combo)
            
            # Create a temporary file for the visualization
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"Correlation: Generation Time vs {self.result_metric_combo.currentText()}"
            
            try:
                # Check if we have enough data points
                if len(all_results) < 3:
                    QMessageBox.warning(
                        self, 
                        "Insufficient Data", 
                        "Need at least 3 benchmark results for correlation analysis."
                    )
                    return
                
                # Create the correlation plot
                fig = plot_metric_correlation(
                    all_results,
                    x_metric="avg_generation_time",
                    y_metric=y_metric,
                    title=title
                )
                
                # Save the visualization
                export_visualization(fig, temp_path)
                
                # Show the visualization
                os.startfile(temp_path)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing result correlation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize result correlation: {e}")
    
    def _on_run_comparison(self):
        """Handle run comparison button clicked."""
        logger.debug("Run comparison button clicked")
        
        try:
            # Get selected models
            selected_items = self.comparison_models_list.selectedItems()
            
            if not selected_items or len(selected_items) < 2:
                QMessageBox.warning(self, "Error", "Please select at least two models to compare.")
                return
            
            # Get model IDs
            model_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            
            # Get comparison parameters
            prompt = self.comparison_prompt_edit.toPlainText()
            max_tokens = self.comparison_max_tokens_spin.value()
            num_runs = self.comparison_num_runs_spin.value()
            
            # Show progress bar
            self.comparison_progress_bar.setValue(0)
            self.comparison_progress_bar.setVisible(True)
            self.comparison_progress_label.setText("Initializing comparison...")
            self.comparison_progress_label.setVisible(True)
            
            # Disable run button
            self.run_comparison_button.setEnabled(False)
            
            # Create and start comparison thread
            self.comparison_thread = ComparisonThread(model_ids, prompt, max_tokens, num_runs)
            self.comparison_thread.progress_updated.connect(self._on_comparison_progress)
            self.comparison_thread.comparison_complete.connect(self._on_comparison_complete)
            self.comparison_thread.error_occurred.connect(self._on_comparison_error)
            self.comparison_thread.start()
            
            logger.debug(f"Started comparison for models: {', '.join(model_ids)}")
        except Exception as e:
            logger.error(f"Error running comparison: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run comparison: {e}")
            
            # Hide progress bar
            self.comparison_progress_bar.setVisible(False)
            self.comparison_progress_label.setVisible(False)
            
            # Enable run button
            self.run_comparison_button.setEnabled(True)
    
    def _on_comparison_progress(self, progress_info: ProgressInfo):
        """
        Handle comparison progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.comparison_progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.comparison_progress_label.setText(progress_info.message)
    
    def _on_comparison_complete(self, results: Dict[str, BenchmarkResult]):
        """
        Handle comparison completion.
        
        Args:
            results: The comparison results.
        """
        logger.debug(f"Comparison completed for {len(results)} models")
        
        # Hide progress bar
        self.comparison_progress_bar.setVisible(False)
        self.comparison_progress_label.setVisible(False)
        
        # Enable run button
        self.run_comparison_button.setEnabled(True)
        
        # Store the results
        self.comparison_results = results
        
        # Show visualization group
        self.visualization_group.setVisible(True)
        
        # Update visualization label
        self.visualization_label.setText(f"Comparison completed for {len(results)} models. Select a visualization type.")
        
        # Visualize tokens per second by default
        self._visualize_comparison("avg_tokens_per_second")
    
    def _on_comparison_error(self, error: str):
        """
        Handle comparison error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Comparison error: {error}")
        
        # Hide progress bar
        self.comparison_progress_bar.setVisible(False)
        self.comparison_progress_label.setVisible(False)
        
        # Enable run button
        self.run_comparison_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Comparison Error", f"Error running comparison: {error}")
    
    def _visualize_comparison_bar(self):
        """Visualize a comparison using a bar chart."""
        logger.debug("Visualizing comparison with bar chart")
        
        try:
            # Check if visualization dependencies are available
            interactive = self.comparison_interactive_check.isChecked()
            if interactive and not check_visualization_dependencies(include_interactive=True):
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Interactive visualization dependencies are not available. Please install plotly."
                )
                interactive = False
            elif not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Check if comparison results are available
            if not hasattr(self, "comparison_results") or not self.comparison_results:
                QMessageBox.warning(self, "Error", "No comparison results available. Run a comparison first.")
                return
            
            # Get the selected metric
            metric = self._get_metric_from_combo(self.comparison_metric_combo)
            
            # Create a temporary file for the visualization
            suffix = ".html" if interactive else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"Model Comparison: {self.comparison_metric_combo.currentText()}"
            
            # Sort ascending for metrics where lower is better
            sort_ascending = metric in ["avg_generation_time", "load_time_seconds", "peak_memory_mb", "perplexity"]
            
            try:
                # Create the visualization
                fig = plot_model_comparison(
                    list(self.comparison_results.values()), 
                    metric, 
                    title=title, 
                    sort_ascending=sort_ascending,
                    interactive=interactive
                )
                
                # Save the visualization
                if interactive:
                    # Save as HTML for interactive visualization
                    fig.write_html(temp_path)
                    
                    # Open in browser
                    os.startfile(temp_path)
                    
                    # Create a static version for display in the UI
                    static_temp_path = temp_path.replace(".html", ".png")
                    static_fig = plot_model_comparison(
                        list(self.comparison_results.values()), 
                        metric, 
                        title=title, 
                        sort_ascending=sort_ascending,
                        interactive=False
                    )
                    export_visualization(static_fig, static_temp_path)
                    
                    # Load the static visualization for display
                    pixmap = QPixmap(static_temp_path)
                    self.visualization_image_label.setPixmap(pixmap)
                    
                    # Store both paths
                    self.current_visualization_path = temp_path
                    self.current_static_visualization_path = static_temp_path
                else:
                    # Save and display static visualization
                    export_visualization(fig, temp_path)
                    pixmap = QPixmap(temp_path)
                    self.visualization_image_label.setPixmap(pixmap)
                    self.current_visualization_path = temp_path
                
                # Enable save button
                self.save_visualization_button.setEnabled(True)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing comparison: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize comparison: {e}")
    
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Model Benchmark Dialog

This module implements a dialog for benchmarking AI models and visualizing results.
"""

import os
import sys
import tempfile
import webbrowser
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QProgressBar, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.model_registry import (
    ModelRegistry, ModelInfo, ModelType, ModelSource,
    discover_models, get_model_info
)
from src.ai.model_benchmarking import (
    ModelBenchmark, BenchmarkMetric, BenchmarkResult,
    run_benchmark, compare_models, get_benchmark_results,
    create_standard_benchmarks, evaluate_model_quality,
    generate_benchmark_report
)
from src.ai.benchmark_visualization import (
    plot_model_comparison, plot_benchmark_history, plot_metric_correlation,
    plot_model_radar_chart, export_visualization, generate_benchmark_report_html,
    check_visualization_dependencies, _prepare_benchmark_data
)
from src.ai.progress_callbacks import (
    ProgressInfo, ProgressCallback, ProgressStatus
)

logger = get_logger(__name__)
config = ConfigManager()


class BenchmarkThread(QThread):
    """Thread for running benchmarks in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the benchmark is complete
    benchmark_complete = pyqtSignal(BenchmarkResult)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, benchmark: ModelBenchmark):
        """
        Initialize the benchmark thread.
        
        Args:
            benchmark: The benchmark to run.
        """
        super().__init__()
        self.benchmark = benchmark
    
    def run(self):
        """Run the benchmark."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the benchmark
            result = run_benchmark(self.benchmark, progress_callback)
            
            # Emit the result
            self.benchmark_complete.emit(result)
        
        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            self.error_occurred.emit(str(e))


class ComparisonThread(QThread):
    """Thread for running model comparisons in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the comparison is complete
    comparison_complete = pyqtSignal(dict)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_ids: List[str], prompt: str, max_tokens: int, num_runs: int):
        """
        Initialize the comparison thread.
        
        Args:
            model_ids: The IDs of the models to compare.
            prompt: The prompt to use for the benchmark.
            max_tokens: The maximum number of tokens to generate.
            num_runs: The number of times to run the benchmark.
        """
        super().__init__()
        self.model_ids = model_ids
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.num_runs = num_runs
    
    def run(self):
        """Run the comparison."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the comparison
            results = compare_models(
                model_ids=self.model_ids,
                prompt=self.prompt,
                max_tokens=self.max_tokens,
                num_runs=self.num_runs,
                progress_callback=progress_callback
            )
            
            # Emit the results
            self.comparison_complete.emit(results)
        
        except Exception as e:
            logger.error(f"Error running comparison: {e}")
            self.error_occurred.emit(str(e))


class BenchmarkDialog(QDialog):
    """
    Model benchmark dialog for RebelSCRIBE.
    
    This dialog allows users to:
    - Run benchmarks on selected models
    - View benchmark results
    - Compare model performance
    - Generate and view benchmark reports
    """
    
    def __init__(self, parent=None):
        """
        Initialize the benchmark dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        # Load models
        self._load_models()
        
        # Load benchmark results
        self._load_benchmark_results()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Benchmark dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing benchmark dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Model Benchmarking")
        self.setMinimumSize(800, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_run_benchmark_tab()
        self._create_results_tab()
        self._create_comparison_tab()
        self._create_reports_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Benchmark dialog UI components initialized")
    
    def _create_run_benchmark_tab(self):
        """Create the run benchmark tab."""
        logger.debug("Creating run benchmark tab")
        
        # Create tab widget
        self.run_benchmark_tab = QWidget()
        self.tab_widget.addTab(self.run_benchmark_tab, "Run Benchmark")
        
        # Create layout
        layout = QVBoxLayout(self.run_benchmark_tab)
        
        # Create form layout for benchmark settings
        form_layout = QFormLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        form_layout.addRow("Model:", self.model_combo)
        
        # Prompt input
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter a prompt for the benchmark")
        self.prompt_edit.setText("Write a short story about a robot learning to paint.")
        form_layout.addRow("Prompt:", self.prompt_edit)
        
        # Reference text for BLEU score calculation
        self.reference_text_edit = QTextEdit()
        self.reference_text_edit.setPlaceholderText("Enter a reference text for BLEU score calculation (optional)")
        self.reference_text_edit.setMaximumHeight(80)
        form_layout.addRow("Reference Text:", self.reference_text_edit)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(10, 2000)
        self.max_tokens_spin.setValue(100)
        form_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Number of runs
        self.num_runs_spin = QSpinBox()
        self.num_runs_spin.setRange(1, 10)
        self.num_runs_spin.setValue(3)
        form_layout.addRow("Number of Runs:", self.num_runs_spin)
        
        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setValue(0.7)
        self.temperature_spin.setSingleStep(0.1)
        form_layout.addRow("Temperature:", self.temperature_spin)
        
        # Top-p
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setValue(0.9)
        self.top_p_spin.setSingleStep(0.1)
        form_layout.addRow("Top-p:", self.top_p_spin)
        
        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        # Save token logprobs for perplexity calculation
        self.save_logprobs_check = QCheckBox()
        self.save_logprobs_check.setChecked(True)
        advanced_layout.addRow("Save Token Logprobs:", self.save_logprobs_check)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas")
        advanced_layout.addRow("Tags:", self.tags_edit)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Enter a description for the benchmark")
        advanced_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Add run button
        self.run_benchmark_button = QPushButton("Run Benchmark")
        layout.addWidget(self.run_benchmark_button)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Add progress label
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Add result group
        self.result_group = QGroupBox("Benchmark Result")
        result_layout = QVBoxLayout(self.result_group)
        
        # Create a form layout for the result
        result_form = QFormLayout()
        
        self.result_model_label = QLabel()
        result_form.addRow("Model:", self.result_model_label)
        
        self.result_load_time_label = QLabel()
        result_form.addRow("Load Time:", self.result_load_time_label)
        
        self.result_generation_time_label = QLabel()
        result_form.addRow("Generation Time:", self.result_generation_time_label)
        
        self.result_tokens_per_second_label = QLabel()
        result_form.addRow("Tokens per Second:", self.result_tokens_per_second_label)
        
        self.result_memory_label = QLabel()
        result_form.addRow("Memory Usage:", self.result_memory_label)
        
        result_layout.addLayout(result_form)
        
        # Add generated text
        result_layout.addWidget(QLabel("Generated Text Sample:"))
        
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        result_layout.addWidget(self.result_text_edit)
        
        # Hide the result group initially
        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Run benchmark tab created")
    
    def _create_results_tab(self):
        """Create the results tab."""
        logger.debug("Creating results tab")
        
        # Create tab widget
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Create layout
        layout = QVBoxLayout(self.results_tab)
        
        # Create a splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create a list widget for results
        self.results_list = QListWidget()
        splitter.addWidget(self.results_list)
        
        # Create a widget for result details
        result_details_widget = QWidget()
        result_details_layout = QVBoxLayout(result_details_widget)
        
        # Create a form layout for the result details
        result_details_form = QFormLayout()
        
        self.result_details_model_label = QLabel()
        result_details_form.addRow("Model:", self.result_details_model_label)
        
        self.result_details_timestamp_label = QLabel()
        result_details_form.addRow("Timestamp:", self.result_details_timestamp_label)
        
        self.result_details_load_time_label = QLabel()
        result_details_form.addRow("Load Time:", self.result_details_load_time_label)
        
        self.result_details_generation_time_label = QLabel()
        result_details_form.addRow("Generation Time:", self.result_details_generation_time_label)
        
        self.result_details_tokens_per_second_label = QLabel()
        result_details_form.addRow("Tokens per Second:", self.result_details_tokens_per_second_label)
        
        self.result_details_memory_label = QLabel()
        result_details_form.addRow("Memory Usage:", self.result_details_memory_label)
        
        self.result_details_prompt_label = QLabel()
        self.result_details_prompt_label.setWordWrap(True)
        result_details_form.addRow("Prompt:", self.result_details_prompt_label)
        
        self.result_details_tags_label = QLabel()
        result_details_form.addRow("Tags:", self.result_details_tags_label)
        
        result_details_layout.addLayout(result_details_form)
        
        # Add generated text
        result_details_layout.addWidget(QLabel("Generated Text:"))
        
        self.result_details_text_edit = QTextEdit()
        self.result_details_text_edit.setReadOnly(True)
        result_details_layout.addWidget(self.result_details_text_edit)
        
        # Add visualization buttons
        visualization_layout = QVBoxLayout()
        
        # Add metric selection
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.result_metric_combo = QComboBox()
        self.result_metric_combo.addItems([
            "Tokens per Second", 
            "Generation Time", 
            "Memory Usage", 
            "Perplexity", 
            "BLEU Score",
            "Response Length Ratio"
        ])
        metric_layout.addWidget(self.result_metric_combo)
        
        # Add interactive checkbox
        self.result_interactive_check = QCheckBox("Interactive")
        self.result_interactive_check.setChecked(True)
        metric_layout.addWidget(self.result_interactive_check)
        
        visualization_layout.addLayout(metric_layout)
        
        # Add visualization buttons
        buttons_layout = QHBoxLayout()
        
        self.visualize_history_button = QPushButton("Visualize History")
        buttons_layout.addWidget(self.visualize_history_button)
        
        self.visualize_correlation_button = QPushButton("Visualize Correlation")
        buttons_layout.addWidget(self.visualize_correlation_button)
        
        visualization_layout.addLayout(buttons_layout)
        
        result_details_layout.addLayout(visualization_layout)
        
        # Add the result details widget to the splitter
        splitter.addWidget(result_details_widget)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([200, 600])
        
        # Add refresh button
        self.refresh_results_button = QPushButton("Refresh Results")
        layout.addWidget(self.refresh_results_button)
        
        logger.debug("Results tab created")
    
    def _create_comparison_tab(self):
        """Create the comparison tab."""
        logger.debug("Creating comparison tab")
        
        # Create tab widget
        self.comparison_tab = QWidget()
        self.tab_widget.addTab(self.comparison_tab, "Comparison")
        
        # Create layout
        layout = QVBoxLayout(self.comparison_tab)
        
        # Create form layout for comparison settings
        form_layout = QFormLayout()
        
        # Model selection
        self.comparison_models_list = QListWidget()
        self.comparison_models_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        form_layout.addRow("Models:", self.comparison_models_list)
        
        # Prompt input
        self.comparison_prompt_edit = QTextEdit()
        self.comparison_prompt_edit.setPlaceholderText("Enter a prompt for the comparison")
        self.comparison_prompt_edit.setText("Explain the concept of artificial intelligence to a high school student.")
        form_layout.addRow("Prompt:", self.comparison_prompt_edit)
        
        # Max tokens
        self.comparison_max_tokens_spin = QSpinBox()
        self.comparison_max_tokens_spin.setRange(10, 2000)
        self.comparison_max_tokens_spin.setValue(150)
        form_layout.addRow("Max Tokens:", self.comparison_max_tokens_spin)
        
        # Number of runs
        self.comparison_num_runs_spin = QSpinBox()
        self.comparison_num_runs_spin.setRange(1, 10)
        self.comparison_num_runs_spin.setValue(2)
        form_layout.addRow("Number of Runs:", self.comparison_num_runs_spin)
        
        layout.addLayout(form_layout)
        
        # Add run comparison button
        self.run_comparison_button = QPushButton("Run Comparison")
        layout.addWidget(self.run_comparison_button)
        
        # Add progress bar
        self.comparison_progress_bar = QProgressBar()
        self.comparison_progress_bar.setRange(0, 100)
        self.comparison_progress_bar.setValue(0)
        self.comparison_progress_bar.setVisible(False)
        layout.addWidget(self.comparison_progress_bar)
        
        # Add progress label
        self.comparison_progress_label = QLabel()
        self.comparison_progress_label.setVisible(False)
        layout.addWidget(self.comparison_progress_label)
        
        # Add visualization group
        self.visualization_group = QGroupBox("Visualization")
        visualization_layout = QVBoxLayout(self.visualization_group)
        
        # Add visualization options
        visualization_options_layout = QHBoxLayout()
        
        # Add metric selection
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.comparison_metric_combo = QComboBox()
        self.comparison_metric_combo.addItems([
            "Tokens per Second", 
            "Generation Time", 
            "Memory Usage", 
            "Perplexity", 
            "BLEU Score",
            "Response Length Ratio"
        ])
        metric_layout.addWidget(self.comparison_metric_combo)
        
        # Add interactive checkbox
        self.comparison_interactive_check = QCheckBox("Interactive")
        self.comparison_interactive_check.setChecked(True)
        metric_layout.addWidget(self.comparison_interactive_check)
        
        visualization_options_layout.addLayout(metric_layout)
        visualization_layout.addLayout(visualization_options_layout)
        
        # Add visualization buttons
        visualization_buttons_layout = QHBoxLayout()
        
        self.visualize_comparison_bar_button = QPushButton("Bar Chart")
        visualization_buttons_layout.addWidget(self.visualize_comparison_bar_button)
        
        self.visualize_comparison_radar_button = QPushButton("Radar Chart")
        visualization_buttons_layout.addWidget(self.visualize_comparison_radar_button)
        
        self.visualize_comparison_correlation_button = QPushButton("Correlation")
        visualization_buttons_layout.addWidget(self.visualize_comparison_correlation_button)
        
        visualization_layout.addLayout(visualization_buttons_layout)
        
        # Add visualization label
        self.visualization_label = QLabel("Run a comparison to generate visualizations.")
        self.visualization_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visualization_layout.addWidget(self.visualization_label)
        
        # Add visualization image label
        self.visualization_image_label = QLabel()
        self.visualization_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visualization_image_label.setMinimumHeight(300)
        
        # Create a scroll area for the visualization image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.visualization_image_label)
        visualization_layout.addWidget(scroll_area)
        
        # Add save visualization button
        self.save_visualization_button = QPushButton("Save Visualization")
        self.save_visualization_button.setEnabled(False)
        visualization_layout.addWidget(self.save_visualization_button)
        
        # Hide the visualization group initially
        self.visualization_group.setVisible(False)
        layout.addWidget(self.visualization_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Comparison tab created")
    
    def _create_reports_tab(self):
        """Create the reports tab."""
        logger.debug("Creating reports tab")
        
        # Create tab widget
        self.reports_tab = QWidget()
        self.tab_widget.addTab(self.reports_tab, "Reports")
        
        # Create layout
        layout = QVBoxLayout(self.reports_tab)
        
        # Create form layout for report settings
        form_layout = QFormLayout()
        
        # Model selection
        self.report_model_combo = QComboBox()
        self.report_model_combo.addItem("All Models")
        form_layout.addRow("Model:", self.report_model_combo)
        
        # Include plots
        self.report_include_plots_check = QCheckBox()
        self.report_include_plots_check.setChecked(True)
        form_layout.addRow("Include Plots:", self.report_include_plots_check)
        
        layout.addLayout(form_layout)
        
        # Add generate report button
        self.generate_report_button = QPushButton("Generate Report")
        layout.addWidget(self.generate_report_button)
        
        # Add progress bar
        self.report_progress_bar = QProgressBar()
        self.report_progress_bar.setRange(0, 100)
        self.report_progress_bar.setValue(0)
        self.report_progress_bar.setVisible(False)
        layout.addWidget(self.report_progress_bar)
        
        # Add progress label
        self.report_progress_label = QLabel()
        self.report_progress_label.setVisible(False)
        layout.addWidget(self.report_progress_label)
        
        # Add report preview
        self.report_preview_group = QGroupBox("Report Preview")
        report_preview_layout = QVBoxLayout(self.report_preview_group)
        
        self.report_preview_text = QTextEdit()
        self.report_preview_text.setReadOnly(True)
        report_preview_layout.addWidget(self.report_preview_text)
        
        # Add open in browser button
        self.open_report_button = QPushButton("Open in Browser")
        self.open_report_button.setEnabled(False)
        report_preview_layout.addWidget(self.open_report_button)
        
        # Hide the report preview group initially
        self.report_preview_group.setVisible(False)
        layout.addWidget(self.report_preview_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Reports tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.rejected.connect(self.reject)
        
        # Connect run benchmark tab signals
        self.run_benchmark_button.clicked.connect(self._on_run_benchmark)
        
        # Connect results tab signals
        self.results_list.currentItemChanged.connect(self._on_result_selected)
        self.refresh_results_button.clicked.connect(self._load_benchmark_results)
        self.visualize_history_button.clicked.connect(self._visualize_result_history)
        self.visualize_correlation_button.clicked.connect(self._visualize_result_correlation)
        
        # Connect comparison tab signals
        self.run_comparison_button.clicked.connect(self._on_run_comparison)
        self.visualize_comparison_bar_button.clicked.connect(self._visualize_comparison_bar)
        self.visualize_comparison_radar_button.clicked.connect(self._visualize_comparison_radar)
        # Remove the correlation button connection as it's not implemented yet
        self.save_visualization_button.clicked.connect(self._on_save_visualization)
        
        # Connect reports tab signals
        self.generate_report_button.clicked.connect(self._on_generate_report)
        self.open_report_button.clicked.connect(self._on_open_report)
        
        logger.debug("Signals connected")
    
    def _load_models(self):
        """Load available models."""
        logger.debug("Loading available models")
        
        try:
            # Get the model registry
            registry = ModelRegistry.get_instance()
            
            # Discover models
            models = registry.get_all_models()
            
            if not models:
                # Try to discover models
                models = registry.discover_models()
            
            # Add models to combo boxes
            for model in models:
                self.model_combo.addItem(f"{model.name} ({model.id})", model.id)
                self.report_model_combo.addItem(f"{model.name} ({model.id})", model.id)
                
                # Add to comparison models list
                item = QListWidgetItem(f"{model.name} ({model.id})")
                item.setData(Qt.ItemDataRole.UserRole, model.id)
                self.comparison_models_list.addItem(item)
            
            logger.debug(f"Loaded {len(models)} models")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load models: {e}")
    
    def _load_benchmark_results(self):
        """Load benchmark results."""
        logger.debug("Loading benchmark results")
        
        try:
            # Clear the results list
            self.results_list.clear()
            
            # Get benchmark results
            results = get_benchmark_results()
            
            # Add results to the list
            for result in results:
                item = QListWidgetItem(f"{result.model_name} - {result.timestamp}")
                item.setData(Qt.ItemDataRole.UserRole, result)
                self.results_list.addItem(item)
            
            logger.debug(f"Loaded {len(results)} benchmark results")
        except Exception as e:
            logger.error(f"Error loading benchmark results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load benchmark results: {e}")
    
    def _on_run_benchmark(self):
        """Handle run benchmark button clicked."""
        logger.debug("Run benchmark button clicked")
        
        try:
            # Get selected model
            model_id = self.model_combo.currentData()
            
            if not model_id:
                QMessageBox.warning(self, "Error", "Please select a model.")
                return
            
            # Get benchmark parameters
            prompt = self.prompt_edit.toPlainText()
            reference_text = self.reference_text_edit.toPlainText()
            max_tokens = self.max_tokens_spin.value()
            num_runs = self.num_runs_spin.value()
            temperature = self.temperature_spin.value()
            top_p = self.top_p_spin.value()
            save_logprobs = self.save_logprobs_check.isChecked()
            tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
            description = self.description_edit.text()
            
            # Create benchmark
            benchmark = ModelBenchmark(
                model_id=model_id,
                prompt=prompt,
                max_tokens=max_tokens,
                num_runs=num_runs,
                temperature=temperature,
                top_p=top_p,
                tags=tags,
                description=description,
                save_logprobs=save_logprobs,
                reference_text=reference_text if reference_text else None
            )
            
            # Show progress bar
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.progress_label.setText("Initializing benchmark...")
            self.progress_label.setVisible(True)
            
            # Disable run button
            self.run_benchmark_button.setEnabled(False)
            
            # Create and start benchmark thread
            self.benchmark_thread = BenchmarkThread(benchmark)
            self.benchmark_thread.progress_updated.connect(self._on_benchmark_progress)
            self.benchmark_thread.benchmark_complete.connect(self._on_benchmark_complete)
            self.benchmark_thread.error_occurred.connect(self._on_benchmark_error)
            self.benchmark_thread.start()
            
            logger.debug(f"Started benchmark for model {model_id}")
        except Exception as e:
            logger.error(f"Error running benchmark: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run benchmark: {e}")
            
            # Hide progress bar
            self.progress_bar.setVisible(False)
            self.progress_label.setVisible(False)
            
            # Enable run button
            self.run_benchmark_button.setEnabled(True)
    
    def _on_benchmark_progress(self, progress_info: ProgressInfo):
        """
        Handle benchmark progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.progress_label.setText(progress_info.message)
    
    def _on_benchmark_complete(self, result: BenchmarkResult):
        """
        Handle benchmark completion.
        
        Args:
            result: The benchmark result.
        """
        logger.debug(f"Benchmark completed for model {result.model_id}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Enable run button
        self.run_benchmark_button.setEnabled(True)
        
        # Show result
        self.result_model_label.setText(f"{result.model_name} ({result.model_id})")
        self.result_load_time_label.setText(f"{result.load_time_seconds:.2f} seconds")
        self.result_generation_time_label.setText(f"{result.avg_generation_time:.2f} seconds")
        self.result_tokens_per_second_label.setText(f"{result.avg_tokens_per_second:.2f}")
        self.result_memory_label.setText(f"{result.peak_memory_mb:.2f} MB")
        
        # Show generated text
        if result.generated_texts:
            self.result_text_edit.setText(result.generated_texts[0])
        
        # Show result group
        self.result_group.setVisible(True)
        
        # Reload benchmark results
        self._load_benchmark_results()
    
    def _on_benchmark_error(self, error: str):
        """
        Handle benchmark error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Benchmark error: {error}")
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Enable run button
        self.run_benchmark_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Benchmark Error", f"Error running benchmark: {error}")
    
    def _on_result_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handle result selection changed.
        
        Args:
            current: The current selected item.
            previous: The previously selected item.
        """
        if not current:
            return
        
        # Get the result
        result = current.data(Qt.ItemDataRole.UserRole)
        
        # Show result details
        self.result_details_model_label.setText(f"{result.model_name} ({result.model_id})")
        self.result_details_timestamp_label.setText(result.timestamp)
        self.result_details_load_time_label.setText(f"{result.load_time_seconds:.2f} seconds")
        self.result_details_generation_time_label.setText(f"{result.avg_generation_time:.2f} seconds")
        self.result_details_tokens_per_second_label.setText(f"{result.avg_tokens_per_second:.2f}")
        self.result_details_memory_label.setText(f"{result.peak_memory_mb:.2f} MB")
        self.result_details_prompt_label.setText(result.prompt)
        self.result_details_tags_label.setText(", ".join(result.tags) if result.tags else "")
        
        # Show generated text
        if result.generated_texts:
            self.result_details_text_edit.setText(result.generated_texts[0])
        else:
            self.result_details_text_edit.setText("")
    
    def _get_metric_from_combo(self, combo_box: QComboBox) -> str:
        """
        Get the metric name from a combo box selection.
        
        Args:
            combo_box: The combo box with the metric selection.
            
        Returns:
            str: The metric name.
        """
        metric_map = {
            "Tokens per Second": "avg_tokens_per_second",
            "Generation Time": "avg_generation_time",
            "Memory Usage": "peak_memory_mb",
            "Perplexity": "perplexity",
            "BLEU Score": "bleu_score",
            "Response Length Ratio": "response_length_ratio"
        }
        
        return metric_map.get(combo_box.currentText(), "avg_tokens_per_second")
    
    def _visualize_result_history(self):
        """Visualize a result history."""
        logger.debug("Visualizing result history")
        
        try:
            # Check if visualization dependencies are available
            interactive = self.result_interactive_check.isChecked()
            if interactive and not check_visualization_dependencies(include_interactive=True):
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Interactive visualization dependencies are not available. Please install plotly."
                )
                interactive = False
            elif not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Get the selected result
            current_item = self.results_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Error", "Please select a result to visualize.")
                return
            
            result = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Get all results for the same model
            all_results = get_benchmark_results(result.model_id)
            
            # Get the selected metric
            metric = self._get_metric_from_combo(self.result_metric_combo)
            
            # Create a temporary file for the visualization
            suffix = ".html" if interactive else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"{self.result_metric_combo.currentText()}: {result.model_name}"
            
            try:
                fig = plot_benchmark_history(
                    all_results, 
                    result.model_id, 
                    metric, 
                    title=title,
                    interactive=interactive
                )
                
                # Save the visualization
                if interactive:
                    fig.write_html(temp_path)
                else:
                    export_visualization(fig, temp_path)
                
                # Show the visualization
                os.startfile(temp_path)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing result history: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize result history: {e}")
    
    def _visualize_result_correlation(self):
        """Visualize a result correlation."""
        logger.debug("Visualizing result correlation")
        
        try:
            # Check if visualization dependencies are available
            if not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Get the selected result
            current_item = self.results_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Error", "Please select a result to visualize.")
                return
            
            result = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Get all results for the same model
            all_results = get_benchmark_results(result.model_id)
            
            # Get the selected metric
            y_metric = self._get_metric_from_combo(self.result_metric_combo)
            
            # Create a temporary file for the visualization
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"Correlation: Generation Time vs {self.result_metric_combo.currentText()}"
            
            try:
                # Check if we have enough data points
                if len(all_results) < 3:
                    QMessageBox.warning(
                        self, 
                        "Insufficient Data", 
                        "Need at least 3 benchmark results for correlation analysis."
                    )
                    return
                
                # Create the correlation plot
                fig = plot_metric_correlation(
                    all_results,
                    x_metric="avg_generation_time",
                    y_metric=y_metric,
                    title=title
                )
                
                # Save the visualization
                export_visualization(fig, temp_path)
                
                # Show the visualization
                os.startfile(temp_path)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing result correlation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize result correlation: {e}")
    
    def _on_run_comparison(self):
        """Handle run comparison button clicked."""
        logger.debug("Run comparison button clicked")
        
        try:
            # Get selected models
            selected_items = self.comparison_models_list.selectedItems()
            
            if not selected_items or len(selected_items) < 2:
                QMessageBox.warning(self, "Error", "Please select at least two models to compare.")
                return
            
            # Get model IDs
            model_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            
            # Get comparison parameters
            prompt = self.comparison_prompt_edit.toPlainText()
            max_tokens = self.comparison_max_tokens_spin.value()
            num_runs = self.comparison_num_runs_spin.value()
            
            # Show progress bar
            self.comparison_progress_bar.setValue(0)
            self.comparison_progress_bar.setVisible(True)
            self.comparison_progress_label.setText("Initializing comparison...")
            self.comparison_progress_label.setVisible(True)
            
            # Disable run button
            self.run_comparison_button.setEnabled(False)
            
            # Create and start comparison thread
            self.comparison_thread = ComparisonThread(model_ids, prompt, max_tokens, num_runs)
            self.comparison_thread.progress_updated.connect(self._on_comparison_progress)
            self.comparison_thread.comparison_complete.connect(self._on_comparison_complete)
            self.comparison_thread.error_occurred.connect(self._on_comparison_error)
            self.comparison_thread.start()
            
            logger.debug(f"Started comparison for models: {', '.join(model_ids)}")
        except Exception as e:
            logger.error(f"Error running comparison: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run comparison: {e}")
            
            # Hide progress bar
            self.comparison_progress_bar.setVisible(False)
            self.comparison_progress_label.setVisible(False)
            
            # Enable run button
            self.run_comparison_button.setEnabled(True)
    
    def _on_comparison_progress(self, progress_info: ProgressInfo):
        """
        Handle comparison progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.comparison_progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.comparison_progress_label.setText(progress_info.message)
    
    def _on_comparison_complete(self, results: Dict[str, BenchmarkResult]):
        """
        Handle comparison completion.
        
        Args:
            results: The comparison results.
        """
        logger.debug(f"Comparison completed for {len(results)} models")
        
        # Hide progress bar
        self.comparison_progress_bar.setVisible(False)
        self.comparison_progress_label.setVisible(False)
        
        # Enable run button
        self.run_comparison_button.setEnabled(True)
        
        # Store the results
        self.comparison_results = results
        
        # Show visualization group
        self.visualization_group.setVisible(True)
        
        # Update visualization label
        self.visualization_label.setText(f"Comparison completed for {len(results)} models. Select a visualization type.")
        
        # Visualize tokens per second by default
        self._visualize_comparison("avg_tokens_per_second")
    
    def _on_comparison_error(self, error: str):
        """
        Handle comparison error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Comparison error: {error}")
        
        # Hide progress bar
        self.comparison_progress_bar.setVisible(False)
        self.comparison_progress_label.setVisible(False)
        
        # Enable run button
        self.run_comparison_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Comparison Error", f"Error running comparison: {error}")
    
    def _visualize_comparison_bar(self):
        """Visualize a comparison using a bar chart."""
        logger.debug("Visualizing comparison with bar chart")
        
        try:
            # Check if visualization dependencies are available
            interactive = self.comparison_interactive_check.isChecked()
            if interactive and not check_visualization_dependencies(include_interactive=True):
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Interactive visualization dependencies are not available. Please install plotly."
                )
                interactive = False
            elif not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Check if comparison results are available
            if not hasattr(self, "comparison_results") or not self.comparison_results:
                QMessageBox.warning(self, "Error", "No comparison results available. Run a comparison first.")
                return
            
            # Get the selected metric
            metric = self._get_metric_from_combo(self.comparison_metric_combo)
            
            # Create a temporary file for the visualization
            suffix = ".html" if interactive else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = f"Model Comparison: {self.comparison_metric_combo.currentText()}"
            
            # Sort ascending for metrics where lower is better
            sort_ascending = metric in ["avg_generation_time", "load_time_seconds", "peak_memory_mb", "perplexity"]
            
            try:
                # Create the visualization
                fig = plot_model_comparison(
                    list(self.comparison_results.values()), 
                    metric, 
                    title=title, 
                    sort_ascending=sort_ascending,
                    interactive=interactive
                )
                
                # Save the visualization
                if interactive:
                    # Save as HTML for interactive visualization
                    fig.write_html(temp_path)
                    
                    # Open in browser
                    os.startfile(temp_path)
                    
                    # Create a static version for display in the UI
                    static_temp_path = temp_path.replace(".html", ".png")
                    static_fig = plot_model_comparison(
                        list(self.comparison_results.values()), 
                        metric, 
                        title=title, 
                        sort_ascending=sort_ascending,
                        interactive=False
                    )
                    export_visualization(static_fig, static_temp_path)
                    
                    # Load the static visualization for display
                    pixmap = QPixmap(static_temp_path)
                    self.visualization_image_label.setPixmap(pixmap)
                    
                    # Store both paths
                    self.current_visualization_path = temp_path
                    self.current_static_visualization_path = static_temp_path
                else:
                    # Save and display static visualization
                    export_visualization(fig, temp_path)
                    pixmap = QPixmap(temp_path)
                    self.visualization_image_label.setPixmap(pixmap)
                    self.current_visualization_path = temp_path
                
                # Enable save button
                self.save_visualization_button.setEnabled(True)
                
                logger.debug(f"Visualization saved to {temp_path}")
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))
                return
            
        except Exception as e:
            logger.error(f"Error visualizing comparison: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize comparison: {e}")
    
    def _visualize_comparison_radar(self):
        """Visualize a comparison using a radar chart."""
        logger.debug("Visualizing comparison with radar chart")
    
    def _visualize_comparison_radar(self):
        """Visualize a comparison using a radar chart."""
        logger.debug("Visualizing comparison with radar chart")
        
        try:
            # Check if visualization dependencies are available
            if not check_visualization_dependencies():
                QMessageBox.warning(
                    self,
                    "Missing Dependencies",
                    "Visualization dependencies are not available. Please install matplotlib, seaborn, and pandas."
                )
                return
            
            # Check if comparison results are available
            if not hasattr(self, "comparison_results") or not self.comparison_results:
                QMessageBox.warning(self, "Error", "No comparison results available. Run a comparison first.")
                return
            
            # Create a temporary file for the visualization
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Create the visualization
            title = "Model Comparison: Radar Chart"
            # Extract model IDs from the benchmark results
            model_ids = [result.model_id for result in self.comparison_results.values()]
            
            fig = plot_model_radar_chart(
                list(self.comparison_results.values()),
                model_ids,
                title=title
            )
            
            # Save the visualization
            export_visualization(fig, temp_path)
            
            # Load the visualization
            pixmap = QPixmap(temp_path)
            self.visualization_image_label.setPixmap(pixmap)
            
            # Store the visualization path
            self.current_visualization_path = temp_path
            
            # Enable save button
            self.save_visualization_button.setEnabled(True)
            
            logger.debug(f"Visualization saved to {temp_path}")
        except Exception as e:
            logger.error(f"Error visualizing comparison with radar chart: {e}")
            QMessageBox.critical(self, "Error", f"Failed to visualize comparison with radar chart: {e}")
    
    def _on_save_visualization(self):
        """Handle save visualization button clicked."""
        logger.debug("Save visualization button clicked")
        
        try:
            # Check if a visualization is available
            if not hasattr(self, "current_visualization_path") or not self.current_visualization_path:
                QMessageBox.warning(self, "Error", "No visualization available to save.")
                return
            
            # Show file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Visualization",
                "",
                "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg)"
            )
            
            if not file_path:
                return
            
            # Copy the visualization
            import shutil
            shutil.copy2(self.current_visualization_path, file_path)
            
            logger.debug(f"Visualization saved to {file_path}")
            QMessageBox.information(self, "Success", f"Visualization saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving visualization: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save visualization: {e}")
    
    def _on_generate_report(self):
        """Handle generate report button clicked."""
        logger.debug("Generate report button clicked")
        
        try:
            # Get selected model
            model_id = None
            if self.report_model_combo.currentIndex() > 0:  # Skip "All Models"
                model_id = self.report_model_combo.currentData()
            
            # Get include plots
            include_plots = self.report_include_plots_check.isChecked()
            
            # Show progress bar
            self.report_progress_bar.setValue(0)
            self.report_progress_bar.setVisible(True)
            self.report_progress_label.setText("Generating report...")
            self.report_progress_label.setVisible(True)
            
            # Disable generate button
            self.generate_report_button.setEnabled(False)
            
            # Get benchmark results
            results = get_benchmark_results(model_id)
            
            if not results:
                QMessageBox.warning(self, "Error", "No benchmark results available.")
                
                # Hide progress bar
                self.report_progress_bar.setVisible(False)
                self.report_progress_label.setVisible(False)
                
                # Enable generate button
                self.generate_report_button.setEnabled(True)
                return
            
            # Update progress
            self.report_progress_bar.setValue(50)
            self.report_progress_label.setText("Generating HTML report...")
            
            # Generate HTML report
            html_report = generate_benchmark_report_html(
                results,
                include_plots=include_plots,
                model_ids=[model_id] if model_id else None
            )
            
            # Create a temporary file for the report
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
                temp_file.write(html_report.encode("utf-8"))
                self.report_path = temp_file.name
            
            # Update progress
            self.report_progress_bar.setValue(100)
            self.report_progress_label.setText("Report generated successfully.")
            
            # Show report preview
            self.report_preview_text.setHtml(html_report)
            self.report_preview_group.setVisible(True)
            
            # Enable open in browser button
            self.open_report_button.setEnabled(True)
            
            # Enable generate button
            self.generate_report_button.setEnabled(True)
            
            logger.debug(f"Report generated and saved to {self.report_path}")
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")
            
            # Hide progress bar
            self.report_progress_bar.setVisible(False)
            self.report_progress_label.setVisible(False)
            
            # Enable generate button
            self.generate_report_button.setEnabled(True)
    
    def _on_open_report(self):
        """Handle open report button clicked."""
        logger.debug("Open report button clicked")
        
        try:
            # Check if a report is available
            if not hasattr(self, "report_path") or not self.report_path:
                QMessageBox.warning(self, "Error", "No report available to open.")
                return
            
            # Open the report in the default browser
            webbrowser.open(f"file://{self.report_path}")
            
            logger.debug(f"Report opened in browser: {self.report_path}")
        except Exception as e:
            logger.error(f"Error opening report: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open report: {e}")
