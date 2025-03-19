#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Adapter Configuration Dialog

This module implements a dialog for configuring model adapters for fine-tuning.
"""

import os
import sys
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QProgressBar, QRadioButton, QButtonGroup, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.adapter_support import AdapterManager
from src.ai.model_registry import ModelRegistry
from src.ai.dataset_preparation import DatasetPreparation
from src.ui.training_visualization_dialog import TrainingVisualizationDialog
from src.ai.training_monitor import TrainingMonitor
from peft import TaskType

logger = get_logger(__name__)
config = ConfigManager()


class AdapterType(Enum):
    """Enum for adapter types."""
    LORA = "lora"
    QLORA = "qlora"
    PREFIX_TUNING = "prefix_tuning"


class DatasetFormat(Enum):
    """Enum for dataset formats."""
    TEXT = "text"
    INSTRUCTION = "instruction"
    CONVERSATION = "conversation"


class AdapterConfigDialog(QDialog):
    """
    Adapter configuration dialog for RebelSCRIBE.
    
    This dialog allows users to configure model adapters for fine-tuning:
    - Adapter type selection (LoRA, QLoRA, Prefix Tuning)
    - Base model selection
    - Adapter parameters configuration
    - Dataset preparation and selection
    - Training configuration
    """
    
    # Signal emitted when adapter configuration is changed
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, adapter_manager=None, model_registry=None, dataset_preparation=None):
        """
        Initialize the adapter configuration dialog.
        
        Args:
            parent: The parent widget.
            adapter_manager: The adapter manager instance.
            model_registry: The model registry instance.
            dataset_preparation: The dataset preparation instance.
        """
        super().__init__(parent)
        
        self.adapter_manager = adapter_manager or AdapterManager()
        self.model_registry = model_registry or ModelRegistry()
        self.dataset_preparation = dataset_preparation or DatasetPreparation()
        
        # Initialize UI components
        self._init_ui()
        
        # Load current configuration
        self._load_configuration()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Adapter configuration dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing adapter configuration dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Adapter Configuration")
        self.setMinimumSize(700, 500)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_adapter_tab()
        self._create_dataset_tab()
        self._create_training_tab()
        self._create_evaluation_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Adapter configuration dialog UI components initialized")
    
    def _create_adapter_tab(self):
        """Create the adapter configuration tab."""
        logger.debug("Creating adapter configuration tab")
        
        # Create tab widget
        self.adapter_tab = QWidget()
        self.tab_widget.addTab(self.adapter_tab, "Adapter")
        
        # Create layout
        layout = QVBoxLayout(self.adapter_tab)
        
        # Base model selection group
        base_model_group = QGroupBox("Base Model")
        base_model_layout = QFormLayout(base_model_group)
        
        self.base_model_combo = QComboBox()
        self.base_model_combo.setEditable(True)
        
        # Populate with available models from model registry
        available_models = self.model_registry.get_all_models()
        for model in available_models:
            self.base_model_combo.addItem(model)
        
        base_model_layout.addRow("Model:", self.base_model_combo)
        
        # Add a refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._refresh_models)
        base_model_layout.addRow("", refresh_button)
        
        layout.addWidget(base_model_group)
        
        # Adapter type selection group
        adapter_type_group = QGroupBox("Adapter Type")
        adapter_type_layout = QVBoxLayout(adapter_type_group)
        
        self.adapter_type_radio_group = QButtonGroup(self)
        
        # LoRA radio button
        self.lora_radio = QRadioButton("LoRA (Low-Rank Adaptation)")
        self.lora_radio.setToolTip("Efficient fine-tuning by adding low-rank matrices to transformer layers")
        self.adapter_type_radio_group.addButton(self.lora_radio, 0)
        adapter_type_layout.addWidget(self.lora_radio)
        
        # QLoRA radio button
        self.qlora_radio = QRadioButton("QLoRA (Quantized LoRA)")
        self.qlora_radio.setToolTip("LoRA with quantized base model for memory efficiency")
        self.adapter_type_radio_group.addButton(self.qlora_radio, 1)
        adapter_type_layout.addWidget(self.qlora_radio)
        
        # Prefix Tuning radio button
        self.prefix_tuning_radio = QRadioButton("Prefix Tuning")
        self.prefix_tuning_radio.setToolTip("Adds trainable continuous prefix vectors to transformer layers")
        self.adapter_type_radio_group.addButton(self.prefix_tuning_radio, 2)
        adapter_type_layout.addWidget(self.prefix_tuning_radio)
        
        # Set default
        self.lora_radio.setChecked(True)
        
        layout.addWidget(adapter_type_group)
        
        # Adapter parameters group
        self.adapter_params_group = QGroupBox("Adapter Parameters")
        self.adapter_params_layout = QFormLayout(self.adapter_params_group)
        
        # Common parameters
        self.adapter_name_edit = QLineEdit()
        self.adapter_name_edit.setPlaceholderText("Enter a name for this adapter")
        self.adapter_params_layout.addRow("Adapter Name:", self.adapter_name_edit)
        
        # LoRA parameters
        self.lora_params_widget = QWidget()
        lora_params_layout = QFormLayout(self.lora_params_widget)
        
        self.lora_r_spin = QSpinBox()
        self.lora_r_spin.setRange(1, 256)
        self.lora_r_spin.setValue(8)
        self.lora_r_spin.setToolTip("Rank of the update matrices")
        lora_params_layout.addRow("Rank (r):", self.lora_r_spin)
        
        self.lora_alpha_spin = QSpinBox()
        self.lora_alpha_spin.setRange(1, 512)
        self.lora_alpha_spin.setValue(16)
        self.lora_alpha_spin.setToolTip("Alpha parameter for LoRA scaling")
        lora_params_layout.addRow("Alpha:", self.lora_alpha_spin)
        
        self.lora_dropout_spin = QDoubleSpinBox()
        self.lora_dropout_spin.setRange(0.0, 0.9)
        self.lora_dropout_spin.setValue(0.05)
        self.lora_dropout_spin.setSingleStep(0.05)
        self.lora_dropout_spin.setToolTip("Dropout probability for LoRA layers")
        lora_params_layout.addRow("Dropout:", self.lora_dropout_spin)
        
        self.target_modules_edit = QLineEdit()
        self.target_modules_edit.setPlaceholderText("q_proj,k_proj,v_proj,o_proj (comma-separated, leave empty for auto)")
        self.target_modules_edit.setToolTip("Comma-separated list of module names to apply LoRA to")
        lora_params_layout.addRow("Target Modules:", self.target_modules_edit)
        
        self.bias_combo = QComboBox()
        self.bias_combo.addItems(["none", "all", "lora_only"])
        self.bias_combo.setToolTip("Bias configuration for LoRA")
        lora_params_layout.addRow("Bias:", self.bias_combo)
        
        # QLoRA specific parameters
        self.qlora_params_widget = QWidget()
        qlora_params_layout = QFormLayout(self.qlora_params_widget)
        
        self.quantization_bits_combo = QComboBox()
        self.quantization_bits_combo.addItems(["4", "8"])
        self.quantization_bits_combo.setToolTip("Number of bits for quantization")
        qlora_params_layout.addRow("Quantization Bits:", self.quantization_bits_combo)
        
        # Prefix Tuning parameters
        self.prefix_tuning_params_widget = QWidget()
        prefix_tuning_params_layout = QFormLayout(self.prefix_tuning_params_widget)
        
        self.num_virtual_tokens_spin = QSpinBox()
        self.num_virtual_tokens_spin.setRange(1, 100)
        self.num_virtual_tokens_spin.setValue(20)
        self.num_virtual_tokens_spin.setToolTip("Number of virtual tokens to add as prefix")
        prefix_tuning_params_layout.addRow("Virtual Tokens:", self.num_virtual_tokens_spin)
        
        self.prefix_projection_check = QCheckBox("Use projection")
        self.prefix_projection_check.setToolTip("Whether to use a projection matrix for the prefix")
        prefix_tuning_params_layout.addRow("Projection:", self.prefix_projection_check)
        
        # Add parameter widgets to layout
        self.adapter_params_layout.addRow(self.lora_params_widget)
        self.adapter_params_layout.addRow(self.qlora_params_widget)
        self.adapter_params_layout.addRow(self.prefix_tuning_params_widget)
        
        # Initially show only LoRA parameters
        self.lora_params_widget.setVisible(True)
        self.qlora_params_widget.setVisible(False)
        self.prefix_tuning_params_widget.setVisible(False)
        
        layout.addWidget(self.adapter_params_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Adapter configuration tab created")
    
    def _create_dataset_tab(self):
        """Create the dataset configuration tab."""
        logger.debug("Creating dataset configuration tab")
        
        # Create tab widget
        self.dataset_tab = QWidget()
        self.tab_widget.addTab(self.dataset_tab, "Dataset")
        
        # Create layout
        layout = QVBoxLayout(self.dataset_tab)
        
        # Dataset source group
        dataset_source_group = QGroupBox("Dataset Source")
        dataset_source_layout = QVBoxLayout(dataset_source_group)
        
        self.dataset_source_radio_group = QButtonGroup(self)
        
        # File radio button
        self.file_radio = QRadioButton("Load from file")
        self.dataset_source_radio_group.addButton(self.file_radio, 0)
        dataset_source_layout.addWidget(self.file_radio)
        
        # File selection
        file_layout = QHBoxLayout()
        self.dataset_file_edit = QLineEdit()
        self.dataset_file_edit.setPlaceholderText("Select a dataset file")
        file_layout.addWidget(self.dataset_file_edit)
        
        self.dataset_file_button = QPushButton("Browse...")
        file_layout.addWidget(self.dataset_file_button)
        
        dataset_source_layout.addLayout(file_layout)
        
        # Format selection for file
        file_format_layout = QFormLayout()
        self.file_format_combo = QComboBox()
        self.file_format_combo.addItems(["JSON", "CSV", "JSONL", "TXT"])
        file_format_layout.addRow("File Format:", self.file_format_combo)
        dataset_source_layout.addLayout(file_format_layout)
        
        # Manual entry radio button
        self.manual_radio = QRadioButton("Manual entry")
        self.dataset_source_radio_group.addButton(self.manual_radio, 1)
        dataset_source_layout.addWidget(self.manual_radio)
        
        # Set default
        self.file_radio.setChecked(True)
        
        layout.addWidget(dataset_source_group)
        
        # Dataset format group
        dataset_format_group = QGroupBox("Dataset Format")
        dataset_format_layout = QVBoxLayout(dataset_format_group)
        
        self.dataset_format_radio_group = QButtonGroup(self)
        
        # Text format radio button
        self.text_format_radio = QRadioButton("Text (continuous text samples)")
        self.text_format_radio.setToolTip("Simple text samples for general fine-tuning")
        self.dataset_format_radio_group.addButton(self.text_format_radio, 0)
        dataset_format_layout.addWidget(self.text_format_radio)
        
        # Instruction format radio button
        self.instruction_format_radio = QRadioButton("Instruction (prompt-completion pairs)")
        self.instruction_format_radio.setToolTip("Instruction-following format with prompt-completion pairs")
        self.dataset_format_radio_group.addButton(self.instruction_format_radio, 1)
        dataset_format_layout.addWidget(self.instruction_format_radio)
        
        # Conversation format radio button
        self.conversation_format_radio = QRadioButton("Conversation (multi-turn dialogues)")
        self.conversation_format_radio.setToolTip("Multi-turn conversation format for dialogue models")
        self.dataset_format_radio_group.addButton(self.conversation_format_radio, 2)
        dataset_format_layout.addWidget(self.conversation_format_radio)
        
        # Set default
        self.instruction_format_radio.setChecked(True)
        
        layout.addWidget(dataset_format_group)
        
        # Dataset content group
        dataset_content_group = QGroupBox("Dataset Content")
        dataset_content_layout = QVBoxLayout(dataset_content_group)
        
        # Create a scroll area for the dataset content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        dataset_content_layout.addWidget(scroll_area)
        
        # Create a widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Text format widget
        self.text_format_widget = QWidget()
        text_format_layout = QVBoxLayout(self.text_format_widget)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter text samples, one per line")
        text_format_layout.addWidget(self.text_edit)
        
        # Instruction format widget
        self.instruction_format_widget = QWidget()
        instruction_format_layout = QVBoxLayout(self.instruction_format_widget)
        
        # Create a table for instruction-completion pairs
        self.instruction_table = QTableWidget(0, 2)
        self.instruction_table.setHorizontalHeaderLabels(["Prompt", "Completion"])
        self.instruction_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        instruction_format_layout.addWidget(self.instruction_table)
        
        # Add buttons to add/remove rows
        instruction_buttons_layout = QHBoxLayout()
        
        self.add_instruction_button = QPushButton("Add Row")
        instruction_buttons_layout.addWidget(self.add_instruction_button)
        
        self.remove_instruction_button = QPushButton("Remove Row")
        instruction_buttons_layout.addWidget(self.remove_instruction_button)
        
        instruction_format_layout.addLayout(instruction_buttons_layout)
        
        # Conversation format widget
        self.conversation_format_widget = QWidget()
        conversation_format_layout = QVBoxLayout(self.conversation_format_widget)
        
        # Create a list for conversations
        self.conversation_list = QListWidget()
        conversation_format_layout.addWidget(self.conversation_list)
        
        # Add buttons to add/remove conversations
        conversation_buttons_layout = QHBoxLayout()
        
        self.add_conversation_button = QPushButton("Add Conversation")
        conversation_buttons_layout.addWidget(self.add_conversation_button)
        
        self.remove_conversation_button = QPushButton("Remove Conversation")
        conversation_buttons_layout.addWidget(self.remove_conversation_button)
        
        conversation_format_layout.addLayout(conversation_buttons_layout)
        
        # Add format widgets to scroll layout
        scroll_layout.addWidget(self.text_format_widget)
        scroll_layout.addWidget(self.instruction_format_widget)
        scroll_layout.addWidget(self.conversation_format_widget)
        
        # Initially show only instruction format widget
        self.text_format_widget.setVisible(False)
        self.instruction_format_widget.setVisible(True)
        self.conversation_format_widget.setVisible(False)
        
        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        
        layout.addWidget(dataset_content_group)
        
        # Dataset statistics group
        dataset_stats_group = QGroupBox("Dataset Statistics")
        dataset_stats_layout = QFormLayout(dataset_stats_group)
        
        self.sample_count_label = QLabel("0")
        dataset_stats_layout.addRow("Samples:", self.sample_count_label)
        
        self.token_count_label = QLabel("0")
        dataset_stats_layout.addRow("Estimated Tokens:", self.token_count_label)
        
        layout.addWidget(dataset_stats_group)
        
        logger.debug("Dataset configuration tab created")
    
    def _create_training_tab(self):
        """Create the training configuration tab."""
        logger.debug("Creating training configuration tab")
        
        # Create tab widget
        self.training_tab = QWidget()
        self.tab_widget.addTab(self.training_tab, "Training")
        
        # Create layout
        layout = QVBoxLayout(self.training_tab)
        
        # Training parameters group
        training_params_group = QGroupBox("Training Parameters")
        training_params_layout = QFormLayout(training_params_group)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 64)
        self.batch_size_spin.setValue(4)
        self.batch_size_spin.setToolTip("Number of samples per batch")
        training_params_layout.addRow("Batch Size:", self.batch_size_spin)
        
        self.gradient_accumulation_spin = QSpinBox()
        self.gradient_accumulation_spin.setRange(1, 32)
        self.gradient_accumulation_spin.setValue(4)
        self.gradient_accumulation_spin.setToolTip("Number of batches to accumulate gradients for")
        training_params_layout.addRow("Gradient Accumulation:", self.gradient_accumulation_spin)
        
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 100)
        self.epochs_spin.setValue(3)
        self.epochs_spin.setToolTip("Number of training epochs")
        training_params_layout.addRow("Epochs:", self.epochs_spin)
        
        self.learning_rate_spin = QDoubleSpinBox()
        self.learning_rate_spin.setRange(1e-6, 1e-2)
        self.learning_rate_spin.setValue(3e-4)
        self.learning_rate_spin.setDecimals(6)
        self.learning_rate_spin.setSingleStep(1e-5)
        self.learning_rate_spin.setToolTip("Learning rate for training")
        training_params_layout.addRow("Learning Rate:", self.learning_rate_spin)
        
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(16, 4096)
        self.max_length_spin.setValue(512)
        self.max_length_spin.setToolTip("Maximum sequence length")
        training_params_layout.addRow("Max Length:", self.max_length_spin)
        
        self.fp16_check = QCheckBox("Enable")
        self.fp16_check.setChecked(True)
        self.fp16_check.setToolTip("Use mixed precision training (faster but may affect quality)")
        training_params_layout.addRow("FP16:", self.fp16_check)
        
        layout.addWidget(training_params_group)
        
        # Output directory group
        output_dir_group = QGroupBox("Output Directory")
        output_dir_layout = QHBoxLayout(output_dir_group)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory")
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.output_dir_button = QPushButton("Browse...")
        output_dir_layout.addWidget(self.output_dir_button)
        
        layout.addWidget(output_dir_group)
        
        # Training control group
        training_control_group = QGroupBox("Training Control")
        training_control_layout = QVBoxLayout(training_control_group)
        
        # Progress bar
        self.training_progress_bar = QProgressBar()
        self.training_progress_bar.setRange(0, 100)
        self.training_progress_bar.setValue(0)
        training_control_layout.addWidget(self.training_progress_bar)
        
        # Status label
        self.training_status_label = QLabel("Ready")
        training_control_layout.addWidget(self.training_status_label)
        
        # Control buttons
        control_buttons_layout = QHBoxLayout()
        
        self.start_training_button = QPushButton("Start Training")
        control_buttons_layout.addWidget(self.start_training_button)
        
        self.stop_training_button = QPushButton("Stop Training")
        self.stop_training_button.setEnabled(False)
        control_buttons_layout.addWidget(self.stop_training_button)
        
        self.load_results_button = QPushButton("Load Results")
        control_buttons_layout.addWidget(self.load_results_button)
        
        training_control_layout.addLayout(control_buttons_layout)
        
        layout.addWidget(training_control_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Training configuration tab created")
    
    def _create_evaluation_tab(self):
        """Create the evaluation tab."""
        logger.debug("Creating evaluation tab")
        
        # Create tab widget
        self.evaluation_tab = QWidget()
        self.tab_widget.addTab(self.evaluation_tab, "Evaluation")
        
        # Create layout
        layout = QVBoxLayout(self.evaluation_tab)
        
        # Evaluation dataset group
        eval_dataset_group = QGroupBox("Evaluation Dataset")
        eval_dataset_layout = QVBoxLayout(eval_dataset_group)
        
        self.use_train_split_check = QCheckBox("Use portion of training data for evaluation")
        self.use_train_split_check.setChecked(True)
        eval_dataset_layout.addWidget(self.use_train_split_check)
        
        # Train/eval split
        split_layout = QFormLayout()
        
        self.eval_split_spin = QSpinBox()
        self.eval_split_spin.setRange(5, 50)
        self.eval_split_spin.setValue(10)
        self.eval_split_spin.setSuffix("%")
        self.eval_split_spin.setToolTip("Percentage of training data to use for evaluation")
        split_layout.addRow("Evaluation Split:", self.eval_split_spin)
        
        eval_dataset_layout.addLayout(split_layout)
        
        # Separate evaluation dataset
        self.separate_eval_check = QCheckBox("Use separate evaluation dataset")
        eval_dataset_layout.addWidget(self.separate_eval_check)
        
        # Separate dataset file selection
        separate_eval_layout = QHBoxLayout()
        
        self.eval_file_edit = QLineEdit()
        self.eval_file_edit.setPlaceholderText("Select evaluation dataset file")
        self.eval_file_edit.setEnabled(False)
        separate_eval_layout.addWidget(self.eval_file_edit)
        
        self.eval_file_button = QPushButton("Browse...")
        self.eval_file_button.setEnabled(False)
        separate_eval_layout.addWidget(self.eval_file_button)
        
        eval_dataset_layout.addLayout(separate_eval_layout)
        
        layout.addWidget(eval_dataset_group)
        
        # Evaluation metrics group
        eval_metrics_group = QGroupBox("Evaluation Metrics")
        eval_metrics_layout = QVBoxLayout(eval_metrics_group)
        
        self.perplexity_check = QCheckBox("Perplexity")
        self.perplexity_check.setChecked(True)
        self.perplexity_check.setToolTip("Measure of how well the model predicts the evaluation data")
        eval_metrics_layout.addWidget(self.perplexity_check)
        
        self.bleu_check = QCheckBox("BLEU Score")
        self.bleu_check.setChecked(True)
        self.bleu_check.setToolTip("Measure of text generation quality compared to reference text")
        eval_metrics_layout.addWidget(self.bleu_check)
        
        self.rouge_check = QCheckBox("ROUGE Score")
        self.rouge_check.setChecked(True)
        self.rouge_check.setToolTip("Measure of overlap between generated and reference text")
        eval_metrics_layout.addWidget(self.rouge_check)
        
        layout.addWidget(eval_metrics_group)
        
        # Evaluation results group
        eval_results_group = QGroupBox("Evaluation Results")
        eval_results_layout = QVBoxLayout(eval_results_group)
        
        # Create a table for evaluation results
        self.eval_results_table = QTableWidget(0, 2)
        self.eval_results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.eval_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        eval_results_layout.addWidget(self.eval_results_table)
        
        # Evaluation control buttons
        eval_buttons_layout = QHBoxLayout()
        
        self.run_eval_button = QPushButton("Run Evaluation")
        eval_buttons_layout.addWidget(self.run_eval_button)
        
        self.export_eval_button = QPushButton("Export Results")
        self.export_eval_button.setEnabled(False)
        eval_buttons_layout.addWidget(self.export_eval_button)
        
        eval_results_layout.addLayout(eval_buttons_layout)
        
        layout.addWidget(eval_results_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Evaluation tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        
        # Connect adapter tab signals
        self.adapter_type_radio_group.buttonClicked.connect(self._on_adapter_type_changed)
        
        # Connect dataset tab signals
        self.dataset_source_radio_group.buttonClicked.connect(self._on_dataset_source_changed)
        self.dataset_format_radio_group.buttonClicked.connect(self._on_dataset_format_changed)
        self.dataset_file_button.clicked.connect(self._on_browse_dataset_file)
        self.add_instruction_button.clicked.connect(self._on_add_instruction_row)
        self.remove_instruction_button.clicked.connect(self._on_remove_instruction_row)
        self.add_conversation_button.clicked.connect(self._on_add_conversation)
        self.remove_conversation_button.clicked.connect(self._on_remove_conversation)
        
        # Connect training tab signals
        self.output_dir_button.clicked.connect(self._on_browse_output_dir)
        self.start_training_button.clicked.connect(self._on_start_training)
        self.stop_training_button.clicked.connect(self._on_stop_training)
        self.load_results_button.clicked.connect(self._on_load_results_clicked)
        
        # Connect evaluation tab signals
        self.separate_eval_check.toggled.connect(self._on_separate_eval_toggled)
        self.eval_file_button.clicked.connect(self._on_browse_eval_file)
        self.run_eval_button.clicked.connect(self._on_run_evaluation)
        self.export_eval_button.clicked.connect(self._on_export_evaluation)
        
        logger.debug("Signals connected")
    
    def _load_configuration(self):
        """Load current adapter configuration."""
        logger.debug("Loading current adapter configuration")
        
        try:
            # Get adapter configuration from config
            adapter_config = config.get_config().get("adapter", {})
            
            # Load base model
            base_model = adapter_config.get("base_model", "")
            if base_model:
                index = self.base_model_combo.findText(base_model)
                if index >= 0:
                    self.base_model_combo.setCurrentIndex(index)
                else:
                    self.base_model_combo.setCurrentText(base_model)
            
            # Load adapter type
            adapter_type = adapter_config.get("adapter_type", "lora")
            if adapter_type == "lora":
                self.lora_radio.setChecked(True)
                self._on_adapter_type_changed(self.lora_radio)
            elif adapter_type == "qlora":
                self.qlora_radio.setChecked(True)
                self._on_adapter_type_changed(self.qlora_radio)
            elif adapter_type == "prefix_tuning":
                self.prefix_tuning_radio.setChecked(True)
                self._on_adapter_type_changed(self.prefix_tuning_radio)
            
            # Load adapter parameters
            adapter_params = adapter_config.get("adapter_params", {})
            
            # Common parameters
            self.adapter_name_edit.setText(adapter_params.get("name", ""))
            
            # LoRA parameters
            self.lora_r_spin.setValue(adapter_params.get("lora_r", 8))
            self.lora_alpha_spin.setValue(adapter_params.get("lora_alpha", 16))
            self.lora_dropout_spin.setValue(adapter_params.get("lora_dropout", 0.05))
            
            target_modules = adapter_params.get("target_modules", [])
            if target_modules:
                self.target_modules_edit.setText(",".join(target_modules))
            
            bias = adapter_params.get("bias", "none")
            index = self.bias_combo.findText(bias)
            if index >= 0:
                self.bias_combo.setCurrentIndex(index)
            
            # QLoRA parameters
            quantization_bits = str(adapter_params.get("quantization_bits", 4))
            index = self.quantization_bits_combo.findText(quantization_bits)
            if index >= 0:
                self.quantization_bits_combo.setCurrentIndex(index)
            
            # Prefix Tuning parameters
            self.num_virtual_tokens_spin.setValue(adapter_params.get("num_virtual_tokens", 20))
            self.prefix_projection_check.setChecked(adapter_params.get("prefix_projection", False))
            
            # Load dataset configuration
            dataset_config = adapter_config.get("dataset", {})
            
            # Dataset source
            dataset_source = dataset_config.get("source", "file")
            if dataset_source == "file":
                self.file_radio.setChecked(True)
                self._on_dataset_source_changed(self.file_radio)
            elif dataset_source == "manual":
                self.manual_radio.setChecked(True)
                self._on_dataset_source_changed(self.manual_radio)
            
            # Dataset file
            self.dataset_file_edit.setText(dataset_config.get("file_path", ""))
            
            # File format
            file_format = dataset_config.get("file_format", "JSON")
            index = self.file_format_combo.findText(file_format)
            if index >= 0:
                self.file_format_combo.setCurrentIndex(index)
            
            # Dataset format
            dataset_format = dataset_config.get("format", "instruction")
            if dataset_format == "text":
                self.text_format_radio.setChecked(True)
                self._on_dataset_format_changed(self.text_format_radio)
            elif dataset_format == "instruction":
                self.instruction_format_radio.setChecked(True)
                self._on_dataset_format_changed(self.instruction_format_radio)
            elif dataset_format == "conversation":
                self.conversation_format_radio.setChecked(True)
                self._on_dataset_format_changed(self.conversation_format_radio)
            
            # Dataset content
            dataset_content = dataset_config.get("content", {})
            
            if dataset_format == "text":
                text_samples = dataset_content.get("text_samples", [])
                if text_samples:
                    self.text_edit.setText("\n".join(text_samples))
            
            elif dataset_format == "instruction":
                instruction_pairs = dataset_content.get("instruction_pairs", [])
                self.instruction_table.setRowCount(0)
                for pair in instruction_pairs:
                    row = self.instruction_table.rowCount()
                    self.instruction_table.insertRow(row)
                    self.instruction_table.setItem(row, 0, QTableWidgetItem(pair.get("prompt", "")))
                    self.instruction_table.setItem(row, 1, QTableWidgetItem(pair.get("completion", "")))
            
            elif dataset_format == "conversation":
                conversations = dataset_content.get("conversations", [])
                self.conversation_list.clear()
                for conversation in conversations:
                    item = QListWidgetItem(f"Conversation ({len(conversation)} turns)")
                    item.setData(Qt.ItemDataRole.UserRole, conversation)
                    self.conversation_list.addItem(item)
            
            # Update dataset statistics
            self._update_dataset_statistics()
            
            # Load training configuration
            training_config = adapter_config.get("training", {})
            
            self.batch_size_spin.setValue(training_config.get("batch_size", 4))
            self.gradient_accumulation_spin.setValue(training_config.get("gradient_accumulation", 4))
            self.epochs_spin.setValue(training_config.get("epochs", 3))
            self.learning_rate_spin.setValue(training_config.get("learning_rate", 3e-4))
            self.max_length_spin.setValue(training_config.get("max_length", 512))
            self.fp16_check.setChecked(training_config.get("fp16", True))
            
            self.output_dir_edit.setText(training_config.get("output_dir", ""))
            
            # Load evaluation configuration
            eval_config = adapter_config.get("evaluation", {})
            
            self.use_train_split_check.setChecked(eval_config.get("use_train_split", True))
            self.eval_split_spin.setValue(eval_config.get("eval_split", 10))
            
            self.separate_eval_check.setChecked(eval_config.get("separate_eval", False))
            self._on_separate_eval_toggled(self.separate_eval_check.isChecked())
            
            self.eval_file_edit.setText(eval_config.get("eval_file", ""))
            
            self.perplexity_check.setChecked(eval_config.get("perplexity", True))
            self.bleu_check.setChecked(eval_config.get("bleu", True))
            self.rouge_check.setChecked(eval_config.get("rouge", True))
            
            logger.debug("Adapter configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading adapter configuration: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load adapter configuration: {e}")
    
    def _get_current_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration from the dialog.
        
        Returns:
            A dictionary containing the current configuration.
        """
        logger.debug("Getting current configuration from dialog")
        
        config_dict = {}
        
        # Get base model
        config_dict["base_model"] = self.base_model_combo.currentText()
        
        # Get adapter type
        if self.lora_radio.isChecked():
            config_dict["adapter_type"] = "lora"
        elif self.qlora_radio.isChecked():
            config_dict["adapter_type"] = "qlora"
        elif self.prefix_tuning_radio.isChecked():
            config_dict["adapter_type"] = "prefix_tuning"
        
        # Get adapter parameters
        adapter_params = {}
        
        # Common parameters
        adapter_params["name"] = self.adapter_name_edit.text()
        
        # LoRA parameters
        adapter_params["lora_r"] = self.lora_r_spin.value()
        adapter_params["lora_alpha"] = self.lora_alpha_spin.value()
        adapter_params["lora_dropout"] = self.lora_dropout_spin.value()
        
        target_modules_text = self.target_modules_edit.text()
        if target_modules_text:
            adapter_params["target_modules"] = [m.strip() for m in target_modules_text.split(",")]
        
        adapter_params["bias"] = self.bias_combo.currentText()
        
        # QLoRA parameters
        adapter_params["quantization_bits"] = int(self.quantization_bits_combo.currentText())
        
        # Prefix Tuning parameters
        adapter_params["num_virtual_tokens"] = self.num_virtual_tokens_spin.value()
        adapter_params["prefix_projection"] = self.prefix_projection_check.isChecked()
        
        config_dict["adapter_params"] = adapter_params
        
        # Get dataset configuration
        dataset_config = {}
        
        # Dataset source
        if self.file_radio.isChecked():
            dataset_config["source"] = "file"
        elif self.manual_radio.isChecked():
            dataset_config["source"] = "manual"
        
        # Dataset file
        dataset_config["file_path"] = self.dataset_file_edit.text()
        
        # File format
        dataset_config["file_format"] = self.file_format_combo.currentText()
        
        # Dataset format
        if self.text_format_radio.isChecked():
            dataset_config["format"] = "text"
        elif self.instruction_format_radio.isChecked():
            dataset_config["format"] = "instruction"
        elif self.conversation_format_radio.isChecked():
            dataset_config["format"] = "conversation"
        
        # Dataset content
        dataset_content = {}
        
        if self.text_format_radio.isChecked():
            text = self.text_edit.toPlainText()
            if text:
                dataset_content["text_samples"] = text.split("\n")
            else:
                dataset_content["text_samples"] = []
        
        elif self.instruction_format_radio.isChecked():
            instruction_pairs = []
            for row in range(self.instruction_table.rowCount()):
                prompt_item = self.instruction_table.item(row, 0)
                completion_item = self.instruction_table.item(row, 1)
                
                prompt = prompt_item.text() if prompt_item else ""
                completion = completion_item.text() if completion_item else ""
                
                if prompt or completion:
                    instruction_pairs.append({
                        "prompt": prompt,
                        "completion": completion
                    })
            
            dataset_content["instruction_pairs"] = instruction_pairs
        
        elif self.conversation_format_radio.isChecked():
            conversations = []
            for i in range(self.conversation_list.count()):
                item = self.conversation_list.item(i)
                conversation = item.data(Qt.ItemDataRole.UserRole)
                if conversation:
                    conversations.append(conversation)
            
            dataset_content["conversations"] = conversations
        
        dataset_config["content"] = dataset_content
        
        config_dict["dataset"] = dataset_config
        
        # Get training configuration
        training_config = {}
        
        training_config["batch_size"] = self.batch_size_spin.value()
        training_config["gradient_accumulation"] = self.gradient_accumulation_spin.value()
        training_config["epochs"] = self.epochs_spin.value()
        training_config["learning_rate"] = self.learning_rate_spin.value()
        training_config["max_length"] = self.max_length_spin.value()
        training_config["fp16"] = self.fp16_check.isChecked()
        
        training_config["output_dir"] = self.output_dir_edit.text()
        
        config_dict["training"] = training_config
        
        # Get evaluation configuration
        eval_config = {}
        
        eval_config["use_train_split"] = self.use_train_split_check.isChecked()
        eval_config["eval_split"] = self.eval_split_spin.value()
        
        eval_config["separate_eval"] = self.separate_eval_check.isChecked()
        eval_config["eval_file"] = self.eval_file_edit.text()
        
        eval_config["perplexity"] = self.perplexity_check.isChecked()
        eval_config["bleu"] = self.bleu_check.isChecked()
        eval_config["rouge"] = self.rouge_check.isChecked()
        
        config_dict["evaluation"] = eval_config
        
        logger.debug("Current configuration retrieved from dialog")
        
        return config_dict
    
    def _save_configuration(self):
        """Save current adapter configuration."""
        logger.debug("Saving current adapter configuration")
        
        try:
            # Get current configuration
            adapter_config = self._get_current_configuration()
            
            # Update config
            config_data = config.get_config()
            config_data["adapter"] = adapter_config
            config.save_config(config_data)
            
            # Emit configuration changed signal
            self.config_changed.emit(adapter_config)
            
            logger.debug("Adapter configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving adapter configuration: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save adapter configuration: {e}")
            return False
    
    def _refresh_models(self):
        """Refresh the list of available models."""
        logger.debug("Refreshing available models")
        
        try:
            # Get current selection
            current_model = self.base_model_combo.currentText()
            
            # Clear the combo box
            self.base_model_combo.clear()
            
            # Populate with available models from model registry
            available_models = self.model_registry.get_all_models()
            for model in available_models:
                self.base_model_combo.addItem(model)
            
            # Restore previous selection if possible
            if current_model:
                index = self.base_model_combo.findText(current_model)
                if index >= 0:
                    self.base_model_combo.setCurrentIndex(index)
                else:
                    self.base_model_combo.setCurrentText(current_model)
            
            logger.debug(f"Refreshed available models: {len(available_models)} models found")
        except Exception as e:
            logger.error(f"Error refreshing available models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh available models: {e}")
    
    def _on_adapter_type_changed(self, button):
        """
        Handle adapter type radio button changed.
        
        Args:
            button: The radio button that was clicked.
        """
        logger.debug(f"Adapter type changed to: {button.text()}")
        
        # Show/hide parameter widgets based on adapter type
        if button == self.lora_radio:
            self.lora_params_widget.setVisible(True)
            self.qlora_params_widget.setVisible(False)
            self.prefix_tuning_params_widget.setVisible(False)
        elif button == self.qlora_radio:
            self.lora_params_widget.setVisible(True)
            self.qlora_params_widget.setVisible(True)
            self.prefix_tuning_params_widget.setVisible(False)
        elif button == self.prefix_tuning_radio:
            self.lora_params_widget.setVisible(False)
            self.qlora_params_widget.setVisible(False)
            self.prefix_tuning_params_widget.setVisible(True)
    
    def _on_dataset_source_changed(self, button):
        """
        Handle dataset source radio button changed.
        
        Args:
            button: The radio button that was clicked.
        """
        logger.debug(f"Dataset source changed to: {button.text()}")
        
        # Enable/disable file selection based on source
        if button == self.file_radio:
            self.dataset_file_edit.setEnabled(True)
            self.dataset_file_button.setEnabled(True)
            self.file_format_combo.setEnabled(True)
        elif button == self.manual_radio:
            self.dataset_file_edit.setEnabled(False)
            self.dataset_file_button.setEnabled(False)
            self.file_format_combo.setEnabled(False)
    
    def _on_dataset_format_changed(self, button):
        """
        Handle dataset format radio button changed.
        
        Args:
            button: The radio button that was clicked.
        """
        logger.debug(f"Dataset format changed to: {button.text()}")
        
        # Show/hide format widgets based on format
        if button == self.text_format_radio:
            self.text_format_widget.setVisible(True)
            self.instruction_format_widget.setVisible(False)
            self.conversation_format_widget.setVisible(False)
        elif button == self.instruction_format_radio:
            self.text_format_widget.setVisible(False)
            self.instruction_format_widget.setVisible(True)
            self.conversation_format_widget.setVisible(False)
        elif button == self.conversation_format_radio:
            self.text_format_widget.setVisible(False)
            self.instruction_format_widget.setVisible(False)
            self.conversation_format_widget.setVisible(True)
        
        # Update dataset statistics
        self._update_dataset_statistics()
    
    def _on_browse_dataset_file(self):
        """Handle browse dataset file button clicked."""
        logger.debug("Browse dataset file button clicked")
        
        # Get file format filter
        file_format = self.file_format_combo.currentText()
        if file_format == "JSON":
            file_filter = "JSON Files (*.json);;All Files (*)"
        elif file_format == "CSV":
            file_filter = "CSV Files (*.csv);;All Files (*)"
        elif file_format == "JSONL":
            file_filter = "JSONL Files (*.jsonl);;All Files (*)"
        elif file_format == "TXT":
            file_filter = "Text Files (*.txt);;All Files (*)"
        else:
            file_filter = "All Files (*)"
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Dataset File",
            self.dataset_file_edit.text() or "",
            file_filter
        )
        
        if file_path:
            # Update dataset file edit
            self.dataset_file_edit.setText(file_path)
            
            logger.debug(f"Dataset file selected: {file_path}")
            
            # Load dataset file and update UI
            try:
                # Load dataset using dataset_preparation
                dataset = self.dataset_preparation.load_dataset(file_path, file_format)
                
                # Set the appropriate format radio button based on detected format
                if dataset["format"] == "text":
                    self.text_format_radio.setChecked(True)
                    self._on_dataset_format_changed(self.text_format_radio)
                elif dataset["format"] == "instruction":
                    self.instruction_format_radio.setChecked(True)
                    self._on_dataset_format_changed(self.instruction_format_radio)
                elif dataset["format"] == "conversation":
                    self.conversation_format_radio.setChecked(True)
                    self._on_dataset_format_changed(self.conversation_format_radio)
                
                # Populate the appropriate widget based on format
                if dataset["format"] == "text":
                    # Populate text edit
                    text_samples = []
                    for item in dataset["data"]:
                        if "text" in item:
                            text_samples.append(item["text"])
                    
                    self.text_edit.setText("\n".join(text_samples))
                
                elif dataset["format"] == "instruction":
                    # Clear existing rows
                    self.instruction_table.setRowCount(0)
                    
                    # Populate instruction table
                    for item in dataset["data"]:
                        if "prompt" in item and "completion" in item:
                            row = self.instruction_table.rowCount()
                            self.instruction_table.insertRow(row)
                            self.instruction_table.setItem(row, 0, QTableWidgetItem(item["prompt"]))
                            self.instruction_table.setItem(row, 1, QTableWidgetItem(item["completion"]))
                
                elif dataset["format"] == "conversation":
                    # Clear existing items
                    self.conversation_list.clear()
                    
                    # Populate conversation list
                    for item in dataset["data"]:
                        if "messages" in item and isinstance(item["messages"], list):
                            messages = item["messages"]
                            list_item = QListWidgetItem(f"Conversation ({len(messages)} turns)")
                            list_item.setData(Qt.ItemDataRole.UserRole, messages)
                            self.conversation_list.addItem(list_item)
                        elif "role" in item and "content" in item:
                            # Handle OpenAI-style conversation format
                            messages = [item]
                            list_item = QListWidgetItem(f"Conversation (1 turn)")
                            list_item.setData(Qt.ItemDataRole.UserRole, messages)
                            self.conversation_list.addItem(list_item)
                
                # Update dataset statistics
                self._update_dataset_statistics()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Dataset Loaded",
                    f"Successfully loaded dataset with format: {dataset['format'].capitalize()}\n"
                    f"Number of samples: {len(dataset['data'])}"
                )
                
            except Exception as e:
                logger.error(f"Error loading dataset: {str(e)}", exc_info=True)
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load dataset: {str(e)}"
                )
    
    def _on_add_instruction_row(self):
        """Handle add instruction row button clicked."""
        logger.debug("Add instruction row button clicked")
        
        # Add a new row to the instruction table
        row = self.instruction_table.rowCount()
        self.instruction_table.insertRow(row)
        
        # Update dataset statistics
        self._update_dataset_statistics()
    
    def _on_remove_instruction_row(self):
        """Handle remove instruction row button clicked."""
        logger.debug("Remove instruction row button clicked")
        
        # Get selected row
        selected_rows = self.instruction_table.selectedIndexes()
        if not selected_rows:
            return
        
        # Get unique row indices
        row_indices = set(index.row() for index in selected_rows)
        
        # Remove rows in reverse order to avoid index shifting
        for row in sorted(row_indices, reverse=True):
            self.instruction_table.removeRow(row)
        
        # Update dataset statistics
        self._update_dataset_statistics()
    
    def _on_add_conversation(self):
        """Handle add conversation button clicked."""
        logger.debug("Add conversation button clicked")
        
        # Create a new conversation
        conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": ""},
            {"role": "assistant", "content": ""}
        ]
        
        # Add to the conversation list
        item = QListWidgetItem(f"Conversation ({len(conversation)} turns)")
        item.setData(Qt.ItemDataRole.UserRole, conversation)
        self.conversation_list.addItem(item)
        
        # TODO: Open a dialog to edit the conversation
        
        # Update dataset statistics
        self._update_dataset_statistics()
    
    def _on_remove_conversation(self):
        """Handle remove conversation button clicked."""
        logger.debug("Remove conversation button clicked")
        
        # Get selected item
        selected_items = self.conversation_list.selectedItems()
        if not selected_items:
            return
        
        # Remove selected items
        for item in selected_items:
            row = self.conversation_list.row(item)
            self.conversation_list.takeItem(row)
        
        # Update dataset statistics
        self._update_dataset_statistics()
    
    def _update_dataset_statistics(self):
        """Update the dataset statistics display."""
        logger.debug("Updating dataset statistics")
        
        try:
            sample_count = 0
            token_count = 0
            
            # Count samples and estimate tokens based on dataset format
            if self.text_format_radio.isChecked():
                # Count text samples
                text = self.text_edit.toPlainText()
                if text:
                    samples = text.split("\n")
                    sample_count = len(samples)
                    
                    # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
                    token_count = sum(len(sample) // 4 for sample in samples)
            
            elif self.instruction_format_radio.isChecked():
                # Count instruction pairs
                sample_count = self.instruction_table.rowCount()
                
                # Estimate tokens
                for row in range(sample_count):
                    prompt_item = self.instruction_table.item(row, 0)
                    completion_item = self.instruction_table.item(row, 1)
                    
                    prompt = prompt_item.text() if prompt_item else ""
                    completion = completion_item.text() if completion_item else ""
                    
                    # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
                    token_count += (len(prompt) + len(completion)) // 4
            
            elif self.conversation_format_radio.isChecked():
                # Count conversations
                sample_count = self.conversation_list.count()
                
                # Estimate tokens
                for i in range(sample_count):
                    item = self.conversation_list.item(i)
                    conversation = item.data(Qt.ItemDataRole.UserRole)
                    
                    # Estimate tokens for each message in the conversation
                    for message in conversation:
                        content = message.get("content", "")
                        token_count += len(content) // 4
            
            # Update the labels
            self.sample_count_label.setText(str(sample_count))
            self.token_count_label.setText(str(token_count))
            
            logger.debug(f"Dataset statistics updated: {sample_count} samples, ~{token_count} tokens")
        except Exception as e:
            logger.error(f"Error updating dataset statistics: {e}")
    
    def _on_browse_output_dir(self):
        """Handle browse output directory button clicked."""
        logger.debug("Browse output directory button clicked")
        
        # Show directory dialog
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_edit.text() or ""
        )
        
        if dir_path:
            # Update output directory edit
            self.output_dir_edit.setText(dir_path)
            
            logger.debug(f"Output directory selected: {dir_path}")
    
    def _create_training_visualization_dialog(self, training_monitor):
        """
        Create a training visualization dialog.
        
        This method is separated to make it easier to test.
        
        Args:
            training_monitor: The training monitor instance.
            
        Returns:
            The training visualization dialog instance.
        """
        return TrainingVisualizationDialog(
            parent=self,
            training_monitor=training_monitor
        )
    
    def _on_start_training(self):
        """Handle start training button clicked."""
        logger.debug("Start training button clicked")
        
        # Validate configuration
        if not self._validate_training_config():
            return
        
        # Get current configuration
        adapter_config = self._get_current_configuration()
        
        # Get dataset info from dataset preparation
        dataset_info = self.dataset_preparation.get_dataset_info()
        if not dataset_info:
            QMessageBox.warning(
                self,
                "Dataset Error",
                "Failed to get dataset information. Please check your dataset configuration."
            )
            return
        
        # Create training monitor
        training_monitor = TrainingMonitor()
        
        # Create training visualization dialog
        self.training_dialog = self._create_training_visualization_dialog(training_monitor)
        
        # Set training configuration
        adapter_name = self.adapter_name_edit.text()
        base_model = self.base_model_combo.currentText()
        
        # Get adapter type
        if self.lora_radio.isChecked():
            adapter_type = "lora"
        elif self.qlora_radio.isChecked():
            adapter_type = "qlora"
        elif self.prefix_tuning_radio.isChecked():
            adapter_type = "prefix_tuning"
        else:
            adapter_type = "lora"  # Default
        
        # Get training parameters
        parameters = self._get_training_parameters()
        
        # Set training configuration in visualization dialog
        self.training_dialog.set_training_config(
            adapter_name=adapter_name,
            base_model=base_model,
            adapter_type=adapter_type,
            total_epochs=self.epochs_spin.value(),
            total_steps=dataset_info.get("samples", 1000) // self.batch_size_spin.value() * self.epochs_spin.value(),
            parameters=parameters,
            dataset_info=dataset_info
        )
        
        # Show the training visualization dialog
        self.training_dialog.show()
    
    def _get_training_parameters(self) -> Dict[str, Any]:
        """
        Get training parameters from the dialog.
        
        Returns:
            A dictionary containing the training parameters.
        """
        logger.debug("Getting training parameters")
        
        parameters = {}
        
        # Common parameters
        parameters["batch_size"] = self.batch_size_spin.value()
        parameters["gradient_accumulation"] = self.gradient_accumulation_spin.value()
        parameters["learning_rate"] = self.learning_rate_spin.value()
        parameters["max_length"] = self.max_length_spin.value()
        parameters["fp16"] = self.fp16_check.isChecked()
        parameters["warmup_steps"] = int(self.epochs_spin.value() * 0.1)  # 10% of epochs
        parameters["weight_decay"] = 0.01
        
        # LoRA parameters
        if self.lora_radio.isChecked() or self.qlora_radio.isChecked():
            parameters["rank"] = self.lora_r_spin.value()
            parameters["alpha"] = self.lora_alpha_spin.value()
            parameters["dropout"] = self.lora_dropout_spin.value()
            
            target_modules_text = self.target_modules_edit.text()
            if target_modules_text:
                parameters["target_modules"] = [m.strip() for m in target_modules_text.split(",")]
            
            parameters["bias"] = self.bias_combo.currentText()
        
        # QLoRA parameters
        if self.qlora_radio.isChecked():
            parameters["quantization_bits"] = int(self.quantization_bits_combo.currentText())
        
        # Prefix Tuning parameters
        if self.prefix_tuning_radio.isChecked():
            parameters["num_virtual_tokens"] = self.num_virtual_tokens_spin.value()
            parameters["prefix_projection"] = self.prefix_projection_check.isChecked()
        
        logger.debug(f"Training parameters: {parameters}")
        return parameters
    
    def _on_load_results_clicked(self):
        """Handle load results button clicked."""
        logger.debug("Load results button clicked")
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Training Results File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            logger.debug(f"Training results file selected: {file_path}")
            
            try:
                # Create training monitor
                training_monitor = TrainingMonitor()
                
                # Create training visualization dialog
                self.training_dialog = self._create_training_visualization_dialog(training_monitor)
                
                # Load training results
                self.training_dialog.load_training_results(file_path)
                
                # Show the training visualization dialog
                self.training_dialog.show()
                
            except Exception as e:
                logger.error(f"Error loading training results: {str(e)}", exc_info=True)
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load training results: {str(e)}"
                )
    
    def _on_stop_training(self):
        """Handle stop training button clicked."""
        logger.debug("Stop training button clicked")
        
        # TODO: Stop the training process
        # This would involve signaling the worker thread to stop
        
        # For now, just show a message
        QMessageBox.information(
            self,
            "Training",
            "Training stop functionality will be implemented in a future update."
        )
    
    def _set_training_ui_enabled(self, enabled: bool):
        """
        Enable or disable UI elements during training.
        
        Args:
            enabled: Whether to enable or disable the UI.
        """
        # Enable/disable tabs
        self.adapter_tab.setEnabled(enabled)
        self.dataset_tab.setEnabled(enabled)
        self.evaluation_tab.setEnabled(enabled)
        
        # Enable/disable training controls
        self.batch_size_spin.setEnabled(enabled)
        self.gradient_accumulation_spin.setEnabled(enabled)
        self.epochs_spin.setEnabled(enabled)
        self.learning_rate_spin.setEnabled(enabled)
        self.max_length_spin.setEnabled(enabled)
        self.fp16_check.setEnabled(enabled)
        self.output_dir_edit.setEnabled(enabled)
        self.output_dir_button.setEnabled(enabled)
        
        # Enable/disable training buttons
        self.start_training_button.setEnabled(enabled)
        self.stop_training_button.setEnabled(not enabled)
        
        # Enable/disable dialog buttons
        self.button_box.setEnabled(enabled)
    
    def _validate_training_config(self) -> bool:
        """
        Validate the training configuration.
        
        Returns:
            True if the configuration is valid, False otherwise.
        """
        # Check base model
        if not self.base_model_combo.currentText():
            QMessageBox.warning(self, "Validation Error", "Please select a base model.")
            self.tab_widget.setCurrentWidget(self.adapter_tab)
            self.base_model_combo.setFocus()
            return False
        
        # Check adapter name
        if not self.adapter_name_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please enter an adapter name.")
            self.tab_widget.setCurrentWidget(self.adapter_tab)
            self.adapter_name_edit.setFocus()
            return False
        
        # Check dataset
        if self.file_radio.isChecked() and not self.dataset_file_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please select a dataset file.")
            self.tab_widget.setCurrentWidget(self.dataset_tab)
            self.dataset_file_edit.setFocus()
            return False
        
        if self.instruction_format_radio.isChecked() and self.instruction_table.rowCount() == 0:
            QMessageBox.warning(self, "Validation Error", "Please add at least one instruction-completion pair.")
            self.tab_widget.setCurrentWidget(self.dataset_tab)
            self.add_instruction_button.setFocus()
            return False
        
        if self.text_format_radio.isChecked() and not self.text_edit.toPlainText():
            QMessageBox.warning(self, "Validation Error", "Please enter at least one text sample.")
            self.tab_widget.setCurrentWidget(self.dataset_tab)
            self.text_edit.setFocus()
            return False
        
        if self.conversation_format_radio.isChecked() and self.conversation_list.count() == 0:
            QMessageBox.warning(self, "Validation Error", "Please add at least one conversation.")
            self.tab_widget.setCurrentWidget(self.dataset_tab)
            self.add_conversation_button.setFocus()
            return False
        
        # Check output directory
        if not self.output_dir_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please select an output directory.")
            self.tab_widget.setCurrentWidget(self.training_tab)
            self.output_dir_edit.setFocus()
            return False
        
        # Check evaluation dataset
        if self.separate_eval_check.isChecked() and not self.eval_file_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please select an evaluation dataset file.")
            self.tab_widget.setCurrentWidget(self.evaluation_tab)
            self.eval_file_edit.setFocus()
            return False
        
        return True
    
    def _on_separate_eval_toggled(self, checked: bool):
        """
        Handle separate evaluation dataset checkbox toggled.
        
        Args:
            checked: Whether the checkbox is checked.
        """
        logger.debug(f"Separate evaluation dataset toggled: {checked}")
        
        # Enable/disable evaluation file selection
        self.eval_file_edit.setEnabled(checked)
        self.eval_file_button.setEnabled(checked)
        
        # Enable/disable train split
        self.eval_split_spin.setEnabled(not checked)
    
    def _on_browse_eval_file(self):
        """Handle browse evaluation file button clicked."""
        logger.debug("Browse evaluation file button clicked")
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Evaluation Dataset File",
            self.eval_file_edit.text() or "",
            "All Files (*)"
        )
        
        if file_path:
            # Update evaluation file edit
            self.eval_file_edit.setText(file_path)
            
            logger.debug(f"Evaluation file selected: {file_path}")
    
    def _on_run_evaluation(self):
        """Handle run evaluation button clicked."""
        logger.debug("Run evaluation button clicked")
        
        # TODO: Implement evaluation
        # This would involve loading the model with the adapter,
        # running evaluation on the dataset, and updating the results table
        
        # For now, just show a message
        QMessageBox.information(
            self,
            "Evaluation",
            "Evaluation functionality will be implemented in a future update."
        )
    
    def _on_export_evaluation(self):
        """Handle export evaluation results button clicked."""
        logger.debug("Export evaluation results button clicked")
        
        # TODO: Implement export
        # This would involve exporting the evaluation results to a file
        
        # For now, just show a message
        QMessageBox.information(
            self,
            "Export",
            "Export functionality will be implemented in a future update."
        )
    
    def _on_accept(self):
        """Handle accept button clicked."""
        logger.debug("Accept button clicked")
        
        # Save configuration
        if self._save_configuration():
            # Accept dialog
            self.accept()
    
    def _on_apply(self):
        """Handle apply button clicked."""
        logger.debug("Apply button clicked")
        
        # Save configuration
        self._save_configuration()
