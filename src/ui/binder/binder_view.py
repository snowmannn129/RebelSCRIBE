#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Binder View

This module implements the binder (project explorer) view for RebelSCRIBE.
"""

from PyQt6.QtWidgets import (
    QTreeView, QWidget, QVBoxLayout, QMenu, QToolBar,
    QInputDialog, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QModelIndex
from PyQt6.QtGui import QIcon, QKeySequence, QStandardItemModel, QStandardItem, QAction

from src.utils.logging_utils import get_logger
from src.backend.services.project_manager import ProjectManager

logger = get_logger(__name__)


class BinderView(QWidget):
    """
    Binder (project explorer) view for RebelSCRIBE.
    
    This class implements the project explorer tree view that displays the
    project structure and allows navigation through documents, chapters,
    scenes, characters, locations, and notes.
    """
    
    # Signal emitted when an item is selected in the binder
    item_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        """Initialize the binder view."""
        super().__init__(parent)
        
        # Set up project manager
        self.project_manager = ProjectManager()
        
        # Initialize UI components
        self._init_ui()
        
        logger.info("Binder view initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing binder UI components")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        self.layout.addWidget(self.toolbar)
        
        # Add actions to toolbar
        self._create_toolbar_actions()
        
        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.setDropIndicatorShown(True)
        self.tree_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.layout.addWidget(self.tree_view)
        
        # Create model
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        
        # Connect selection changed signal after model is set
        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
        # Create placeholder data
        self._create_placeholder_data()
        
        logger.debug("Binder UI components initialized")
    
    def _create_toolbar_actions(self):
        """Create toolbar actions."""
        logger.debug("Creating toolbar actions")
        
        # Add document action
        self.add_document_action = QAction("Add Document", self)
        self.add_document_action.triggered.connect(self._on_add_document)
        self.toolbar.addAction(self.add_document_action)
        
        # Add folder action
        self.add_folder_action = QAction("Add Folder", self)
        self.add_folder_action.triggered.connect(self._on_add_folder)
        self.toolbar.addAction(self.add_folder_action)
        
        self.toolbar.addSeparator()
        
        # Add character action
        self.add_character_action = QAction("Add Character", self)
        self.add_character_action.triggered.connect(self._on_add_character)
        self.toolbar.addAction(self.add_character_action)
        
        # Add location action
        self.add_location_action = QAction("Add Location", self)
        self.add_location_action.triggered.connect(self._on_add_location)
        self.toolbar.addAction(self.add_location_action)
        
        # Add note action
        self.add_note_action = QAction("Add Note", self)
        self.add_note_action.triggered.connect(self._on_add_note)
        self.toolbar.addAction(self.add_note_action)
        
        logger.debug("Toolbar actions created")
    
    def _create_placeholder_data(self):
        """Create placeholder data for the tree view."""
        logger.debug("Creating placeholder data")
        
        # Clear model
        self.model.clear()
        
        # Create root item
        root_item = self.model.invisibleRootItem()
        
        # Create manuscript item
        manuscript_item = QStandardItem("Manuscript")
        manuscript_item.setData("manuscript_folder", Qt.ItemDataRole.UserRole)  # Store document ID
        root_item.appendRow(manuscript_item)
        
        # Create chapters
        for i in range(1, 4):
            chapter_item = QStandardItem(f"Chapter {i}")
            chapter_item.setData(f"chapter_{i}", Qt.ItemDataRole.UserRole)  # Store document ID
            manuscript_item.appendRow(chapter_item)
            
            # Create scenes
            for j in range(1, 4):
                scene_item = QStandardItem(f"Scene {j}")
                scene_item.setData(f"chapter_{i}_scene_{j}", Qt.ItemDataRole.UserRole)  # Store document ID
                chapter_item.appendRow(scene_item)
        
        # Create characters folder
        characters_item = QStandardItem("Characters")
        characters_item.setData("characters_folder", Qt.ItemDataRole.UserRole)  # Store document ID
        root_item.appendRow(characters_item)
        
        # Create characters
        characters = ["Protagonist", "Antagonist", "Supporting Character"]
        for i, character in enumerate(characters):
            character_item = QStandardItem(character)
            character_item.setData(f"character_{i+1}", Qt.ItemDataRole.UserRole)  # Store document ID
            characters_item.appendRow(character_item)
        
        # Create locations folder
        locations_item = QStandardItem("Locations")
        locations_item.setData("locations_folder", Qt.ItemDataRole.UserRole)  # Store document ID
        root_item.appendRow(locations_item)
        
        # Create locations
        locations = ["Main Setting", "Secondary Location", "Final Showdown"]
        for i, location in enumerate(locations):
            location_item = QStandardItem(location)
            location_item.setData(f"location_{i+1}", Qt.ItemDataRole.UserRole)  # Store document ID
            locations_item.appendRow(location_item)
        
        # Create notes folder
        notes_item = QStandardItem("Notes")
        notes_item.setData("notes_folder", Qt.ItemDataRole.UserRole)  # Store document ID
        root_item.appendRow(notes_item)
        
        # Create notes
        notes = ["Plot Ideas", "Research", "To-Do"]
        for i, note in enumerate(notes):
            note_item = QStandardItem(note)
            note_item.setData(f"note_{i+1}", Qt.ItemDataRole.UserRole)  # Store document ID
            notes_item.appendRow(note_item)
        
        # Expand manuscript item
        self.tree_view.expand(self.model.indexFromItem(manuscript_item))
        
        logger.debug("Placeholder data created")
    
    def load_project(self, project):
        """
        Load a project into the binder view.
        
        Args:
            project: The project to load.
        """
        logger.info(f"Loading project: {project.title if project else 'None'}")
        
        if project is None:
            # Clear the model
            self.model.clear()
            return
        
        # Clear model
        self.model.clear()
        
        # Set the current project in the project manager
        self.project_manager.current_project = project
        
        # Ensure documents are loaded before getting the document tree
        if hasattr(self.project_manager, 'documents') and not self.project_manager.documents:
            self.project_manager._load_documents()
        
        # Get document tree from project manager
        document_tree = self.project_manager.get_document_tree()
        
        if not document_tree:
            # If no document tree is available, use placeholder data
            logger.warning("No document tree available, using placeholder data")
            self._create_placeholder_data()
            return
        
        # Create root item
        root_item = self.model.invisibleRootItem()
        
        # Build tree from document tree
        for node in document_tree:
            item = self._create_tree_item(node)
            root_item.appendRow(item)
        
        # Expand top-level items
        for i in range(self.model.rowCount()):
            index = self.model.index(i, 0)
            self.tree_view.expand(index)
        
        logger.info(f"Project loaded: {project.title}")
    
    def _create_tree_item(self, node):
        """
        Create a tree item from a document tree node.
        
        Args:
            node: The document tree node.
            
        Returns:
            The created QStandardItem.
        """
        # Create item
        item = QStandardItem(node["title"])
        
        # Set document ID
        item.setData(node["id"], Qt.ItemDataRole.UserRole)
        
        # Add children
        for child_node in node["children"]:
            child_item = self._create_tree_item(child_node)
            item.appendRow(child_item)
        
        return item
    
    def _show_context_menu(self, position):
        """
        Show context menu for the selected item.
        
        Args:
            position: The position where the context menu should be shown.
        """
        logger.debug(f"Showing context menu at position: {position}")
        
        # Get the index at the position
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Add actions
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._on_rename_item(index))
        context_menu.addAction(rename_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._on_delete_item(index))
        context_menu.addAction(delete_action)
        
        # Show the context menu
        context_menu.exec(self.tree_view.viewport().mapToGlobal(position))
    
    def _on_selection_changed(self, selected, deselected):
        """
        Handle selection changed event.
        
        Args:
            selected: The selected indexes.
            deselected: The deselected indexes.
        """
        logger.debug("Selection changed")
        
        # Get the selected index
        indexes = selected.indexes()
        if not indexes:
            return
        
        # Get the selected item
        index = indexes[0]
        item = self.model.itemFromIndex(index)
        
        # Emit the item_selected signal
        self.item_selected.emit(item)
    
    def _on_add_document(self):
        """Handle add document action."""
        logger.debug("Add document action triggered")
        
        # Get the selected index
        indexes = self.tree_view.selectedIndexes()
        parent_item = self.model.invisibleRootItem()
        parent_id = None
        
        if indexes:
            # Get the selected item
            index = indexes[0]
            item = self.model.itemFromIndex(index)
            
            # Get parent document ID
            parent_id = item.data(Qt.ItemDataRole.UserRole)
            
            # If the item is a folder, use it as the parent
            parent_item = item
        
        # Show input dialog
        name, ok = QInputDialog.getText(
            self,
            "Add Document",
            "Document name:"
        )
        
        if ok and name:
            # Create document in project manager
            document = self.project_manager.create_document(
                title=name,
                doc_type="scene",  # Default to scene type
                parent_id=parent_id
            )
            
            if document:
                # Create new document item
                document_item = QStandardItem(name)
                document_item.setData(document.id, Qt.ItemDataRole.UserRole)
                parent_item.appendRow(document_item)
                
                # Expand the parent item
                self.tree_view.expand(self.model.indexFromItem(parent_item))
                
                logger.info(f"Document created: {name}")
            else:
                logger.error(f"Failed to create document: {name}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create document: {name}"
                )
    
    def _on_add_folder(self):
        """Handle add folder action."""
        logger.debug("Add folder action triggered")
        
        # Get the selected index
        indexes = self.tree_view.selectedIndexes()
        parent_item = self.model.invisibleRootItem()
        parent_id = None
        
        if indexes:
            # Get the selected item
            index = indexes[0]
            item = self.model.itemFromIndex(index)
            
            # Get parent document ID
            parent_id = item.data(Qt.ItemDataRole.UserRole)
            
            # If the item is a folder, use it as the parent
            parent_item = item
        
        # Show input dialog
        name, ok = QInputDialog.getText(
            self,
            "Add Folder",
            "Folder name:"
        )
        
        if ok and name:
            # Create folder in project manager
            document = self.project_manager.create_document(
                title=name,
                doc_type="folder",  # Folder type
                parent_id=parent_id
            )
            
            if document:
                # Create new folder item
                folder_item = QStandardItem(name)
                folder_item.setData(document.id, Qt.ItemDataRole.UserRole)
                parent_item.appendRow(folder_item)
                
                # Expand the parent item
                self.tree_view.expand(self.model.indexFromItem(parent_item))
                
                logger.info(f"Folder created: {name}")
            else:
                logger.error(f"Failed to create folder: {name}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create folder: {name}"
                )
    
    def _on_add_character(self):
        """Handle add character action."""
        logger.debug("Add character action triggered")
        
        # Find the characters folder
        characters_item = None
        characters_folder_id = None
        
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.text() == "Characters":
                characters_item = item
                characters_folder_id = item.data(Qt.ItemDataRole.UserRole)
                break
        
        # If the characters folder doesn't exist, create it
        if characters_item is None:
            # Create folder in project manager
            folder_document = self.project_manager.create_document(
                title="Characters",
                doc_type="folder"
            )
            
            if folder_document:
                characters_item = QStandardItem("Characters")
                characters_item.setData(folder_document.id, Qt.ItemDataRole.UserRole)
                self.model.appendRow(characters_item)
                characters_folder_id = folder_document.id
            else:
                logger.error("Failed to create Characters folder")
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to create Characters folder"
                )
                return
        
        # Show input dialog
        name, ok = QInputDialog.getText(
            self,
            "Add Character",
            "Character name:"
        )
        
        if ok and name:
            # Create character in project manager
            document = self.project_manager.create_document(
                title=name,
                doc_type="character",  # Character type
                parent_id=characters_folder_id
            )
            
            if document:
                # Create new character item
                character_item = QStandardItem(name)
                character_item.setData(document.id, Qt.ItemDataRole.UserRole)
                characters_item.appendRow(character_item)
                
                # Expand the characters folder
                self.tree_view.expand(self.model.indexFromItem(characters_item))
                
                logger.info(f"Character created: {name}")
            else:
                logger.error(f"Failed to create character: {name}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create character: {name}"
                )
    
    def _on_add_location(self):
        """Handle add location action."""
        logger.debug("Add location action triggered")
        
        # Find the locations folder
        locations_item = None
        locations_folder_id = None
        
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.text() == "Locations":
                locations_item = item
                locations_folder_id = item.data(Qt.ItemDataRole.UserRole)
                break
        
        # If the locations folder doesn't exist, create it
        if locations_item is None:
            # Create folder in project manager
            folder_document = self.project_manager.create_document(
                title="Locations",
                doc_type="folder"
            )
            
            if folder_document:
                locations_item = QStandardItem("Locations")
                locations_item.setData(folder_document.id, Qt.ItemDataRole.UserRole)
                self.model.appendRow(locations_item)
                locations_folder_id = folder_document.id
            else:
                logger.error("Failed to create Locations folder")
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to create Locations folder"
                )
                return
        
        # Show input dialog
        name, ok = QInputDialog.getText(
            self,
            "Add Location",
            "Location name:"
        )
        
        if ok and name:
            # Create location in project manager
            document = self.project_manager.create_document(
                title=name,
                doc_type="location",  # Location type
                parent_id=locations_folder_id
            )
            
            if document:
                # Create new location item
                location_item = QStandardItem(name)
                location_item.setData(document.id, Qt.ItemDataRole.UserRole)
                locations_item.appendRow(location_item)
                
                # Expand the locations folder
                self.tree_view.expand(self.model.indexFromItem(locations_item))
                
                logger.info(f"Location created: {name}")
            else:
                logger.error(f"Failed to create location: {name}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create location: {name}"
                )
    
    def _on_add_note(self):
        """Handle add note action."""
        logger.debug("Add note action triggered")
        
        # Find the notes folder
        notes_item = None
        notes_folder_id = None
        
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.text() == "Notes":
                notes_item = item
                notes_folder_id = item.data(Qt.ItemDataRole.UserRole)
                break
        
        # If the notes folder doesn't exist, create it
        if notes_item is None:
            # Create folder in project manager
            folder_document = self.project_manager.create_document(
                title="Notes",
                doc_type="folder"
            )
            
            if folder_document:
                notes_item = QStandardItem("Notes")
                notes_item.setData(folder_document.id, Qt.ItemDataRole.UserRole)
                self.model.appendRow(notes_item)
                notes_folder_id = folder_document.id
            else:
                logger.error("Failed to create Notes folder")
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to create Notes folder"
                )
                return
        
        # Show input dialog
        name, ok = QInputDialog.getText(
            self,
            "Add Note",
            "Note name:"
        )
        
        if ok and name:
            # Create note in project manager
            document = self.project_manager.create_document(
                title=name,
                doc_type="note",  # Note type
                parent_id=notes_folder_id
            )
            
            if document:
                # Create new note item
                note_item = QStandardItem(name)
                note_item.setData(document.id, Qt.ItemDataRole.UserRole)
                notes_item.appendRow(note_item)
                
                # Expand the notes folder
                self.tree_view.expand(self.model.indexFromItem(notes_item))
                
                logger.info(f"Note created: {name}")
            else:
                logger.error(f"Failed to create note: {name}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create note: {name}"
                )
    
    def _on_rename_item(self, index):
        """
        Handle rename item action.
        
        Args:
            index: The index of the item to rename.
        """
        logger.debug(f"Rename item action triggered for index: {index}")
        
        # Get the item
        item = self.model.itemFromIndex(index)
        
        # Get document ID
        document_id = item.data(Qt.ItemDataRole.UserRole)
        if not document_id:
            logger.warning("No document ID found for item")
            return
        
        # Show input dialog
        name, ok = QInputDialog.getText(
            self,
            "Rename Item",
            "New name:",
            text=item.text()
        )
        
        if ok and name:
            # Rename document in project manager
            success = self.project_manager.rename_document(document_id, name)
            
            if success:
                # Rename the item in the tree view
                item.setText(name)
                logger.info(f"Document renamed: {name}")
            else:
                logger.error(f"Failed to rename document: {name}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to rename document: {name}"
                )
    
    def _on_delete_item(self, index):
        """
        Handle delete item action.
        
        Args:
            index: The index of the item to delete.
        """
        logger.debug(f"Delete item action triggered for index: {index}")
        
        # Get the item
        item = self.model.itemFromIndex(index)
        
        # Get document ID
        document_id = item.data(Qt.ItemDataRole.UserRole)
        if not document_id:
            logger.warning("No document ID found for item")
            return
        
        # Show confirmation dialog
        result = QMessageBox.question(
            self,
            "Delete Item",
            f"Are you sure you want to delete '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Delete document in project manager
            success = self.project_manager.delete_document(document_id)
            
            if success:
                # Delete the item from the tree view
                parent = item.parent() or self.model.invisibleRootItem()
                parent.removeRow(index.row())
                logger.info(f"Document deleted: {item.text()}")
            else:
                logger.error(f"Failed to delete document: {item.text()}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete document: {item.text()}"
                )
