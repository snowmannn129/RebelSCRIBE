#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the adapter configuration dialog.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QTableWidgetItem
from PyQt6.QtCore import Qt

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.adapter_config_dialog import AdapterConfigDialog, AdapterType, DatasetFormat
from src.ai.adapter_support import AdapterManager
from src.ai.model_registry import ModelRegistry


class TestAdapterConfigDialog(unittest.TestCase):
    """Test cases for the adapter configuration dialog."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Create mocks
        self.adapter_manager_mock = MagicMock(spec=AdapterManager)
        self.model_registry_mock = MagicMock(spec=ModelRegistry)
        
        # Set up model registry mock to return some models
        self.model_registry_mock.get_all_models.return_value = [
            "llama3-8b", "mistral-7b", "phi-2"
        ]
        
        # Create dialog
        self.dialog = AdapterConfigDialog(
            adapter_manager=self.adapter_manager_mock,
            model_registry=self.model_registry_mock
        )
    
    def tearDown(self):
        """Tear down the test case."""
        self.dialog.close()
    
    def test_init(self):
        """Test initialization of the dialog."""
        # Check that the dialog was created
        self.assertIsNotNone(self.dialog)
        
        # Check that the tab widget was created
        self.assertIsNotNone(self.dialog.tab_widget)
        
        # Check that the tabs were created
        self.assertEqual(self.dialog.tab_widget.count(), 4)
        self.assertEqual(self.dialog.tab_widget.tabText(0), "Adapter")
        self.assertEqual(self.dialog.tab_widget.tabText(1), "Dataset")
        self.assertEqual(self.dialog.tab_widget.tabText(2), "Training")
        self.assertEqual(self.dialog.tab_widget.tabText(3), "Evaluation")
        
        # Check that the button box was created
        self.assertIsNotNone(self.dialog.button_box)
        self.assertIsNotNone(self.dialog.button_box.button(QDialogButtonBox.StandardButton.Ok))
        self.assertIsNotNone(self.dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel))
        self.assertIsNotNone(self.dialog.button_box.button(QDialogButtonBox.StandardButton.Apply))
    
    def test_adapter_tab(self):
        """Test the adapter tab."""
        # Check that the adapter tab was created
        self.assertIsNotNone(self.dialog.adapter_tab)
        
        # Check that the base model combo was created and populated
        self.assertIsNotNone(self.dialog.base_model_combo)
        self.assertEqual(self.dialog.base_model_combo.count(), 3)
        self.assertEqual(self.dialog.base_model_combo.itemText(0), "llama3-8b")
        self.assertEqual(self.dialog.base_model_combo.itemText(1), "mistral-7b")
        self.assertEqual(self.dialog.base_model_combo.itemText(2), "phi-2")
        
        # Check that the adapter type radio buttons were created
        self.assertIsNotNone(self.dialog.adapter_type_radio_group)
        self.assertIsNotNone(self.dialog.lora_radio)
        self.assertIsNotNone(self.dialog.qlora_radio)
        self.assertIsNotNone(self.dialog.prefix_tuning_radio)
        
        # Check that LoRA is selected by default
        self.assertTrue(self.dialog.lora_radio.isChecked())
        self.assertFalse(self.dialog.qlora_radio.isChecked())
        self.assertFalse(self.dialog.prefix_tuning_radio.isChecked())
        
        # Check that the adapter parameters widgets were created
        self.assertIsNotNone(self.dialog.adapter_params_group)
        self.assertIsNotNone(self.dialog.adapter_name_edit)
        self.assertIsNotNone(self.dialog.lora_params_widget)
        self.assertIsNotNone(self.dialog.qlora_params_widget)
        self.assertIsNotNone(self.dialog.prefix_tuning_params_widget)
        
        # Check that all parameter widgets exist
        self.assertIsNotNone(self.dialog.lora_params_widget)
        self.assertIsNotNone(self.dialog.qlora_params_widget)
        self.assertIsNotNone(self.dialog.prefix_tuning_params_widget)
    
    def test_dataset_tab(self):
        """Test the dataset tab."""
        # Check that the dataset tab was created
        self.assertIsNotNone(self.dialog.dataset_tab)
        
        # Check that the dataset source radio buttons were created
        self.assertIsNotNone(self.dialog.dataset_source_radio_group)
        self.assertIsNotNone(self.dialog.file_radio)
        self.assertIsNotNone(self.dialog.manual_radio)
        
        # Check that file is selected by default
        self.assertTrue(self.dialog.file_radio.isChecked())
        self.assertFalse(self.dialog.manual_radio.isChecked())
        
        # Check that the dataset format radio buttons were created
        self.assertIsNotNone(self.dialog.dataset_format_radio_group)
        self.assertIsNotNone(self.dialog.text_format_radio)
        self.assertIsNotNone(self.dialog.instruction_format_radio)
        self.assertIsNotNone(self.dialog.conversation_format_radio)
        
        # Check that instruction format is selected by default
        self.assertFalse(self.dialog.text_format_radio.isChecked())
        self.assertTrue(self.dialog.instruction_format_radio.isChecked())
        self.assertFalse(self.dialog.conversation_format_radio.isChecked())
        
        # Check that the dataset content widgets were created
        self.assertIsNotNone(self.dialog.text_format_widget)
        self.assertIsNotNone(self.dialog.instruction_format_widget)
        self.assertIsNotNone(self.dialog.conversation_format_widget)
        
        # Check that all format widgets exist
        self.assertIsNotNone(self.dialog.text_format_widget)
        self.assertIsNotNone(self.dialog.instruction_format_widget)
        self.assertIsNotNone(self.dialog.conversation_format_widget)
    
    def test_training_tab(self):
        """Test the training tab."""
        # Check that the training tab was created
        self.assertIsNotNone(self.dialog.training_tab)
        
        # Check that the training parameters widgets were created
        self.assertIsNotNone(self.dialog.batch_size_spin)
        self.assertIsNotNone(self.dialog.gradient_accumulation_spin)
        self.assertIsNotNone(self.dialog.epochs_spin)
        self.assertIsNotNone(self.dialog.learning_rate_spin)
        self.assertIsNotNone(self.dialog.max_length_spin)
        self.assertIsNotNone(self.dialog.fp16_check)
        
        # Check that the output directory widgets were created
        self.assertIsNotNone(self.dialog.output_dir_edit)
        self.assertIsNotNone(self.dialog.output_dir_button)
        
        # Check that the training control widgets were created
        self.assertIsNotNone(self.dialog.training_progress_bar)
        self.assertIsNotNone(self.dialog.training_status_label)
        self.assertIsNotNone(self.dialog.start_training_button)
        self.assertIsNotNone(self.dialog.stop_training_button)
        self.assertIsNotNone(self.dialog.load_results_button)
    
    def test_evaluation_tab(self):
        """Test the evaluation tab."""
        # Check that the evaluation tab was created
        self.assertIsNotNone(self.dialog.evaluation_tab)
        
        # Check that the evaluation dataset widgets were created
        self.assertIsNotNone(self.dialog.use_train_split_check)
        self.assertIsNotNone(self.dialog.eval_split_spin)
        self.assertIsNotNone(self.dialog.separate_eval_check)
        self.assertIsNotNone(self.dialog.eval_file_edit)
        self.assertIsNotNone(self.dialog.eval_file_button)
        
        # Check that the evaluation metrics widgets were created
        self.assertIsNotNone(self.dialog.perplexity_check)
        self.assertIsNotNone(self.dialog.bleu_check)
        self.assertIsNotNone(self.dialog.rouge_check)
        
        # Check that the evaluation results widgets were created
        self.assertIsNotNone(self.dialog.eval_results_table)
        self.assertIsNotNone(self.dialog.run_eval_button)
        self.assertIsNotNone(self.dialog.export_eval_button)
    
    def test_adapter_type_changed(self):
        """Test changing the adapter type."""
        # Check that all parameter widgets exist
        self.assertIsNotNone(self.dialog.lora_params_widget)
        self.assertIsNotNone(self.dialog.qlora_params_widget)
        self.assertIsNotNone(self.dialog.prefix_tuning_params_widget)
        
        # Initially LoRA is selected
        self.assertTrue(self.dialog.lora_radio.isChecked())
        
        # Change to QLoRA
        self.dialog.qlora_radio.setChecked(True)
        self.dialog._on_adapter_type_changed(self.dialog.qlora_radio)
        
        # Check that QLoRA is selected
        self.assertTrue(self.dialog.qlora_radio.isChecked())
        
        # Change to Prefix Tuning
        self.dialog.prefix_tuning_radio.setChecked(True)
        self.dialog._on_adapter_type_changed(self.dialog.prefix_tuning_radio)
        
        # Check that Prefix Tuning is selected
        self.assertTrue(self.dialog.prefix_tuning_radio.isChecked())
        
        # Change back to LoRA
        self.dialog.lora_radio.setChecked(True)
        self.dialog._on_adapter_type_changed(self.dialog.lora_radio)
        
        # Check that LoRA is selected
        self.assertTrue(self.dialog.lora_radio.isChecked())
    
    def test_dataset_format_changed(self):
        """Test changing the dataset format."""
        # Check that all format widgets exist
        self.assertIsNotNone(self.dialog.text_format_widget)
        self.assertIsNotNone(self.dialog.instruction_format_widget)
        self.assertIsNotNone(self.dialog.conversation_format_widget)
        
        # Initially instruction format is selected
        self.assertTrue(self.dialog.instruction_format_radio.isChecked())
        
        # Change to text format
        self.dialog.text_format_radio.setChecked(True)
        self.dialog._on_dataset_format_changed(self.dialog.text_format_radio)
        
        # Check that text format is selected
        self.assertTrue(self.dialog.text_format_radio.isChecked())
        
        # Change to conversation format
        self.dialog.conversation_format_radio.setChecked(True)
        self.dialog._on_dataset_format_changed(self.dialog.conversation_format_radio)
        
        # Check that conversation format is selected
        self.assertTrue(self.dialog.conversation_format_radio.isChecked())
        
        # Change back to instruction format
        self.dialog.instruction_format_radio.setChecked(True)
        self.dialog._on_dataset_format_changed(self.dialog.instruction_format_radio)
        
        # Check that instruction format is selected
        self.assertTrue(self.dialog.instruction_format_radio.isChecked())
    
    def test_dataset_source_changed(self):
        """Test changing the dataset source."""
        # Initially file is selected
        self.assertTrue(self.dialog.dataset_file_edit.isEnabled())
        self.assertTrue(self.dialog.dataset_file_button.isEnabled())
        self.assertTrue(self.dialog.file_format_combo.isEnabled())
        
        # Change to manual entry
        self.dialog.manual_radio.setChecked(True)
        self.dialog._on_dataset_source_changed(self.dialog.manual_radio)
        
        # Check that file selection is disabled
        self.assertFalse(self.dialog.dataset_file_edit.isEnabled())
        self.assertFalse(self.dialog.dataset_file_button.isEnabled())
        self.assertFalse(self.dialog.file_format_combo.isEnabled())
        
        # Change back to file
        self.dialog.file_radio.setChecked(True)
        self.dialog._on_dataset_source_changed(self.dialog.file_radio)
        
        # Check that file selection is enabled
        self.assertTrue(self.dialog.dataset_file_edit.isEnabled())
        self.assertTrue(self.dialog.dataset_file_button.isEnabled())
        self.assertTrue(self.dialog.file_format_combo.isEnabled())
    
    def test_separate_eval_toggled(self):
        """Test toggling the separate evaluation dataset checkbox."""
        # Initially separate evaluation is not checked
        self.assertFalse(self.dialog.eval_file_edit.isEnabled())
        self.assertFalse(self.dialog.eval_file_button.isEnabled())
        self.assertTrue(self.dialog.eval_split_spin.isEnabled())
        
        # Check separate evaluation
        self.dialog.separate_eval_check.setChecked(True)
        self.dialog._on_separate_eval_toggled(True)
        
        # Check that evaluation file selection is enabled and split is disabled
        self.assertTrue(self.dialog.eval_file_edit.isEnabled())
        self.assertTrue(self.dialog.eval_file_button.isEnabled())
        self.assertFalse(self.dialog.eval_split_spin.isEnabled())
        
        # Uncheck separate evaluation
        self.dialog.separate_eval_check.setChecked(False)
        self.dialog._on_separate_eval_toggled(False)
        
        # Check that evaluation file selection is disabled and split is enabled
        self.assertFalse(self.dialog.eval_file_edit.isEnabled())
        self.assertFalse(self.dialog.eval_file_button.isEnabled())
        self.assertTrue(self.dialog.eval_split_spin.isEnabled())
    
    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
    def test_browse_dataset_file(self, mock_get_open_file_name):
        """Test browsing for a dataset file."""
        # Set up mock to return a file path
        mock_get_open_file_name.return_value = ('/path/to/dataset.json', 'JSON Files (*.json)')
        
        # Call the method
        self.dialog._on_browse_dataset_file()
        
        # Check that the file path was set
        self.assertEqual(self.dialog.dataset_file_edit.text(), '/path/to/dataset.json')
    
    @patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
    def test_browse_output_dir(self, mock_get_existing_directory):
        """Test browsing for an output directory."""
        # Set up mock to return a directory path
        mock_get_existing_directory.return_value = '/path/to/output'
        
        # Call the method
        self.dialog._on_browse_output_dir()
        
        # Check that the directory path was set
        self.assertEqual(self.dialog.output_dir_edit.text(), '/path/to/output')
    
    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
    def test_browse_eval_file(self, mock_get_open_file_name):
        """Test browsing for an evaluation file."""
        # Set up mock to return a file path
        mock_get_open_file_name.return_value = ('/path/to/eval.json', 'All Files (*)')
        
        # Call the method
        self.dialog._on_browse_eval_file()
        
        # Check that the file path was set
        self.assertEqual(self.dialog.eval_file_edit.text(), '/path/to/eval.json')
    
    def test_add_instruction_row(self):
        """Test adding an instruction row."""
        # Get initial row count
        initial_row_count = self.dialog.instruction_table.rowCount()
        
        # Add a row
        self.dialog._on_add_instruction_row()
        
        # Check that a row was added
        self.assertEqual(self.dialog.instruction_table.rowCount(), initial_row_count + 1)
    
    def test_remove_instruction_row(self):
        """Test removing an instruction row."""
        # Add some rows
        self.dialog._on_add_instruction_row()
        self.dialog._on_add_instruction_row()
        initial_row_count = self.dialog.instruction_table.rowCount()
        
        # Select a row
        self.dialog.instruction_table.selectRow(0)
        
        # Remove the row
        self.dialog._on_remove_instruction_row()
        
        # Check that a row was removed
        self.assertEqual(self.dialog.instruction_table.rowCount(), initial_row_count - 1)
    
    def test_add_conversation(self):
        """Test adding a conversation."""
        # Get initial count
        initial_count = self.dialog.conversation_list.count()
        
        # Add a conversation
        self.dialog._on_add_conversation()
        
        # Check that a conversation was added
        self.assertEqual(self.dialog.conversation_list.count(), initial_count + 1)
    
    def test_remove_conversation(self):
        """Test removing a conversation."""
        # Add some conversations
        self.dialog._on_add_conversation()
        self.dialog._on_add_conversation()
        initial_count = self.dialog.conversation_list.count()
        
        # Select a conversation
        self.dialog.conversation_list.setCurrentRow(0)
        
        # Remove the conversation
        self.dialog._on_remove_conversation()
        
        # Check that a conversation was removed
        self.assertEqual(self.dialog.conversation_list.count(), initial_count - 1)
    
    def test_load_results_button_exists(self):
        """Test that the load results button exists and has the correct text."""
        # Check that the load results button exists and is enabled
        self.assertIsNotNone(self.dialog.load_results_button)
        self.assertTrue(self.dialog.load_results_button.isEnabled())
        
        # Check that the button has the correct text
        self.assertEqual(self.dialog.load_results_button.text(), "Load Results")
    
    def test_load_results_button(self):
        """Test the load results button functionality."""
        # Check that the load results button exists and is enabled
        self.assertIsNotNone(self.dialog.load_results_button)
        self.assertTrue(self.dialog.load_results_button.isEnabled())
        
        # Check that the button has the correct text
        self.assertEqual(self.dialog.load_results_button.text(), "Load Results")
    
    @patch('src.ui.adapter_config_dialog.config')
    def test_get_current_configuration(self, mock_config):
        """Test getting the current configuration."""
        # Set up a configuration
        self.dialog.base_model_combo.setCurrentText("llama3-8b")
        self.dialog.lora_radio.setChecked(True)
        self.dialog.adapter_name_edit.setText("test-adapter")
        self.dialog.lora_r_spin.setValue(16)
        self.dialog.lora_alpha_spin.setValue(32)
        self.dialog.lora_dropout_spin.setValue(0.1)
        self.dialog.target_modules_edit.setText("q_proj,k_proj,v_proj")
        self.dialog.bias_combo.setCurrentText("none")
        
        self.dialog.file_radio.setChecked(True)
        self.dialog.dataset_file_edit.setText("/path/to/dataset.json")
        self.dialog.file_format_combo.setCurrentText("JSON")
        self.dialog.instruction_format_radio.setChecked(True)
        
        self.dialog.batch_size_spin.setValue(8)
        self.dialog.gradient_accumulation_spin.setValue(2)
        self.dialog.epochs_spin.setValue(5)
        self.dialog.learning_rate_spin.setValue(5e-4)
        self.dialog.max_length_spin.setValue(1024)
        self.dialog.fp16_check.setChecked(True)
        self.dialog.output_dir_edit.setText("/path/to/output")
        
        self.dialog.use_train_split_check.setChecked(True)
        self.dialog.eval_split_spin.setValue(20)
        self.dialog.perplexity_check.setChecked(True)
        self.dialog.bleu_check.setChecked(True)
        self.dialog.rouge_check.setChecked(True)
        
        # Get the configuration
        config = self.dialog._get_current_configuration()
        
        # Check the configuration
        self.assertEqual(config["base_model"], "llama3-8b")
        self.assertEqual(config["adapter_type"], "lora")
        self.assertEqual(config["adapter_params"]["name"], "test-adapter")
        self.assertEqual(config["adapter_params"]["lora_r"], 16)
        self.assertEqual(config["adapter_params"]["lora_alpha"], 32)
        self.assertEqual(config["adapter_params"]["lora_dropout"], 0.1)
        self.assertEqual(config["adapter_params"]["target_modules"], ["q_proj", "k_proj", "v_proj"])
        self.assertEqual(config["adapter_params"]["bias"], "none")
        
        self.assertEqual(config["dataset"]["source"], "file")
        self.assertEqual(config["dataset"]["file_path"], "/path/to/dataset.json")
        self.assertEqual(config["dataset"]["file_format"], "JSON")
        self.assertEqual(config["dataset"]["format"], "instruction")
        
        self.assertEqual(config["training"]["batch_size"], 8)
        self.assertEqual(config["training"]["gradient_accumulation"], 2)
        self.assertEqual(config["training"]["epochs"], 5)
        self.assertEqual(config["training"]["learning_rate"], 5e-4)
        self.assertEqual(config["training"]["max_length"], 1024)
        self.assertTrue(config["training"]["fp16"])
        self.assertEqual(config["training"]["output_dir"], "/path/to/output")
        
        self.assertTrue(config["evaluation"]["use_train_split"])
        self.assertEqual(config["evaluation"]["eval_split"], 20)
        self.assertTrue(config["evaluation"]["perplexity"])
        self.assertTrue(config["evaluation"]["bleu"])
        self.assertTrue(config["evaluation"]["rouge"])


if __name__ == '__main__':
    unittest.main()
