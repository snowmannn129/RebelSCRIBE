#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Main Window Hybrid

This module implements the main window for the hybrid version of RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QStatusBar, QMenuBar, QMenu, QToolBar,
    QAction, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QKeySequence

from src.utils.logging_utils import get_logger
from src.ui.theme_manager import ThemeManager
from src.ui.error_handler_init import error_handler

logger = get_logger(__name__)

class MainWindowHybrid(QMainWindow):
    """
    Main window for the hybrid version of RebelSCRIBE.
    
    This class implements the main window for the hybrid version of RebelSCRIBE,
    which combines documentation management and novel writing functionality.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Store application instance
        self.app = QApplication.instance()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Initialize error handler
        self.error_handler = error_handler
        self.error_handler.set_main_window(self)
        
        # Initialize UI
        self._init_ui()
        
        # Load settings
        self._load_settings()
        
        # Apply theme
        self.theme_manager.apply_theme(self.app)
        
        # Connect event bus signals
        self._connect_event_bus_signals()
        
        logger.debug("Main window initialized")
    
    def _init_ui(self):
        """Initialize the UI."""
        # Set window properties
        self.setWindowTitle("RebelSCRIBE")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create novel writing tab
        self.novel_writing_tab = QWidget()
        self.tab_widget.addTab(self.novel_writing_tab, "Novel Writing")
        
        # Create documentation tab
        self.documentation_tab = QWidget()
        self.tab_widget.addTab(self.documentation_tab, "Documentation")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create tool bar
        self._create_tool_bar()
        
        # Initialize novel writing tab
        self._init_novel_writing_tab()
        
        # Initialize documentation tab
        self._init_documentation_tab()
        
        # Show status message
        self.status_bar.showMessage("Ready", 3000)
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        # Create menu bar
        self.menu_bar = self.menuBar()
        
        # Create file menu
        self.file_menu = self.menu_bar.addMenu("&File")
        
        # Create new action
        self.new_action = QAction("&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self._on_new)
        self.file_menu.addAction(self.new_action)
        
        # Create open action
        self.open_action = QAction("&Open", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self._on_open)
        self.file_menu.addAction(self.open_action)
        
        # Create save action
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self._on_save)
        self.file_menu.addAction(self.save_action)
        
        # Create save as action
        self.save_as_action = QAction("Save &As", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self._on_save_as)
        self.file_menu.addAction(self.save_as_action)
        
        # Add separator
        self.file_menu.addSeparator()
        
        # Create exit action
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # Create edit menu
        self.edit_menu = self.menu_bar.addMenu("&Edit")
        
        # Create undo action
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self._on_undo)
        self.edit_menu.addAction(self.undo_action)
        
        # Create redo action
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self._on_redo)
        self.edit_menu.addAction(self.redo_action)
        
        # Add separator
        self.edit_menu.addSeparator()
        
        # Create cut action
        self.cut_action = QAction("Cu&t", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self._on_cut)
        self.edit_menu.addAction(self.cut_action)
        
        # Create copy action
        self.copy_action = QAction("&Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self._on_copy)
        self.edit_menu.addAction(self.copy_action)
        
        # Create paste action
        self.paste_action = QAction("&Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self._on_paste)
        self.edit_menu.addAction(self.paste_action)
        
        # Create view menu
        self.view_menu = self.menu_bar.addMenu("&View")
        
        # Create theme settings action
        self.theme_settings_action = QAction("&Theme Settings", self)
        self.theme_settings_action.triggered.connect(self._on_theme_settings)
        self.view_menu.addAction(self.theme_settings_action)
        
        # Create tools menu
        self.tools_menu = self.menu_bar.addMenu("&Tools")
        
        # Create AI settings action
        self.ai_settings_action = QAction("&AI Settings", self)
        self.ai_settings_action.triggered.connect(self._on_ai_settings)
        self.tools_menu.addAction(self.ai_settings_action)
        
        # Add separator
        self.tools_menu.addSeparator()
        
        # Create model benchmarking action
        self.model_benchmarking_action = QAction("Model &Benchmarking", self)
        self.model_benchmarking_action.triggered.connect(self._on_model_benchmarking)
        self.tools_menu.addAction(self.model_benchmarking_action)
        
        # Create batch benchmarking action
        self.batch_benchmarking_action = QAction("&Batch Benchmarking", self)
        self.batch_benchmarking_action.triggered.connect(self._on_batch_benchmarking)
        self.tools_menu.addAction(self.batch_benchmarking_action)
        
        # Create model fine-tuning action
        self.model_finetuning_action = QAction("Model &Fine-tuning", self)
        self.model_finetuning_action.triggered.connect(self._on_model_finetuning)
        self.tools_menu.addAction(self.model_finetuning_action)
        
        # Create documentation menu
        self.documentation_menu = self.menu_bar.addMenu("&Documentation")
        
        # Create extract documentation action
        self.extract_documentation_action = QAction("&Extract Documentation", self)
        self.extract_documentation_action.triggered.connect(self._on_extract_documentation)
        self.documentation_menu.addAction(self.extract_documentation_action)
        
        # Create generate static site action
        self.generate_static_site_action = QAction("&Generate Static Site", self)
        self.generate_static_site_action.triggered.connect(self._on_generate_static_site)
        self.documentation_menu.addAction(self.generate_static_site_action)
        
        # Create integrate with component action
        self.integrate_with_component_action = QAction("&Integrate with Component", self)
        self.integrate_with_component_action.triggered.connect(self._on_integrate_with_component)
        self.documentation_menu.addAction(self.integrate_with_component_action)
        
        # Create help menu
        self.help_menu = self.menu_bar.addMenu("&Help")
        
        # Create about action
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self._on_about)
        self.help_menu.addAction(self.about_action)
    
    def _create_tool_bar(self):
        """Create the tool bar."""
        # Create tool bar
        self.tool_bar = QToolBar("Main Toolbar")
        self.addToolBar(self.tool_bar)
        
        # Add actions
        self.tool_bar.addAction(self.new_action)
        self.tool_bar.addAction(self.open_action)
        self.tool_bar.addAction(self.save_action)
        
        # Add separator
        self.tool_bar.addSeparator()
        
        # Add actions
        self.tool_bar.addAction(self.cut_action)
        self.tool_bar.addAction(self.copy_action)
        self.tool_bar.addAction(self.paste_action)
    
    def _init_novel_writing_tab(self):
        """Initialize the novel writing tab."""
        # Create layout
        layout = QVBoxLayout(self.novel_writing_tab)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create binder view placeholder
        binder_view_placeholder = QWidget()
        binder_view_placeholder.setMinimumWidth(200)
        splitter.addWidget(binder_view_placeholder)
        
        # Create editor placeholder
        editor_placeholder = QWidget()
        splitter.addWidget(editor_placeholder)
        
        # Create inspector placeholder
        inspector_placeholder = QWidget()
        inspector_placeholder.setMinimumWidth(200)
        splitter.addWidget(inspector_placeholder)
        
        # Set stretch factors
        splitter.setStretchFactor(0, 1)  # Binder view
        splitter.setStretchFactor(1, 3)  # Editor
        splitter.setStretchFactor(2, 1)  # Inspector
    
    def _init_documentation_tab(self):
        """Initialize the documentation tab."""
        # Create layout
        layout = QVBoxLayout(self.documentation_tab)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create documentation tree placeholder
        documentation_tree_placeholder = QWidget()
        documentation_tree_placeholder.setMinimumWidth(200)
        splitter.addWidget(documentation_tree_placeholder)
        
        # Create documentation editor placeholder
        documentation_editor_placeholder = QWidget()
        splitter.addWidget(documentation_editor_placeholder)
        
        # Set stretch factors
        splitter.setStretchFactor(0, 1)  # Documentation tree
        splitter.setStretchFactor(1, 3)  # Documentation editor
    
    def _load_settings(self):
        """Load settings."""
        settings = QSettings()
        
        # Load window geometry
        geometry = settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load window state
        state = settings.value("window/state")
        if state:
            self.restoreState(state)
        
        # Load current tab
        current_tab = settings.value("window/currentTab", 0, type=int)
        self.tab_widget.setCurrentIndex(current_tab)
    
    def _save_settings(self):
        """Save settings."""
        settings = QSettings()
        
        # Save window geometry
        settings.setValue("window/geometry", self.saveGeometry())
        
        # Save window state
        settings.setValue("window/state", self.saveState())
        
        # Save current tab
        settings.setValue("window/currentTab", self.tab_widget.currentIndex())
    
    def closeEvent(self, event):
        """
        Handle close event.
        
        Args:
            event: The close event.
        """
        # Save settings
        self._save_settings()
        
        # Accept event
        event.accept()
    
    def run(self):
        """Run the application."""
        # Show window
        self.show()
    
    def _on_new(self):
        """Handle new action."""
        logger.debug("New action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Create new novel
            QMessageBox.information(self, "New Novel", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Create new documentation
            QMessageBox.information(self, "New Documentation", "This feature is not yet implemented.")
    
    def _on_open(self):
        """Handle open action."""
        logger.debug("Open action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Open novel
            QMessageBox.information(self, "Open Novel", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Open documentation
            QMessageBox.information(self, "Open Documentation", "This feature is not yet implemented.")
    
    def _on_save(self):
        """Handle save action."""
        logger.debug("Save action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Save novel
            QMessageBox.information(self, "Save Novel", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Save documentation
            QMessageBox.information(self, "Save Documentation", "This feature is not yet implemented.")
    
    def _on_save_as(self):
        """Handle save as action."""
        logger.debug("Save as action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Save novel as
            QMessageBox.information(self, "Save Novel As", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Save documentation as
            QMessageBox.information(self, "Save Documentation As", "This feature is not yet implemented.")
    
    def _on_undo(self):
        """Handle undo action."""
        logger.debug("Undo action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Undo in novel editor
            QMessageBox.information(self, "Undo", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Undo in documentation editor
            QMessageBox.information(self, "Undo", "This feature is not yet implemented.")
    
    def _on_redo(self):
        """Handle redo action."""
        logger.debug("Redo action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Redo in novel editor
            QMessageBox.information(self, "Redo", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Redo in documentation editor
            QMessageBox.information(self, "Redo", "This feature is not yet implemented.")
    
    def _on_cut(self):
        """Handle cut action."""
        logger.debug("Cut action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Cut in novel editor
            QMessageBox.information(self, "Cut", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Cut in documentation editor
            QMessageBox.information(self, "Cut", "This feature is not yet implemented.")
    
    def _on_copy(self):
        """Handle copy action."""
        logger.debug("Copy action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Copy in novel editor
            QMessageBox.information(self, "Copy", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Copy in documentation editor
            QMessageBox.information(self, "Copy", "This feature is not yet implemented.")
    
    def _on_paste(self):
        """Handle paste action."""
        logger.debug("Paste action triggered")
        
        # Check which tab is active
        if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
            # Paste in novel editor
            QMessageBox.information(self, "Paste", "This feature is not yet implemented.")
        else:  # Documentation tab
            # Paste in documentation editor
            QMessageBox.information(self, "Paste", "This feature is not yet implemented.")
