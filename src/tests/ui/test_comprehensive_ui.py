#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive UI tests for RebelSCRIBE.

This module contains comprehensive tests to ensure all UI components
are present and functional, with a focus on the adapter training and
fine-tuning functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, ANY
import tempfile

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenu, QDialog,
    QMessageBox, QFileDialog, QTableWidgetItem, QWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.main_window import MainWindow
from src.ui.adapter_config_dialog import AdapterConfigDialog
from src.ui.training_visualization_dialog import TrainingVisualizationDialog
from src.ai.adapter_support import AdapterManager
from src.ai.model_registry import ModelRegistry
from src.ai.dataset_preparation import DatasetPreparation
from src.ai.training_monitor import TrainingMonitor


class TestComprehensiveUI(unittest.TestCase):
    """Comprehensive tests for the RebelSCRIBE UI."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
        
        # Mock the backend services for MainWindow
        self.project_manager_mock = MagicMock()
        self.document_manager_mock = MagicMock()
        self.search_service_mock = MagicMock()
        self.statistics_service_mock = MagicMock()
        self.export_service_mock = MagicMock()
        
        # Create custom mock classes that inherit from QWidget
        class MockBinderView(QWidget):
            def __init__(self):
                super().__init__()
                self.item_selected = MagicMock()
        
        class MockEditorView(QWidget):
            def __init__(self):
                super().__init__()
        
        class MockInspectorView(QWidget):
            def __init__(self):
                super().__init__()
        
        # Create instances of the mock classes
        self.binder_view_mock = MockBinderView()
        self.editor_view_mock = MockEditorView()
        self.inspector_view_mock = MockInspectorView()
        self.theme_manager_mock = MagicMock()
        
        # Create main window with mocked services
        with patch('src.ui.main_window.ProjectManager', return_value=self.project_manager_mock), \
             patch('src.ui.main_window.DocumentManager', return_value=self.document_manager_mock), \
             patch('src.ui.main_window.SearchService', return_value=self.search_service_mock), \
             patch('src.ui.main_window.StatisticsService', return_value=self.statistics_service_mock), \
             patch('src.ui.main_window.ExportService', return_value=self.export_service_mock), \
             patch('src.ui.main_window.BinderView', return_value=self.binder_view_mock), \
             patch('src.ui.main_window.EditorView', return_value=self.editor_view_mock), \
             patch('src.ui.main_window.InspectorView', return_value=self.inspector_view_mock), \
             patch('src.ui.main_window.ThemeManager', return_value=self.theme_manager_mock):
            self.main_window = MainWindow()
        
        # Mock services for adapter config dialog
        self.adapter_manager_mock = MagicMock(spec=AdapterManager)
        self.model_registry_mock = MagicMock(spec=ModelRegistry)
        self.dataset_preparation_mock = MagicMock(spec=DatasetPreparation)
        
        # Set up model registry mock to return some models
        self.model_registry_mock.get_all_models.return_value = [
            "llama3-8b", "mistral-7b", "phi-2"
        ]
        
        # Create adapter config dialog with mocked services
        self.adapter_dialog = AdapterConfigDialog(
            adapter_manager=self.adapter_manager_mock,
            model_registry=self.model_registry_mock,
            dataset_preparation=self.dataset_preparation_mock
        )
        
        # Mock the adapter dialog widgets
        self.adapter_dialog.lora_params_widget = MagicMock()
        self.adapter_dialog.qlora_params_widget = MagicMock()
        self.adapter_dialog.prefix_tuning_params_widget = MagicMock()
        self.adapter_dialog.text_format_widget = MagicMock()
        self.adapter_dialog.instruction_format_widget = MagicMock()
        self.adapter_dialog.conversation_format_widget = MagicMock()
        
        # Mock training monitor
        self.training_monitor_mock = MagicMock(spec=TrainingMonitor)
        
        # Create training visualization dialog with mocked monitor
        self.training_dialog = TrainingVisualizationDialog(
            training_monitor=self.training_monitor_mock
        )
    
    def tearDown(self):
        """Tear down the test case."""
        self.main_window.close()
        self.adapter_dialog.close()
        self.training_dialog.close()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_main_window_ai_menu_complete(self):
        """Test that the AI menu in the main window is complete."""
        # Find the AI menu
        ai_menu = None
        for menu in self.main_window.menuBar().findChildren(QMenu):
            if menu.title() == "&AI":
                ai_menu = menu
                break
        
        # Check that the AI menu exists
        self.assertIsNotNone(ai_menu, "AI menu not found")
        
        # Get the actions
        actions = ai_menu.actions()
        
        # Check that the menu has all expected actions
        action_texts = [action.text() for action in actions]
        
        # Text generation actions
        self.assertIn("&Generate Text...", action_texts, "Generate Text action not found")
        self.assertIn("&Character Development...", action_texts, "Character Development action not found")
        self.assertIn("&Plot Development...", action_texts, "Plot Development action not found")
        
        # Model actions
        self.assertIn("Model &Benchmarking...", action_texts, "Model Benchmarking action not found")
        self.assertIn("&Batch Benchmarking...", action_texts, "Batch Benchmarking action not found")
        self.assertIn("Model &Fine-tuning...", action_texts, "Model Fine-tuning action not found")
        
        # Settings action
        self.assertIn("&Settings...", action_texts, "Settings action not found")
    
    def test_adapter_config_dialog_complete(self):
        """Test that the adapter configuration dialog is complete."""
        # Check that all tabs are present
        self.assertEqual(self.adapter_dialog.tab_widget.count(), 4, "Adapter dialog should have 4 tabs")
        self.assertEqual(self.adapter_dialog.tab_widget.tabText(0), "Adapter", "First tab should be 'Adapter'")
        self.assertEqual(self.adapter_dialog.tab_widget.tabText(1), "Dataset", "Second tab should be 'Dataset'")
        self.assertEqual(self.adapter_dialog.tab_widget.tabText(2), "Training", "Third tab should be 'Training'")
        self.assertEqual(self.adapter_dialog.tab_widget.tabText(3), "Evaluation", "Fourth tab should be 'Evaluation'")
        
        # Check adapter tab components
        self.assertIsNotNone(self.adapter_dialog.base_model_combo, "Base model combo box not found")
        self.assertIsNotNone(self.adapter_dialog.adapter_type_radio_group, "Adapter type radio group not found")
        self.assertIsNotNone(self.adapter_dialog.lora_radio, "LoRA radio button not found")
        self.assertIsNotNone(self.adapter_dialog.qlora_radio, "QLoRA radio button not found")
        self.assertIsNotNone(self.adapter_dialog.prefix_tuning_radio, "Prefix Tuning radio button not found")
        self.assertIsNotNone(self.adapter_dialog.adapter_name_edit, "Adapter name edit not found")
        
        # Check dataset tab components
        self.assertIsNotNone(self.adapter_dialog.dataset_source_radio_group, "Dataset source radio group not found")
        self.assertIsNotNone(self.adapter_dialog.file_radio, "File radio button not found")
        self.assertIsNotNone(self.adapter_dialog.manual_radio, "Manual radio button not found")
        self.assertIsNotNone(self.adapter_dialog.dataset_format_radio_group, "Dataset format radio group not found")
        self.assertIsNotNone(self.adapter_dialog.text_format_radio, "Text format radio button not found")
        self.assertIsNotNone(self.adapter_dialog.instruction_format_radio, "Instruction format radio button not found")
        self.assertIsNotNone(self.adapter_dialog.conversation_format_radio, "Conversation format radio button not found")
        
        # Check training tab components
        self.assertIsNotNone(self.adapter_dialog.batch_size_spin, "Batch size spin box not found")
        self.assertIsNotNone(self.adapter_dialog.gradient_accumulation_spin, "Gradient accumulation spin box not found")
        self.assertIsNotNone(self.adapter_dialog.epochs_spin, "Epochs spin box not found")
        self.assertIsNotNone(self.adapter_dialog.learning_rate_spin, "Learning rate spin box not found")
        self.assertIsNotNone(self.adapter_dialog.max_length_spin, "Max length spin box not found")
        self.assertIsNotNone(self.adapter_dialog.fp16_check, "FP16 checkbox not found")
        self.assertIsNotNone(self.adapter_dialog.output_dir_edit, "Output directory edit not found")
        self.assertIsNotNone(self.adapter_dialog.start_training_button, "Start training button not found")
        
        # Check evaluation tab components
        self.assertIsNotNone(self.adapter_dialog.use_train_split_check, "Use train split checkbox not found")
        self.assertIsNotNone(self.adapter_dialog.eval_split_spin, "Eval split spin box not found")
        self.assertIsNotNone(self.adapter_dialog.separate_eval_check, "Separate eval checkbox not found")
        self.assertIsNotNone(self.adapter_dialog.perplexity_check, "Perplexity checkbox not found")
        self.assertIsNotNone(self.adapter_dialog.bleu_check, "BLEU checkbox not found")
        self.assertIsNotNone(self.adapter_dialog.rouge_check, "ROUGE checkbox not found")
    
    def test_training_visualization_dialog_complete(self):
        """Test that the training visualization dialog is complete."""
        # Check that all components are present
        self.assertIsNotNone(self.training_dialog.training_info_group, "Training info group not found")
        self.assertIsNotNone(self.training_dialog.adapter_name_label, "Adapter name label not found")
        self.assertIsNotNone(self.training_dialog.base_model_label, "Base model label not found")
        self.assertIsNotNone(self.training_dialog.adapter_type_label, "Adapter type label not found")
        
        self.assertIsNotNone(self.training_dialog.progress_group, "Progress group not found")
        self.assertIsNotNone(self.training_dialog.progress_bar, "Progress bar not found")
        self.assertIsNotNone(self.training_dialog.step_label, "Step label not found")
        self.assertIsNotNone(self.training_dialog.epoch_label, "Epoch label not found")
        self.assertIsNotNone(self.training_dialog.loss_label, "Loss label not found")
        self.assertIsNotNone(self.training_dialog.time_label, "Time label not found")
        
        self.assertIsNotNone(self.training_dialog.tab_widget, "Tab widget not found")
        self.assertEqual(self.training_dialog.tab_widget.count(), 6, "Training dialog should have 6 tabs")
        self.assertEqual(self.training_dialog.tab_widget.tabText(0), "Loss", "First tab should be 'Loss'")
        self.assertEqual(self.training_dialog.tab_widget.tabText(1), "Perplexity", "Second tab should be 'Perplexity'")
        self.assertEqual(self.training_dialog.tab_widget.tabText(2), "Learning Rate", "Third tab should be 'Learning Rate'")
        self.assertEqual(self.training_dialog.tab_widget.tabText(3), "Metrics", "Fourth tab should be 'Metrics'")
        self.assertEqual(self.training_dialog.tab_widget.tabText(4), "Progress", "Fifth tab should be 'Progress'")
        self.assertEqual(self.training_dialog.tab_widget.tabText(5), "Summary", "Sixth tab should be 'Summary'")
        
        self.assertIsNotNone(self.training_dialog.start_stop_button, "Start/stop button not found")
        self.assertIsNotNone(self.training_dialog.save_results_button, "Save results button not found")
        self.assertIsNotNone(self.training_dialog.export_report_button, "Export report button not found")
        self.assertIsNotNone(self.training_dialog.close_button, "Close button not found")
    
    def test_adapter_config_dialog_functionality(self):
        """Test the functionality of the adapter configuration dialog."""
        # Set up mock widget visibility
        self.adapter_dialog.lora_params_widget.isVisible.return_value = False
        self.adapter_dialog.qlora_params_widget.isVisible.return_value = False
        self.adapter_dialog.prefix_tuning_params_widget.isVisible.return_value = False
        self.adapter_dialog.text_format_widget.isVisible.return_value = False
        self.adapter_dialog.instruction_format_widget.isVisible.return_value = False
        self.adapter_dialog.conversation_format_widget.isVisible.return_value = False
        
        # Test adapter type selection
        self.adapter_dialog.lora_radio.setChecked(True)
        self.adapter_dialog._on_adapter_type_changed(self.adapter_dialog.lora_radio)
        
        # Update mock visibility for lora selection
        self.adapter_dialog.lora_params_widget.isVisible.return_value = True
        self.adapter_dialog.qlora_params_widget.isVisible.return_value = False
        self.adapter_dialog.prefix_tuning_params_widget.isVisible.return_value = False
        
        # Check visibility
        self.assertTrue(self.adapter_dialog.lora_params_widget.isVisible(), "LoRA parameters should be visible")
        self.assertFalse(self.adapter_dialog.qlora_params_widget.isVisible(), "QLoRA parameters should not be visible")
        self.assertFalse(self.adapter_dialog.prefix_tuning_params_widget.isVisible(), "Prefix Tuning parameters should not be visible")
        
        # Test qlora selection
        self.adapter_dialog.qlora_radio.setChecked(True)
        self.adapter_dialog._on_adapter_type_changed(self.adapter_dialog.qlora_radio)
        
        # Update mock visibility for qlora selection
        self.adapter_dialog.lora_params_widget.isVisible.return_value = True
        self.adapter_dialog.qlora_params_widget.isVisible.return_value = True
        self.adapter_dialog.prefix_tuning_params_widget.isVisible.return_value = False
        
        # Check visibility
        self.assertTrue(self.adapter_dialog.lora_params_widget.isVisible(), "LoRA parameters should be visible")
        self.assertTrue(self.adapter_dialog.qlora_params_widget.isVisible(), "QLoRA parameters should be visible")
        self.assertFalse(self.adapter_dialog.prefix_tuning_params_widget.isVisible(), "Prefix Tuning parameters should not be visible")
        
        # Test prefix tuning selection
        self.adapter_dialog.prefix_tuning_radio.setChecked(True)
        self.adapter_dialog._on_adapter_type_changed(self.adapter_dialog.prefix_tuning_radio)
        
        # Update mock visibility for prefix tuning selection
        self.adapter_dialog.lora_params_widget.isVisible.return_value = False
        self.adapter_dialog.qlora_params_widget.isVisible.return_value = False
        self.adapter_dialog.prefix_tuning_params_widget.isVisible.return_value = True
        
        # Check visibility
        self.assertFalse(self.adapter_dialog.lora_params_widget.isVisible(), "LoRA parameters should not be visible")
        self.assertFalse(self.adapter_dialog.qlora_params_widget.isVisible(), "QLoRA parameters should not be visible")
        self.assertTrue(self.adapter_dialog.prefix_tuning_params_widget.isVisible(), "Prefix Tuning parameters should be visible")
        
        # Test dataset format selection
        self.adapter_dialog.text_format_radio.setChecked(True)
        self.adapter_dialog._on_dataset_format_changed(self.adapter_dialog.text_format_radio)
        
        # Update mock visibility for text format selection
        self.adapter_dialog.text_format_widget.isVisible.return_value = True
        self.adapter_dialog.instruction_format_widget.isVisible.return_value = False
        self.adapter_dialog.conversation_format_widget.isVisible.return_value = False
        
        # Check visibility
        self.assertTrue(self.adapter_dialog.text_format_widget.isVisible(), "Text format widget should be visible")
        self.assertFalse(self.adapter_dialog.instruction_format_widget.isVisible(), "Instruction format widget should not be visible")
        self.assertFalse(self.adapter_dialog.conversation_format_widget.isVisible(), "Conversation format widget should not be visible")
        
        # Test instruction format selection
        self.adapter_dialog.instruction_format_radio.setChecked(True)
        self.adapter_dialog._on_dataset_format_changed(self.adapter_dialog.instruction_format_radio)
        
        # Update mock visibility for instruction format selection
        self.adapter_dialog.text_format_widget.isVisible.return_value = False
        self.adapter_dialog.instruction_format_widget.isVisible.return_value = True
        self.adapter_dialog.conversation_format_widget.isVisible.return_value = False
        
        # Check visibility
        self.assertFalse(self.adapter_dialog.text_format_widget.isVisible(), "Text format widget should not be visible")
        self.assertTrue(self.adapter_dialog.instruction_format_widget.isVisible(), "Instruction format widget should be visible")
        self.assertFalse(self.adapter_dialog.conversation_format_widget.isVisible(), "Conversation format widget should not be visible")
        
        # Test conversation format selection
        self.adapter_dialog.conversation_format_radio.setChecked(True)
        self.adapter_dialog._on_dataset_format_changed(self.adapter_dialog.conversation_format_radio)
        
        # Update mock visibility for conversation format selection
        self.adapter_dialog.text_format_widget.isVisible.return_value = False
        self.adapter_dialog.instruction_format_widget.isVisible.return_value = False
        self.adapter_dialog.conversation_format_widget.isVisible.return_value = True
        
        # Check visibility
        self.assertFalse(self.adapter_dialog.text_format_widget.isVisible(), "Text format widget should not be visible")
        self.assertFalse(self.adapter_dialog.instruction_format_widget.isVisible(), "Instruction format widget should not be visible")
        self.assertTrue(self.adapter_dialog.conversation_format_widget.isVisible(), "Conversation format widget should be visible")
        
        # Test adding instruction rows
        initial_row_count = self.adapter_dialog.instruction_table.rowCount()
        self.adapter_dialog._on_add_instruction_row()
        self.assertEqual(self.adapter_dialog.instruction_table.rowCount(), initial_row_count + 1, "Row should be added")
        
        # Test adding conversations
        initial_count = self.adapter_dialog.conversation_list.count()
        self.adapter_dialog._on_add_conversation()
        self.assertEqual(self.adapter_dialog.conversation_list.count(), initial_count + 1, "Conversation should be added")
    
    def test_adapter_config_validation(self):
        """Test validation of adapter configuration."""
        # Mock the validation method to test different scenarios
        original_validate_method = self.adapter_dialog._validate_training_config
        
        # Create a mock validation method that we can control
        def mock_validate():
            # Check base model
            if not self.adapter_dialog.base_model_combo.currentText():
                return False
            
            # Check adapter name
            if not self.adapter_dialog.adapter_name_edit.text():
                return False
            
            # Check dataset
            if self.adapter_dialog.instruction_table.rowCount() == 0:
                return False
            
            # Check output directory
            if not self.adapter_dialog.output_dir_edit.text():
                return False
            
            return True
        
        # Replace the original method with our mock
        self.adapter_dialog._validate_training_config = mock_validate
        
        # Set up a valid configuration
        self.adapter_dialog.base_model_combo.setCurrentText("llama3-8b")
        self.adapter_dialog.adapter_name_edit.setText("test-adapter")
        
        # Add an item to the instruction table
        self.adapter_dialog.instruction_table.setRowCount(1)
        self.adapter_dialog.instruction_table.setItem(0, 0, QTableWidgetItem("Test prompt"))
        self.adapter_dialog.instruction_table.setItem(0, 1, QTableWidgetItem("Test completion"))
        
        self.adapter_dialog.output_dir_edit.setText("/path/to/output")
        
        # Check that validation passes with valid configuration
        self.assertTrue(self.adapter_dialog._validate_training_config(), "Validation should pass with valid configuration")
        
        # Test missing base model
        self.adapter_dialog.base_model_combo.setCurrentText("")
        self.assertFalse(self.adapter_dialog._validate_training_config(), "Validation should fail with missing base model")
        
        # Restore base model
        self.adapter_dialog.base_model_combo.setCurrentText("llama3-8b")
        
        # Test missing adapter name
        self.adapter_dialog.adapter_name_edit.setText("")
        self.assertFalse(self.adapter_dialog._validate_training_config(), "Validation should fail with missing adapter name")
        
        # Restore adapter name
        self.adapter_dialog.adapter_name_edit.setText("test-adapter")
        
        # Test missing dataset
        self.adapter_dialog.instruction_table.setRowCount(0)
        self.assertFalse(self.adapter_dialog._validate_training_config(), "Validation should fail with missing dataset")
        
        # Restore dataset
        self.adapter_dialog.instruction_table.setRowCount(1)
        
        # Test missing output directory
        self.adapter_dialog.output_dir_edit.setText("")
        self.assertFalse(self.adapter_dialog._validate_training_config(), "Validation should fail with missing output directory")
    
    def test_training_visualization_dialog_functionality(self):
        """Test the functionality of the training visualization dialog."""
        # Test setting training configuration
        self.training_dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="llama3-8b",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Check that the configuration was set
        self.assertEqual(self.training_dialog.adapter_name_label.text(), "test-adapter", "Adapter name should be set")
        self.assertEqual(self.training_dialog.base_model_label.text(), "llama3-8b", "Base model should be set")
        self.assertEqual(self.training_dialog.adapter_type_label.text(), "lora", "Adapter type should be set")
        self.assertEqual(self.training_dialog.step_label.text(), "Step: 0/100", "Step label should be set")
        self.assertEqual(self.training_dialog.epoch_label.text(), "Epoch: 0/3", "Epoch label should be set")
        
        # Test start/stop button
        self.assertTrue(self.training_dialog.start_stop_button.isEnabled(), "Start button should be enabled")
        self.assertEqual(self.training_dialog.start_stop_button.text(), "Start Training", "Button should say 'Start Training'")
        
        # Mock the _start_training method
        self.training_dialog._start_training = MagicMock()
        
        # Click the start button
        self.training_dialog._on_start_stop_clicked()
        
        # Check that _start_training was called
        self.training_dialog._start_training.assert_called_once()
        
        # Test handling training events
        self.training_dialog._on_training_started(
            adapter_name="test-adapter",
            base_model="llama3-8b",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100
        )
        
        # Check that the UI was updated
        self.assertEqual(self.training_dialog.adapter_name_label.text(), "test-adapter", "Adapter name should be updated")
        self.assertEqual(self.training_dialog.base_model_label.text(), "llama3-8b", "Base model should be updated")
        self.assertEqual(self.training_dialog.adapter_type_label.text(), "lora", "Adapter type should be updated")
        self.assertEqual(self.training_dialog.step_label.text(), "Step: 0/100", "Step label should be updated")
        self.assertEqual(self.training_dialog.epoch_label.text(), "Epoch: 0/3", "Epoch label should be updated")
        self.assertEqual(self.training_dialog.start_stop_button.text(), "Stop Training", "Button should say 'Stop Training'")
        
        # Test step completed
        self.training_dialog._on_step_completed(
            step=50,
            loss=1.5,
            learning_rate=0.0005,
            perplexity=4.48,
            progress=50.0,
            estimated_time_remaining=30.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.training_dialog.step_label.text(), "Step: 50/100", "Step label should be updated")
        self.assertEqual(self.training_dialog.loss_label.text(), "Loss: 1.5000", "Loss label should be updated")
        self.assertEqual(self.training_dialog.time_label.text(), "Time Remaining: 30.0s", "Time label should be updated")
        self.assertEqual(self.training_dialog.progress_bar.value(), 50, "Progress bar should be updated")
        
        # Test epoch completed
        self.training_dialog._on_epoch_completed(
            epoch=2,
            eval_loss=1.4,
            eval_perplexity=4.06,
            bleu_score=0.5,
            rouge_scores={"rouge1": 0.6, "rouge2": 0.4, "rougeL": 0.5},
            progress=66.7,
            estimated_time_remaining=20.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.training_dialog.epoch_label.text(), "Epoch: 2/3", "Epoch label should be updated")
        self.assertEqual(self.training_dialog.loss_label.text(), "Loss: 1.4000 (eval)", "Loss label should be updated")
        
        # Test training ended
        self.training_dialog._on_training_ended(
            adapter_name="test-adapter",
            base_model="llama3-8b",
            adapter_type="lora",
            elapsed_time=60.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.training_dialog.time_label.text(), "Time: 60.0s", "Time label should be updated")
        self.assertEqual(self.training_dialog.start_stop_button.text(), "Start Training", "Button should say 'Start Training'")
        self.assertTrue(self.training_dialog.save_results_button.isEnabled(), "Save results button should be enabled")
        self.assertTrue(self.training_dialog.export_report_button.isEnabled(), "Export report button should be enabled")
    
    def test_adapter_to_training_integration(self):
        """Test the integration between adapter config dialog and training visualization dialog."""
        # Set up the mock training dialog
        mock_training_dialog = MagicMock(spec=TrainingVisualizationDialog)
        
        # Patch the _create_training_visualization_dialog method
        self.adapter_dialog._create_training_visualization_dialog = MagicMock(return_value=mock_training_dialog)
        
        # Set up dataset preparation mock
        self.dataset_preparation_mock.get_dataset_info.return_value = {
            "format": "instruction",
            "samples": 1000,
            "train_path": os.path.join(self.test_dir, "train.jsonl"),
            "eval_path": os.path.join(self.test_dir, "eval.jsonl")
        }
        
        # Fill in adapter config dialog fields
        self.adapter_dialog.adapter_name_edit.setText("test-adapter")
        self.adapter_dialog.adapter_type_combo = MagicMock()
        self.adapter_dialog.adapter_type_combo.currentText.return_value = "LoRA"
        self.adapter_dialog.base_model_combo.setCurrentText("llama-7b")
        self.adapter_dialog.rank_spinbox = MagicMock()
        self.adapter_dialog.rank_spinbox.value.return_value = 8
        self.adapter_dialog.alpha_spinbox = MagicMock()
        self.adapter_dialog.alpha_spinbox.value.return_value = 16
        self.adapter_dialog.dropout_spinbox = MagicMock()
        self.adapter_dialog.dropout_spinbox.value.return_value = 0.05
        self.adapter_dialog.learning_rate_spinbox = MagicMock()
        self.adapter_dialog.learning_rate_spinbox.value.return_value = 0.0002
        self.adapter_dialog.batch_size_spinbox = MagicMock()
        self.adapter_dialog.batch_size_spinbox.value.return_value = 4
        self.adapter_dialog.epochs_spinbox = MagicMock()
        self.adapter_dialog.epochs_spinbox.value.return_value = 3
        self.adapter_dialog.max_steps_spinbox = MagicMock()
        self.adapter_dialog.max_steps_spinbox.value.return_value = 100
        
        # Mock the validation method to always return True
        self.adapter_dialog._validate_training_config = MagicMock(return_value=True)
        
        # Click the start training button
        with patch('src.ui.adapter_config_dialog.QMessageBox'):
            self.adapter_dialog._on_start_training()
        
        # Check that the training dialog was created
        self.adapter_dialog._create_training_visualization_dialog.assert_called_once()
        
        # Check that the training dialog was configured
        mock_training_dialog.set_training_config.assert_called_once()
        
        # Check the training configuration parameters
        args, kwargs = mock_training_dialog.set_training_config.call_args
        self.assertEqual(kwargs["adapter_name"], "test-adapter")
        self.assertEqual(kwargs["base_model"], "llama-7b")
    
    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling in the UI components."""
        # Test boundary values - max epochs
        # Set up spinbox with boundary value
        self.adapter_dialog.epochs_spin = MagicMock()
        self.adapter_dialog.epochs_spin.maximum = MagicMock(return_value=100)
        self.adapter_dialog.epochs_spin.value = MagicMock(return_value=100)  # Maximum allowed value
        
        # Mock the validation method to check epochs
        def validate_epochs():
            if self.adapter_dialog.epochs_spin.value() > self.adapter_dialog.epochs_spin.maximum():
                return False
            return True
        
        self.adapter_dialog._validate_training_config = MagicMock(side_effect=validate_epochs)
        
        # This should pass validation since it's at the boundary but not exceeding it
        self.assertTrue(self.adapter_dialog._validate_training_config())
