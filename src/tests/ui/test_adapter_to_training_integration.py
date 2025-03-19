#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for the integration between adapter config dialog and training visualization dialog.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, ANY
import tempfile

from PyQt6.QtWidgets import QApplication

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.adapter_config_dialog import AdapterConfigDialog
from src.ui.training_visualization_dialog import TrainingVisualizationDialog
from src.ai.adapter_support import AdapterManager
from src.ai.model_registry import ModelRegistry
from src.ai.dataset_preparation import DatasetPreparation
from src.ai.training_monitor import TrainingMonitor


class TestAdapterToTrainingIntegration(unittest.TestCase):
    """Test the integration between adapter config dialog and training visualization dialog."""
    
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
        
        # Mock services for adapter config dialog
        self.adapter_manager_mock = MagicMock(spec=AdapterManager)
        self.model_registry_mock = MagicMock(spec=ModelRegistry)
        self.dataset_preparation_mock = MagicMock(spec=DatasetPreparation)
        
        # Add get_dataset_info method to dataset_preparation_mock
        # This method is used in AdapterConfigDialog but not defined in DatasetPreparation
        self.dataset_preparation_mock.get_dataset_info = MagicMock()
        
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
    
    def tearDown(self):
        """Tear down the test case."""
        self.adapter_dialog.close()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    @patch('src.ui.adapter_config_dialog.TrainingVisualizationDialog')
    def test_adapter_to_training_integration(self, mock_training_dialog_class):
        """Test the integration between adapter config dialog and training visualization dialog."""
        # Set up the mock training dialog
        mock_training_dialog = MagicMock(spec=TrainingVisualizationDialog)
        mock_training_dialog_class.return_value = mock_training_dialog
        
        # Set up dataset preparation mock
        self.dataset_preparation_mock.get_dataset_info.return_value = {
            "format": "instruction",
            "samples": 1000,
            "train_path": os.path.join(self.test_dir, "train.jsonl"),
            "eval_path": os.path.join(self.test_dir, "eval.jsonl")
        }
        
        # Fill in adapter config dialog fields
        self.adapter_dialog.adapter_name_edit.setText("test-adapter")
        self.adapter_dialog.base_model_combo.setCurrentText("llama-7b")
        
        # Mock the validation method to always return True
        self.adapter_dialog._validate_training_config = MagicMock(return_value=True)
        
        # Mock the get_current_configuration method
        self.adapter_dialog._get_current_configuration = MagicMock(return_value={
            "adapter_type": "lora",
            "adapter_params": {
                "name": "test-adapter",
                "lora_r": 8,
                "lora_alpha": 16,
                "lora_dropout": 0.05
            },
            "training": {
                "batch_size": 4,
                "epochs": 3
            }
        })
        
        # Mock the get_training_parameters method
        self.adapter_dialog._get_training_parameters = MagicMock(return_value={
            "batch_size": 4,
            "learning_rate": 0.0002,
            "rank": 8,
            "alpha": 16,
            "dropout": 0.05
        })
        
        # Click the start training button
        with patch('src.ui.adapter_config_dialog.QMessageBox'):
            self.adapter_dialog._on_start_training()
        
        # Check that the training dialog was created
        mock_training_dialog_class.assert_called_once()
        
        # Check that the training dialog was configured
        mock_training_dialog.set_training_config.assert_called_once()
        
        # Check that the training dialog was shown
        mock_training_dialog.show.assert_called_once()


if __name__ == "__main__":
    unittest.main()
