#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Dialog for RebelSCRIBE.

This module provides a dialog for exporting projects to various formats.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QCheckBox, QLineEdit, QPushButton, QFileDialog, QGroupBox,
    QFormLayout, QSpinBox, QDoubleSpinBox, QTabWidget, QWidget,
    QMessageBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings

from src.backend.services.export_service import ExportService
from src.backend.models.project import Project
from src.backend.models.document import Document

logger = logging.getLogger(__name__)

class ExportDialog(QDialog):
    """
    Dialog for exporting projects to various formats.
    
    This dialog allows the user to export a project or document to various formats
    with customizable export settings.
    """
    
    def __init__(self, parent=None, project_manager=None, document_manager=None):
        """
        Initialize the ExportDialog.
        
        Args:
            parent: The parent widget.
            project_manager: The ProjectManager instance.
            document_manager: The DocumentManager instance.
        """
        super().__init__(parent)
        
        self.project_manager = project_manager
        self.document_manager = document_manager
        self.export_service = ExportService(project_manager, document_manager)
        
        self.current_project = None
        self.current_document = None
        self.export_mode = "project"  # "project" or "document"
        
        self.setWindowTitle("Export")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Export mode selection
        mode_group = QGroupBox("Export Mode")
        mode_layout = QHBoxLayout()
        
        self.project_radio = QRadioButton("Export Project")
        self.document_radio = QRadioButton("Export Current Document")
        
        mode_group_buttons = QButtonGroup(self)
        mode_group_buttons.addButton(self.project_radio)
        mode_group_buttons.addButton(self.document_radio)
        
        self.project_radio.setChecked(True)
        self.project_radio.toggled.connect(self._on_mode_changed)
        
        mode_layout.addWidget(self.project_radio)
        mode_layout.addWidget(self.document_radio)
        mode_group.setLayout(mode_layout)
        
        main_layout.addWidget(mode_group)
        
        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QFormLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("Microsoft Word (DOCX)", "docx")
        self.format_combo.addItem("PDF Document", "pdf")
        self.format_combo.addItem("Markdown", "md")
        self.format_combo.addItem("HTML", "html")
        self.format_combo.addItem("EPUB E-book", "epub")
        self.format_combo.addItem("Plain Text", "txt")
        
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        
        format_layout.addRow("Format:", self.format_combo)
        format_group.setLayout(format_layout)
        
        main_layout.addWidget(format_group)
        
        # Settings tabs
        self.settings_tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.title_page_check = QCheckBox("Include title page")
        self.title_page_check.setChecked(True)
        
        self.toc_check = QCheckBox("Include table of contents")
        self.toc_check.setChecked(True)
        
        self.page_numbers_check = QCheckBox("Include page numbers")
        self.page_numbers_check.setChecked(True)
        
        self.synopsis_check = QCheckBox("Include synopses")
        self.synopsis_check.setChecked(False)
        
        self.notes_check = QCheckBox("Include notes")
        self.notes_check.setChecked(False)
        
        self.metadata_check = QCheckBox("Include metadata")
        self.metadata_check.setChecked(False)
        
        general_layout.addRow(self.title_page_check)
        general_layout.addRow(self.toc_check)
        general_layout.addRow(self.page_numbers_check)
        general_layout.addRow(self.synopsis_check)
        general_layout.addRow(self.notes_check)
        general_layout.addRow(self.metadata_check)
        
        # Formatting settings tab
        formatting_tab = QWidget()
        formatting_layout = QFormLayout(formatting_tab)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Times New Roman", "Arial", "Calibri", "Courier New", 
            "Georgia", "Verdana", "Helvetica"
        ])
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        
        self.line_spacing_spin = QDoubleSpinBox()
        self.line_spacing_spin.setRange(1.0, 3.0)
        self.line_spacing_spin.setSingleStep(0.1)
        self.line_spacing_spin.setValue(1.5)
        
        self.paragraph_spacing_spin = QSpinBox()
        self.paragraph_spacing_spin.setRange(0, 36)
        self.paragraph_spacing_spin.setValue(12)
        
        formatting_layout.addRow("Font:", self.font_combo)
        formatting_layout.addRow("Font Size:", self.font_size_spin)
        formatting_layout.addRow("Line Spacing:", self.line_spacing_spin)
        formatting_layout.addRow("Paragraph Spacing:", self.paragraph_spacing_spin)
        
        # Page settings tab
        page_tab = QWidget()
        page_layout = QFormLayout(page_tab)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["Letter", "A4", "Legal"])
        
        self.margin_top_spin = QDoubleSpinBox()
        self.margin_top_spin.setRange(0.5, 3.0)
        self.margin_top_spin.setSingleStep(0.1)
        self.margin_top_spin.setValue(1.0)
        
        self.margin_bottom_spin = QDoubleSpinBox()
        self.margin_bottom_spin.setRange(0.5, 3.0)
        self.margin_bottom_spin.setSingleStep(0.1)
        self.margin_bottom_spin.setValue(1.0)
        
        self.margin_left_spin = QDoubleSpinBox()
        self.margin_left_spin.setRange(0.5, 3.0)
        self.margin_left_spin.setSingleStep(0.1)
        self.margin_left_spin.setValue(1.0)
        
        self.margin_right_spin = QDoubleSpinBox()
        self.margin_right_spin.setRange(0.5, 3.0)
        self.margin_right_spin.setSingleStep(0.1)
        self.margin_right_spin.setValue(1.0)
        
        page_layout.addRow("Page Size:", self.page_size_combo)
        page_layout.addRow("Top Margin (inches):", self.margin_top_spin)
        page_layout.addRow("Bottom Margin (inches):", self.margin_bottom_spin)
        page_layout.addRow("Left Margin (inches):", self.margin_left_spin)
        page_layout.addRow("Right Margin (inches):", self.margin_right_spin)
        
        # Chapter settings tab
        chapter_tab = QWidget()
        chapter_layout = QFormLayout(chapter_tab)
        
        self.chapter_new_page_check = QCheckBox("Start chapters on new page")
        self.chapter_new_page_check.setChecked(True)
        
        self.number_chapters_check = QCheckBox("Number chapters")
        self.number_chapters_check.setChecked(True)
        
        self.chapter_prefix_edit = QLineEdit("Chapter ")
        
        self.scene_separator_edit = QLineEdit("* * *")
        
        chapter_layout.addRow(self.chapter_new_page_check)
        chapter_layout.addRow(self.number_chapters_check)
        chapter_layout.addRow("Chapter Prefix:", self.chapter_prefix_edit)
        chapter_layout.addRow("Scene Separator:", self.scene_separator_edit)
        
        # Add tabs to tab widget
        self.settings_tabs.addTab(general_tab, "General")
        self.settings_tabs.addTab(formatting_tab, "Formatting")
        self.settings_tabs.addTab(page_tab, "Page")
        self.settings_tabs.addTab(chapter_tab, "Chapters")
        
        main_layout.addWidget(self.settings_tabs)
        
        # Export path
        path_group = QGroupBox("Export Path")
        path_layout = QHBoxLayout()
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._on_browse)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._on_export)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def _load_settings(self):
        """Load export settings from QSettings."""
        settings = QSettings()
        
        # Load general settings
        self.title_page_check.setChecked(settings.value("export/title_page", True, bool))
        self.toc_check.setChecked(settings.value("export/toc", True, bool))
        self.page_numbers_check.setChecked(settings.value("export/page_numbers", True, bool))
        self.synopsis_check.setChecked(settings.value("export/synopsis", False, bool))
        self.notes_check.setChecked(settings.value("export/notes", False, bool))
        self.metadata_check.setChecked(settings.value("export/metadata", False, bool))
        
        # Load formatting settings
        font_index = self.font_combo.findText(settings.value("export/font", "Times New Roman"))
        if font_index >= 0:
            self.font_combo.setCurrentIndex(font_index)
        
        self.font_size_spin.setValue(settings.value("export/font_size", 12, int))
        self.line_spacing_spin.setValue(settings.value("export/line_spacing", 1.5, float))
        self.paragraph_spacing_spin.setValue(settings.value("export/paragraph_spacing", 12, int))
        
        # Load page settings
        page_size_index = self.page_size_combo.findText(settings.value("export/page_size", "Letter"))
        if page_size_index >= 0:
            self.page_size_combo.setCurrentIndex(page_size_index)
        
        self.margin_top_spin.setValue(settings.value("export/margin_top", 1.0, float))
        self.margin_bottom_spin.setValue(settings.value("export/margin_bottom", 1.0, float))
        self.margin_left_spin.setValue(settings.value("export/margin_left", 1.0, float))
        self.margin_right_spin.setValue(settings.value("export/margin_right", 1.0, float))
        
        # Load chapter settings
        self.chapter_new_page_check.setChecked(settings.value("export/chapter_new_page", True, bool))
        self.number_chapters_check.setChecked(settings.value("export/number_chapters", True, bool))
        self.chapter_prefix_edit.setText(settings.value("export/chapter_prefix", "Chapter "))
        self.scene_separator_edit.setText(settings.value("export/scene_separator", "* * *"))
        
        # Load format
        format_index = self.format_combo.findData(settings.value("export/format", "docx"))
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)
    
    def _save_settings(self):
        """Save export settings to QSettings."""
        settings = QSettings()
        
        # Save general settings
        settings.setValue("export/title_page", self.title_page_check.isChecked())
        settings.setValue("export/toc", self.toc_check.isChecked())
        settings.setValue("export/page_numbers", self.page_numbers_check.isChecked())
        settings.setValue("export/synopsis", self.synopsis_check.isChecked())
        settings.setValue("export/notes", self.notes_check.isChecked())
        settings.setValue("export/metadata", self.metadata_check.isChecked())
        
        # Save formatting settings
        settings.setValue("export/font", self.font_combo.currentText())
        settings.setValue("export/font_size", self.font_size_spin.value())
        settings.setValue("export/line_spacing", self.line_spacing_spin.value())
        settings.setValue("export/paragraph_spacing", self.paragraph_spacing_spin.value())
        
        # Save page settings
        settings.setValue("export/page_size", self.page_size_combo.currentText())
        settings.setValue("export/margin_top", self.margin_top_spin.value())
        settings.setValue("export/margin_bottom", self.margin_bottom_spin.value())
        settings.setValue("export/margin_left", self.margin_left_spin.value())
        settings.setValue("export/margin_right", self.margin_right_spin.value())
        
        # Save chapter settings
        settings.setValue("export/chapter_new_page", self.chapter_new_page_check.isChecked())
        settings.setValue("export/number_chapters", self.number_chapters_check.isChecked())
        settings.setValue("export/chapter_prefix", self.chapter_prefix_edit.text())
        settings.setValue("export/scene_separator", self.scene_separator_edit.text())
        
        # Save format
        settings.setValue("export/format", self.format_combo.currentData())
    
    def _on_mode_changed(self):
        """Handle export mode change."""
        if self.project_radio.isChecked():
            self.export_mode = "project"
            self.toc_check.setEnabled(True)
            self.chapter_new_page_check.setEnabled(True)
            self.number_chapters_check.setEnabled(True)
            self.chapter_prefix_edit.setEnabled(True)
        else:
            self.export_mode = "document"
            self.toc_check.setEnabled(False)
            self.chapter_new_page_check.setEnabled(False)
            self.number_chapters_check.setEnabled(False)
            self.chapter_prefix_edit.setEnabled(False)
    
    def _on_format_changed(self, index):
        """
        Handle format change.
        
        Args:
            index: The index of the selected format.
        """
        format_data = self.format_combo.currentData()
        
        # Enable/disable settings based on format
        if format_data in ["docx", "pdf"]:
            # Full formatting options for DOCX and PDF
            self.settings_tabs.setTabEnabled(1, True)  # Formatting tab
            self.settings_tabs.setTabEnabled(2, True)  # Page tab
            self.page_numbers_check.setEnabled(True)
        elif format_data == "html":
            # Limited formatting options for HTML
            self.settings_tabs.setTabEnabled(1, True)  # Formatting tab
            self.settings_tabs.setTabEnabled(2, False)  # Page tab
            self.page_numbers_check.setEnabled(False)
        else:
            # Minimal formatting options for Markdown, EPUB, TXT
            self.settings_tabs.setTabEnabled(1, False)  # Formatting tab
            self.settings_tabs.setTabEnabled(2, False)  # Page tab
            self.page_numbers_check.setEnabled(False)
        
        # Update file extension in path
        self._update_path_extension()
    
    def _update_path_extension(self):
        """Update the file extension in the path based on the selected format."""
        path = self.path_edit.text()
        if not path:
            return
        
        # Get the new extension
        format_data = self.format_combo.currentData()
        new_ext = f".{format_data}"
        
        # Replace the extension
        base_path, _ = os.path.splitext(path)
        new_path = f"{base_path}{new_ext}"
        
        self.path_edit.setText(new_path)
    
    def _on_browse(self):
        """Handle browse button click."""
        # Get the current project or document title
        title = ""
        if self.export_mode == "project" and self.current_project:
            title = self.current_project.title
        elif self.export_mode == "document" and self.current_document:
            title = self.current_document.title
        
        # Create a safe filename
        if title:
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
            safe_title = safe_title.replace(" ", "_")
        else:
            safe_title = "export"
        
        # Get the format extension
        format_data = self.format_combo.currentData()
        extension = f".{format_data}"
        
        # Get the initial path
        initial_path = os.path.join(os.path.expanduser("~"), "Documents", f"{safe_title}{extension}")
        
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export To",
            initial_path,
            f"Export Files (*{extension});;All Files (*.*)"
        )
        
        if file_path:
            # Ensure the file has the correct extension
            if not file_path.lower().endswith(extension.lower()):
                file_path += extension
            
            self.path_edit.setText(file_path)
    
    def _get_export_settings(self) -> Dict[str, Any]:
        """
        Get the export settings from the UI.
        
        Returns:
            A dictionary of export settings.
        """
        settings = {
            # General settings
            "include_title_page": self.title_page_check.isChecked(),
            "include_toc": self.toc_check.isChecked(),
            "include_page_numbers": self.page_numbers_check.isChecked(),
            "include_synopsis": self.synopsis_check.isChecked(),
            "include_notes": self.notes_check.isChecked(),
            "include_metadata": self.metadata_check.isChecked(),
            
            # Formatting settings
            "font_name": self.font_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "line_spacing": self.line_spacing_spin.value(),
            "paragraph_spacing": self.paragraph_spacing_spin.value(),
            
            # Page settings
            "page_size": self.page_size_combo.currentText().lower(),
            "margin_top": self.margin_top_spin.value(),
            "margin_bottom": self.margin_bottom_spin.value(),
            "margin_left": self.margin_left_spin.value(),
            "margin_right": self.margin_right_spin.value(),
            
            # Chapter settings
            "chapter_start_new_page": self.chapter_new_page_check.isChecked(),
            "number_chapters": self.number_chapters_check.isChecked(),
            "chapter_prefix": self.chapter_prefix_edit.text(),
            "scene_separator": self.scene_separator_edit.text()
        }
        
        return settings
    
    def _on_export(self):
        """Handle export button click."""
        # Check if we have a project or document to export
        if self.export_mode == "project" and not self.current_project:
            QMessageBox.warning(self, "Export Error", "No project to export.")
            return
        elif self.export_mode == "document" and not self.current_document:
            QMessageBox.warning(self, "Export Error", "No document to export.")
            return
        
        # Check if we have a path
        export_path = self.path_edit.text()
        if not export_path:
            QMessageBox.warning(self, "Export Error", "Please select an export path.")
            return
        
        # Get export format
        format_data = self.format_combo.currentData()
        
        # Get export settings
        export_settings = self._get_export_settings()
        
        # Save settings
        self._save_settings()
        
        try:
            # Perform export
            success = False
            if self.export_mode == "project":
                success = self.export_service.export_project(
                    self.current_project,
                    export_path,
                    format_data,
                    export_settings
                )
            else:
                success = self.export_service.export_document(
                    self.current_document,
                    export_path,
                    format_data,
                    export_settings
                )
            
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Export completed successfully to:\n{export_path}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    "An error occurred during export. Please check the logs for details."
                )
        
        except Exception as e:
            logger.error(f"Error during export: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export:\n{str(e)}"
            )
    
    def set_project(self, project: Project):
        """
        Set the project to export.
        
        Args:
            project: The project to export.
        """
        self.current_project = project
        self.project_radio.setChecked(True)
        self.export_mode = "project"
    
    def set_document(self, document: Document):
        """
        Set the document to export.
        
        Args:
            document: The document to export.
        """
        self.current_document = document
        self.document_radio.setChecked(True)
        self.export_mode = "document"
