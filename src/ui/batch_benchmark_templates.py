#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Batch Benchmark Templates

This module implements template-related functionality for the batch benchmark dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog,
    QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from src.utils.logging_utils import get_logger
from src.ai.batch_benchmarking import (
    BenchmarkTemplate, create_benchmark_template, create_predefined_benchmark_templates
)

logger = get_logger(__name__)


class BatchBenchmarkTemplates:
    """Mixin class for template-related functionality in the batch benchmark dialog."""
    
    def _create_templates_tab(self):
        """Create the templates tab."""
        logger.debug("Creating templates tab")
        
        # Create tab widget
        self.templates_tab = QWidget()
        self.tab_widget.addTab(self.templates_tab, "Templates")
        
        # Create layout
        layout = QHBoxLayout(self.templates_tab)
        
        # Create a splitter
        splitter = self._create_splitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create a list widget for templates
        self.templates_list = QListWidget()
        self.templates_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        splitter.addWidget(self.templates_list)
        
        # Create a widget for template details
        template_details_widget = QWidget()
        template_details_layout = QVBoxLayout(template_details_widget)
        
        # Create a form layout for the template details
        template_details_form = QFormLayout()
        
        # Template name
        self.template_name_edit = QLineEdit()
        template_details_form.addRow("Name:", self.template_name_edit)
        
        # Template description
        self.template_description_edit = QLineEdit()
        template_details_form.addRow("Description:", self.template_description_edit)
        
        # Template tags
        self.template_tags_edit = QLineEdit()
        self.template_tags_edit.setPlaceholderText("Enter tags separated by commas")
        template_details_form.addRow("Tags:", self.template_tags_edit)
        
        # Max tokens
        self.template_max_tokens_spin = QSpinBox()
        self.template_max_tokens_spin.setRange(10, 2000)
        self.template_max_tokens_spin.setValue(100)
        template_details_form.addRow("Max Tokens:", self.template_max_tokens_spin)
        
        # Number of runs
        self.template_num_runs_spin = QSpinBox()
        self.template_num_runs_spin.setRange(1, 10)
        self.template_num_runs_spin.setValue(3)
        template_details_form.addRow("Number of Runs:", self.template_num_runs_spin)
        
        # Temperature
        self.template_temperature_spin = QDoubleSpinBox()
        self.template_temperature_spin.setRange(0.0, 2.0)
        self.template_temperature_spin.setValue(0.7)
        self.template_temperature_spin.setSingleStep(0.1)
        template_details_form.addRow("Temperature:", self.template_temperature_spin)
        
        # Top-p
        self.template_top_p_spin = QDoubleSpinBox()
        self.template_top_p_spin.setRange(0.0, 1.0)
        self.template_top_p_spin.setValue(0.9)
        self.template_top_p_spin.setSingleStep(0.1)
        template_details_form.addRow("Top-p:", self.template_top_p_spin)
        
        # Save token logprobs
        self.template_save_logprobs_check = QCheckBox()
        self.template_save_logprobs_check.setChecked(True)
        template_details_form.addRow("Save Token Logprobs:", self.template_save_logprobs_check)
        
        template_details_layout.addLayout(template_details_form)
        
        # Add prompts group
        prompts_group = QGroupBox("Prompts")
        prompts_layout = QVBoxLayout(prompts_group)
        
        # Add prompts list
        self.prompts_list = QListWidget()
        self.prompts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        prompts_layout.addWidget(self.prompts_list)
        
        # Add prompt buttons
        prompts_buttons_layout = QHBoxLayout()
        
        self.add_prompt_button = QPushButton("Add Prompt")
        prompts_buttons_layout.addWidget(self.add_prompt_button)
        
        self.edit_prompt_button = QPushButton("Edit Prompt")
        prompts_buttons_layout.addWidget(self.edit_prompt_button)
        
        self.remove_prompt_button = QPushButton("Remove Prompt")
        prompts_buttons_layout.addWidget(self.remove_prompt_button)
        
        prompts_layout.addLayout(prompts_buttons_layout)
        
        template_details_layout.addWidget(prompts_group)
        
        # Add reference texts group
        reference_texts_group = QGroupBox("Reference Texts (for BLEU score)")
        reference_texts_layout = QVBoxLayout(reference_texts_group)
        
        # Add reference texts list
        self.reference_texts_list = QListWidget()
        self.reference_texts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        reference_texts_layout.addWidget(self.reference_texts_list)
        
        # Add reference text buttons
        reference_texts_buttons_layout = QHBoxLayout()
        
        self.add_reference_text_button = QPushButton("Add Reference Text")
        reference_texts_buttons_layout.addWidget(self.add_reference_text_button)
        
        self.edit_reference_text_button = QPushButton("Edit Reference Text")
        reference_texts_buttons_layout.addWidget(self.edit_reference_text_button)
        
        self.remove_reference_text_button = QPushButton("Remove Reference Text")
        reference_texts_buttons_layout.addWidget(self.remove_reference_text_button)
        
        reference_texts_layout.addLayout(reference_texts_buttons_layout)
        
        template_details_layout.addWidget(reference_texts_group)
        
        # Add template buttons
        template_buttons_layout = QHBoxLayout()
        
        self.create_template_button = QPushButton("Create Template")
        template_buttons_layout.addWidget(self.create_template_button)
        
        self.update_template_button = QPushButton("Update Template")
        self.update_template_button.setEnabled(False)
        template_buttons_layout.addWidget(self.update_template_button)
        
        self.create_predefined_templates_button = QPushButton("Create Predefined Templates")
        template_buttons_layout.addWidget(self.create_predefined_templates_button)
        
        template_details_layout.addLayout(template_buttons_layout)
        
        # Add the template details widget to the splitter
        splitter.addWidget(template_details_widget)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([300, 600])
        
        logger.debug("Templates tab created")
    
    def _connect_template_signals(self):
        """Connect template-related signals."""
        # Connect templates tab signals
        self.templates_list.currentItemChanged.connect(self._on_template_selected)
        self.templates_list.customContextMenuRequested.connect(self._on_templates_list_context_menu)
        self.add_prompt_button.clicked.connect(self._on_add_prompt)
        self.edit_prompt_button.clicked.connect(self._on_edit_prompt)
        self.remove_prompt_button.clicked.connect(self._on_remove_prompt)
        self.prompts_list.customContextMenuRequested.connect(self._on_prompts_list_context_menu)
        self.add_reference_text_button.clicked.connect(self._on_add_reference_text)
        self.edit_reference_text_button.clicked.connect(self._on_edit_reference_text)
        self.remove_reference_text_button.clicked.connect(self._on_remove_reference_text)
        self.reference_texts_list.customContextMenuRequested.connect(self._on_reference_texts_list_context_menu)
        self.create_template_button.clicked.connect(self._on_create_template)
        self.update_template_button.clicked.connect(self._on_update_template)
        self.create_predefined_templates_button.clicked.connect(self._on_create_predefined_templates)
    
    def _load_templates(self):
        """Load benchmark templates."""
        logger.debug("Loading benchmark templates")
        
        try:
            # Clear the templates list
            self.templates_list.clear()
            
            # Clear the batch template combo
            self.batch_template_combo.clear()
            
            # Get benchmark templates
            templates = self._get_benchmark_templates()
            
            # Add templates to the list
            for template in templates:
                item = QListWidgetItem(f"{template.name} ({template.id})")
                item.setData(Qt.ItemDataRole.UserRole, template)
                self.templates_list.addItem(item)
                
                # Add to batch template combo
                self.batch_template_combo.addItem(f"{template.name} ({template.id})", template.id)
            
            logger.debug(f"Loaded {len(templates)} benchmark templates")
        except Exception as e:
            logger.error(f"Error loading benchmark templates: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load benchmark templates: {e}")
    
    def _on_template_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handle template selection changed.
        
        Args:
            current: The current selected item.
            previous: The previously selected item.
        """
        if not current:
            # Clear template details
            self._clear_template_details()
            self.update_template_button.setEnabled(False)
            return
        
        # Get the template
        template = current.data(Qt.ItemDataRole.UserRole)
        
        # Show template details
        self.template_name_edit.setText(template.name)
        self.template_description_edit.setText(template.description or "")
        self.template_tags_edit.setText(", ".join(template.tags))
        self.template_max_tokens_spin.setValue(template.max_tokens)
        self.template_num_runs_spin.setValue(template.num_runs)
        self.template_temperature_spin.setValue(template.temperature)
        self.template_top_p_spin.setValue(template.top_p)
        self.template_save_logprobs_check.setChecked(template.save_logprobs)
        
        # Show prompts
        self.prompts_list.clear()
        for prompt in template.prompts:
            item = QListWidgetItem(prompt[:50] + "..." if len(prompt) > 50 else prompt)
            item.setData(Qt.ItemDataRole.UserRole, prompt)
            self.prompts_list.addItem(item)
        
        # Show reference texts
        self.reference_texts_list.clear()
        if template.reference_texts:
            for text in template.reference_texts:
                item = QListWidgetItem(text[:50] + "..." if len(text) > 50 else text)
                item.setData(Qt.ItemDataRole.UserRole, text)
                self.reference_texts_list.addItem(item)
        
        # Enable update button
        self.update_template_button.setEnabled(True)
    
    def _clear_template_details(self):
        """Clear template details."""
        self.template_name_edit.clear()
        self.template_description_edit.clear()
        self.template_tags_edit.clear()
        self.template_max_tokens_spin.setValue(100)
        self.template_num_runs_spin.setValue(3)
        self.template_temperature_spin.setValue(0.7)
        self.template_top_p_spin.setValue(0.9)
        self.template_save_logprobs_check.setChecked(True)
        self.prompts_list.clear()
        self.reference_texts_list.clear()
    
    def _on_templates_list_context_menu(self, position: QPoint):
        """
        Handle templates list context menu.
        
        Args:
            position: The position of the context menu.
        """
        # Get the selected item
        item = self.templates_list.itemAt(position)
        if not item:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        delete_action = QAction("Delete Template", self)
        delete_action.triggered.connect(lambda: self._on_delete_template(item))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(self.templates_list.mapToGlobal(position))
    
    def _on_delete_template(self, item: QListWidgetItem):
        """
        Handle delete template action.
        
        Args:
            item: The item to delete.
        """
        # Get the template
        template = item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Template",
            f"Are you sure you want to delete template '{template.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove the template from the list
            row = self.templates_list.row(item)
            self.templates_list.takeItem(row)
            
            # Clear template details
            self._clear_template_details()
            self.update_template_button.setEnabled(False)
            
            # Reload templates
            self._load_templates()
    
    def _on_add_prompt(self):
        """Handle add prompt button clicked."""
        # Show input dialog
        prompt, ok = QInputDialog.getMultiLineText(
            self,
            "Add Prompt",
            "Enter a prompt:",
            ""
        )
        
        if ok and prompt:
            # Add the prompt to the list
            item = QListWidgetItem(prompt[:50] + "..." if len(prompt) > 50 else prompt)
            item.setData(Qt.ItemDataRole.UserRole, prompt)
            self.prompts_list.addItem(item)
    
    def _on_edit_prompt(self):
        """Handle edit prompt button clicked."""
        # Get the selected prompt
        current_item = self.prompts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a prompt to edit.")
            return
        
        # Get the prompt
        prompt = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Show input dialog
        new_prompt, ok = QInputDialog.getMultiLineText(
            self,
            "Edit Prompt",
            "Edit the prompt:",
            prompt
        )
        
        if ok and new_prompt:
            # Update the prompt
            current_item.setText(new_prompt[:50] + "..." if len(new_prompt) > 50 else new_prompt)
            current_item.setData(Qt.ItemDataRole.UserRole, new_prompt)
    
    def _on_remove_prompt(self):
        """Handle remove prompt button clicked."""
        # Get the selected prompt
        current_item = self.prompts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a prompt to remove.")
            return
        
        # Remove the prompt
        row = self.prompts_list.row(current_item)
        self.prompts_list.takeItem(row)
    
    def _on_prompts_list_context_menu(self, position: QPoint):
        """
        Handle prompts list context menu.
        
        Args:
            position: The position of the context menu.
        """
        # Get the selected item
        item = self.prompts_list.itemAt(position)
        if not item:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        edit_action = QAction("Edit Prompt", self)
        edit_action.triggered.connect(self._on_edit_prompt)
        menu.addAction(edit_action)
        
        remove_action = QAction("Remove Prompt", self)
        remove_action.triggered.connect(self._on_remove_prompt)
        menu.addAction(remove_action)
        
        # Show the menu
        menu.exec(self.prompts_list.mapToGlobal(position))
    
    def _on_add_reference_text(self):
        """Handle add reference text button clicked."""
        # Show input dialog
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Add Reference Text",
            "Enter a reference text:",
            ""
        )
        
        if ok and text:
            # Add the reference text to the list
            item = QListWidgetItem(text[:50] + "..." if len(text) > 50 else text)
            item.setData(Qt.ItemDataRole.UserRole, text)
            self.reference_texts_list.addItem(item)
    
    def _on_edit_reference_text(self):
        """Handle edit reference text button clicked."""
        # Get the selected reference text
        current_item = self.reference_texts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a reference text to edit.")
            return
        
        # Get the reference text
        text = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Show input dialog
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Edit Reference Text",
            "Edit the reference text:",
            text
        )
        
        if ok and new_text:
            # Update the reference text
            current_item.setText(new_text[:50] + "..." if len(new_text) > 50 else new_text)
            current_item.setData(Qt.ItemDataRole.UserRole, new_text)
    
    def _on_remove_reference_text(self):
        """Handle remove reference text button clicked."""
        # Get the selected reference text
        current_item = self.reference_texts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a reference text to remove.")
            return
        
        # Remove the reference text
        row = self.reference_texts_list.row(current_item)
        self.reference_texts_list.takeItem(row)
    
    def _on_reference_texts_list_context_menu(self, position: QPoint):
        """
        Handle reference texts list context menu.
        
        Args:
            position: The position of the context menu.
        """
        # Get the selected item
        item = self.reference_texts_list.itemAt(position)
        if not item:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        edit_action = QAction("Edit Reference Text", self)
        edit_action.triggered.connect(self._on_edit_reference_text)
        menu.addAction(edit_action)
        
        remove_action = QAction("Remove Reference Text", self)
        remove_action.triggered.connect(self._on_remove_reference_text)
        menu.addAction(remove_action)
        
        # Show the menu
        menu.exec(self.reference_texts_list.mapToGlobal(position))
    
    def _on_create_template(self):
        """Handle create template button clicked."""
        # Get template details
        name = self.template_name_edit.text()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a template name.")
            return
        
        # Get prompts
        prompts = []
        for i in range(self.prompts_list.count()):
            prompt = self.prompts_list.item(i).data(Qt.ItemDataRole.UserRole)
            prompts.append(prompt)
        
        if not prompts:
            QMessageBox.warning(self, "Error", "Please add at least one prompt.")
            return
        
        # Get reference texts
        reference_texts = []
        for i in range(self.reference_texts_list.count()):
            text = self.reference_texts_list.item(i).data(Qt.ItemDataRole.UserRole)
            reference_texts.append(text)
        
        # Get other details
        description = self.template_description_edit.text()
        tags = [tag.strip() for tag in self.template_tags_edit.text().split(",") if tag.strip()]
        max_tokens = self.template_max_tokens_spin.value()
        num_runs = self.template_num_runs_spin.value()
        temperature = self.template_temperature_spin.value()
        top_p = self.template_top_p_spin.value()
        save_logprobs = self.template_save_logprobs_check.isChecked()
        
        try:
            # Create the template
            template = create_benchmark_template(
                name=name,
                prompts=prompts,
                max_tokens=max_tokens,
                num_runs=num_runs,
                temperature=temperature,
                top_p=top_p,
                tags=tags,
                description=description,
                reference_texts=reference_texts if reference_texts else None,
                save_logprobs=save_logprobs
            )
            
            # Add the template to the list
            item = QListWidgetItem(f"{template.name} ({template.id})")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.templates_list.addItem(item)
            
            # Clear template details
            self._clear_template_details()
            
            # Reload templates
            self._load_templates()
            
            # Show success message
            QMessageBox.information(self, "Success", f"Template '{name}' created successfully.")
        
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create template: {e}")
    
    def _on_update_template(self):
        """Handle update template button clicked."""
        # Get the selected template
        current_item = self.templates_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a template to update.")
            return
        
        # Get the template
        template = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Get template details
        name = self.template_name_edit.text()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a template name.")
            return
        
        # Get prompts
        prompts = []
        for i in range(self.prompts_list.count()):
            prompt = self.prompts_list.item(i).data(Qt.ItemDataRole.UserRole)
            prompts.append(prompt)
        
        if not prompts:
            QMessageBox.warning(self, "Error", "Please add at least one prompt.")
            return
        
        # Get reference texts
        reference_texts = []
        for i in range(self.reference_texts_list.count()):
            text = self.reference_texts_list.item(i).data(Qt.ItemDataRole.UserRole)
            reference_texts.append(text)
        
        # Get other details
        description = self.template_description_edit.text()
        tags = [tag.strip() for tag in self.template_tags_edit.text().split(",") if tag.strip()]
        max_tokens = self.template_max_tokens_spin.value()
        num_runs = self.template_num_runs_spin.value()
        temperature = self.template_temperature_spin.value()
        top_p = self.template_top_p_spin.value()
        save_logprobs = self.template_save_logprobs_check.isChecked()
        
        try:
            # Update the template
            template.name = name
            template.description = description
            template.tags = tags
            template.max_tokens = max_tokens
            template.num_runs = num_runs
            template.temperature = temperature
            template.top_p = top_p
            template.prompts = prompts
            template.reference_texts = reference_texts if reference_texts else None
            template.save_logprobs = save_logprobs
            
            # Update the template in the list
            current_item.setText(f"{template.name} ({template.id})")
            current_item.setData(Qt.ItemDataRole.UserRole, template)
            
            # Reload templates
            self._load_templates()
            
            # Show success message
            QMessageBox.information(self, "Success", f"Template '{name}' updated successfully.")
        
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update template: {e}")
    
    def _on_create_predefined_templates(self):
        """Handle create predefined templates button clicked."""
        # Confirm creation
        reply = QMessageBox.question(
            self,
            "Create Predefined Templates",
            "Are you sure you want to create predefined templates?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Create predefined templates
                template_ids = create_predefined_benchmark_templates()
                
                # Reload templates
                self._load_templates()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    f"Created {len(template_ids)} predefined templates successfully."
                )
            
            except Exception as e:
                logger.error(f"Error creating predefined templates: {e}")
                QMessageBox.critical(self, "Error", f"Failed to create predefined templates: {e}")
