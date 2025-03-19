#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the AI actions in the main window.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QWidget
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.main_window import MainWindow


class TestMainWindowAIActions(unittest.TestCase):
    """Test cases for the AI actions in the main window."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Mock the backend services
        self.project_manager_mock = MagicMock()
        self.document_manager_mock = MagicMock()
        self.search_service_mock = MagicMock()
        self.statistics_service_mock = MagicMock()
        self.export_service_mock = MagicMock()
        
        # Create QWidget mocks for UI components
        self.binder_view_mock = QWidget()
        self.binder_view_mock.item_selected = MagicMock()  # Add the signal as a mock
        self.editor_view_mock = QWidget()
        self.inspector_view_mock = QWidget()
        self.theme_manager_mock = MagicMock()
        
        # Create main window with mocked services and UI components
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
    
    def tearDown(self):
        """Tear down the test case."""
        self.main_window.close()
    
    def test_ai_menu_exists(self):
        """Test that the AI menu exists."""
        # Find the AI menu
        ai_menu = None
        for menu in self.main_window.menuBar().findChildren(QMenu):
            if menu.title() == "&AI":
                ai_menu = menu
                break
        
        # Check that the AI menu exists
        self.assertIsNotNone(ai_menu, "AI menu not found")
    
    def test_ai_menu_actions(self):
        """Test that the AI menu has the expected actions."""
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
        
        # Check that the menu has the expected number of actions
        # 3 text generation actions + 1 separator + 3 model actions + 1 separator + 1 settings action = 9 actions
        self.assertEqual(len(actions), 9, "AI menu does not have the expected number of actions")
        
        # Check that the menu has the expected actions
        action_texts = [action.text() for action in actions]
        self.assertIn("&Generate Text...", action_texts, "Generate Text action not found")
        self.assertIn("&Character Development...", action_texts, "Character Development action not found")
        self.assertIn("&Plot Development...", action_texts, "Plot Development action not found")
        self.assertIn("Model &Benchmarking...", action_texts, "Model Benchmarking action not found")
        self.assertIn("&Batch Benchmarking...", action_texts, "Batch Benchmarking action not found")
        self.assertIn("Model &Fine-tuning...", action_texts, "Model Fine-tuning action not found")
        self.assertIn("&Settings...", action_texts, "Settings action not found")
    
    @patch('src.ui.benchmark_dialog.BenchmarkDialog')
    def test_model_benchmarking_action(self, mock_benchmark_dialog):
        """Test the model benchmarking action."""
        # Create mock dialog
        mock_dialog = MagicMock()
        mock_benchmark_dialog.return_value = mock_dialog
        
        # Find the model benchmarking action
        model_benchmark_action = None
        for action in self.main_window.findChildren(QAction):
            if action.text() == "Model &Benchmarking...":
                model_benchmark_action = action
                break
        
        # Check that the action exists
        self.assertIsNotNone(model_benchmark_action, "Model Benchmarking action not found")
        
        # Trigger the action
        model_benchmark_action.trigger()
        
        # Check that the dialog was created and shown
        mock_benchmark_dialog.assert_called_once()
        mock_dialog.exec.assert_called_once()
    
    @patch('src.ui.batch_benchmark_dialog.BatchBenchmarkDialog')
    def test_batch_benchmarking_action(self, mock_batch_benchmark_dialog):
        """Test the batch benchmarking action."""
        # Create mock dialog
        mock_dialog = MagicMock()
        mock_batch_benchmark_dialog.return_value = mock_dialog
        
        # Find the batch benchmarking action
        batch_benchmark_action = None
        for action in self.main_window.findChildren(QAction):
            if action.text() == "&Batch Benchmarking...":
                batch_benchmark_action = action
                break
        
        # Check that the action exists
        self.assertIsNotNone(batch_benchmark_action, "Batch Benchmarking action not found")
        
        # Trigger the action
        batch_benchmark_action.trigger()
        
        # Check that the dialog was created and shown
        mock_batch_benchmark_dialog.assert_called_once()
        mock_dialog.exec.assert_called_once()
    
    @patch('src.ui.adapter_config_dialog.AdapterConfigDialog')
    def test_model_finetuning_action(self, mock_adapter_config_dialog):
        """Test the model fine-tuning action."""
        # Create mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True  # Dialog accepted
        mock_adapter_config_dialog.return_value = mock_dialog
        
        # Find the model fine-tuning action
        model_finetuning_action = None
        for action in self.main_window.findChildren(QAction):
            if action.text() == "Model &Fine-tuning...":
                model_finetuning_action = action
                break
        
        # Check that the action exists
        self.assertIsNotNone(model_finetuning_action, "Model Fine-tuning action not found")
        
        # Trigger the action
        model_finetuning_action.trigger()
        
        # Check that the dialog was created and shown
        mock_adapter_config_dialog.assert_called_once()
        mock_dialog.exec.assert_called_once()
        
        # Check that the status bar was updated
        self.assertEqual(self.main_window.status_bar.currentMessage(), "Adapter configuration saved")
    
    @patch('src.ui.adapter_config_dialog.AdapterConfigDialog')
    def test_model_finetuning_action_canceled(self, mock_adapter_config_dialog):
        """Test the model fine-tuning action when the dialog is canceled."""
        # Create mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False  # Dialog rejected
        mock_adapter_config_dialog.return_value = mock_dialog
        
        # Find the model fine-tuning action
        model_finetuning_action = None
        for action in self.main_window.findChildren(QAction):
            if action.text() == "Model &Fine-tuning...":
                model_finetuning_action = action
                break
        
        # Check that the action exists
        self.assertIsNotNone(model_finetuning_action, "Model Fine-tuning action not found")
        
        # Trigger the action
        model_finetuning_action.trigger()
        
        # Check that the dialog was created and shown
        mock_adapter_config_dialog.assert_called_once()
        mock_dialog.exec.assert_called_once()
        
        # Check that the status bar was not updated
        self.assertNotEqual(self.main_window.status_bar.currentMessage(), "Adapter configuration saved")


if __name__ == '__main__':
    unittest.main()
