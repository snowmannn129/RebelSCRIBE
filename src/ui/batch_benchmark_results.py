#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Batch Benchmark Results

This module implements results-related functionality for the batch benchmark dialog.
"""

import os
import webbrowser
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from src.utils.logging_utils import get_logger
from src.ai.batch_benchmarking import (
    BatchResult, get_batch_results, get_batch_result, export_batch_results
)

logger = get_logger(__name__)


class BatchBenchmarkResults:
    """Mixin class for results-related functionality in the batch benchmark dialog."""
    
    def _create_results_tab(self):
        """Create the results tab."""
        logger.debug("Creating results tab")
        
        # Create tab widget
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Create layout
        layout = QHBoxLayout(self.results_tab)
        
        # Create a splitter
        splitter = self._create_splitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create a list widget for results
        self.results_list = QListWidget()
        self.results_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        splitter.addWidget(self.results_list)
        
        # Create a widget for result details
        result_details_widget = QWidget()
        result_details_layout = QVBoxLayout(result_details_widget)
        
        # Create a form layout for the result details
        result_details_form = QFormLayout()
        
        self.result_name_label = QLabel()
        result_details_form.addRow("Name:", self.result_name_label)
        
        self.result_template_label = QLabel()
        result_details_form.addRow("Template:", self.result_template_label)
        
        self.result_models_label = QLabel()
        result_details_form.addRow("Models:", self.result_models_label)
        
        self.result_started_label = QLabel()
        result_details_form.addRow("Started:", self.result_started_label)
        
        self.result_completed_label = QLabel()
        result_details_form.addRow("Completed:", self.result_completed_label)
        
        self.result_duration_label = QLabel()
        result_details_form.addRow("Duration:", self.result_duration_label)
        
        result_details_layout.addLayout(result_details_form)
        
        # Add model results group
        model_results_group = QGroupBox("Model Results")
        model_results_layout = QVBoxLayout(model_results_group)
        
        # Add model results list
        self.model_results_list = QListWidget()
        model_results_layout.addWidget(self.model_results_list)
        
        result_details_layout.addWidget(model_results_group)
        
        # Add export buttons
        export_buttons_layout = QHBoxLayout()
        
        self.export_html_button = QPushButton("Export HTML")
        self.export_html_button.setEnabled(False)
        export_buttons_layout.addWidget(self.export_html_button)
        
        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.setEnabled(False)
        export_buttons_layout.addWidget(self.export_pdf_button)
        
        self.export_pptx_button = QPushButton("Export PowerPoint")
        self.export_pptx_button.setEnabled(False)
        export_buttons_layout.addWidget(self.export_pptx_button)
        
        result_details_layout.addLayout(export_buttons_layout)
        
        # Add the result details widget to the splitter
        splitter.addWidget(result_details_widget)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([300, 600])
        
        # Add refresh button
        self.refresh_results_button = QPushButton("Refresh Results")
        layout.addWidget(self.refresh_results_button, 0, Qt.AlignmentFlag.AlignBottom)
        
        logger.debug("Results tab created")
    
    def _connect_result_signals(self):
        """Connect result-related signals."""
        # Connect results tab signals
        self.results_list.currentItemChanged.connect(self._on_result_selected)
        self.results_list.customContextMenuRequested.connect(self._on_results_list_context_menu)
        self.model_results_list.itemClicked.connect(self._on_model_result_clicked)
        self.export_html_button.clicked.connect(lambda: self._on_export_result("html"))
        self.export_pdf_button.clicked.connect(lambda: self._on_export_result("pdf"))
        self.export_pptx_button.clicked.connect(lambda: self._on_export_result("pptx"))
        self.refresh_results_button.clicked.connect(self._load_results)
    
    def _load_results(self):
        """Load batch results."""
        logger.debug("Loading batch results")
        
        try:
            # Clear the results list
            self.results_list.clear()
            
            # Get batch results
            results = self._get_batch_results()
            
            # Add results to the list
            for result in results:
                item = QListWidgetItem(f"{result.name} ({result.batch_id})")
                item.setData(Qt.ItemDataRole.UserRole, result)
                self.results_list.addItem(item)
            
            logger.debug(f"Loaded {len(results)} batch results")
        except Exception as e:
            logger.error(f"Error loading batch results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load batch results: {e}")
    
    def _on_result_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handle result selection changed.
        
        Args:
            current: The current selected item.
            previous: The previously selected item.
        """
        if not current:
            # Clear result details
            self._clear_result_details()
            self.export_html_button.setEnabled(False)
            self.export_pdf_button.setEnabled(False)
            self.export_pptx_button.setEnabled(False)
            return
        
        # Get the result
        result = current.data(Qt.ItemDataRole.UserRole)
        
        # Show result details
        self.result_name_label.setText(result.name)
        self.result_template_label.setText(result.template_id)
        self.result_models_label.setText(", ".join(result.model_ids))
        self.result_started_label.setText(result.started_at)
        self.result_completed_label.setText(result.completed_at)
        self.result_duration_label.setText(f"{result.duration_seconds:.2f} seconds")
        
        # Show model results
        self.model_results_list.clear()
        for model_id, results in result.benchmark_results.items():
            item = QListWidgetItem(f"{model_id} ({len(results)} results)")
            item.setData(Qt.ItemDataRole.UserRole, (model_id, results))
            self.model_results_list.addItem(item)
        
        # Enable export buttons
        self.export_html_button.setEnabled(True)
        self.export_pdf_button.setEnabled(True)
        self.export_pptx_button.setEnabled(True)
    
    def _clear_result_details(self):
        """Clear result details."""
        self.result_name_label.clear()
        self.result_template_label.clear()
        self.result_models_label.clear()
        self.result_started_label.clear()
        self.result_completed_label.clear()
        self.result_duration_label.clear()
        self.model_results_list.clear()
    
    def _on_results_list_context_menu(self, position: QPoint):
        """
        Handle results list context menu.
        
        Args:
            position: The position of the context menu.
        """
        # Get the selected item
        item = self.results_list.itemAt(position)
        if not item:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        delete_action = QAction("Delete Result", self)
        delete_action.triggered.connect(lambda: self._on_delete_result(item))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(self.results_list.mapToGlobal(position))
    
    def _on_delete_result(self, item: QListWidgetItem):
        """
        Handle delete result action.
        
        Args:
            item: The item to delete.
        """
        # Get the result
        result = item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Result",
            f"Are you sure you want to delete result '{result.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove the result from the list
            row = self.results_list.row(item)
            self.results_list.takeItem(row)
            
            # Clear result details
            self._clear_result_details()
            self.export_html_button.setEnabled(False)
            self.export_pdf_button.setEnabled(False)
            self.export_pptx_button.setEnabled(False)
            
            # Reload results
            self._load_results()
    
    def _on_model_result_clicked(self, item: QListWidgetItem):
        """
        Handle model result clicked.
        
        Args:
            item: The clicked item.
        """
        # Get the model results
        model_id, results = item.data(Qt.ItemDataRole.UserRole)
        
        # Show model results
        model_results_text = f"Model: {model_id}\n\n"
        
        for i, result in enumerate(results):
            model_results_text += f"Result {i + 1}:\n"
            model_results_text += f"Prompt: {result.prompt}\n"
            model_results_text += f"Load Time: {result.load_time_seconds:.2f} seconds\n"
            model_results_text += f"Generation Time: {result.avg_generation_time:.2f} seconds\n"
            model_results_text += f"Tokens per Second: {result.avg_tokens_per_second:.2f}\n"
            model_results_text += f"Memory Usage: {result.peak_memory_mb:.2f} MB\n"
            
            if result.generated_texts:
                model_results_text += f"Generated Text: {result.generated_texts[0]}\n"
            
            model_results_text += "\n"
        
        # Show the model results in a message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Model Results: {model_id}")
        msg_box.setText(model_results_text)
        msg_box.setDetailedText(model_results_text)
        msg_box.exec()
    
    def _on_export_result(self, format: str):
        """
        Handle export result button clicked.
        
        Args:
            format: The export format.
        """
        # Get the selected result
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a result to export.")
            return
        
        # Get the result
        result = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Get export file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Result as {format.upper()}",
            f"{result.name}.{format}",
            f"{format.upper()} Files (*.{format})"
        )
        
        if not file_path:
            return
        
        try:
            # Show progress dialog
            progress_dialog = QMessageBox(self)
            progress_dialog.setWindowTitle("Exporting Result")
            progress_dialog.setText(f"Exporting result to {format.upper()}...")
            progress_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
            progress_dialog.show()
            
            # Export the result
            export_batch_results(result.batch_id, file_path, format)
            
            # Close progress dialog
            progress_dialog.close()
            
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Result exported successfully to {file_path}"
            )
            
            # Open the exported file
            if format == "html":
                webbrowser.open(f"file://{os.path.abspath(file_path)}")
        
        except Exception as e:
            logger.error(f"Error exporting result: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export result: {e}")
