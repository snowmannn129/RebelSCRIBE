#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Batch Benchmark Dialog

This module implements a dialog for batch benchmarking AI models using templates
and generating comprehensive reports.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox, QSplitter, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import Qt

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.model_registry import ModelRegistry
from src.ai.batch_benchmarking import (
    get_benchmark_templates, get_batch_benchmarks, get_batch_results
)

from src.ui.batch_benchmark_templates import BatchBenchmarkTemplates
from src.ui.batch_benchmark_batches import BatchBenchmarkBatches
from src.ui.batch_benchmark_results import BatchBenchmarkResults

logger = get_logger(__name__)
config = ConfigManager()


class BatchBenchmarkDialog(QDialog, BatchBenchmarkTemplates, BatchBenchmarkBatches, BatchBenchmarkResults):
    """
    Batch benchmark dialog for RebelSCRIBE.
    
    This dialog allows users to:
    - Create and manage benchmark templates
    - Run batch benchmarks on multiple models
    - View and export benchmark results
    """
    
    def __init__(self, parent=None):
        """
        Initialize the batch benchmark dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        # Load models
        self._load_models()
        
        # Load templates
        self._load_templates()
        
        # Load batches
        self._load_batches()
        
        # Load results
        self._load_results()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Batch benchmark dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing batch benchmark dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Batch Benchmarking")
        self.setMinimumSize(900, 700)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_templates_tab()
        self._create_batches_tab()
        self._create_results_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Batch benchmark dialog UI components initialized")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.rejected.connect(self.reject)
        
        # Connect tab-specific signals
        self._connect_template_signals()
        self._connect_batch_signals()
        self._connect_result_signals()
        
        logger.debug("Signals connected")
    
    def _create_splitter(self, orientation):
        """
        Create a splitter with the given orientation.
        
        Args:
            orientation: The orientation of the splitter.
            
        Returns:
            The created splitter.
        """
        return QSplitter(orientation)
    
    def _get_benchmark_templates(self):
        """
        Get benchmark templates.
        
        Returns:
            The benchmark templates.
        """
        return get_benchmark_templates()
    
    def _get_batch_benchmarks(self):
        """
        Get batch benchmarks.
        
        Returns:
            The batch benchmarks.
        """
        return get_batch_benchmarks()
    
    def _get_batch_results(self):
        """
        Get batch results.
        
        Returns:
            The batch results.
        """
        return get_batch_results()
    
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
            
            # Add models to the batch models list
            self.batch_models_list.clear()
            for model in models:
                item = QListWidgetItem(f"{model.name} ({model.id})")
                item.setData(Qt.ItemDataRole.UserRole, model.id)
                self.batch_models_list.addItem(item)
            
            logger.debug(f"Loaded {len(models)} models")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load models: {e}")
