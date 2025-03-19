#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the benchmark dialog UI component.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QDialogButtonBox
from PyQt6.QtCore import Qt

from src.ui.benchmark_dialog import BenchmarkDialog
from src.ui.main_window import MainWindow
from src.ai.model_benchmarking import ModelBenchmark, BenchmarkResult
from src.ai.model_registry import ModelRegistry, ModelInfo, ModelType, ModelSource

# Initialize QApplication for tests
app = QApplication.instance() or QApplication(sys.argv)


class TestBenchmarkDialog(unittest.TestCase):
    """Tests for the benchmark dialog."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model registry
        self.mock_registry = MagicMock(spec=ModelRegistry)
        self.mock_registry.get_all_models.return_value = [
            ModelInfo(
                id="model1",
                name="Test Model 1",
                version="1.0",
                model_type=ModelType.LLAMA,
                source=ModelSource.LOCAL,
                path="/path/to/model1",
                description="Test model 1 description"
            ),
            ModelInfo(
                id="model2",
                name="Test Model 2",
                version="1.0",
                model_type=ModelType.LLAMA,
                source=ModelSource.LOCAL,
                path="/path/to/model2",
                description="Test model 2 description"
            )
        ]
        
        # Patch the ModelRegistry.get_instance method
        self.registry_patcher = patch('src.ai.model_registry.ModelRegistry.get_instance')
        self.mock_get_instance = self.registry_patcher.start()
        self.mock_get_instance.return_value = self.mock_registry
        
        # Create the dialog
        self.dialog = BenchmarkDialog()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Close the dialog
        self.dialog.close()
        
        # Stop the patcher
        self.registry_patcher.stop()
    
    def test_dialog_initialization(self):
        """Test that the dialog initializes correctly."""
        # Check that the dialog has the correct title
        self.assertEqual(self.dialog.windowTitle(), "Model Benchmarking")
        
        # Check that the dialog has the correct minimum size
        self.assertEqual(self.dialog.minimumSize().width(), 800)
        self.assertEqual(self.dialog.minimumSize().height(), 600)
        
        # Check that the dialog has the correct number of tabs
        self.assertEqual(self.dialog.tab_widget.count(), 4)
        
        # Check that the tabs have the correct titles
        self.assertEqual(self.dialog.tab_widget.tabText(0), "Run Benchmark")
        self.assertEqual(self.dialog.tab_widget.tabText(1), "Results")
        self.assertEqual(self.dialog.tab_widget.tabText(2), "Comparison")
        self.assertEqual(self.dialog.tab_widget.tabText(3), "Reports")
        
        # Check that the dialog has a close button
        self.assertIsNotNone(self.dialog.button_box.button(QDialogButtonBox.StandardButton.Close))
    
    def test_model_loading(self):
        """Test that models are loaded correctly."""
        # Check that the model registry was called
        self.mock_registry.get_all_models.assert_called_once()
        
        # Check that the models were added to the combo box
        self.assertEqual(self.dialog.model_combo.count(), 2)
        
        # Check that the models were added to the report model combo box
        self.assertEqual(self.dialog.report_model_combo.count(), 3)  # All Models + 2 models
        
        # Check that the models were added to the comparison models list
        self.assertEqual(self.dialog.comparison_models_list.count(), 2)
    
    @patch('src.ai.model_benchmarking.run_benchmark')
    def test_run_benchmark(self, mock_run_benchmark):
        """Test running a benchmark."""
        # Create a mock benchmark result
        mock_result = BenchmarkResult(
            benchmark_id="benchmark_123",
            model_id="model1",
            model_name="Test Model 1",
            model_type="LLAMA",
            prompt="Test prompt",
            max_tokens=100,
            num_runs=3,
            temperature=0.7,
            top_p=0.9,
            load_time_seconds=0.5,
            generation_times_seconds=[1.0, 1.1, 0.9],
            tokens_generated=[100, 100, 100],
            avg_generation_time=1.0,
            avg_tokens_per_second=100.67,
            peak_memory_mb=500.0,
            generated_texts=["Generated text 1", "Generated text 2", "Generated text 3"],
            timestamp="2025-03-12T12:00:00",
            tags=["test"],
            token_logprobs=[-1.5, -1.6, -1.7],
            reference_text="Reference text for BLEU score calculation"
        )
        
        # Set up the mock to return the result
        mock_run_benchmark.return_value = mock_result
        
        # Set up the dialog
        self.dialog.model_combo.setCurrentIndex(0)
        self.dialog.prompt_edit.setText("Test prompt")
        self.dialog.reference_text_edit.setText("Reference text for BLEU score calculation")
        self.dialog.max_tokens_spin.setValue(100)
        self.dialog.num_runs_spin.setValue(3)
        self.dialog.temperature_spin.setValue(0.7)
        self.dialog.top_p_spin.setValue(0.9)
        self.dialog.save_logprobs_check.setChecked(True)
        self.dialog.tags_edit.setText("test")
        self.dialog.description_edit.setText("Test benchmark")
        
        # Run the benchmark
        with patch('src.ui.benchmark_dialog.BenchmarkThread') as mock_benchmark_thread:
            # Create a mock thread instance
            mock_thread_instance = MagicMock()
            mock_benchmark_thread.return_value = mock_thread_instance
            
            # Call the method
            self.dialog._on_run_benchmark()
            
            # Check that the benchmark thread was created and started
            mock_benchmark_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            
            # Simulate benchmark completion
            self.dialog._on_benchmark_complete(mock_result)
            
            # Check that the result was displayed
            self.assertEqual(self.dialog.result_model_label.text(), "Test Model 1 (model1)")
            self.assertEqual(self.dialog.result_load_time_label.text(), "0.50 seconds")
            self.assertEqual(self.dialog.result_generation_time_label.text(), "1.00 seconds")
            self.assertEqual(self.dialog.result_tokens_per_second_label.text(), "100.67")
            self.assertEqual(self.dialog.result_memory_label.text(), "500.00 MB")
            self.assertEqual(self.dialog.result_text_edit.toPlainText(), "Generated text 1")
            
            # Check that the result group exists
            self.assertIsNotNone(self.dialog.result_group)
    
    @patch('src.ui.benchmark_dialog.BenchmarkDialog._visualize_result_history')
    def test_visualize_result_history(self, mock_visualize_result_history):
        """Test visualizing a result history."""
        # Create a mock result
        mock_result = MagicMock()
        mock_result.model_id = "model1"
        mock_result.model_name = "Test Model 1"
        
        # Create a mock list item
        mock_item = MagicMock()
        mock_item.data.return_value = mock_result
        
        # Add the item to the results list
        self.dialog.results_list.addItem(mock_item)
        self.dialog.results_list.setCurrentItem(mock_item)
        
        # Set the metric
        self.dialog.result_metric_combo.setCurrentText("Tokens per Second")
        
        # Click the visualize history button
        self.dialog.visualize_history_button.click()
        
        # Check that the visualize_result_history method was called
        mock_visualize_result_history.assert_called_once()
    
    @patch('src.ui.benchmark_dialog.BenchmarkDialog._visualize_result_correlation')
    def test_visualize_result_correlation(self, mock_visualize_result_correlation):
        """Test visualizing a result correlation."""
        # Create a mock result
        mock_result = MagicMock()
        mock_result.model_id = "model1"
        mock_result.model_name = "Test Model 1"
        
        # Create a mock list item
        mock_item = MagicMock()
        mock_item.data.return_value = mock_result
        
        # Add the item to the results list
        self.dialog.results_list.addItem(mock_item)
        self.dialog.results_list.setCurrentItem(mock_item)
        
        # Set the metric
        self.dialog.result_metric_combo.setCurrentText("Perplexity")
        
        # Click the visualize correlation button
        self.dialog.visualize_correlation_button.click()
        
        # Check that the visualize_result_correlation method was called
        mock_visualize_result_correlation.assert_called_once()
    
    @patch('src.ui.benchmark_dialog.BenchmarkDialog._visualize_comparison_bar')
    def test_visualize_comparison_bar(self, mock_visualize_comparison_bar):
        """Test visualizing a comparison bar chart."""
        # Set up the dialog with comparison results
        self.dialog.comparison_results = {
            "model1": MagicMock(),
            "model2": MagicMock()
        }
        
        # Set the metric
        self.dialog.comparison_metric_combo.setCurrentText("Tokens per Second")
        
        # Click the visualize bar chart button
        self.dialog.visualize_comparison_bar_button.click()
        
        # Check that the visualize_comparison_bar method was called
        mock_visualize_comparison_bar.assert_called_once()
    
    @patch('src.ui.benchmark_dialog.BenchmarkDialog._visualize_comparison_radar')
    def test_visualize_comparison_radar(self, mock_visualize_comparison_radar):
        """Test visualizing a comparison radar chart."""
        # Set up the dialog with comparison results
        self.dialog.comparison_results = {
            "model1": MagicMock(),
            "model2": MagicMock()
        }
        
        # Click the visualize radar chart button
        self.dialog.visualize_comparison_radar_button.click()
        
        # Check that the visualize_comparison_radar method was called
        mock_visualize_comparison_radar.assert_called_once()
    
    @patch('src.ui.benchmark_dialog.check_visualization_dependencies')
    @patch('src.ui.benchmark_dialog.plot_benchmark_history')
    @patch('os.startfile')
    def test_visualize_result_history_implementation(self, mock_startfile, mock_plot_history, mock_check_deps):
        """Test the implementation of visualize_result_history."""
        # Set up mocks
        mock_check_deps.return_value = True
        mock_fig = MagicMock()
        mock_plot_history.return_value = mock_fig
        
        # Create a mock result
        mock_result = MagicMock()
        mock_result.model_id = "model1"
        mock_result.model_name = "Test Model 1"
        
        # Create a mock list item
        mock_item = MagicMock()
        mock_item.data.return_value = mock_result
        
        # Add the item to the results list
        self.dialog.results_list.addItem(mock_item)
        self.dialog.results_list.setCurrentItem(mock_item)
        
        # Set the metric and interactive checkbox
        self.dialog.result_metric_combo.setCurrentText("Tokens per Second")
        self.dialog.result_interactive_check.setChecked(False)
        
        # Mock get_benchmark_results
        with patch('src.ui.benchmark_dialog.get_benchmark_results') as mock_get_results:
            mock_get_results.return_value = [mock_result]
            
            # Call the method directly
            self.dialog._visualize_result_history()
            
            # Check that the dependencies were checked
            mock_check_deps.assert_called_once()
            
            # Check that get_benchmark_results was called
            mock_get_results.assert_called_once_with(mock_result.model_id)
            
            # Check that plot_benchmark_history was called
            mock_plot_history.assert_called_once()
            
            # Check that os.startfile was called
            mock_startfile.assert_called_once()
    
    @patch('src.ui.benchmark_dialog.check_visualization_dependencies')
    @patch('src.ui.benchmark_dialog.plot_model_comparison')
    @patch('src.ui.benchmark_dialog.export_visualization')
    def test_visualize_comparison_bar_implementation(self, mock_export, mock_plot_comparison, mock_check_deps):
        """Test the implementation of visualize_comparison_bar."""
        # Set up mocks
        mock_check_deps.return_value = True
        mock_fig = MagicMock()
        mock_plot_comparison.return_value = mock_fig
        
        # Set up the dialog with comparison results
        self.dialog.comparison_results = {
            "model1": MagicMock(),
            "model2": MagicMock()
        }
        
        # Set the metric and interactive checkbox
        self.dialog.comparison_metric_combo.setCurrentText("Tokens per Second")
        self.dialog.comparison_interactive_check.setChecked(False)
        
        # Call the method directly
        self.dialog._visualize_comparison_bar()
        
        # Check that the dependencies were checked
        mock_check_deps.assert_called_once()
        
        # Check that plot_model_comparison was called
        mock_plot_comparison.assert_called_once()
        
        # Check that export_visualization was called
        mock_export.assert_called_once()


class TestMainWindowBenchmarkIntegration(unittest.TestCase):
    """Tests for the integration of the benchmark dialog with the main window."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model registry
        self.mock_registry = MagicMock(spec=ModelRegistry)
        self.mock_registry.get_all_models.return_value = [
            ModelInfo(
                id="model1",
                name="Test Model 1",
                version="1.0",
                model_type=ModelType.LLAMA,
                source=ModelSource.LOCAL,
                path="/path/to/model1",
                description="Test model 1 description"
            )
        ]
        
        # Patch the ModelRegistry.get_instance method
        self.registry_patcher = patch('src.ai.model_registry.ModelRegistry.get_instance')
        self.mock_get_instance = self.registry_patcher.start()
        self.mock_get_instance.return_value = self.mock_registry
        
        # Create the main window
        with patch('src.ui.main_window.QApplication'):
            self.main_window = MainWindow()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Close the main window
        self.main_window.close()
        
        # Stop the patcher
        self.registry_patcher.stop()
    
    @patch('src.ui.benchmark_dialog.BenchmarkDialog')
    def test_on_model_benchmarking(self, mock_benchmark_dialog):
        """Test the _on_model_benchmarking method."""
        # Create a mock dialog instance
        mock_dialog_instance = MagicMock()
        mock_benchmark_dialog.return_value = mock_dialog_instance
        
        # Call the method
        self.main_window._on_model_benchmarking()
        
        # Check that the dialog was created
        mock_benchmark_dialog.assert_called_once_with(self.main_window)
        
        # Check that the dialog was shown
        mock_dialog_instance.exec.assert_called_once()
        
        # Check that the status bar was updated
        self.assertEqual(self.main_window.status_bar.currentMessage(), "Model benchmarking completed")


if __name__ == '__main__':
    unittest.main()
