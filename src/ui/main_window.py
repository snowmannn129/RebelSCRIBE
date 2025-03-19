#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Main Application Window

This module implements the main application window for RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QToolBar,
    QStatusBar, QFileDialog, QMessageBox, QSplitter, QWidget,
    QVBoxLayout, QHBoxLayout, QInputDialog
)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QIcon, QKeySequence, QAction

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager

# Import UI components
from src.ui.binder import BinderView
from src.ui.editor.editor_view import EditorView
from src.ui.inspector.inspector_view import InspectorView
from src.ui.distraction_free_mode import DistractionFreeMode
from src.ui.theme_manager import ThemeManager
from src.ui.theme_settings_dialog import ThemeSettingsDialog
from src.ui.event_bus import get_event_bus
from src.ui.state_manager import get_state_manager
from src.ui.error_handler_integration import get_integrated_error_handler as get_error_handler

# Import backend services
from src.backend.services.project_manager import ProjectManager
from src.backend.services.document_manager import DocumentManager
from src.backend.services.search_service import SearchService
from src.backend.services.statistics_service import StatisticsService
from src.backend.services.export_service import ExportService

# Import dialogs
from src.ui.project_settings_dialog import ProjectSettingsDialog
from src.ui.export_dialog import ExportDialog
from src.ui.ai_settings_dialog import AISettingsDialog

logger = get_logger(__name__)
config = ConfigManager()


class MainWindow(QMainWindow):
    """
    Main application window for RebelSCRIBE.
    
    This class implements the main UI window that contains all the components
    of the application, including the binder (project explorer), editor, and
    inspector panels.
    """
    
    def __init__(self):
        """Initialize the main window."""
        # Initialize QApplication first
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("RebelSCRIBE")
        self.app.setOrganizationName("RebelSCRIBE")
        
        # Initialize main window
        super().__init__()
        
        # Set up window properties
        self.setWindowTitle("RebelSCRIBE")
        self.setMinimumSize(1024, 768)
        
        # Initialize backend services
        self.project_manager = ProjectManager()
        self.document_manager = DocumentManager()
        self.search_service = SearchService()
        self.statistics_service = StatisticsService()
        self.export_service = ExportService()
        
        # Current project
        self.current_project = None
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Get event bus, state manager, and error handler instances
        self.event_bus = get_event_bus()
        self.state_manager = get_state_manager()
        self.error_handler = get_error_handler(self)
        
        # Initialize UI components
        self._init_ui()
        
        # Connect event bus signals
        self._connect_event_bus_signals()
        
        # Load settings
        self._load_settings()
        
        # Apply theme
        self.theme_manager.apply_theme(self.app)
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing UI components")
        
        # Create central widget with splitter
        self.central_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.central_splitter)
        
        # Create binder view
        self.binder_view = BinderView(self)
        
        # Create editor view
        self.editor = EditorView(self)
        
        # Create inspector view
        self.inspector = InspectorView(self)
        
        # Add components to splitter
        self.central_splitter.addWidget(self.binder_view)
        self.central_splitter.addWidget(self.editor)
        self.central_splitter.addWidget(self.inspector)
        
        # Set initial splitter sizes (30% binder, 40% editor, 30% inspector)
        self.central_splitter.setSizes([300, 400, 300])
        
        # Create menus
        self._create_menus()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect signals
        self.binder_view.item_selected.connect(self._on_binder_item_selected)
        
        logger.debug("UI components initialized")
    
    def _create_menus(self):
        """Create the application menus."""
        logger.debug("Creating menus")
        
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        
        # New project action
        new_project_action = QAction("&New Project...", self)
        new_project_action.setShortcut(QKeySequence.StandardKey.New)
        new_project_action.triggered.connect(self._on_new_project)
        self.file_menu.addAction(new_project_action)
        
        # Open project action
        open_project_action = QAction("&Open Project...", self)
        open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        open_project_action.triggered.connect(self._on_open_project)
        self.file_menu.addAction(open_project_action)
        
        self.file_menu.addSeparator()
        
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        self.file_menu.addAction(save_action)
        
        # Save as action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        self.file_menu.addAction(save_as_action)
        
        self.file_menu.addSeparator()
        
        # Export action
        export_action = QAction("&Export...", self)
        export_action.triggered.connect(self._on_export)
        self.file_menu.addAction(export_action)
        
        self.file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
        # Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")
        
        # Undo action
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._on_undo)
        self.edit_menu.addAction(undo_action)
        
        # Redo action
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._on_redo)
        self.edit_menu.addAction(redo_action)
        
        self.edit_menu.addSeparator()
        
        # Cut action
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self._on_cut)
        self.edit_menu.addAction(cut_action)
        
        # Copy action
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._on_copy)
        self.edit_menu.addAction(copy_action)
        
        # Paste action
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._on_paste)
        self.edit_menu.addAction(paste_action)
        
        self.edit_menu.addSeparator()
        
        # Find action
        find_action = QAction("&Find...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self._on_find)
        self.edit_menu.addAction(find_action)
        
        # Replace action
        replace_action = QAction("&Replace...", self)
        replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        replace_action.triggered.connect(self._on_replace)
        self.edit_menu.addAction(replace_action)
        
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        
        # Toggle binder action
        self.toggle_binder_action = QAction("Show &Binder", self)
        self.toggle_binder_action.setCheckable(True)
        self.toggle_binder_action.setChecked(True)
        self.toggle_binder_action.triggered.connect(self._on_toggle_binder)
        self.view_menu.addAction(self.toggle_binder_action)
        
        # Toggle inspector action
        self.toggle_inspector_action = QAction("Show &Inspector", self)
        self.toggle_inspector_action.setCheckable(True)
        self.toggle_inspector_action.setChecked(True)
        self.toggle_inspector_action.triggered.connect(self._on_toggle_inspector)
        self.view_menu.addAction(self.toggle_inspector_action)
        
        self.view_menu.addSeparator()
        
        # Distraction free mode action
        distraction_free_action = QAction("&Distraction Free Mode", self)
        distraction_free_action.setShortcut("F11")
        distraction_free_action.triggered.connect(self._on_distraction_free)
        self.view_menu.addAction(distraction_free_action)
        
        self.view_menu.addSeparator()
        
        # Theme settings action
        theme_settings_action = QAction("&Theme Settings...", self)
        theme_settings_action.triggered.connect(self._on_theme_settings)
        self.view_menu.addAction(theme_settings_action)
        
        # Project menu
        self.project_menu = self.menuBar().addMenu("&Project")
        
        # Project settings action
        project_settings_action = QAction("&Settings...", self)
        project_settings_action.triggered.connect(self._on_project_settings)
        self.project_menu.addAction(project_settings_action)
        
        # Statistics action
        statistics_action = QAction("St&atistics...", self)
        statistics_action.triggered.connect(self._on_statistics)
        self.project_menu.addAction(statistics_action)
        
        # AI menu
        self.ai_menu = self.menuBar().addMenu("&AI")
        
        # Generate text action
        generate_text_action = QAction("&Generate Text...", self)
        generate_text_action.triggered.connect(self._on_generate_text)
        self.ai_menu.addAction(generate_text_action)
        
        # Character development action
        character_dev_action = QAction("&Character Development...", self)
        character_dev_action.triggered.connect(self._on_character_development)
        self.ai_menu.addAction(character_dev_action)
        
        # Plot development action
        plot_dev_action = QAction("&Plot Development...", self)
        plot_dev_action.triggered.connect(self._on_plot_development)
        self.ai_menu.addAction(plot_dev_action)
        
        self.ai_menu.addSeparator()
        
        # Model benchmarking action
        model_benchmark_action = QAction("Model &Benchmarking...", self)
        model_benchmark_action.triggered.connect(self._on_model_benchmarking)
        self.ai_menu.addAction(model_benchmark_action)
        
        # Batch benchmarking action
        batch_benchmark_action = QAction("&Batch Benchmarking...", self)
        batch_benchmark_action.triggered.connect(self._on_batch_benchmarking)
        self.ai_menu.addAction(batch_benchmark_action)
        
        # Model fine-tuning action
        model_finetuning_action = QAction("Model &Fine-tuning...", self)
        model_finetuning_action.triggered.connect(self._on_model_finetuning)
        self.ai_menu.addAction(model_finetuning_action)
        
        self.ai_menu.addSeparator()
        
        # AI settings action
        ai_settings_action = QAction("&Settings...", self)
        ai_settings_action.triggered.connect(self._on_ai_settings)
        self.ai_menu.addAction(ai_settings_action)
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QAction("&About RebelSCRIBE", self)
        about_action.triggered.connect(self._on_about)
        self.help_menu.addAction(about_action)
        
        logger.debug("Menus created")
    
    def _create_toolbar(self):
        """Create the application toolbar."""
        logger.debug("Creating toolbar")
        
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("mainToolbar")  # Set object name for state saving
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)
        
        # New project action
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self._on_new_project)
        self.toolbar.addAction(new_project_action)
        
        # Open project action
        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(self._on_open_project)
        self.toolbar.addAction(open_project_action)
        
        # Save action
        save_action = QAction("Save", self)
        save_action.triggered.connect(self._on_save)
        self.toolbar.addAction(save_action)
        
        self.toolbar.addSeparator()
        
        # Cut action
        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(self._on_cut)
        self.toolbar.addAction(cut_action)
        
        # Copy action
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self._on_copy)
        self.toolbar.addAction(copy_action)
        
        # Paste action
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self._on_paste)
        self.toolbar.addAction(paste_action)
        
        self.toolbar.addSeparator()
        
        # Find action
        find_action = QAction("Find", self)
        find_action.triggered.connect(self._on_find)
        self.toolbar.addAction(find_action)
        
        logger.debug("Toolbar created")
    
    def _load_settings(self):
        """Load application settings."""
        logger.debug("Loading settings")
        
        settings = QSettings()
        
        # Load window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
        
        # Load splitter sizes
        splitter_sizes = settings.value("splitterSizes")
        if splitter_sizes:
            # Convert string values to integers
            int_sizes = [int(size) for size in splitter_sizes]
            self.central_splitter.setSizes(int_sizes)
        
        logger.debug("Settings loaded")
    
    def _save_settings(self):
        """Save application settings."""
        logger.debug("Saving settings")
        
        settings = QSettings()
        
        # Save window geometry
        settings.setValue("geometry", self.saveGeometry())
        
        # Save window state
        settings.setValue("windowState", self.saveState())
        
        # Save splitter sizes
        settings.setValue("splitterSizes", self.central_splitter.sizes())
        
        logger.debug("Settings saved")
    
    def run(self):
        """Run the application."""
        logger.info("Starting application main loop")
        self.show()
        return self.app.exec()
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.debug("Close event triggered")
        
        # Check for unsaved changes
        # This will be implemented later
        
        # Save settings
        self._save_settings()
        
        # Accept the close event
        event.accept()
    
    # Event handlers
    
    def _on_binder_item_selected(self, item):
        """
        Handle binder item selection.
        
        Args:
            item: The selected item.
        """
        logger.debug(f"Binder item selected: {item.text() if item else 'None'}")
        
        # Clear editor and inspector if no item is selected
        if not item:
            # Clear editor
            if hasattr(self, 'editor') and self.editor:
                self.editor.set_content("")
                self.editor.current_document = None
                self.editor.last_saved_content = ""
                self.editor._update_status_bar()
            
            # Clear inspector
            if hasattr(self, 'inspector') and self.inspector:
                self.inspector.set_document(None)
            
            self.status_bar.showMessage("No item selected", 3000)
            return
        
        # Update status bar
        self.status_bar.showMessage(f"Selected: {item.text()}", 3000)
        
        # Get document ID from item data
        document_id = item.data(Qt.ItemDataRole.UserRole)
        if not document_id:
            logger.warning(f"No document ID found for item: {item.text()}")
            self.status_bar.showMessage(f"No document ID found for item: {item.text()}", 3000)
            return
        
        # Emit document selected event
        self.event_bus.emit_document_selected(document_id)
    
    def _on_new_project(self):
        """Handle new project action."""
        logger.debug("New project action triggered")
        
        # Show dialog to get project details
        title, ok = QInputDialog.getText(
            self,
            "New Project",
            "Project title:"
        )
        
        if ok and title:
            # Get author
            author, ok = QInputDialog.getText(
                self,
                "New Project",
                "Author name:",
                text=config.get("user", "name", "")
            )
            
            if not ok:
                return
            
            # Get template
            templates = ["novel", "short_story", "screenplay", "empty"]
            template, ok = QInputDialog.getItem(
                self,
                "New Project",
                "Project template:",
                templates,
                0,
                False
            )
            
            if not ok:
                return
            
            # Get save path
            default_dir = config.get("application", "projects_directory", "")
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Project",
                default_dir,
                f"RebelSCRIBE Projects (*{self.project_manager.PROJECT_FILE_EXTENSION})"
            )
            
            if not save_path:
                return
            
            # Add extension if not present
            if not save_path.endswith(self.project_manager.PROJECT_FILE_EXTENSION):
                save_path += self.project_manager.PROJECT_FILE_EXTENSION
            
            # Create project
            project = self.project_manager.create_project(
                title=title,
                author=author,
                template=template,
                path=save_path
            )
            
            if project:
                # Set current project
                self.current_project = project
                
                # Update document manager with project path
                project_dir = os.path.dirname(save_path)
                self.document_manager.set_project_path(project_dir)
                
                # Load documents
                self.document_manager.load_all_documents()
                
                # Update binder view
                self.binder_view.load_project(project)
                
                # Update window title
                self.setWindowTitle(f"RebelSCRIBE - {project.title}")
                
                # Update status bar
                self.status_bar.showMessage(f"Created new project: {project.title}", 3000)
            else:
                # Show error message
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create project: {title}"
                )
    
    def _on_open_project(self):
        """Handle open project action."""
        logger.debug("Open project action triggered")
        
        # Get default directory
        default_dir = config.get("application", "projects_directory", "")
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            default_dir,
            f"RebelSCRIBE Projects (*{self.project_manager.PROJECT_FILE_EXTENSION})"
        )
        
        if not file_path:
            return
        
        # Close current project if any
        if self.current_project:
            # Check for unsaved changes
            # This will be implemented later
            
            # Close project
            self.project_manager.close_project()
            self.current_project = None
        
        # Load project
        project = self.project_manager.load_project(file_path)
        
        if project:
            # Set current project
            self.current_project = project
            
            # Update document manager with project path
            project_dir = os.path.dirname(file_path)
            self.document_manager.set_project_path(project_dir)
            
            # Create documents directory if it doesn't exist
            documents_dir = os.path.join(project_dir, "documents")
            if not os.path.exists(documents_dir):
                os.makedirs(documents_dir)
            
            # Load documents
            documents = self.document_manager.load_all_documents()
            logger.info(f"Loaded {len(documents)} documents")
            
            # Update binder view
            self.binder_view.load_project(project)
            
            # Update window title
            self.setWindowTitle(f"RebelSCRIBE - {project.title}")
            
            # Update status bar
            self.status_bar.showMessage(f"Opened project: {project.title}", 3000)
        else:
            # Show error message
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open project: {file_path}"
            )
    
    def _on_save(self):
        """Handle save action."""
        logger.debug("Save action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to save")
            self.status_bar.showMessage("No project to save", 3000)
            return
        
        # Save project
        success = self.project_manager.save_project()
        
        # Save all documents
        doc_success = self.document_manager.save_all_documents()
        
        if success and doc_success:
            self.status_bar.showMessage(f"Project saved: {self.current_project.title}", 3000)
        else:
            # Show error message
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save project: {self.current_project.title}"
            )
    
    def _on_save_as(self):
        """Handle save as action."""
        logger.debug("Save as action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to save")
            self.status_bar.showMessage("No project to save", 3000)
            return
        
        # Get default directory
        default_dir = os.path.dirname(self.project_manager.get_project_path())
        
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            default_dir,
            f"RebelSCRIBE Projects (*{self.project_manager.PROJECT_FILE_EXTENSION})"
        )
        
        if not file_path:
            return
        
        # Add extension if not present
        if not file_path.endswith(self.project_manager.PROJECT_FILE_EXTENSION):
            file_path += self.project_manager.PROJECT_FILE_EXTENSION
        
        # Save project
        success = self.project_manager.save_project_as(file_path)
        
        # Update document manager
        if success:
            self.document_manager.set_project_path(os.path.dirname(file_path))
            
            # Save all documents
            doc_success = self.document_manager.save_all_documents()
            
            if doc_success:
                # Update window title
                self.setWindowTitle(f"RebelSCRIBE - {self.current_project.title}")
                
                # Update status bar
                self.status_bar.showMessage(f"Project saved as: {file_path}", 3000)
            else:
                # Show error message
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save documents for project: {self.current_project.title}"
                )
        else:
            # Show error message
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save project as: {file_path}"
            )
    
    def _on_export(self):
        """Handle export action."""
        logger.debug("Export action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to export")
            self.status_bar.showMessage("No project to export", 3000)
            return
        
        # Create export dialog
        export_dialog = ExportDialog(self, self.current_project)
        
        # Connect signals
        export_dialog.export_completed.connect(self._on_export_completed)
        
        # Show dialog
        export_dialog.exec()
    
    def _on_export_completed(self, success: bool, export_path: str, format_name: str):
        """
        Handle export completed event.
        
        Args:
            success: Whether the export was successful.
            export_path: The path to the exported file.
            format_name: The name of the export format.
        """
        if success:
            self.status_bar.showMessage(f"Project exported to {format_name} format: {export_path}", 5000)
        else:
            self.status_bar.showMessage(f"Failed to export project to {format_name} format", 5000)
    
    def _on_undo(self):
        """Handle undo action."""
        logger.debug("Undo action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor.text_edit.undo()
            self.status_bar.showMessage("Undo", 3000)
    
    def _on_redo(self):
        """Handle redo action."""
        logger.debug("Redo action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor.text_edit.redo()
            self.status_bar.showMessage("Redo", 3000)
    
    def _on_cut(self):
        """Handle cut action."""
        logger.debug("Cut action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor.text_edit.cut()
            self.status_bar.showMessage("Cut", 3000)
    
    def _on_copy(self):
        """Handle copy action."""
        logger.debug("Copy action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor.text_edit.copy()
            self.status_bar.showMessage("Copy", 3000)
    
    def _on_paste(self):
        """Handle paste action."""
        logger.debug("Paste action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor.text_edit.paste()
            self.status_bar.showMessage("Paste", 3000)
    
    def _on_find(self):
        """Handle find action."""
        logger.debug("Find action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor._show_find_replace_dialog()
            self.status_bar.showMessage("Find", 3000)
    
    def _on_replace(self):
        """Handle replace action."""
        logger.debug("Replace action triggered")
        
        # Forward to editor
        if hasattr(self, 'editor') and self.editor:
            self.editor._show_find_replace_dialog()
            self.status_bar.showMessage("Replace", 3000)
    
    def _on_toggle_binder(self, checked):
        """Handle toggle binder action."""
        logger.debug(f"Toggle binder action triggered: {checked}")
        
        # Show/hide binder
        self.binder_view.setVisible(checked)
        
        # Update status bar
        self.status_bar.showMessage(f"Binder {'shown' if checked else 'hidden'}", 3000)
    
    def _on_toggle_inspector(self, checked):
        """Handle toggle inspector action."""
        logger.debug(f"Toggle inspector action triggered: {checked}")
        
        # Show/hide inspector
        self.inspector.setVisible(checked)
        
        # Update status bar
        self.status_bar.showMessage(f"Inspector {'shown' if checked else 'hidden'}", 3000)
    
    def _on_distraction_free(self):
        """Handle distraction free mode action."""
        logger.debug("Distraction free mode action triggered")
        
        # Check if editor is available
        if not hasattr(self, 'editor') or not self.editor:
            logger.warning("Cannot enter distraction-free mode: No editor available")
            self.status_bar.showMessage("Cannot enter distraction-free mode: No document open", 3000)
            return
        
        # Get current document content and title
        content = self.editor.get_content()
        document_title = "Untitled"
        if hasattr(self.editor, 'current_document') and self.editor.current_document:
            document_title = self.editor.current_document.title
        
        # Create distraction-free mode window
        self.distraction_free_window = DistractionFreeMode(
            parent=self,
            content=content,
            document_title=document_title
        )
        
        # Connect closed signal
        self.distraction_free_window.closed.connect(self._on_distraction_free_closed)
        
        # Show distraction-free mode window
        self.distraction_free_window.show()
        
        self.status_bar.showMessage("Entered distraction-free mode", 3000)
    
    def _on_distraction_free_closed(self, content: str):
        """
        Handle distraction-free mode window closed.
        
        Args:
            content: The content from the distraction-free mode editor.
        """
        logger.debug("Distraction-free mode window closed")
        
        # Update editor content
        if hasattr(self, 'editor') and self.editor:
            # Check if content has changed
            original_content = self.editor.get_content()
            if content != original_content:
                # Content has changed, update editor
                self.editor.set_content(content)
                
                # Check if we have a current document
                if hasattr(self.editor, 'current_document') and self.editor.current_document:
                    # Check if auto-save is enabled
                    if hasattr(self.editor, 'auto_save_timer') and self.editor.auto_save_timer.isActive():
                        # Auto-save is enabled, save document
                        success = self.editor.save_document()
                        if success:
                            self.status_bar.showMessage("Exited distraction-free mode, document saved", 3000)
                        else:
                            self.status_bar.showMessage("Exited distraction-free mode, failed to save document", 3000)
                    else:
                        # Auto-save is not enabled, ask user if they want to save
                        result = QMessageBox.question(
                            self,
                            "Save Document",
                            "The document has been modified in distraction-free mode. Do you want to save the changes?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if result == QMessageBox.StandardButton.Yes:
                            # User wants to save, save document
                            success = self.editor.save_document()
                            if success:
                                self.status_bar.showMessage("Exited distraction-free mode, document saved", 3000)
                            else:
                                self.status_bar.showMessage("Exited distraction-free mode, failed to save document", 3000)
                        else:
                            # User doesn't want to save
                            self.status_bar.showMessage("Exited distraction-free mode, changes not saved", 3000)
                else:
                    # No current document, just update status bar
                    self.status_bar.showMessage("Exited distraction-free mode", 3000)
            else:
                # Content hasn't changed, just update status bar
                self.status_bar.showMessage("Exited distraction-free mode", 3000)
    
    def _on_project_settings(self):
        """Handle project settings action."""
        logger.debug("Project settings action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to configure")
            self.status_bar.showMessage("No project to configure", 3000)
            return
        
        # Create project settings dialog
        settings_dialog = ProjectSettingsDialog(self, self.current_project)
        
        # Show dialog
        if settings_dialog.exec():
            # Update project
            self.project_manager.save_project()
            self.status_bar.showMessage("Project settings updated", 3000)
    
    def _on_statistics(self):
        """Handle statistics action."""
        logger.debug("Statistics action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to show statistics for")
            self.status_bar.showMessage("No project to show statistics for", 3000)
            return
        
        # Get statistics
        stats = self.statistics_service.get_project_statistics(self.current_project.id)
        
        if stats:
            # Create message
            message = f"Project Statistics for {self.current_project.title}:\n\n"
            message += f"Total Word Count: {stats['total_word_count']}\n"
            message += f"Total Character Count: {stats['total_character_count']}\n"
            message += f"Document Count: {stats['document_count']}\n"
            message += f"Average Words per Document: {stats['avg_words_per_document']:.1f}\n"
            
            if 'writing_sessions' in stats and stats['writing_sessions']:
                message += f"\nWriting Sessions: {stats['writing_sessions']}\n"
                message += f"Total Writing Time: {stats['total_writing_time']} minutes\n"
                message += f"Average Words per Minute: {stats['avg_words_per_minute']:.1f}\n"
            
            # Show message box
            QMessageBox.information(
                self,
                "Project Statistics",
                message
            )
        else:
            # Show error message
            QMessageBox.warning(
                self,
                "Statistics",
                "Failed to retrieve project statistics"
            )
    
    def _on_generate_text(self):
        """Handle generate text action."""
        logger.debug("Generate text action triggered")
        
        # Check if editor is available
        if not hasattr(self, 'editor') or not self.editor:
            logger.warning("Cannot generate text: No editor available")
            self.status_bar.showMessage("Cannot generate text: No document open", 3000)
            return
        
        # Get current document content
        content = self.editor.get_content()
        
        # Get current document title
        document_title = "Untitled"
        if hasattr(self.editor, 'current_document') and self.editor.current_document:
            document_title = self.editor.current_document.title
        
        # Import AI service
        from src.ai.ai_service import AIService
        from src.ai.text_generator import TextGenerator
        
        # Create AI service
        ai_service = AIService()
        text_generator = TextGenerator(ai_service)
        
        # Get prompt from user
        prompt, ok = QInputDialog.getText(
            self,
            "Generate Text",
            "Enter a prompt for text generation:",
            text="Continue the story"
        )
        
        if not ok or not prompt:
            return
        
        # Show status message
        self.status_bar.showMessage("Generating text...", 0)
        
        try:
            # Generate text
            generated_text = text_generator.generate_text(content, prompt)
            
            if generated_text:
                # Insert generated text at cursor position
                cursor = self.editor.text_edit.textCursor()
                cursor.insertText(generated_text)
                
                # Update status bar
                self.status_bar.showMessage("Text generated successfully", 3000)
            else:
                # Show error message
                QMessageBox.warning(
                    self,
                    "Text Generation",
                    "Failed to generate text. Please try again with a different prompt."
                )
                self.status_bar.showMessage("Text generation failed", 3000)
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Text Generation Error",
                f"An error occurred during text generation: {str(e)}"
            )
            self.status_bar.showMessage("Text generation error", 3000)
    
    def _on_character_development(self):
        """Handle character development action."""
        logger.debug("Character development action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to develop characters for")
            self.status_bar.showMessage("No project to develop characters for", 3000)
            return
        
        # Import AI service
        from src.ai.ai_service import AIService
        from src.ai.character_assistant import CharacterAssistant
        
        # Create AI service
        ai_service = AIService()
        character_assistant = CharacterAssistant(ai_service)
        
        # Get character name from user
        character_name, ok = QInputDialog.getText(
            self,
            "Character Development",
            "Enter character name:",
        )
        
        if not ok or not character_name:
            return
        
        # Show status message
        self.status_bar.showMessage("Generating character profile...", 0)
        
        try:
            # Generate character profile
            character_profile = character_assistant.generate_character_profile(character_name)
            
            if character_profile:
                # Create a new character document
                document = self.document_manager.create_document(
                    title=character_name,
                    content=character_profile,
                    doc_type="character"
                )
                
                if document:
                    # Find the characters folder
                    characters_folder = None
                    for i in range(self.binder_view.model.rowCount()):
                        item = self.binder_view.model.item(i)
                        if item.text() == "Characters":
                            characters_folder = item
                            break
                    
                    # If the characters folder doesn't exist, create it
                    if not characters_folder:
                        # Create folder in project manager
                        folder_document = self.project_manager.create_document(
                            title="Characters",
                            doc_type="folder"
                        )
                        
                        if folder_document:
                            characters_folder = QStandardItem("Characters")
                            characters_folder.setData(folder_document.id, Qt.ItemDataRole.UserRole)
                            self.binder_view.model.appendRow(characters_folder)
                    
                    # Add character to characters folder
                    if characters_folder:
                        character_item = QStandardItem(character_name)
                        character_item.setData(document.id, Qt.ItemDataRole.UserRole)
                        characters_folder.appendRow(character_item)
                        
                        # Expand the characters folder
                        self.binder_view.tree_view.expand(self.binder_view.model.indexFromItem(characters_folder))
                        
                        # Select the new character
                        index = self.binder_view.model.indexFromItem(character_item)
                        self.binder_view.tree_view.setCurrentIndex(index)
                        
                        # Update status bar
                        self.status_bar.showMessage(f"Character profile generated for {character_name}", 3000)
                    else:
                        # Show error message
                        QMessageBox.warning(
                            self,
                            "Character Development",
                            f"Failed to add character to binder: {character_name}"
                        )
                else:
                    # Show error message
                    QMessageBox.warning(
                        self,
                        "Character Development",
                        f"Failed to create character document: {character_name}"
                    )
            else:
                # Show error message
                QMessageBox.warning(
                    self,
                    "Character Development",
                    "Failed to generate character profile. Please try again with a different name."
                )
                self.status_bar.showMessage("Character profile generation failed", 3000)
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Character Development Error",
                f"An error occurred during character profile generation: {str(e)}"
            )
            self.status_bar.showMessage("Character profile generation error", 3000)
    
    def _on_plot_development(self):
        """Handle plot development action."""
        logger.debug("Plot development action triggered")
        
        # Check if a project is open
        if not self.current_project:
            logger.warning("No project to develop plot for")
            self.status_bar.showMessage("No project to develop plot for", 3000)
            return
        
        # Import AI service
        from src.ai.ai_service import AIService
        from src.ai.plot_assistant import PlotAssistant
        
        # Create AI service
        ai_service = AIService()
        plot_assistant = PlotAssistant(ai_service)
        
        # Get plot premise from user
        premise, ok = QInputDialog.getText(
            self,
            "Plot Development",
            "Enter plot premise:",
            text="A story about"
        )
        
        if not ok or not premise:
            return
        
        # Show status message
        self.status_bar.showMessage("Generating plot outline...", 0)
        
        try:
            # Generate plot outline
            plot_outline = plot_assistant.generate_plot_outline(premise)
            
            if plot_outline:
                # Create a new note document
                document = self.document_manager.create_document(
                    title=f"Plot Outline: {premise[:30]}...",
                    content=plot_outline,
                    doc_type="note"
                )
                
                if document:
                    # Find the notes folder
                    notes_folder = None
                    for i in range(self.binder_view.model.rowCount()):
                        item = self.binder_view.model.item(i)
                        if item.text() == "Notes":
                            notes_folder = item
                            break
                    
                    # If the notes folder doesn't exist, create it
                    if not notes_folder:
                        # Create folder in project manager
                        folder_document = self.project_manager.create_document(
                            title="Notes",
                            doc_type="folder"
                        )
                        
                        if folder_document:
                            notes_folder = QStandardItem("Notes")
                            notes_folder.setData(folder_document.id, Qt.ItemDataRole.UserRole)
                            self.binder_view.model.appendRow(notes_folder)
                    
                    # Add note to notes folder
                    if notes_folder:
                        note_item = QStandardItem(f"Plot Outline: {premise[:30]}...")
                        note_item.setData(document.id, Qt.ItemDataRole.UserRole)
                        notes_folder.appendRow(note_item)
                        
                        # Expand the notes folder
                        self.binder_view.tree_view.expand(self.binder_view.model.indexFromItem(notes_folder))
                        
                        # Select the new note
                        index = self.binder_view.model.indexFromItem(note_item)
                        self.binder_view.tree_view.setCurrentIndex(index)
                        
                        # Update status bar
                        self.status_bar.showMessage("Plot outline generated", 3000)
                    else:
                        # Show error message
                        QMessageBox.warning(
                            self,
                            "Plot Development",
                            "Failed to add plot outline to binder"
                        )
                else:
                    # Show error message
                    QMessageBox.warning(
                        self,
                        "Plot Development",
                        "Failed to create plot outline document"
                    )
            else:
                # Show error message
                QMessageBox.warning(
                    self,
                    "Plot Development",
                    "Failed to generate plot outline. Please try again with a different premise."
                )
                self.status_bar.showMessage("Plot outline generation failed", 3000)
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Plot Development Error",
                f"An error occurred during plot outline generation: {str(e)}"
            )
            self.status_bar.showMessage("Plot outline generation error", 3000)
    
    def _on_model_benchmarking(self):
        """Handle model benchmarking action."""
        logger.debug("Model benchmarking action triggered")
        
        # Import benchmark dialog
        from src.ui.benchmark_dialog import BenchmarkDialog
        
        # Create benchmark dialog
        benchmark_dialog = BenchmarkDialog(self)
        
        # Show dialog
        benchmark_dialog.exec()
        
        # Update status bar
        self.status_bar.showMessage("Model benchmarking completed", 3000)
    
    def _on_batch_benchmarking(self):
        """Handle batch benchmarking action."""
        logger.debug("Batch benchmarking action triggered")
        
        # Import batch benchmark dialog
        from src.ui.batch_benchmark_dialog import BatchBenchmarkDialog
        
        # Create batch benchmark dialog
        batch_benchmark_dialog = BatchBenchmarkDialog(self)
        
        # Show dialog
        batch_benchmark_dialog.exec()
        
        # Update status bar
        self.status_bar.showMessage("Batch benchmarking completed", 3000)
    
    def _on_model_finetuning(self):
        """Handle model fine-tuning action."""
        logger.debug("Model fine-tuning action triggered")
        
        # Import adapter configuration dialog
        from src.ui.adapter_config_dialog import AdapterConfigDialog
        
        # Create adapter configuration dialog
        adapter_config_dialog = AdapterConfigDialog(self)
        
        # Show dialog
        if adapter_config_dialog.exec():
            # Update status bar
            self.status_bar.showMessage("Adapter configuration saved", 3000)
    
    def _on_ai_settings(self):
        """Handle AI settings action."""
        logger.debug("AI settings action triggered")
        
        # Create AI settings dialog
        settings_dialog = AISettingsDialog(self)
        
        # Show dialog
        if settings_dialog.exec():
            # Update AI settings
            self.status_bar.showMessage("AI settings updated", 3000)
    
    def _on_theme_settings(self):
        """Handle theme settings action."""
        logger.debug("Theme settings action triggered")
        
        # Create theme settings dialog
        dialog = ThemeSettingsDialog(self)
        
        # Connect theme applied signal
        dialog.theme_applied.connect(self._on_theme_applied)
        
        # Show dialog
        dialog.exec()
    
    def _on_theme_applied(self, theme_name: str):
        """
        Handle theme applied event.
        
        Args:
            theme_name: The name of the applied theme.
        """
        logger.debug(f"Theme applied: {theme_name}")
        
        # Apply theme to application
        self.theme_manager.apply_theme(self.app)
        
        # Apply theme to editor
        if hasattr(self, 'editor') and self.editor:
            self.theme_manager.apply_theme_to_editor(self.editor)
        
        # Update status bar
        self.status_bar.showMessage(f"Theme applied: {theme_name}", 3000)
    
    def _connect_event_bus_signals(self):
        """Connect event bus signals to handlers."""
        logger.debug("Connecting event bus signals")
        
        # Document events
        self.event_bus.document_selected.connect(self._on_document_selected)
        self.event_bus.document_loaded.connect(self._on_document_loaded)
        self.event_bus.document_saved.connect(self._on_document_saved)
        self.event_bus.document_modified.connect(self._on_document_modified)
        self.event_bus.document_created.connect(self._on_document_created)
        self.event_bus.document_deleted.connect(self._on_document_deleted)
        
        # Project events
        self.event_bus.project_loaded.connect(self._on_project_loaded)
        self.event_bus.project_saved.connect(self._on_project_saved)
        self.event_bus.project_closed.connect(self._on_project_closed)
        self.event_bus.project_created.connect(self._on_project_created)
        
        # UI events
        self.event_bus.ui_theme_changed.connect(self._on_ui_theme_changed)
        self.event_bus.ui_state_changed.connect(self._on_ui_state_changed)
        
        # Error events
        self.event_bus.error_occurred.connect(self._on_error_occurred)
        
        logger.debug("Event bus signals connected")
    
    def _on_document_selected(self, document_id: str):
        """
        Handle document selected event.
        
        Args:
            document_id: The ID of the selected document.
        """
        logger.debug(f"Document selected event: {document_id}")
        
        try:
            # Load document
            document = self.document_manager.get_document(document_id)
            if not document:
                error_msg = f"Failed to load document with ID: {document_id}"
                self.error_handler.handle_error("DocumentLoadError", error_msg, parent=self)
                self.status_bar.showMessage(error_msg, 3000)
                return
            
            # Update editor
            success = self.editor.load_document(document_id)
            if not success:
                error_msg = f"Failed to load document in editor: {document.title}"
                self.error_handler.handle_error("EditorLoadError", error_msg, parent=self)
                self.status_bar.showMessage(error_msg, 3000)
                return
            
            # Update inspector
            self.inspector.set_document(document)
            
            # Update status bar
            self.status_bar.showMessage(f"Loaded document: {document.title}", 3000)
            
            # Update state
            self.state_manager.set_state("current_document_id", document_id)
            
            # Emit document loaded event
            self.event_bus.emit_document_loaded(document_id)
        except Exception as e:
            # Handle exception
            self.error_handler.handle_exception(e, "Error loading document", parent=self)
            self.status_bar.showMessage(f"Error loading document: {str(e)}", 3000)
    
    def _on_document_loaded(self, document_id: str):
        """
        Handle document loaded event.
        
        Args:
            document_id: The ID of the loaded document.
        """
        logger.debug(f"Document loaded event: {document_id}")
        # This will be implemented as we update the components
    
    def _on_document_saved(self, document_id: str):
        """
        Handle document saved event.
        
        Args:
            document_id: The ID of the saved document.
        """
        logger.debug(f"Document saved event: {document_id}")
        # This will be implemented as we update the components
    
    def _on_document_modified(self, document_id: str):
        """
        Handle document modified event.
        
        Args:
            document_id: The ID of the modified document.
        """
        logger.debug(f"Document modified event: {document_id}")
        # This will be implemented as we update the components
    
    def _on_document_created(self, document_id: str):
        """
        Handle document created event.
        
        Args:
            document_id: The ID of the created document.
        """
        logger.debug(f"Document created event: {document_id}")
        # This will be implemented as we update the components
    
    def _on_document_deleted(self, document_id: str):
        """
        Handle document deleted event.
        
        Args:
            document_id: The ID of the deleted document.
        """
        logger.debug(f"Document deleted event: {document_id}")
        # This will be implemented as we update the components
    
    def _on_project_loaded(self, project_id: str):
        """
        Handle project loaded event.
        
        Args:
            project_id: The ID of the loaded project.
        """
        logger.debug(f"Project loaded event: {project_id}")
        # This will be implemented as we update the components
    
    def _on_project_saved(self, project_id: str):
        """
        Handle project saved event.
        
        Args:
            project_id: The ID of the saved project.
        """
        logger.debug(f"Project saved event: {project_id}")
        # This will be implemented as we update the components
    
    def _on_project_closed(self):
        """Handle project closed event."""
        logger.debug("Project closed event")
        # This will be implemented as we update the components
    
    def _on_project_created(self, project_id: str):
        """
        Handle project created event.
        
        Args:
            project_id: The ID of the created project.
        """
        logger.debug(f"Project created event: {project_id}")
        # This will be implemented as we update the components
    
    def _on_ui_theme_changed(self, theme_name: str):
        """
        Handle UI theme changed event.
        
        Args:
            theme_name: The name of the new theme.
        """
        logger.debug(f"UI theme changed event: {theme_name}")
        # Apply theme to application
        self.theme_manager.apply_theme(self.app)
        
        # Apply theme to editor
        if hasattr(self, 'editor') and self.editor:
            self.theme_manager.apply_theme_to_editor(self.editor)
        
        # Update status bar
        self.status_bar.showMessage(f"Theme applied: {theme_name}", 3000)
    
    def _on_ui_state_changed(self, state_key: str, state_value: Any):
        """
        Handle UI state changed event.
        
        Args:
            state_key: The key of the changed state.
            state_value: The new value of the state.
        """
        logger.debug(f"UI state changed event: {state_key}={state_value}")
        # This will be implemented as we update the components
    
    def _on_error_occurred(self, error_type: str, error_message: str):
        """
        Handle error occurred event.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
        """
        logger.debug(f"Error occurred event: {error_type}: {error_message}")
        
        # Use error handler to handle the error
        self.error_handler.handle_error(error_type, error_message, parent=self)
        
        # Update status bar
        self.status_bar.showMessage(f"Error: {error_message}", 5000)
    
    def _on_about(self):
        """Handle about action."""
        logger.debug("About action triggered")
        
        QMessageBox.about(
            self,
            "About RebelSCRIBE",
            "RebelSCRIBE - AI-powered novel writing program\n\n"
            "Version: 0.1.0\n"
            "© 2025 RebelSCRIBE Team"
        )
