#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Inspector View

This module implements the inspector panel for RebelSCRIBE.
"""

from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QDateEdit, QColorDialog, QPushButton, QFormLayout,
    QScrollArea, QGroupBox, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont

from src.utils.logging_utils import get_logger
from src.backend.services.document_manager import DocumentManager
from src.backend.models.document import Document
from src.backend.models.character import Character
from src.backend.models.location import Location
from src.backend.models.note import Note

logger = get_logger(__name__)


class MetadataPanel(QWidget):
    """
    Metadata panel for the inspector.
    
    This panel displays and allows editing of document metadata,
    such as title, synopsis, status, tags, etc.
    """
    
    # Signal emitted when metadata is changed
    metadata_changed = pyqtSignal(str, object)  # key, value
    
    def __init__(self, parent=None):
        """
        Initialize the metadata panel.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Current document
        self.document: Optional[Document] = None
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Metadata panel initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing metadata panel UI components")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create form layout
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)
        
        # Title field
        self.title_label = QLabel("Title:")
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(lambda text: self.metadata_changed.emit("title", text))
        self.form_layout.addRow(self.title_label, self.title_edit)
        
        # Synopsis field
        self.synopsis_label = QLabel("Synopsis:")
        self.synopsis_edit = QTextEdit()
        self.synopsis_edit.setMaximumHeight(100)
        self.synopsis_edit.textChanged.connect(lambda: self.metadata_changed.emit("synopsis", self.synopsis_edit.toPlainText()))
        self.form_layout.addRow(self.synopsis_label, self.synopsis_edit)
        
        # Status field
        self.status_label = QLabel("Status:")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Draft", "Revised", "Final", "To Review", "Completed"])
        self.status_combo.currentTextChanged.connect(lambda text: self.metadata_changed.emit("status", text))
        self.form_layout.addRow(self.status_label, self.status_combo)
        
        # Include in compile checkbox
        self.include_label = QLabel("Include in Compile:")
        self.include_check = QCheckBox()
        self.include_check.setChecked(True)
        self.include_check.stateChanged.connect(lambda state: self.metadata_changed.emit("is_included_in_compile", state == Qt.CheckState.Checked))
        self.form_layout.addRow(self.include_label, self.include_check)
        
        # Tags field
        self.tags_label = QLabel("Tags:")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags")
        self.tags_edit.textChanged.connect(self._on_tags_changed)
        self.form_layout.addRow(self.tags_label, self.tags_edit)
        
        # Color field
        self.color_label = QLabel("Color:")
        self.color_button = QPushButton()
        self.color_button.setFixedWidth(50)
        self.color_button.clicked.connect(self._on_color_button_clicked)
        self.form_layout.addRow(self.color_label, self.color_button)
        
        # Word count field
        self.word_count_label = QLabel("Word Count:")
        self.word_count_value = QLabel("0")
        self.form_layout.addRow(self.word_count_label, self.word_count_value)
        
        # Character count field
        self.char_count_label = QLabel("Character Count:")
        self.char_count_value = QLabel("0")
        self.form_layout.addRow(self.char_count_label, self.char_count_value)
        
        # Created date field
        self.created_label = QLabel("Created:")
        self.created_value = QLabel()
        self.form_layout.addRow(self.created_label, self.created_value)
        
        # Updated date field
        self.updated_label = QLabel("Updated:")
        self.updated_value = QLabel()
        self.form_layout.addRow(self.updated_label, self.updated_value)
        
        # Custom metadata section
        self.custom_group = QGroupBox("Custom Metadata")
        self.custom_layout = QVBoxLayout(self.custom_group)
        self.custom_form = QFormLayout()
        self.custom_layout.addLayout(self.custom_form)
        
        # Add custom metadata button
        self.add_custom_button = QPushButton("Add Custom Metadata")
        self.add_custom_button.clicked.connect(self._on_add_custom_metadata)
        self.custom_layout.addWidget(self.add_custom_button)
        
        self.layout.addWidget(self.custom_group)
        
        # Stretch to fill space
        self.layout.addStretch()
        
        # Disable all fields initially
        self._set_fields_enabled(False)
        
        logger.debug("Metadata panel UI components initialized")
    
    def _set_fields_enabled(self, enabled: bool):
        """
        Enable or disable all fields.
        
        Args:
            enabled: Whether to enable the fields.
        """
        self.title_edit.setEnabled(enabled)
        self.synopsis_edit.setEnabled(enabled)
        self.status_combo.setEnabled(enabled)
        self.include_check.setEnabled(enabled)
        self.tags_edit.setEnabled(enabled)
        self.color_button.setEnabled(enabled)
        self.add_custom_button.setEnabled(enabled)
    
    def _on_tags_changed(self, text: str):
        """
        Handle tags changed event.
        
        Args:
            text: The new tags text.
        """
        # Split tags by comma and strip whitespace
        tags = [tag.strip() for tag in text.split(",") if tag.strip()]
        self.metadata_changed.emit("tags", tags)
    
    def _on_color_button_clicked(self):
        """Handle color button click event."""
        # Get current color
        current_color = self.color_button.property("color")
        if not current_color:
            current_color = QColor(Qt.GlobalColor.white)
        
        # Show color dialog
        color = QColorDialog.getColor(current_color, self, "Select Color")
        if color.isValid():
            # Set button color
            self.color_button.setStyleSheet(f"background-color: {color.name()}")
            self.color_button.setProperty("color", color)
            
            # Emit metadata changed signal
            self.metadata_changed.emit("color", color.name())
    
    def _on_add_custom_metadata(self):
        """Handle add custom metadata button click event."""
        # Create key field
        key_edit = QLineEdit()
        key_edit.setPlaceholderText("Key")
        
        # Create value field
        value_edit = QLineEdit()
        value_edit.setPlaceholderText("Value")
        
        # Create layout for key-value pair
        pair_layout = QHBoxLayout()
        pair_layout.addWidget(key_edit)
        pair_layout.addWidget(value_edit)
        
        # Add to form layout
        self.custom_form.addRow(pair_layout)
        
        # Connect signals
        key_edit.textChanged.connect(lambda: self._on_custom_metadata_changed(key_edit, value_edit))
        value_edit.textChanged.connect(lambda: self._on_custom_metadata_changed(key_edit, value_edit))
    
    def _on_custom_metadata_changed(self, key_edit: QLineEdit, value_edit: QLineEdit):
        """
        Handle custom metadata changed event.
        
        Args:
            key_edit: The key edit field.
            value_edit: The value edit field.
        """
        key = key_edit.text()
        value = value_edit.text()
        
        if key:
            # Emit metadata changed signal
            self.metadata_changed.emit(f"metadata.{key}", value)
    
    def set_document(self, document: Optional[Document]):
        """
        Set the document to display.
        
        Args:
            document: The document to display, or None to clear.
        """
        logger.debug(f"Setting document: {document.title if document else 'None'}")
        
        # Store document
        self.document = document
        
        # Enable/disable fields
        self._set_fields_enabled(document is not None)
        
        if document:
            # Update fields
            self.title_edit.setText(document.title)
            self.synopsis_edit.setText(document.synopsis)
            self.status_combo.setCurrentText(document.status)
            self.include_check.setChecked(document.is_included_in_compile)
            self.tags_edit.setText(", ".join(document.tags))
            
            # Update color button
            if document.color:
                self.color_button.setStyleSheet(f"background-color: {document.color}")
                self.color_button.setProperty("color", QColor(document.color))
            else:
                self.color_button.setStyleSheet("")
                self.color_button.setProperty("color", None)
            
            # Update counts
            self.word_count_value.setText(str(document.word_count))
            self.char_count_value.setText(str(document.character_count))
            
            # Update dates
            self.created_value.setText(document.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            self.updated_value.setText(document.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Clear custom metadata
            self._clear_custom_metadata()
            
            # Add custom metadata fields
            for key, value in document.metadata.items():
                self._add_custom_metadata_field(key, value)
        else:
            # Clear fields
            self.title_edit.clear()
            self.synopsis_edit.clear()
            self.status_combo.setCurrentIndex(0)
            self.include_check.setChecked(True)
            self.tags_edit.clear()
            self.color_button.setStyleSheet("")
            self.color_button.setProperty("color", None)
            self.word_count_value.setText("0")
            self.char_count_value.setText("0")
            self.created_value.clear()
            self.updated_value.clear()
            
            # Clear custom metadata
            self._clear_custom_metadata()
    
    def _clear_custom_metadata(self):
        """Clear all custom metadata fields."""
        # Remove all items from the form layout
        while self.custom_form.rowCount() > 0:
            # Get the layout at row 0
            layout_item = self.custom_form.itemAt(0, QFormLayout.ItemRole.FieldRole)
            if layout_item:
                # Remove all widgets from the layout
                layout = layout_item.layout()
                if layout:
                    while layout.count() > 0:
                        item = layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
            
            # Remove the row
            self.custom_form.removeRow(0)
    
    def _add_custom_metadata_field(self, key: str, value: Any):
        """
        Add a custom metadata field.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        # Create key field
        key_edit = QLineEdit()
        key_edit.setText(key)
        
        # Create value field
        value_edit = QLineEdit()
        value_edit.setText(str(value))
        
        # Create layout for key-value pair
        pair_layout = QHBoxLayout()
        pair_layout.addWidget(key_edit)
        pair_layout.addWidget(value_edit)
        
        # Add to form layout
        self.custom_form.addRow(pair_layout)
        
        # Connect signals
        key_edit.textChanged.connect(lambda: self._on_custom_metadata_changed(key_edit, value_edit))
        value_edit.textChanged.connect(lambda: self._on_custom_metadata_changed(key_edit, value_edit))


class CharacterInspector(QWidget):
    """Character inspector panel."""
    
    # Signal emitted when character data is changed
    character_changed = pyqtSignal(str, object)  # field, value
    
    def __init__(self, parent=None):
        """Initialize the character inspector."""
        super().__init__(parent)
        
        # Current character
        self.character: Optional[Character] = None
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Character inspector initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Create scroll content widget
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        
        # Create form layout
        self.form_layout = QFormLayout(self.scroll_content)
        
        # Basic information section
        self.basic_group = QGroupBox("Basic Information")
        self.basic_layout = QFormLayout(self.basic_group)
        
        # Name field
        self.name_label = QLabel("Name:")
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(lambda text: self.character_changed.emit("name", text))
        self.basic_layout.addRow(self.name_label, self.name_edit)
        
        # Role field
        self.role_label = QLabel("Role:")
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Protagonist", "Antagonist", "Supporting", "Minor"])
        self.role_combo.currentTextChanged.connect(lambda text: self.character_changed.emit("role", text))
        self.basic_layout.addRow(self.role_label, self.role_combo)
        
        # Age field
        self.age_label = QLabel("Age:")
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 150)
        self.age_spin.valueChanged.connect(lambda value: self.character_changed.emit("age", value))
        self.basic_layout.addRow(self.age_label, self.age_spin)
        
        # Add more fields as needed
        
        self.form_layout.addRow(self.basic_group)
        
        # Disable all fields initially
        self._set_fields_enabled(False)
    
    def _set_fields_enabled(self, enabled: bool):
        """Enable or disable all fields."""
        self.name_edit.setEnabled(enabled)
        self.role_combo.setEnabled(enabled)
        self.age_spin.setEnabled(enabled)
        # Enable/disable other fields
    
    def set_character(self, character: Optional[Character]):
        """Set the character to display."""
        logger.debug(f"Setting character: {character.name if character else 'None'}")
        
        # Store character
        self.character = character
        
        # Enable/disable fields
        self._set_fields_enabled(character is not None)
        
        if character:
            # Update fields
            self.name_edit.setText(character.name)
            self.role_combo.setCurrentText(character.role)
            self.age_spin.setValue(character.age)
            # Update other fields
        else:
            # Clear fields
            self.name_edit.clear()
            self.role_combo.setCurrentIndex(0)
            self.age_spin.setValue(0)
            # Clear other fields


class LocationInspector(QWidget):
    """Location inspector panel."""
    
    # Signal emitted when location data is changed
    location_changed = pyqtSignal(str, object)  # field, value
    
    def __init__(self, parent=None):
        """Initialize the location inspector."""
        super().__init__(parent)
        
        # Current location
        self.location: Optional[Location] = None
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Location inspector initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Create scroll content widget
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        
        # Create form layout
        self.form_layout = QFormLayout(self.scroll_content)
        
        # Basic information section
        self.basic_group = QGroupBox("Basic Information")
        self.basic_layout = QFormLayout(self.basic_group)
        
        # Name field
        self.name_label = QLabel("Name:")
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(lambda text: self.location_changed.emit("name", text))
        self.basic_layout.addRow(self.name_label, self.name_edit)
        
        # Type field
        self.type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["City", "Town", "Village", "Building", "Room", "Landscape", "Other"])
        self.type_combo.currentTextChanged.connect(lambda text: self.location_changed.emit("type", text))
        self.basic_layout.addRow(self.type_label, self.type_combo)
        
        # Add more fields as needed
        
        self.form_layout.addRow(self.basic_group)
        
        # Disable all fields initially
        self._set_fields_enabled(False)
    
    def _set_fields_enabled(self, enabled: bool):
        """Enable or disable all fields."""
        self.name_edit.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        # Enable/disable other fields
    
    def set_location(self, location: Optional[Location]):
        """Set the location to display."""
        logger.debug(f"Setting location: {location.name if location else 'None'}")
        
        # Store location
        self.location = location
        
        # Enable/disable fields
        self._set_fields_enabled(location is not None)
        
        if location:
            # Update fields
            self.name_edit.setText(location.name)
            self.type_combo.setCurrentText(location.type)
            # Update other fields
        else:
            # Clear fields
            self.name_edit.clear()
            self.type_combo.setCurrentIndex(0)
            # Clear other fields


class NotesInspector(QWidget):
    """Notes inspector panel."""
    
    # Signal emitted when note data is changed
    note_changed = pyqtSignal(str, object)  # field, value
    
    def __init__(self, parent=None):
        """Initialize the notes inspector."""
        super().__init__(parent)
        
        # Current note
        self.note: Optional[Note] = None
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("Notes inspector initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Create scroll content widget
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        
        # Create form layout
        self.form_layout = QFormLayout(self.scroll_content)
        
        # Title field
        self.title_label = QLabel("Title:")
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(lambda text: self.note_changed.emit("title", text))
        self.form_layout.addRow(self.title_label, self.title_edit)
        
        # Content field
        self.content_label = QLabel("Content:")
        self.content_edit = QTextEdit()
        self.content_edit.setMinimumHeight(300)
        self.content_edit.textChanged.connect(lambda: self.note_changed.emit("content", self.content_edit.toPlainText()))
        self.form_layout.addRow(self.content_label, self.content_edit)
        
        # Disable all fields initially
        self._set_fields_enabled(False)
    
    def _set_fields_enabled(self, enabled: bool):
        """Enable or disable all fields."""
        self.title_edit.setEnabled(enabled)
        self.content_edit.setEnabled(enabled)
    
    def set_note(self, note: Optional[Note]):
        """Set the note to display."""
        logger.debug(f"Setting note: {note.title if note else 'None'}")
        
        # Store note
        self.note = note
        
        # Enable/disable fields
        self._set_fields_enabled(note is not None)
        
        if note:
            # Update fields
            self.title_edit.setText(note.title)
            self.content_edit.setText(note.content)
        else:
            # Clear fields
            self.title_edit.clear()
            self.content_edit.clear()


class InspectorView(QWidget):
    """
    Inspector panel for RebelSCRIBE.
    
    This panel displays and allows editing of document metadata,
    character information, location information, and notes.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the inspector view.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Set up document manager
        self.document_manager = DocumentManager()
        
        # Current document
        self.current_document: Optional[Document] = None
        
        # Initialize UI components
        self._init_ui()
        
        logger.info("Inspector view initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing inspector UI components")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create metadata panel
        self.metadata_panel = MetadataPanel()
        self.metadata_panel.metadata_changed.connect(self._on_metadata_changed)
        self.tab_widget.addTab(self.metadata_panel, "Metadata")
        
        # Create character inspector
        self.character_inspector = CharacterInspector()
        self.character_inspector.character_changed.connect(self._on_character_changed)
        self.tab_widget.addTab(self.character_inspector, "Character")
        
        # Create location inspector
        self.location_inspector = LocationInspector()
        self.location_inspector.location_changed.connect(self._on_location_changed)
        self.tab_widget.addTab(self.location_inspector, "Location")
        
        # Create notes inspector
        self.notes_inspector = NotesInspector()
        self.notes_inspector.note_changed.connect(self._on_note_changed)
        self.tab_widget.addTab(self.notes_inspector, "Notes")
        
        logger.debug("Inspector UI components initialized")
    
    def set_document(self, document: Optional[Document]):
        """
        Set the document to display.
        
        Args:
            document: The document to display, or None to clear.
        """
        logger.info(f"Setting document: {document.title if document else 'None'}")
        
        # Store document
        self.current_document = document
        
        # Update metadata panel
        self.metadata_panel.set_document(document)
        
        # Update other panels based on document type
        if document:
            if document.type == Document.TYPE_CHARACTER:
                # Load character
                character = Character.from_document(document)
                self.character_inspector.set_character(character)
                self.tab_widget.setCurrentWidget(self.character_inspector)
            elif document.type == Document.TYPE_LOCATION:
                # Load location
                location = Location.from_document(document)
                self.location_inspector.set_location(location)
                self.tab_widget.setCurrentWidget(self.location_inspector)
            elif document.type == Document.TYPE_NOTE:
                # Load note
                note = Note.from_document(document)
                self.notes_inspector.set_note(note)
                self.tab_widget.setCurrentWidget(self.notes_inspector)
            else:
                # Default to metadata panel
                self.character_inspector.set_character(None)
                self.location_inspector.set_location(None)
                self.notes_inspector.set_note(None)
                self.tab_widget.setCurrentWidget(self.metadata_panel)
        else:
            # Clear all panels
            self.character_inspector.set_character(None)
            self.location_inspector.set_location(None)
            self.notes_inspector.set_note(None)
    
    def _on_metadata_changed(self, key: str, value: Any):
        """
        Handle metadata changed event.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        if not self.current_document:
            return
        
        logger.debug(f"Metadata changed: {key} = {value}")
        
        # Update document
        if key == "title":
            self.current_document.title = value
        elif key == "synopsis":
            self.current_document.synopsis = value
        elif key == "status":
            self.current_document.status = value
        elif key == "is_included_in_compile":
            self.current_document.is_included_in_compile = value
        elif key == "tags":
            self.current_document.tags = value
        elif key == "color":
            self.current_document.color = value
        elif key.startswith("metadata."):
            # Extract metadata key
            metadata_key = key[len("metadata."):]
            self.current_document.set_metadata(metadata_key, value)
        
        # Save document
        self.document_manager.update_document(self.current_document.id)
    
    def _on_character_changed(self, field: str, value: Any):
        """
        Handle character changed event.
        
        Args:
            field: The character field.
            value: The field value.
        """
        if not self.current_document or not self.character_inspector.character:
            return
        
        logger.debug(f"Character changed: {field} = {value}")
        
        # Update character
        character = self.character_inspector.character
        setattr(character, field, value)
        
        # Update document
        character.to_document(self.current_document)
        
        # Save document
        self.document_manager.update_document(self.current_document.id)
    
    def _on_location_changed(self, field: str, value: Any):
        """
        Handle location changed event.
        
        Args:
            field: The location field.
            value: The field value.
        """
        if not self.current_document or not self.location_inspector.location:
            return
        
        logger.debug(f"Location changed: {field} = {value}")
        
        # Update location
        location = self.location_inspector.location
        setattr(location, field, value)
        
        # Update document
        location.to_document(self.current_document)
        
        # Save document
        self.document_manager.update_document(self.current_document.id)
    
    def _on_note_changed(self, field: str, value: Any):
        """
        Handle note changed event.
        
        Args:
            field: The note field.
            value: The field value.
        """
        if not self.current_document or not self.notes_inspector.note:
            return
        
        logger.debug(f"Note changed: {field} = {value}")
        
        # Update note
        note = self.notes_inspector.note
        setattr(note, field, value)
        
        # Update document
        note.to_document(self.current_document)
        
        # Save document
        self.document_manager.update_document(self.current_document.id)
