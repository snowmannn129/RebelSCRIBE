#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the training visualization dialog.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile

from PyQt6.QtWidgets import QApplication, QDialogButtonBox
from PyQt6.QtCore import Qt

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.training_visualization_dialog import TrainingVisualizationDialog, TrainingProgressCallback
from src.ai.training_monitor import TrainingMonitor, TrainingMetrics


class TestTrainingVisualizationDialog(unittest.TestCase):
    """Test cases for the training visualization dialog."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Create mocks
        self.training_monitor_mock = MagicMock(spec=TrainingMonitor)
        
        # Add visualizer attribute to the training monitor mock
        self.training_monitor_mock.visualizer = MagicMock()
        
        # Add metrics attribute to the training monitor mock
        self.training_monitor_mock.metrics = MagicMock()
        
        # Create a mock for the TrainingProgressCallback
        self.progress_callback_mock = MagicMock()
        
        # Patch the TrainingProgressCallback class and _connect_signals method
        with patch('src.ui.training_visualization_dialog.TrainingProgressCallback', return_value=self.progress_callback_mock), \
             patch.object(TrainingVisualizationDialog, '_connect_signals', return_value=None):
            
            # Create dialog
            self.dialog = TrainingVisualizationDialog(
                training_monitor=self.training_monitor_mock
            )
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
    
    def tearDown(self):
        """Tear down the test case."""
        self.dialog.close()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initialization of the dialog."""
        # Check that the dialog was created
        self.assertIsNotNone(self.dialog)
        
        # Check that the tab widget was created
        self.assertIsNotNone(self.dialog.tab_widget)
        
        # Check that the tabs were created
        self.assertEqual(self.dialog.tab_widget.count(), 6)
        self.assertEqual(self.dialog.tab_widget.tabText(0), "Loss")
        self.assertEqual(self.dialog.tab_widget.tabText(1), "Perplexity")
        self.assertEqual(self.dialog.tab_widget.tabText(2), "Learning Rate")
        self.assertEqual(self.dialog.tab_widget.tabText(3), "Metrics")
        self.assertEqual(self.dialog.tab_widget.tabText(4), "Progress")
        self.assertEqual(self.dialog.tab_widget.tabText(5), "Summary")
        
        # Check that the training info group was created
        self.assertIsNotNone(self.dialog.training_info_group)
        self.assertIsNotNone(self.dialog.adapter_name_label)
        self.assertIsNotNone(self.dialog.base_model_label)
        self.assertIsNotNone(self.dialog.adapter_type_label)
        
        # Check that the progress group was created
        self.assertIsNotNone(self.dialog.progress_group)
        self.assertIsNotNone(self.dialog.progress_bar)
        self.assertIsNotNone(self.dialog.step_label)
        self.assertIsNotNone(self.dialog.epoch_label)
        self.assertIsNotNone(self.dialog.loss_label)
        self.assertIsNotNone(self.dialog.time_label)
        
        # Check that the buttons were created
        self.assertIsNotNone(self.dialog.start_stop_button)
        self.assertIsNotNone(self.dialog.save_results_button)
        self.assertIsNotNone(self.dialog.export_report_button)
        self.assertIsNotNone(self.dialog.close_button)
    
    def test_set_training_config(self):
        """Test setting the training configuration."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Check that the configuration was set
        self.assertEqual(self.dialog.adapter_name_label.text(), "test-adapter")
        self.assertEqual(self.dialog.base_model_label.text(), "test-model")
        self.assertEqual(self.dialog.adapter_type_label.text(), "lora")
        self.assertEqual(self.dialog.step_label.text(), "Step: 0/100")
        self.assertEqual(self.dialog.epoch_label.text(), "Epoch: 0/3")
        
        # Check that the start button is enabled
        self.assertTrue(self.dialog.start_stop_button.isEnabled())
        self.assertEqual(self.dialog.start_stop_button.text(), "Start Training")
        
        # Check that the configuration was stored
        self.assertEqual(self.dialog.adapter_name, "test-adapter")
        self.assertEqual(self.dialog.base_model, "test-model")
        self.assertEqual(self.dialog.adapter_type, "lora")
        self.assertEqual(self.dialog.total_epochs, 3)
        self.assertEqual(self.dialog.total_steps, 100)
        self.assertEqual(self.dialog.parameters, {"batch_size": 4, "learning_rate": 0.001})
        self.assertEqual(self.dialog.dataset_info, {"format": "instruction", "samples": 1000})
    
    @patch('src.ui.training_visualization_dialog.QMessageBox')
    def test_load_training_results(self, mock_message_box):
        """Test loading training results."""
        # Create a mock metrics object
        mock_metrics = MagicMock(spec=TrainingMetrics)
        mock_metrics.adapter_name = "test-adapter"
        mock_metrics.base_model = "test-model"
        mock_metrics.adapter_type = "lora"
        mock_metrics.steps_completed = 100
        mock_metrics.total_steps = 100
        mock_metrics.epochs_completed = 3
        mock_metrics.total_epochs = 3
        mock_metrics.train_loss = [2.0, 1.5, 1.0]
        mock_metrics.get_elapsed_time.return_value = 60.0
        mock_metrics.get_progress.return_value = (100.0, 100.0)
        
        # Set up the training monitor mock to return the mock metrics
        mock_results = {
            "metrics": mock_metrics,
            "visualizations": {},
            "summary": {}
        }
        self.training_monitor_mock.load_results.return_value = mock_results
        
        # Load training results
        self.dialog.load_training_results("metrics_file.json")
        
        # Check that the training monitor was called
        self.training_monitor_mock.load_results.assert_called_once_with("metrics_file.json")
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.adapter_name_label.text(), "test-adapter")
        self.assertEqual(self.dialog.base_model_label.text(), "test-model")
        self.assertEqual(self.dialog.adapter_type_label.text(), "lora")
        self.assertEqual(self.dialog.step_label.text(), "Step: 100/100")
        self.assertEqual(self.dialog.epoch_label.text(), "Epoch: 3/3")
        self.assertEqual(self.dialog.loss_label.text(), "Loss: 1.0000")
        self.assertEqual(self.dialog.time_label.text(), "Time: 60.0s")
        
        # Check that the progress bar was updated
        self.assertEqual(self.dialog.progress_bar.value(), 100)
        
        # Check that the save and export buttons are enabled
        self.assertTrue(self.dialog.save_results_button.isEnabled())
        self.assertTrue(self.dialog.export_report_button.isEnabled())
        
        # Check that the message box was shown
        mock_message_box.information.assert_called_once()
    
    def test_on_start_stop_clicked_start(self):
        """Test clicking the start button."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Mock the _start_training method
        self.dialog._start_training = MagicMock()
        
        # Click the start button
        self.dialog._on_start_stop_clicked()
        
        # Check that _start_training was called
        self.dialog._start_training.assert_called_once()
    
    def test_on_start_stop_clicked_stop(self):
        """Test clicking the stop button."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Set the button text to "Stop Training"
        self.dialog.start_stop_button.setText("Stop Training")
        
        # Mock the _stop_training method
        self.dialog._stop_training = MagicMock()
        
        # Click the stop button
        self.dialog._on_start_stop_clicked()
        
        # Check that _stop_training was called
        self.dialog._stop_training.assert_called_once()
    
    def test_start_training(self):
        """Test starting training."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Mock the _simulate_training method
        self.dialog._simulate_training = MagicMock()
        
        # Start training
        self.dialog._start_training()
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.start_stop_button.text(), "Stop Training")
        self.assertFalse(self.dialog.save_results_button.isEnabled())
        self.assertFalse(self.dialog.export_report_button.isEnabled())
        
        # Check that the progress bar was reset
        self.assertEqual(self.dialog.progress_bar.value(), 0)
        
        # Check that the training monitor was called
        self.training_monitor_mock.start_training.assert_called_once_with(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Check that _simulate_training was called
        self.dialog._simulate_training.assert_called_once()
    
    def test_stop_training(self):
        """Test stopping training."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Start training
        self.dialog.start_stop_button.setText("Stop Training")
        self.dialog.save_results_button.setEnabled(False)
        self.dialog.export_report_button.setEnabled(False)
        
        # Stop training
        self.dialog._stop_training()
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.start_stop_button.text(), "Start Training")
        self.assertTrue(self.dialog.save_results_button.isEnabled())
        self.assertTrue(self.dialog.export_report_button.isEnabled())
        
        # Check that the training monitor was called
        self.training_monitor_mock.end_training.assert_called_once()
    
    @patch('src.ui.training_visualization_dialog.QFileDialog.getExistingDirectory')
    @patch('src.ui.training_visualization_dialog.QMessageBox')
    def test_on_save_results_clicked(self, mock_message_box, mock_get_existing_directory):
        """Test clicking the save results button."""
        # Set up mock to return a directory path
        mock_get_existing_directory.return_value = self.test_dir
        
        # Set up the training monitor mock to return some result files
        self.training_monitor_mock.save_results.return_value = {
            "metrics": os.path.join(self.test_dir, "metrics.json"),
            "report": os.path.join(self.test_dir, "report.html")
        }
        
        # Click the save results button
        self.dialog._on_save_results_clicked()
        
        # Check that the directory dialog was shown
        mock_get_existing_directory.assert_called_once()
        
        # Check that the training monitor was called
        self.training_monitor_mock.save_results.assert_called_once_with(self.test_dir)
        
        # Check that the message box was shown
        mock_message_box.information.assert_called_once()
    
    @patch('src.ui.training_visualization_dialog.QFileDialog.getExistingDirectory')
    @patch('src.ui.training_visualization_dialog.QMessageBox')
    def test_on_export_report_clicked(self, mock_message_box, mock_get_existing_directory):
        """Test clicking the export report button."""
        # Set up mock to return a directory path
        mock_get_existing_directory.return_value = self.test_dir
        
        # Create mock figures
        mock_loss_plot = MagicMock()
        mock_perplexity_plot = MagicMock()
        
        # Set up the training monitor mock to return some visualizations
        self.training_monitor_mock.get_current_visualizations.return_value = {
            "loss_plot": mock_loss_plot,
            "perplexity_plot": mock_perplexity_plot
        }
        
        # Set up the training monitor's visualizer mock to return a report file
        self.training_monitor_mock.visualizer.create_html_report.return_value = os.path.join(self.test_dir, "report.html")
        
        # Click the export report button
        with patch('tempfile.mkdtemp') as mock_mkdtemp, \
             patch('shutil.rmtree') as mock_rmtree:
            
            # Set up mock to return a temporary directory
            mock_mkdtemp.return_value = os.path.join(self.test_dir, "temp")
            
            # Mock the savefig method on the mock figures
            mock_loss_plot.savefig = MagicMock()
            mock_perplexity_plot.savefig = MagicMock()
            
            # Click the export report button
            self.dialog._on_export_report_clicked()
            
            # Check that the directory dialog was shown
            mock_get_existing_directory.assert_called_once()
            
            # Check that the training monitor was called
            self.training_monitor_mock.get_current_visualizations.assert_called_once()
            
            # Check that the figures were saved
            mock_loss_plot.savefig.assert_called_once()
            mock_perplexity_plot.savefig.assert_called_once()
            
            # Check that the report was created
            self.training_monitor_mock.visualizer.create_html_report.assert_called_once()
            
            # Check that the temporary directory was cleaned up
            mock_rmtree.assert_called_once()
            
            # Check that the message box was shown
            mock_message_box.information.assert_called_once()
    
    def test_update_visualizations(self):
        """Test updating visualizations."""
        # Set up the training monitor mock to return some visualizations
        mock_visualizations = {
            "loss_plot": MagicMock(),
            "perplexity_plot": MagicMock(),
            "learning_rate_plot": MagicMock(),
            "bleu_rouge_plot": MagicMock(),
            "progress_plot": MagicMock(),
            "summary_plot": MagicMock()
        }
        self.training_monitor_mock.get_current_visualizations.return_value = mock_visualizations
        
        # Mock the canvas update_figure methods
        self.dialog.loss_canvas.update_figure = MagicMock()
        self.dialog.perplexity_canvas.update_figure = MagicMock()
        self.dialog.learning_rate_canvas.update_figure = MagicMock()
        self.dialog.metrics_canvas.update_figure = MagicMock()
        self.dialog.progress_canvas.update_figure = MagicMock()
        self.dialog.summary_canvas.update_figure = MagicMock()
        
        # Update visualizations
        self.dialog._update_visualizations()
        
        # Check that the training monitor was called
        self.training_monitor_mock.get_current_visualizations.assert_called_once()
        
        # Check that the canvases were updated
        self.dialog.loss_canvas.update_figure.assert_called_once_with(mock_visualizations["loss_plot"])
        self.dialog.perplexity_canvas.update_figure.assert_called_once_with(mock_visualizations["perplexity_plot"])
        self.dialog.learning_rate_canvas.update_figure.assert_called_once_with(mock_visualizations["learning_rate_plot"])
        self.dialog.metrics_canvas.update_figure.assert_called_once_with(mock_visualizations["bleu_rouge_plot"])
        self.dialog.progress_canvas.update_figure.assert_called_once_with(mock_visualizations["progress_plot"])
        self.dialog.summary_canvas.update_figure.assert_called_once_with(mock_visualizations["summary_plot"])
    
    def test_on_training_started(self):
        """Test handling training started."""
        # Call the method
        self.dialog._on_training_started(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100
        )
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.adapter_name_label.text(), "test-adapter")
        self.assertEqual(self.dialog.base_model_label.text(), "test-model")
        self.assertEqual(self.dialog.adapter_type_label.text(), "lora")
        self.assertEqual(self.dialog.step_label.text(), "Step: 0/100")
        self.assertEqual(self.dialog.epoch_label.text(), "Epoch: 0/3")
        self.assertEqual(self.dialog.start_stop_button.text(), "Stop Training")
    
    def test_on_training_ended(self):
        """Test handling training ended."""
        # Call the method
        self.dialog._on_training_ended(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            elapsed_time=60.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.time_label.text(), "Time: 60.0s")
        self.assertEqual(self.dialog.start_stop_button.text(), "Start Training")
        self.assertTrue(self.dialog.save_results_button.isEnabled())
        self.assertTrue(self.dialog.export_report_button.isEnabled())
    
    def test_on_step_completed(self):
        """Test handling step completed."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Call the method
        self.dialog._on_step_completed(
            step=50,
            loss=1.5,
            learning_rate=0.0005,
            perplexity=4.48,
            progress=50.0,
            estimated_time_remaining=30.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.step_label.text(), "Step: 50/100")
        self.assertEqual(self.dialog.loss_label.text(), "Loss: 1.5000")
        self.assertEqual(self.dialog.time_label.text(), "Time Remaining: 30.0s")
        self.assertEqual(self.dialog.progress_bar.value(), 50)
    
    def test_on_epoch_completed(self):
        """Test handling epoch completed."""
        # Set training configuration
        self.dialog.set_training_config(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100,
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Call the method
        self.dialog._on_epoch_completed(
            epoch=2,
            eval_loss=1.4,
            eval_perplexity=4.06,
            bleu_score=0.5,
            rouge_scores={"rouge1": 0.6, "rouge2": 0.4, "rougeL": 0.5},
            progress=66.7,
            estimated_time_remaining=20.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.epoch_label.text(), "Epoch: 2/3")
        self.assertEqual(self.dialog.loss_label.text(), "Loss: 1.4000 (eval)")
    
    def test_on_progress_updated(self):
        """Test handling progress updated."""
        # Call the method
        self.dialog._on_progress_updated(
            progress=75.0,
            estimated_time_remaining=15.0
        )
        
        # Check that the UI was updated
        self.assertEqual(self.dialog.progress_bar.value(), 75)
        self.assertEqual(self.dialog.time_label.text(), "Time Remaining: 15.0s")


class MockTrainingProgressCallback(TrainingProgressCallback):
    """Mock implementation of TrainingProgressCallback for testing."""
    
    def __call__(self, progress_info):
        """Implement the __call__ method required by ProgressCallback."""
        pass


class TestTrainingProgressCallback(unittest.TestCase):
    """Test cases for the TrainingProgressCallback class."""
    
    def setUp(self):
        """Set up the test case."""
        self.callback = MockTrainingProgressCallback()
        
        # Create signal mocks
        self.callback.training_started = MagicMock()
        self.callback.training_ended = MagicMock()
        self.callback.step_completed = MagicMock()
        self.callback.epoch_completed = MagicMock()
        self.callback.progress_updated = MagicMock()
    
    def test_on_training_start(self):
        """Test on_training_start method."""
        # Call the method
        self.callback.on_training_start(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100
        )
        
        # Check that the signal was emitted
        self.callback.training_started.emit.assert_called_once_with(
            "test-adapter", "test-model", "lora", 3, 100
        )
    
    def test_on_training_end(self):
        """Test on_training_end method."""
        # Call the method
        self.callback.on_training_end(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            elapsed_time=60.0
        )
        
        # Check that the signal was emitted
        self.callback.training_ended.emit.assert_called_once_with(
            "test-adapter", "test-model", "lora", 60.0
        )
    
    def test_on_step_complete(self):
        """Test on_step_complete method."""
        # Call the method
        self.callback.on_step_complete(
            step=50,
            loss=1.5,
            learning_rate=0.0005,
            perplexity=4.48,
            progress=50.0,
            estimated_time_remaining=30.0
        )
        
        # Check that the signal was emitted
        self.callback.step_completed.emit.assert_called_once_with(
            50, 1.5, 0.0005, 4.48, 50.0, 30.0
        )
    
    def test_on_epoch_complete(self):
        """Test on_epoch_complete method."""
        # Call the method
        rouge_scores = {"rouge1": 0.6, "rouge2": 0.4, "rougeL": 0.5}
        self.callback.on_epoch_complete(
            epoch=2,
            eval_loss=1.4,
            eval_perplexity=4.06,
            bleu_score=0.5,
            rouge_scores=rouge_scores,
            progress=66.7,
            estimated_time_remaining=20.0
        )
        
        # Check that the signal was emitted
        self.callback.epoch_completed.emit.assert_called_once_with(
            2, 1.4, 4.06, 0.5, rouge_scores, 66.7, 20.0
        )
    
    def test_on_progress_update(self):
        """Test on_progress_update method."""
        # Call the method
        self.callback.on_progress_update(
            progress=75.0,
            estimated_time_remaining=15.0
        )
        
        # Check that the signal was emitted
        self.callback.progress_updated.emit.assert_called_once_with(
            75.0, 15.0
        )


if __name__ == '__main__':
    unittest.main()
