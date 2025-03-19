#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Batch Benchmark Batches

This module implements batch-related functionality for the batch benchmark dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QListWidget, QListWidgetItem, QProgressBar,
    QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from src.utils.logging_utils import get_logger
from src.ai.batch_benchmarking import (
    BatchBenchmark, BatchStatus, create_batch_benchmark,
    cancel_batch_benchmark
)
from src.ui.batch_benchmark_thread import BatchBenchmarkThread

logger = get_logger(__name__)


class BatchBenchmarkBatches:
    """Mixin class for batch-related functionality in the batch benchmark dialog."""
    
    def _create_batches_tab(self):
        """Create the batches tab."""
        logger.debug("Creating batches tab")
        
        # Create tab widget
        self.batches_tab = QWidget()
        self.tab_widget.addTab(self.batches_tab, "Batches")
        
        # Create layout
        layout = QHBoxLayout(self.batches_tab)
        
        # Create a splitter
        splitter = self._create_splitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create a list widget for batches
        self.batches_list = QListWidget()
        self.batches_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        splitter.addWidget(self.batches_list)
        
        # Create a widget for batch details
        batch_details_widget = QWidget()
        batch_details_layout = QVBoxLayout(batch_details_widget)
        
        # Create a form layout for the batch details
        batch_details_form = QFormLayout()
        
        # Batch name
        self.batch_name_edit = QLineEdit()
        batch_details_form.addRow("Name:", self.batch_name_edit)
        
        # Batch description
        self.batch_description_edit = QLineEdit()
        batch_details_form.addRow("Description:", self.batch_description_edit)
        
        # Batch tags
        self.batch_tags_edit = QLineEdit()
        self.batch_tags_edit.setPlaceholderText("Enter tags separated by commas")
        batch_details_form.addRow("Tags:", self.batch_tags_edit)
        
        # Template selection
        self.batch_template_combo = QComboBox()
        batch_details_form.addRow("Template:", self.batch_template_combo)
        
        # Parallel execution
        self.batch_parallel_check = QCheckBox()
        batch_details_form.addRow("Parallel Execution:", self.batch_parallel_check)
        
        # Max workers
        self.batch_max_workers_spin = QSpinBox()
        self.batch_max_workers_spin.setRange(1, 10)
        self.batch_max_workers_spin.setValue(1)
        self.batch_max_workers_spin.setEnabled(False)
        batch_details_form.addRow("Max Workers:", self.batch_max_workers_spin)
        
        batch_details_layout.addLayout(batch_details_form)
        
        # Add models group
        models_group = QGroupBox("Models")
        models_layout = QVBoxLayout(models_group)
        
        # Add models list
        self.batch_models_list = QListWidget()
        self.batch_models_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        models_layout.addWidget(self.batch_models_list)
        
        batch_details_layout.addWidget(models_group)
        
        # Add batch buttons
        batch_buttons_layout = QHBoxLayout()
        
        self.create_batch_button = QPushButton("Create Batch")
        batch_buttons_layout.addWidget(self.create_batch_button)
        
        self.run_batch_button = QPushButton("Run Batch")
        self.run_batch_button.setEnabled(False)
        batch_buttons_layout.addWidget(self.run_batch_button)
        
        self.cancel_batch_button = QPushButton("Cancel Batch")
        self.cancel_batch_button.setEnabled(False)
        batch_buttons_layout.addWidget(self.cancel_batch_button)
        
        batch_details_layout.addLayout(batch_buttons_layout)
        
        # Add progress bar
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setRange(0, 100)
        self.batch_progress_bar.setValue(0)
        self.batch_progress_bar.setVisible(False)
        batch_details_layout.addWidget(self.batch_progress_bar)
        
        # Add progress label
        self.batch_progress_label = QLabel()
        self.batch_progress_label.setVisible(False)
        batch_details_layout.addWidget(self.batch_progress_label)
        
        # Add the batch details widget to the splitter
        splitter.addWidget(batch_details_widget)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([300, 600])
        
        logger.debug("Batches tab created")
    
    def _connect_batch_signals(self):
        """Connect batch-related signals."""
        # Connect batches tab signals
        self.batches_list.currentItemChanged.connect(self._on_batch_selected)
        self.batches_list.customContextMenuRequested.connect(self._on_batches_list_context_menu)
        self.batch_parallel_check.stateChanged.connect(self._on_batch_parallel_changed)
        self.create_batch_button.clicked.connect(self._on_create_batch)
        self.run_batch_button.clicked.connect(self._on_run_batch)
        self.cancel_batch_button.clicked.connect(self._on_cancel_batch)
    
    def _load_batches(self):
        """Load batch benchmarks."""
        logger.debug("Loading batch benchmarks")
        
        try:
            # Clear the batches list
            self.batches_list.clear()
            
            # Get batch benchmarks
            batches = self._get_batch_benchmarks()
            
            # Add batches to the list
            for batch in batches:
                item = QListWidgetItem(f"{batch.name} ({batch.id}) - {batch.status.name}")
                item.setData(Qt.ItemDataRole.UserRole, batch)
                self.batches_list.addItem(item)
            
            logger.debug(f"Loaded {len(batches)} batch benchmarks")
        except Exception as e:
            logger.error(f"Error loading batch benchmarks: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load batch benchmarks: {e}")
    
    def _on_batch_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handle batch selection changed.
        
        Args:
            current: The current selected item.
            previous: The previously selected item.
        """
        if not current:
            # Clear batch details
            self._clear_batch_details()
            self.run_batch_button.setEnabled(False)
            self.cancel_batch_button.setEnabled(False)
            return
        
        # Get the batch
        batch = current.data(Qt.ItemDataRole.UserRole)
        
        # Show batch details
        self.batch_name_edit.setText(batch.name)
        self.batch_description_edit.setText(batch.description or "")
        self.batch_tags_edit.setText(", ".join(batch.tags))
        
        # Select template
        index = self.batch_template_combo.findData(batch.template_id)
        if index >= 0:
            self.batch_template_combo.setCurrentIndex(index)
        
        # Set parallel execution
        self.batch_parallel_check.setChecked(batch.parallel)
        self.batch_max_workers_spin.setValue(batch.max_workers)
        self.batch_max_workers_spin.setEnabled(batch.parallel)
        
        # Select models
        self.batch_models_list.clearSelection()
        for i in range(self.batch_models_list.count()):
            item = self.batch_models_list.item(i)
            model_id = item.data(Qt.ItemDataRole.UserRole)
            if model_id in batch.model_ids:
                item.setSelected(True)
        
        # Enable run button if the batch is pending
        self.run_batch_button.setEnabled(batch.status == BatchStatus.PENDING)
        
        # Enable cancel button if the batch is running
        self.cancel_batch_button.setEnabled(batch.status == BatchStatus.RUNNING)
    
    def _clear_batch_details(self):
        """Clear batch details."""
        self.batch_name_edit.clear()
        self.batch_description_edit.clear()
        self.batch_tags_edit.clear()
        self.batch_template_combo.setCurrentIndex(0)
        self.batch_parallel_check.setChecked(False)
        self.batch_max_workers_spin.setValue(1)
        self.batch_max_workers_spin.setEnabled(False)
        self.batch_models_list.clearSelection()
    
    def _on_batches_list_context_menu(self, position: QPoint):
        """
        Handle batches list context menu.
        
        Args:
            position: The position of the context menu.
        """
        # Get the selected item
        item = self.batches_list.itemAt(position)
        if not item:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        delete_action = QAction("Delete Batch", self)
        delete_action.triggered.connect(lambda: self._on_delete_batch(item))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(self.batches_list.mapToGlobal(position))
    
    def _on_delete_batch(self, item: QListWidgetItem):
        """
        Handle delete batch action.
        
        Args:
            item: The item to delete.
        """
        # Get the batch
        batch = item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Batch",
            f"Are you sure you want to delete batch '{batch.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove the batch from the list
            row = self.batches_list.row(item)
            self.batches_list.takeItem(row)
            
            # Clear batch details
            self._clear_batch_details()
            self.run_batch_button.setEnabled(False)
            self.cancel_batch_button.setEnabled(False)
            
            # Reload batches
            self._load_batches()
    
    def _on_batch_parallel_changed(self, state: int):
        """
        Handle batch parallel changed.
        
        Args:
            state: The state of the checkbox.
        """
        # Enable/disable max workers
        self.batch_max_workers_spin.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _on_create_batch(self):
        """Handle create batch button clicked."""
        # Get batch details
        name = self.batch_name_edit.text()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a batch name.")
            return
        
        # Get template
        template_id = self.batch_template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Error", "Please select a template.")
            return
        
        # Get models
        model_ids = []
        for item in self.batch_models_list.selectedItems():
            model_id = item.data(Qt.ItemDataRole.UserRole)
            model_ids.append(model_id)
        
        if not model_ids:
            QMessageBox.warning(self, "Error", "Please select at least one model.")
            return
        
        # Get other details
        description = self.batch_description_edit.text()
        tags = [tag.strip() for tag in self.batch_tags_edit.text().split(",") if tag.strip()]
        parallel = self.batch_parallel_check.isChecked()
        max_workers = self.batch_max_workers_spin.value()
        
        try:
            # Create the batch
            batch = create_batch_benchmark(
                name=name,
                model_ids=model_ids,
                template_id=template_id,
                description=description,
                tags=tags,
                parallel=parallel,
                max_workers=max_workers
            )
            
            # Add the batch to the list
            item = QListWidgetItem(f"{batch.name} ({batch.id}) - {batch.status.name}")
            item.setData(Qt.ItemDataRole.UserRole, batch)
            self.batches_list.addItem(item)
            
            # Clear batch details
            self._clear_batch_details()
            
            # Show success message
            QMessageBox.information(self, "Success", f"Batch '{name}' created successfully.")
        
        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create batch: {e}")
    
    def _on_run_batch(self):
        """Handle run batch button clicked."""
        # Get the selected batch
        current_item = self.batches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a batch to run.")
            return
        
        # Get the batch
        batch = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Check if the batch is pending
        if batch.status != BatchStatus.PENDING:
            QMessageBox.warning(self, "Error", f"Batch is not pending (status: {batch.status.name}).")
            return
        
        # Show progress bar
        self.batch_progress_bar.setValue(0)
        self.batch_progress_bar.setVisible(True)
        self.batch_progress_label.setText("Initializing batch benchmark...")
        self.batch_progress_label.setVisible(True)
        
        # Disable run button
        self.run_batch_button.setEnabled(False)
        
        # Enable cancel button
        self.cancel_batch_button.setEnabled(True)
        
        # Create and start batch benchmark thread
        self.batch_thread = BatchBenchmarkThread(batch)
        self.batch_thread.progress_updated.connect(self._on_batch_progress)
        self.batch_thread.benchmark_complete.connect(self._on_batch_complete)
        self.batch_thread.error_occurred.connect(self._on_batch_error)
        self.batch_thread.start()
        
        # Update batch status
        batch.status = BatchStatus.RUNNING
        current_item.setText(f"{batch.name} ({batch.id}) - {batch.status.name}")
        current_item.setData(Qt.ItemDataRole.UserRole, batch)
        
        logger.debug(f"Started batch benchmark: {batch.id}")
    
    def _on_batch_progress(self, progress_info):
        """
        Handle batch progress update.
        
        Args:
            progress_info: The progress information.
        """
        # Update progress bar
        self.batch_progress_bar.setValue(int(progress_info.progress * 100))
        
        # Update progress label
        self.batch_progress_label.setText(progress_info.message)
    
    def _on_batch_complete(self, result):
        """
        Handle batch completion.
        
        Args:
            result: The batch result.
        """
        logger.debug(f"Batch benchmark completed: {result.batch_id}")
        
        # Hide progress bar
        self.batch_progress_bar.setVisible(False)
        self.batch_progress_label.setVisible(False)
        
        # Disable cancel button
        self.cancel_batch_button.setEnabled(False)
        
        # Update batch status
        current_item = self.batches_list.currentItem()
        if current_item:
            batch = current_item.data(Qt.ItemDataRole.UserRole)
            batch.status = BatchStatus.COMPLETED
            batch.completed_at = result.completed_at
            current_item.setText(f"{batch.name} ({batch.id}) - {batch.status.name}")
            current_item.setData(Qt.ItemDataRole.UserRole, batch)
        
        # Reload batches
        self._load_batches()
        
        # Reload results
        self._load_results()
        
        # Show success message
        QMessageBox.information(
            self,
            "Success",
            f"Batch benchmark '{result.name}' completed successfully."
        )
    
    def _on_batch_error(self, error):
        """
        Handle batch error.
        
        Args:
            error: The error message.
        """
        logger.error(f"Batch benchmark error: {error}")
        
        # Hide progress bar
        self.batch_progress_bar.setVisible(False)
        self.batch_progress_label.setVisible(False)
        
        # Disable cancel button
        self.cancel_batch_button.setEnabled(False)
        
        # Update batch status
        current_item = self.batches_list.currentItem()
        if current_item:
            batch = current_item.data(Qt.ItemDataRole.UserRole)
            batch.status = BatchStatus.FAILED
            batch.error = error
            current_item.setText(f"{batch.name} ({batch.id}) - {batch.status.name}")
            current_item.setData(Qt.ItemDataRole.UserRole, batch)
        
        # Reload batches
        self._load_batches()
        
        # Show error message
        QMessageBox.critical(self, "Batch Error", f"Error running batch benchmark: {error}")
    
    def _on_cancel_batch(self):
        """Handle cancel batch button clicked."""
        # Get the selected batch
        current_item = self.batches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a batch to cancel.")
            return
        
        # Get the batch
        batch = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Check if the batch is running
        if batch.status != BatchStatus.RUNNING:
            QMessageBox.warning(self, "Error", f"Batch is not running (status: {batch.status.name}).")
            return
        
        try:
            # Cancel the batch
            cancelled = cancel_batch_benchmark(batch.id)
            
            if cancelled:
                # Hide progress bar
                self.batch_progress_bar.setVisible(False)
                self.batch_progress_label.setVisible(False)
                
                # Disable cancel button
                self.cancel_batch_button.setEnabled(False)
                
                # Update batch status
                batch.status = BatchStatus.CANCELLED
                current_item.setText(f"{batch.name} ({batch.id}) - {batch.status.name}")
                current_item.setData(Qt.ItemDataRole.UserRole, batch)
                
                # Reload batches
                self._load_batches()
                
                # Show success message
                QMessageBox.information(self, "Success", f"Batch '{batch.name}' cancelled successfully.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to cancel batch '{batch.name}'.")
        
        except Exception as e:
            logger.error(f"Error cancelling batch: {e}")
            QMessageBox.critical(self, "Error", f"Failed to cancel batch: {e}")
