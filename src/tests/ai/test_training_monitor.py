#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the training monitoring and visualization module.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ai.training_monitor import TrainingMetrics, TrainingVisualizer, TrainingMonitor


class TestTrainingMetrics(unittest.TestCase):
    """Test cases for the TrainingMetrics class."""
    
    def setUp(self):
        """Set up the test case."""
        self.metrics = TrainingMetrics()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
    
    def tearDown(self):
        """Tear down the test case."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_start_training(self):
        """Test starting training tracking."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Check that training was started
        self.assertEqual(self.metrics.total_epochs, 3)
        self.assertEqual(self.metrics.total_steps, 100)
        self.assertEqual(self.metrics.adapter_name, "test-adapter")
        self.assertEqual(self.metrics.base_model, "test-model")
        self.assertEqual(self.metrics.adapter_type, "lora")
        self.assertEqual(self.metrics.parameters, {"batch_size": 4, "learning_rate": 0.001})
        self.assertEqual(self.metrics.dataset_info, {"format": "instruction", "samples": 1000})
        self.assertIsNotNone(self.metrics.start_time)
        self.assertIsNone(self.metrics.end_time)
    
    def test_end_training(self):
        """Test ending training tracking."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # End training
        self.metrics.end_training()
        
        # Check that training was ended
        self.assertIsNotNone(self.metrics.end_time)
    
    def test_update_step(self):
        """Test updating step metrics."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update step metrics
        self.metrics.update_step(
            step=1,
            loss=2.0,
            learning_rate=0.001,
            perplexity=7.389
        )
        
        # Check that step metrics were updated
        self.assertEqual(self.metrics.steps_completed, 1)
        self.assertEqual(self.metrics.train_loss, [2.0])
        self.assertEqual(self.metrics.learning_rate, [0.001])
        self.assertEqual(self.metrics.train_perplexity, [7.389])
        self.assertEqual(len(self.metrics.step_times), 1)
    
    def test_update_epoch(self):
        """Test updating epoch metrics."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update epoch metrics
        self.metrics.update_epoch(
            epoch=1,
            eval_loss=1.8,
            eval_perplexity=6.05,
            bleu_score=0.4,
            rouge_scores={"rouge1": 0.5, "rouge2": 0.3, "rougeL": 0.4}
        )
        
        # Check that epoch metrics were updated
        self.assertEqual(self.metrics.epochs_completed, 1)
        self.assertEqual(self.metrics.eval_loss, [1.8])
        self.assertEqual(self.metrics.eval_perplexity, [6.05])
        self.assertEqual(self.metrics.bleu_scores, [0.4])
        self.assertEqual(self.metrics.rouge_scores["rouge1"], [0.5])
        self.assertEqual(self.metrics.rouge_scores["rouge2"], [0.3])
        self.assertEqual(self.metrics.rouge_scores["rougeL"], [0.4])
        self.assertEqual(len(self.metrics.epoch_times), 1)
    
    def test_get_progress(self):
        """Test getting training progress."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update metrics
        self.metrics.update_step(step=50, loss=1.5, learning_rate=0.0005)
        self.metrics.update_epoch(epoch=2, eval_loss=1.4)
        
        # Get progress
        epoch_progress, overall_progress = self.metrics.get_progress()
        
        # Check progress
        self.assertEqual(epoch_progress, (2 / 3) * 100)
        self.assertEqual(overall_progress, 50.0)
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update metrics
        self.metrics.update_step(step=1, loss=2.0, learning_rate=0.001, perplexity=7.389)
        self.metrics.update_step(step=2, loss=1.8, learning_rate=0.0009, perplexity=6.05)
        self.metrics.update_epoch(
            epoch=1,
            eval_loss=1.7,
            eval_perplexity=5.47,
            bleu_score=0.4,
            rouge_scores={"rouge1": 0.5, "rouge2": 0.3, "rougeL": 0.4}
        )
        
        # Get summary
        summary = self.metrics.get_metrics_summary()
        
        # Check summary
        self.assertEqual(summary["adapter_name"], "test-adapter")
        self.assertEqual(summary["base_model"], "test-model")
        self.assertEqual(summary["adapter_type"], "lora")
        self.assertEqual(summary["epochs_completed"], 1)
        self.assertEqual(summary["total_epochs"], 3)
        self.assertEqual(summary["steps_completed"], 2)
        self.assertEqual(summary["total_steps"], 100)
        self.assertEqual(summary["final_train_loss"], 1.8)
        self.assertEqual(summary["min_train_loss"], 1.8)
        self.assertEqual(summary["avg_train_loss"], 1.9)
        self.assertEqual(summary["final_eval_loss"], 1.7)
        self.assertEqual(summary["min_eval_loss"], 1.7)
        self.assertEqual(summary["avg_eval_loss"], 1.7)
        self.assertEqual(summary["final_train_perplexity"], 6.05)
        self.assertEqual(summary["min_train_perplexity"], 6.05)
        self.assertEqual(summary["avg_train_perplexity"], 6.7195)
        self.assertEqual(summary["final_eval_perplexity"], 5.47)
        self.assertEqual(summary["min_eval_perplexity"], 5.47)
        self.assertEqual(summary["avg_eval_perplexity"], 5.47)
        self.assertEqual(summary["final_bleu_score"], 0.4)
        self.assertEqual(summary["max_bleu_score"], 0.4)
        self.assertEqual(summary["avg_bleu_score"], 0.4)
        self.assertEqual(summary["final_rouge1"], 0.5)
        self.assertEqual(summary["max_rouge1"], 0.5)
        self.assertEqual(summary["avg_rouge1"], 0.5)
    
    def test_save_and_load_metrics(self):
        """Test saving and loading metrics."""
        # Start training
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update metrics
        self.metrics.update_step(step=1, loss=2.0, learning_rate=0.001, perplexity=7.389)
        self.metrics.update_epoch(
            epoch=1,
            eval_loss=1.8,
            eval_perplexity=6.05,
            bleu_score=0.4,
            rouge_scores={"rouge1": 0.5, "rouge2": 0.3, "rougeL": 0.4}
        )
        
        # Save metrics
        metrics_file = self.metrics.save_metrics(self.test_dir)
        
        # Load metrics
        loaded_metrics = TrainingMetrics.load_metrics(metrics_file)
        
        # Check loaded metrics
        self.assertEqual(loaded_metrics.adapter_name, "test-adapter")
        self.assertEqual(loaded_metrics.base_model, "test-model")
        self.assertEqual(loaded_metrics.adapter_type, "lora")
        self.assertEqual(loaded_metrics.epochs_completed, 1)
        self.assertEqual(loaded_metrics.total_epochs, 3)
        self.assertEqual(loaded_metrics.steps_completed, 1)
        self.assertEqual(loaded_metrics.total_steps, 100)
        self.assertEqual(loaded_metrics.train_loss, [2.0])
        self.assertEqual(loaded_metrics.train_perplexity, [7.389])
        self.assertEqual(loaded_metrics.eval_loss, [1.8])
        self.assertEqual(loaded_metrics.eval_perplexity, [6.05])
        self.assertEqual(loaded_metrics.learning_rate, [0.001])
        self.assertEqual(loaded_metrics.bleu_scores, [0.4])
        self.assertEqual(loaded_metrics.rouge_scores["rouge1"], [0.5])
        self.assertEqual(loaded_metrics.rouge_scores["rouge2"], [0.3])
        self.assertEqual(loaded_metrics.rouge_scores["rougeL"], [0.4])


class TestTrainingVisualizer(unittest.TestCase):
    """Test cases for the TrainingVisualizer class."""
    
    def setUp(self):
        """Set up the test case."""
        self.visualizer = TrainingVisualizer()
        self.metrics = TrainingMetrics()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
        
        # Set up metrics with some data
        self.metrics.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Add some metrics data
        for step in range(1, 101):
            loss = 2.0 * np.exp(-step / 33) + 0.5
            learning_rate = 0.001 * np.exp(-step / 50)
            perplexity = np.exp(loss)
            
            self.metrics.update_step(
                step=step,
                loss=loss,
                learning_rate=learning_rate,
                perplexity=perplexity
            )
            
            if step % 33 == 0:
                epoch = step // 33
                
                self.metrics.update_epoch(
                    epoch=epoch,
                    eval_loss=loss * 1.1,
                    eval_perplexity=np.exp(loss * 1.1),
                    bleu_score=0.3 + 0.2 * (epoch / 3),
                    rouge_scores={
                        "rouge1": 0.4 + 0.2 * (epoch / 3),
                        "rouge2": 0.3 + 0.2 * (epoch / 3),
                        "rougeL": 0.35 + 0.2 * (epoch / 3)
                    }
                )
    
    def tearDown(self):
        """Tear down the test case."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_create_loss_plot(self):
        """Test creating a loss plot."""
        # Create loss plot
        fig = self.visualizer.create_loss_plot(self.metrics)
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) > 0)
    
    def test_create_perplexity_plot(self):
        """Test creating a perplexity plot."""
        # Create perplexity plot
        fig = self.visualizer.create_perplexity_plot(self.metrics)
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) > 0)
    
    def test_create_learning_rate_plot(self):
        """Test creating a learning rate plot."""
        # Create learning rate plot
        fig = self.visualizer.create_learning_rate_plot(self.metrics)
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) > 0)
    
    def test_create_bleu_rouge_plot(self):
        """Test creating a BLEU and ROUGE plot."""
        # Create BLEU and ROUGE plot
        fig = self.visualizer.create_bleu_rouge_plot(self.metrics)
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) > 0)
    
    def test_create_training_progress_plot(self):
        """Test creating a training progress plot."""
        # Create training progress plot
        fig = self.visualizer.create_training_progress_plot(self.metrics)
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) > 0)
    
    def test_create_metrics_summary_plot(self):
        """Test creating a metrics summary plot."""
        # Create metrics summary plot
        fig = self.visualizer.create_metrics_summary_plot(self.metrics)
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.axes) > 0)
    
    def test_save_visualizations(self):
        """Test saving visualizations."""
        # Save visualizations
        visualization_files = self.visualizer.save_visualizations(self.metrics, self.test_dir)
        
        # Check that visualization files were created
        self.assertTrue("loss_plot" in visualization_files)
        self.assertTrue("perplexity_plot" in visualization_files)
        self.assertTrue("learning_rate_plot" in visualization_files)
        self.assertTrue("bleu_rouge_plot" in visualization_files)
        self.assertTrue("progress_plot" in visualization_files)
        self.assertTrue("summary_plot" in visualization_files)
        
        # Check that files exist
        for file_path in visualization_files.values():
            self.assertTrue(os.path.exists(file_path))
    
    def test_create_html_report(self):
        """Test creating an HTML report."""
        # Save visualizations
        visualization_files = self.visualizer.save_visualizations(self.metrics, self.test_dir)
        
        # Create HTML report
        report_file = self.visualizer.create_html_report(
            self.metrics, visualization_files, self.test_dir
        )
        
        # Check that report file was created
        self.assertTrue(os.path.exists(report_file))
        
        # Check that report file contains expected content
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Training Report - test-adapter", content)
            # Check for base model and adapter type, allowing for whitespace variations
            self.assertTrue("Base Model" in content and "test-model" in content)
            self.assertTrue("Adapter Type" in content and "lora" in content)


class TestTrainingMonitor(unittest.TestCase):
    """Test cases for the TrainingMonitor class."""
    
    def setUp(self):
        """Set up the test case."""
        self.monitor = TrainingMonitor()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
        
        # Create mock callback
        self.mock_callback = MagicMock()
        self.monitor.set_callback(self.mock_callback)
    
    def tearDown(self):
        """Tear down the test case."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_start_training(self):
        """Test starting training."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Check that training was started
        self.assertEqual(self.monitor.metrics.total_epochs, 3)
        self.assertEqual(self.monitor.metrics.total_steps, 100)
        self.assertEqual(self.monitor.metrics.adapter_name, "test-adapter")
        self.assertEqual(self.monitor.metrics.base_model, "test-model")
        self.assertEqual(self.monitor.metrics.adapter_type, "lora")
        
        # Check that callback was called
        self.mock_callback.on_training_start.assert_called_once_with(
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            total_epochs=3,
            total_steps=100
        )
    
    def test_end_training(self):
        """Test ending training."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # End training
        self.monitor.end_training()
        
        # Check that training was ended
        self.assertIsNotNone(self.monitor.metrics.end_time)
        
        # Check that callback was called
        self.mock_callback.on_training_end.assert_called_once()
    
    def test_update_step(self):
        """Test updating step metrics."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update step metrics
        self.monitor.update_step(
            step=1,
            loss=2.0,
            learning_rate=0.001,
            perplexity=7.389
        )
        
        # Check that step metrics were updated
        self.assertEqual(self.monitor.metrics.steps_completed, 1)
        self.assertEqual(self.monitor.metrics.train_loss, [2.0])
        self.assertEqual(self.monitor.metrics.learning_rate, [0.001])
        self.assertEqual(self.monitor.metrics.train_perplexity, [7.389])
        
        # Check that callback was called
        self.mock_callback.on_step_complete.assert_called_once()
    
    def test_update_epoch(self):
        """Test updating epoch metrics."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update epoch metrics
        self.monitor.update_epoch(
            epoch=1,
            eval_loss=1.8,
            eval_perplexity=6.05,
            bleu_score=0.4,
            rouge_scores={"rouge1": 0.5, "rouge2": 0.3, "rougeL": 0.4}
        )
        
        # Check that epoch metrics were updated
        self.assertEqual(self.monitor.metrics.epochs_completed, 1)
        self.assertEqual(self.monitor.metrics.eval_loss, [1.8])
        self.assertEqual(self.monitor.metrics.eval_perplexity, [6.05])
        self.assertEqual(self.monitor.metrics.bleu_scores, [0.4])
        self.assertEqual(self.monitor.metrics.rouge_scores["rouge1"], [0.5])
        
        # Check that callback was called
        self.mock_callback.on_epoch_complete.assert_called_once()
    
    def test_get_current_visualizations(self):
        """Test getting current visualizations."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update metrics
        self.monitor.update_step(step=1, loss=2.0, learning_rate=0.001, perplexity=7.389)
        
        # Get visualizations
        visualizations = self.monitor.get_current_visualizations()
        
        # Check that visualizations were created
        self.assertTrue("loss_plot" in visualizations)
        self.assertTrue("progress_plot" in visualizations)
        self.assertTrue("summary_plot" in visualizations)
    
    def test_save_results(self):
        """Test saving results."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update metrics
        self.monitor.update_step(step=1, loss=2.0, learning_rate=0.001, perplexity=7.389)
        self.monitor.update_epoch(
            epoch=1,
            eval_loss=1.8,
            eval_perplexity=6.05,
            bleu_score=0.4,
            rouge_scores={"rouge1": 0.5, "rouge2": 0.3, "rougeL": 0.4}
        )
        
        # Save results
        result_files = self.monitor.save_results(self.test_dir)
        
        # Check that result files were created
        self.assertTrue("metrics" in result_files)
        self.assertTrue("report" in result_files)
        self.assertTrue("visualization_loss_plot" in result_files)
        
        # Check that files exist
        for file_path in result_files.values():
            self.assertTrue(os.path.exists(file_path))
    
    def test_load_results(self):
        """Test loading results."""
        # Start training
        self.monitor.start_training(
            total_epochs=3,
            total_steps=100,
            adapter_name="test-adapter",
            base_model="test-model",
            adapter_type="lora",
            parameters={"batch_size": 4, "learning_rate": 0.001},
            dataset_info={"format": "instruction", "samples": 1000}
        )
        
        # Update metrics
        self.monitor.update_step(step=1, loss=2.0, learning_rate=0.001, perplexity=7.389)
        self.monitor.update_epoch(
            epoch=1,
            eval_loss=1.8,
            eval_perplexity=6.05,
            bleu_score=0.4,
            rouge_scores={"rouge1": 0.5, "rouge2": 0.3, "rougeL": 0.4}
        )
        
        # Save results
        result_files = self.monitor.save_results(self.test_dir)
        
        # Create a new monitor
        new_monitor = TrainingMonitor()
        
        # Load results
        results = new_monitor.load_results(result_files["metrics"])
        
        # Check that results were loaded
        self.assertEqual(new_monitor.metrics.adapter_name, "test-adapter")
        self.assertEqual(new_monitor.metrics.base_model, "test-model")
        self.assertEqual(new_monitor.metrics.adapter_type, "lora")
        self.assertEqual(new_monitor.metrics.epochs_completed, 1)
        self.assertEqual(new_monitor.metrics.total_epochs, 3)
        self.assertEqual(new_monitor.metrics.steps_completed, 1)
        self.assertEqual(new_monitor.metrics.total_steps, 100)
        
        # Check that visualizations were created
        self.assertTrue("metrics" in results)
        self.assertTrue("visualizations" in results)
        self.assertTrue("summary" in results)
        self.assertTrue("loss_plot" in results["visualizations"])


if __name__ == '__main__':
    unittest.main()
