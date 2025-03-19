#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Project Settings Dialog

This module implements a dialog for configuring project-specific settings.
"""

import os
import sys
from typing import Optional, Dict, Any, List, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize
from PyQt6.QtGui import QFont, QIcon

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.backend.models.project import Project

logger = get_logger(__name__)
config = ConfigManager()


class ProjectSettingsDialog(QDialog):
    """
    Project settings dialog for RebelSCRIBE.
    
    This dialog allows users to configure project-specific settings including:
    - Project metadata (title, author, description)
    - Project structure (folder organization, default templates)
    - Compilation settings (which documents to include in compilation)
    - Project-specific formatting preferences
    """
    
    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, project=None):
        """
        Initialize the project settings dialog.
        
        Args:
            parent: The parent widget.
            project: The current project.
        """
        super().__init__(parent)
        
        self.project = project
        
        # Initialize UI components
        self._init_ui()
        
        # Load current settings
        self._load_settings()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Project settings dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing project settings dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Project Settings")
        self.setMinimumSize(600, 450)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_metadata_tab()
        self._create_structure_tab()
        self._create_compilation_tab()
        self._create_formatting_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("Project settings dialog UI components initialized")
    
    def _create_metadata_tab(self):
        """Create the metadata settings tab."""
        logger.debug("Creating metadata settings tab")
        
        # Create tab widget
        self.metadata_tab = QWidget()
        self.tab_widget.addTab(self.metadata_tab, "Metadata")
        
        # Create layout
        layout = QVBoxLayout(self.metadata_tab)
        
        # Basic metadata group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.title_edit = QLineEdit()
        basic_layout.addRow("Title:", self.title_edit)
        
        self.author_edit = QLineEdit()
        basic_layout.addRow("Author:", self.author_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(basic_group)
        
        # Additional metadata group
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)
        
        self.genre_edit = QLineEdit()
        additional_layout.addRow("Genre:", self.genre_edit)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian", "Chinese", "Japanese"])
        additional_layout.addRow("Language:", self.language_combo)
        
        self.copyright_edit = QLineEdit()
        additional_layout.addRow("Copyright:", self.copyright_edit)
        
        self.publisher_edit = QLineEdit()
        additional_layout.addRow("Publisher:", self.publisher_edit)
        
        layout.addWidget(additional_group)
        
        # Keywords group
        keywords_group = QGroupBox("Keywords")
        keywords_layout = QVBoxLayout(keywords_group)
        
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("Enter keywords separated by commas")
        keywords_layout.addWidget(self.keywords_edit)
        
        layout.addWidget(keywords_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Metadata settings tab created")
    
    def _create_structure_tab(self):
        """Create the project structure settings tab."""
        logger.debug("Creating project structure settings tab")
        
        # Create tab widget
        self.structure_tab = QWidget()
        self.tab_widget.addTab(self.structure_tab, "Structure")
        
        # Create layout
        layout = QVBoxLayout(self.structure_tab)
        
        # Default folders group
        folders_group = QGroupBox("Default Folders")
        folders_layout = QVBoxLayout(folders_group)
        
        self.create_chapters_check = QCheckBox("Create Chapters folder")
        self.create_chapters_check.setChecked(True)
        folders_layout.addWidget(self.create_chapters_check)
        
        self.create_characters_check = QCheckBox("Create Characters folder")
        self.create_characters_check.setChecked(True)
        folders_layout.addWidget(self.create_characters_check)
        
        self.create_locations_check = QCheckBox("Create Locations folder")
        self.create_locations_check.setChecked(True)
        folders_layout.addWidget(self.create_locations_check)
        
        self.create_research_check = QCheckBox("Create Research folder")
        self.create_research_check.setChecked(True)
        folders_layout.addWidget(self.create_research_check)
        
        self.create_notes_check = QCheckBox("Create Notes folder")
        self.create_notes_check.setChecked(True)
        folders_layout.addWidget(self.create_notes_check)
        
        self.create_trash_check = QCheckBox("Create Trash folder")
        self.create_trash_check.setChecked(True)
        folders_layout.addWidget(self.create_trash_check)
        
        layout.addWidget(folders_group)
        
        # Templates group
        templates_group = QGroupBox("Default Templates")
        templates_layout = QFormLayout(templates_group)
        
        self.chapter_template_combo = QComboBox()
        self.chapter_template_combo.addItems(["Empty", "Basic Chapter", "Chapter with Synopsis"])
        templates_layout.addRow("Chapter Template:", self.chapter_template_combo)
        
        self.character_template_combo = QComboBox()
        self.character_template_combo.addItems(["Empty", "Basic Character", "Detailed Character"])
        templates_layout.addRow("Character Template:", self.character_template_combo)
        
        self.location_template_combo = QComboBox()
        self.location_template_combo.addItems(["Empty", "Basic Location", "Detailed Location"])
        templates_layout.addRow("Location Template:", self.location_template_combo)
        
        layout.addWidget(templates_group)
        
        # Project location group
        location_group = QGroupBox("Project Location")
        location_layout = QHBoxLayout(location_group)
        
        self.location_edit = QLineEdit()
        self.location_edit.setReadOnly(True)
        location_layout.addWidget(self.location_edit)
        
        self.location_button = QPushButton("Change...")
        location_layout.addWidget(self.location_button)
        
        layout.addWidget(location_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Project structure settings tab created")
    
    def _create_compilation_tab(self):
        """Create the compilation settings tab."""
        logger.debug("Creating compilation settings tab")
        
        # Create tab widget
        self.compilation_tab = QWidget()
        self.tab_widget.addTab(self.compilation_tab, "Compilation")
        
        # Create layout
        layout = QVBoxLayout(self.compilation_tab)
        
        # Include in compilation group
        include_group = QGroupBox("Include in Compilation")
        include_layout = QVBoxLayout(include_group)
        
        self.include_title_page_check = QCheckBox("Include title page")
        self.include_title_page_check.setChecked(True)
        include_layout.addWidget(self.include_title_page_check)
        
        self.include_toc_check = QCheckBox("Include table of contents")
        self.include_toc_check.setChecked(True)
        include_layout.addWidget(self.include_toc_check)
        
        self.include_synopsis_check = QCheckBox("Include synopses")
        include_layout.addWidget(self.include_synopsis_check)
        
        self.include_notes_check = QCheckBox("Include notes")
        include_layout.addWidget(self.include_notes_check)
        
        self.include_comments_check = QCheckBox("Include comments")
        include_layout.addWidget(self.include_comments_check)
        
        layout.addWidget(include_group)
        
        # Document selection group
        documents_group = QGroupBox("Documents to Include")
        documents_layout = QVBoxLayout(documents_group)
        
        self.documents_list = QListWidget()
        documents_layout.addWidget(self.documents_list)
        
        # Add some placeholder items (these would be populated from the project)
        if self.project:
            # This would be replaced with actual document loading from the project
            pass
        else:
            # Just add some placeholders for now
            self.documents_list.addItem("Front Matter")
            item = QListWidgetItem("Chapter 1")
            item.setCheckState(Qt.CheckState.Checked)
            self.documents_list.addItem(item)
            item = QListWidgetItem("Chapter 2")
            item.setCheckState(Qt.CheckState.Checked)
            self.documents_list.addItem(item)
            item = QListWidgetItem("Chapter 3")
            item.setCheckState(Qt.CheckState.Checked)
            self.documents_list.addItem(item)
            item = QListWidgetItem("Notes")
            item.setCheckState(Qt.CheckState.Unchecked)
            self.documents_list.addItem(item)
        
        documents_buttons_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("Select All")
        documents_buttons_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        documents_buttons_layout.addWidget(self.deselect_all_button)
        
        documents_layout.addLayout(documents_buttons_layout)
        
        layout.addWidget(documents_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Compilation settings tab created")
    
    def _create_formatting_tab(self):
        """Create the formatting settings tab."""
        logger.debug("Creating formatting settings tab")
        
        # Create tab widget
        self.formatting_tab = QWidget()
        self.tab_widget.addTab(self.formatting_tab, "Formatting")
        
        # Create layout
        layout = QVBoxLayout(self.formatting_tab)
        
        # Font settings group
        font_group = QGroupBox("Font Settings")
        font_layout = QFormLayout(font_group)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Times New Roman", "Arial", "Calibri", "Courier New", 
            "Georgia", "Verdana", "Helvetica"
        ])
        font_layout.addRow("Default Font:", self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        font_layout.addRow("Font Size:", self.font_size_spin)
        
        layout.addWidget(font_group)
        
        # Paragraph settings group
        paragraph_group = QGroupBox("Paragraph Settings")
        paragraph_layout = QFormLayout(paragraph_group)
        
        self.line_spacing_combo = QComboBox()
        self.line_spacing_combo.addItems(["Single", "1.5 Lines", "Double"])
        self.line_spacing_combo.setCurrentIndex(1)  # Default to 1.5 lines
        paragraph_layout.addRow("Line Spacing:", self.line_spacing_combo)
        
        self.paragraph_spacing_spin = QSpinBox()
        self.paragraph_spacing_spin.setRange(0, 36)
        self.paragraph_spacing_spin.setValue(12)
        self.paragraph_spacing_spin.setSuffix(" pt")
        paragraph_layout.addRow("Paragraph Spacing:", self.paragraph_spacing_spin)
        
        self.first_line_indent_spin = QSpinBox()
        self.first_line_indent_spin.setRange(0, 72)
        self.first_line_indent_spin.setValue(36)
        self.first_line_indent_spin.setSuffix(" pt")
        paragraph_layout.addRow("First Line Indent:", self.first_line_indent_spin)
        
        layout.addWidget(paragraph_group)
        
        # Page settings group
        page_group = QGroupBox("Page Settings")
        page_layout = QFormLayout(page_group)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["Letter", "A4", "Legal"])
        page_layout.addRow("Page Size:", self.page_size_combo)
        
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 2)
        self.margin_spin.setValue(1)
        self.margin_spin.setSuffix(" in")
        page_layout.addRow("Margins:", self.margin_spin)
        
        layout.addWidget(page_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Formatting settings tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        
        # Connect structure tab signals
        self.location_button.clicked.connect(self._on_change_location)
        
        # Connect compilation tab signals
        self.select_all_button.clicked.connect(self._on_select_all)
        self.deselect_all_button.clicked.connect(self._on_deselect_all)
        
        logger.debug("Signals connected")
    
    def _load_settings(self):
        """Load current project settings."""
        logger.debug("Loading current project settings")
        
        if not self.project:
            logger.debug("No project provided, using default settings")
            return
        
        try:
            # Load metadata
            self.title_edit.setText(self.project.title)
            self.author_edit.setText(self.project.author)
            self.description_edit.setText(self.project.description)
            
            # Load additional metadata if available
            metadata = self.project.metadata if hasattr(self.project, "metadata") else {}
            
            self.genre_edit.setText(metadata.get("genre", ""))
            
            language = metadata.get("language", "English")
            language_index = self.language_combo.findText(language)
            if language_index >= 0:
                self.language_combo.setCurrentIndex(language_index)
            
            self.copyright_edit.setText(metadata.get("copyright", ""))
            self.publisher_edit.setText(metadata.get("publisher", ""))
            
            # Load keywords
            keywords = metadata.get("keywords", [])
            if isinstance(keywords, list):
                self.keywords_edit.setText(", ".join(keywords))
            else:
                self.keywords_edit.setText(str(keywords))
            
            # Load structure settings
            structure = metadata.get("structure", {})
            
            self.create_chapters_check.setChecked(structure.get("create_chapters", True))
            self.create_characters_check.setChecked(structure.get("create_characters", True))
            self.create_locations_check.setChecked(structure.get("create_locations", True))
            self.create_research_check.setChecked(structure.get("create_research", True))
            self.create_notes_check.setChecked(structure.get("create_notes", True))
            self.create_trash_check.setChecked(structure.get("create_trash", True))
            
            # Load template settings
            templates = structure.get("templates", {})
            
            chapter_template = templates.get("chapter", "Basic Chapter")
            chapter_index = self.chapter_template_combo.findText(chapter_template)
            if chapter_index >= 0:
                self.chapter_template_combo.setCurrentIndex(chapter_index)
            
            character_template = templates.get("character", "Basic Character")
            character_index = self.character_template_combo.findText(character_template)
            if character_index >= 0:
                self.character_template_combo.setCurrentIndex(character_index)
            
            location_template = templates.get("location", "Basic Location")
            location_index = self.location_template_combo.findText(location_template)
            if location_index >= 0:
                self.location_template_combo.setCurrentIndex(location_index)
            
            # Load project location
            self.location_edit.setText(self.project.path if hasattr(self.project, "path") else "")
            
            # Load compilation settings
            compilation = metadata.get("compilation", {})
            
            self.include_title_page_check.setChecked(compilation.get("include_title_page", True))
            self.include_toc_check.setChecked(compilation.get("include_toc", True))
            self.include_synopsis_check.setChecked(compilation.get("include_synopsis", False))
            self.include_notes_check.setChecked(compilation.get("include_notes", False))
            self.include_comments_check.setChecked(compilation.get("include_comments", False))
            
            # Load formatting settings
            formatting = metadata.get("formatting", {})
            
            font_name = formatting.get("font_name", "Times New Roman")
            font_index = self.font_combo.findText(font_name)
            if font_index >= 0:
                self.font_combo.setCurrentIndex(font_index)
            
            self.font_size_spin.setValue(formatting.get("font_size", 12))
            
            line_spacing = formatting.get("line_spacing", "1.5 Lines")
            spacing_index = self.line_spacing_combo.findText(line_spacing)
            if spacing_index >= 0:
                self.line_spacing_combo.setCurrentIndex(spacing_index)
            
            self.paragraph_spacing_spin.setValue(formatting.get("paragraph_spacing", 12))
            self.first_line_indent_spin.setValue(formatting.get("first_line_indent", 36))
            
            page_size = formatting.get("page_size", "Letter")
            page_index = self.page_size_combo.findText(page_size)
            if page_index >= 0:
                self.page_size_combo.setCurrentIndex(page_index)
            
            self.margin_spin.setValue(formatting.get("margin", 1))
            
            logger.debug("Project settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading project settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load project settings: {e}")
    
    def _get_current_settings(self) -> Dict[str, Any]:
        """
        Get current settings from the dialog.
        
        Returns:
            A dictionary containing the current settings.
        """
        logger.debug("Getting current settings from dialog")
        
        settings = {}
        
        # Get metadata
        settings["title"] = self.title_edit.text()
        settings["author"] = self.author_edit.text()
        settings["description"] = self.description_edit.toPlainText()
        
        # Get additional metadata
        metadata = {}
        
        metadata["genre"] = self.genre_edit.text()
        metadata["language"] = self.language_combo.currentText()
        metadata["copyright"] = self.copyright_edit.text()
        metadata["publisher"] = self.publisher_edit.text()
        
        # Get keywords
        keywords_text = self.keywords_edit.text()
        if keywords_text:
            metadata["keywords"] = [k.strip() for k in keywords_text.split(",")]
        else:
            metadata["keywords"] = []
        
        # Get structure settings
        structure = {}
        
        structure["create_chapters"] = self.create_chapters_check.isChecked()
        structure["create_characters"] = self.create_characters_check.isChecked()
        structure["create_locations"] = self.create_locations_check.isChecked()
        structure["create_research"] = self.create_research_check.isChecked()
        structure["create_notes"] = self.create_notes_check.isChecked()
        structure["create_trash"] = self.create_trash_check.isChecked()
        
        # Get template settings
        templates = {}
        
        templates["chapter"] = self.chapter_template_combo.currentText()
        templates["character"] = self.character_template_combo.currentText()
        templates["location"] = self.location_template_combo.currentText()
        
        structure["templates"] = templates
        
        metadata["structure"] = structure
        
        # Get compilation settings
        compilation = {}
        
        compilation["include_title_page"] = self.include_title_page_check.isChecked()
        compilation["include_toc"] = self.include_toc_check.isChecked()
        compilation["include_synopsis"] = self.include_synopsis_check.isChecked()
        compilation["include_notes"] = self.include_notes_check.isChecked()
        compilation["include_comments"] = self.include_comments_check.isChecked()
        
        # Get selected documents
        selected_documents = []
        for i in range(self.documents_list.count()):
            item = self.documents_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_documents.append(item.text())
        
        compilation["selected_documents"] = selected_documents
        
        metadata["compilation"] = compilation
        
        # Get formatting settings
        formatting = {}
        
        formatting["font_name"] = self.font_combo.currentText()
        formatting["font_size"] = self.font_size_spin.value()
        formatting["line_spacing"] = self.line_spacing_combo.currentText()
        formatting["paragraph_spacing"] = self.paragraph_spacing_spin.value()
        formatting["first_line_indent"] = self.first_line_indent_spin.value()
        formatting["page_size"] = self.page_size_combo.currentText()
        formatting["margin"] = self.margin_spin.value()
        
        metadata["formatting"] = formatting
        
        settings["metadata"] = metadata
        
        logger.debug("Current settings retrieved from dialog")
        
        return settings
    
    def _save_settings(self):
        """Save current settings to the project."""
        logger.debug("Saving current settings to project")
        
        if not self.project:
            logger.warning("No project provided, cannot save settings")
            QMessageBox.warning(self, "Error", "No project provided, cannot save settings")
            return False
        
        try:
            # Get current settings
            settings = self._get_current_settings()
            
            # Update project properties
            self.project.title = settings["title"]
            self.project.author = settings["author"]
            self.project.description = settings["description"]
            
            # Update project metadata
            if not hasattr(self.project, "metadata"):
                self.project.metadata = {}
            
            self.project.metadata.update(settings["metadata"])
            
            # Emit settings changed signal
            self.settings_changed.emit(settings)
            
            logger.debug("Project settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving project settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save project settings: {e}")
            return False
    
    def _on_accept(self):
        """Handle accept button clicked."""
        logger.debug("Accept button clicked")
        
        # Save settings
        if self._save_settings():
            # Accept dialog
            self.accept()
    
    def _on_apply(self):
        """Handle apply button clicked."""
        logger.debug("Apply button clicked")
        
        # Save settings
        self._save_settings()
    
    def _on_change_location(self):
        """Handle change location button clicked."""
        logger.debug("Change location button clicked")
        
        # Show directory dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Project Location",
            self.location_edit.text() or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Update location edit
            self.location_edit.setText(directory)
            
            # Confirm with user
            result = QMessageBox.question(
                self,
                "Change Project Location",
                "Changing the project location will move all project files to the new location. "
                "This operation cannot be undone. Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                # This would be handled by the project manager
                logger.debug(f"Project location changed to: {directory}")
                
                # For now, just update the location
                if hasattr(self.project, "path"):
                    self.project.path = directory
            else:
                # Revert to original location
                if hasattr(self.project, "path"):
                    self.location_edit.setText(self.project.path)
                else:
                    self.location_edit.clear()
    
    def _on_select_all(self):
        """Handle select all button clicked."""
        logger.debug("Select all button clicked")
        
        # Select all items in the documents list
        for i in range(self.documents_list.count()):
            item = self.documents_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def _on_deselect_all(self):
        """Handle deselect all button clicked."""
        logger.debug("Deselect all button clicked")
        
        # Deselect all items in the documents list
        for i in range(self.documents_list.count()):
            item = self.documents_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def set_project(self, project: Project):
        """
        Set the project for the dialog.
        
        Args:
            project: The project to configure.
        """
        logger.debug(f"Setting project: {project.title if project else 'None'}")
        
        self.project = project
        
        # Load settings
        self._load_settings()
