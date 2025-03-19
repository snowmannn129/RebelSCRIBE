#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the integration between adapter configuration and training visualization.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile

from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QTableWidgetItem
from PyQt6.QtCore import Qt

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.adapter_config_dialog import AdapterConfigDialog
from src.ui.training_visualization_dialog import TrainingVisualizationDialog
from src.ai.training_monitor import TrainingMonitor
from src.ai.dataset_preparation import DatasetPreparation


class TestAdapterTrainingIntegration(unittest.TestCase):
    """Test cases for the integration between adapter configuration and training visualization."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Create mocks
        self.training_monitor_mock = MagicMock(spec=TrainingMonitor)
        self.dataset_preparation_mock = MagicMock(spec=DatasetPreparation)
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
        
        # Create adapter config dialog
        self.adapter_dialog = AdapterConfigDialog(
            dataset_preparation=self.dataset_preparation_mock
        )
        
        # Create training visualization dialog
        self.training_dialog = TrainingVisualizationDialog(
            training_monitor=self.training_monitor_mock
        )
    
    def tearDown(self):
        """Tear down the test case."""
        self.adapter_dialog.close()
        self.training_dialog.close()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_start_training_integration(self):
        """Test starting training from adapter config dialog."""
        # Create a mock TrainingVisualizationDialog
        mock_tvd = MagicMock(spec=TrainingVisualizationDialog)
        
        # Patch the _create_training_visualization_dialog method to return our mock
        original_create_tvd = self.adapter_dialog._create_training_visualization_dialog
        self.adapter_dialog._create_training_visualization_dialog = MagicMock(return_value=mock_tvd)
        
        # Fill in adapter config dialog fields
        self.adapter_dialog.adapter_name_edit.setText("test-adapter")
        self.adapter_dialog.lora_radio.setChecked(True)
        self.adapter_dialog.base_model_combo.setCurrentText("llama-7b")
        self.adapter_dialog.lora_r_spin.setValue(8)
        self.adapter_dialog.lora_alpha_spin.setValue(16)
        self.adapter_dialog.lora_dropout_spin.setValue(0.05)
        self.adapter_dialog.learning_rate_spin.setValue(0.0002)
        self.adapter_dialog.batch_size_spin.setValue(4)
        self.adapter_dialog.epochs_spin.setValue(3)
        
        # Set up dataset preparation mock
        # Add the get_dataset_info method to the mock
        self.dataset_preparation_mock.get_dataset_info = MagicMock()
        self.dataset_preparation_mock.get_dataset_info.return_value = {
            "format": "instruction",
            "samples": 1000,
            "train_path": os.path.join(self.test_dir, "train.jsonl"),
            "eval_path": os.path.join(self.test_dir, "eval.jsonl")
        }
        
        # Mock the _validate_training_config method to always return True
        original_validate = self.adapter_dialog._validate_training_config
        self.adapter_dialog._validate_training_config = MagicMock(return_value=True)
        
        # Click the start training button
        with patch('src.ui.adapter_config_dialog.QMessageBox'):
            self.adapter_dialog._on_start_training()
        
        # Check that the _create_training_visualization_dialog method was called
        self.adapter_dialog._create_training_visualization_dialog.assert_called_once()
        
        # Check that set_training_config was called on our mock
        mock_tvd.set_training_config.assert_called_once()
        
        # Check that show was called on our mock
        mock_tvd.show.assert_called_once()
        
        # Restore the original method
        self.adapter_dialog._create_training_visualization_dialog = original_create_tvd
    
    def test_load_training_results_integration(self):
        """Test loading training results from adapter config dialog."""
        # Create a mock metrics file
        metrics_file = os.path.join(self.test_dir, "metrics.json")
        with open(metrics_file, "w") as f:
            f.write("{}")
        
        # Create a mock TrainingVisualizationDialog
        mock_tvd = MagicMock(spec=TrainingVisualizationDialog)
        
        # Patch the _create_training_visualization_dialog method to return our mock
        original_create_tvd = self.adapter_dialog._create_training_visualization_dialog
        self.adapter_dialog._create_training_visualization_dialog = MagicMock(return_value=mock_tvd)
        
        # Call the load training results method
        with patch('src.ui.adapter_config_dialog.QFileDialog.getOpenFileName') as mock_get_open_filename:
            # Set up mock to return the metrics file
            mock_get_open_filename.return_value = (metrics_file, "JSON Files (*.json)")
            
            # Click the load results button
            self.adapter_dialog._on_load_results_clicked()
        
        # Check that the training dialog's load_training_results method was called
        mock_tvd.load_training_results.assert_called_once_with(metrics_file)
        
        # Check that the training dialog was shown
        mock_tvd.show.assert_called_once()
        
        # Restore the original method
        self.adapter_dialog._create_training_visualization_dialog = original_create_tvd
    
    def test_adapter_config_validation(self):
        """Test validation of adapter configuration before starting training."""
        # Create a method to test validation with different configurations
        def test_validation(adapter_name, adapter_type, base_model, expected_valid):
            # Reset mocks
            self.dataset_preparation_mock.reset_mock()
            
            # Fill in adapter config dialog fields
            self.adapter_dialog.adapter_name_edit.setText(adapter_name)
            
            # Set adapter type based on the parameter
            if adapter_type == "LoRA":
                self.adapter_dialog.lora_radio.setChecked(True)
            elif adapter_type == "QLoRA":
                self.adapter_dialog.qlora_radio.setChecked(True)
            elif adapter_type == "Prefix Tuning":
                self.adapter_dialog.prefix_tuning_radio.setChecked(True)
                
            self.adapter_dialog.base_model_combo.setCurrentText(base_model)
            
            # Set up dataset preparation mock
            # Add the get_dataset_info method to the mock
            self.dataset_preparation_mock.get_dataset_info = MagicMock()
            if expected_valid:
                # Create a dataset file
                dataset_file = os.path.join(self.test_dir, "dataset.jsonl")
                with open(dataset_file, "w") as f:
                    f.write('{"prompt": "Test prompt", "completion": "Test completion"}')
                
                self.dataset_preparation_mock.get_dataset_info.return_value = {
                    "format": "instruction",
                    "samples": 1000,
                    "train_path": os.path.join(self.test_dir, "train.jsonl"),
                    "eval_path": os.path.join(self.test_dir, "eval.jsonl")
                }
                
                # Set the dataset file
                self.adapter_dialog.dataset_file_edit.setText(dataset_file)
                
                # Add a row to the instruction table
                self.adapter_dialog.instruction_table.setRowCount(0)
                row = self.adapter_dialog.instruction_table.rowCount()
                self.adapter_dialog.instruction_table.insertRow(row)
                self.adapter_dialog.instruction_table.setItem(row, 0, QTableWidgetItem("Test prompt"))
                self.adapter_dialog.instruction_table.setItem(row, 1, QTableWidgetItem("Test completion"))
            else:
                self.dataset_preparation_mock.get_dataset_info.return_value = None
            
            # Set up output directory
            if expected_valid:
                self.adapter_dialog.output_dir_edit.setText(os.path.join(self.test_dir, "output"))
            else:
                self.adapter_dialog.output_dir_edit.setText("")
                
            # Make sure separate evaluation dataset is not checked
            self.adapter_dialog.separate_eval_check.setChecked(False)
            
            # Check validation
            with patch('src.ui.adapter_config_dialog.QMessageBox'):
                result = self.adapter_dialog._validate_training_config()
            
            # Print debug information
            print(f"Validation result: {result}, expected: {expected_valid}")
            print(f"Adapter name: {self.adapter_dialog.adapter_name_edit.text()}")
            print(f"Base model: {self.adapter_dialog.base_model_combo.currentText()}")
            print(f"Output dir: {self.adapter_dialog.output_dir_edit.text()}")
            print(f"Instruction table rows: {self.adapter_dialog.instruction_table.rowCount()}")
            print(f"Dataset info: {self.dataset_preparation_mock.get_dataset_info.return_value}")
            print(f"Instruction format checked: {self.adapter_dialog.instruction_format_radio.isChecked()}")
            print(f"File format checked: {self.adapter_dialog.file_radio.isChecked()}")
            print(f"Dataset file: {self.adapter_dialog.dataset_file_edit.text()}")
            
            # Check the result
            self.assertEqual(result, expected_valid)
        
        # Test with valid configuration
        test_validation("test-adapter", "LoRA", "llama-7b", True)
        
        # Test with missing adapter name
        test_validation("", "LoRA", "llama-7b", False)
        
        # Test with missing base model
        test_validation("test-adapter", "LoRA", "", False)
        
        # Test with missing dataset
        self.dataset_preparation_mock.get_dataset_info.return_value = None
        test_validation("test-adapter", "LoRA", "llama-7b", False)
    
    def test_training_parameter_collection(self):
        """Test collection of training parameters from adapter config dialog."""
        # Fill in adapter config dialog fields
        self.adapter_dialog.adapter_name_edit.setText("test-adapter")
        self.adapter_dialog.lora_radio.setChecked(True)
        self.adapter_dialog.base_model_combo.setCurrentText("llama-7b")
        self.adapter_dialog.lora_r_spin.setValue(8)
        self.adapter_dialog.lora_alpha_spin.setValue(16)
        self.adapter_dialog.lora_dropout_spin.setValue(0.05)
        self.adapter_dialog.learning_rate_spin.setValue(0.0002)
        self.adapter_dialog.batch_size_spin.setValue(4)
        self.adapter_dialog.epochs_spin.setValue(3)
        self.adapter_dialog.gradient_accumulation_spin.setValue(1)
        
        # Get training parameters
        parameters = self.adapter_dialog._get_training_parameters()
        
        # Check parameters
        self.assertEqual(parameters["rank"], 8)
        self.assertEqual(parameters["alpha"], 16)
        self.assertEqual(parameters["dropout"], 0.05)
        self.assertEqual(parameters["learning_rate"], 0.0002)
        self.assertEqual(parameters["batch_size"], 4)
        self.assertEqual(parameters["warmup_steps"], 0)  # 10% of 3 epochs, rounded down to 0
        self.assertEqual(parameters["weight_decay"], 0.01)
        self.assertEqual(parameters["gradient_accumulation"], 1)
    
    def test_adapter_type_change(self):
        """Test changing adapter type updates UI elements."""
        # Mock the _on_adapter_type_changed method to avoid UI visibility issues in tests
        with patch.object(self.adapter_dialog, '_on_adapter_type_changed') as mock_on_adapter_type_changed:
            # Test LoRA adapter type
            self.adapter_dialog.lora_radio.setChecked(True)
            self.adapter_dialog._on_adapter_type_changed(self.adapter_dialog.lora_radio)
            
            # Check that the method was called with the LoRA radio button
            mock_on_adapter_type_changed.assert_called_with(self.adapter_dialog.lora_radio)
            
            # Test QLoRA adapter type
            self.adapter_dialog.qlora_radio.setChecked(True)
            self.adapter_dialog._on_adapter_type_changed(self.adapter_dialog.qlora_radio)
            
            # Check that the method was called with the QLoRA radio button
            mock_on_adapter_type_changed.assert_called_with(self.adapter_dialog.qlora_radio)
            
            # Test Prefix Tuning adapter type
            self.adapter_dialog.prefix_tuning_radio.setChecked(True)
            self.adapter_dialog._on_adapter_type_changed(self.adapter_dialog.prefix_tuning_radio)
            
            # Check that the method was called with the Prefix Tuning radio button
            mock_on_adapter_type_changed.assert_called_with(self.adapter_dialog.prefix_tuning_radio)


if __name__ == '__main__':
    unittest.main()
