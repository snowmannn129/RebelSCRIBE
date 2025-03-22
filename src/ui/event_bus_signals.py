#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Event Bus Signals

This module provides event bus signal connection methods for the hybrid version of RebelSCRIBE.
"""

import os
import sys
from pathlib import Path

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def connect_event_bus_signals(self):
    """Connect event bus signals to handlers."""
    logger.debug("Connecting event bus signals")
    
    # Connect document selected signal
    self.event_bus.document_selected.connect(self._on_document_selected)
    
    # Connect document content changed signal
    self.event_bus.document_content_changed.connect(self._on_document_content_changed)
    
    # Connect document saved signal
    self.event_bus.document_saved.connect(self._on_document_saved)
    
    # Connect document deleted signal
    self.event_bus.document_deleted.connect(self._on_document_deleted)
    
    # Connect project closed signal
    self.event_bus.project_closed.connect(self._on_project_closed)
    
    # Connect error signal
    self.event_bus.error.connect(self._on_error)
    
    logger.debug("Event bus signals connected")

def on_document_selected(self, document_id):
    """
    Handle document selected event.
    
    Args:
        document_id: The ID of the selected document.
    """
    logger.debug(f"Document selected: {document_id}")
    
    # Check which tab is active
    if self.tab_widget.currentIndex() == 0:  # Novel Writing tab
        # Get document from document manager
        document = self.document_manager.get_document(document_id)
        
        if document:
            # Update editor
            if hasattr(self, 'editor') and self.editor:
                self.editor.set_document(document)
            
            # Update inspector
            if hasattr(self, 'inspector') and self.inspector:
                self.inspector.set_document(document)
            
            # Update status bar
            self.status_bar.showMessage(f"Document loaded: {document.title}", 3000)
        else:
            logger.warning(f"Document not found: {document_id}")
            self.status_bar.showMessage(f"Document not found: {document_id}", 3000)
    else:  # Documentation tab
        # Get documentation from documentation manager
        documentation = self.documentation_manager.get_documentation(document_id)
        
        if documentation:
            # Update documentation editor
            if hasattr(self, 'documentation_editor') and self.documentation_editor:
                self.documentation_editor.set_documentation(documentation)
            
            # Update status bar
            self.status_bar.showMessage(f"Documentation loaded: {documentation.title}", 3000)
        else:
            logger.warning(f"Documentation not found: {document_id}")
            self.status_bar.showMessage(f"Documentation not found: {document_id}", 3000)

def on_document_content_changed(self, document_id):
    """
    Handle document content changed event.
    
    Args:
        document_id: The ID of the document that changed.
    """
    logger.debug(f"Document content changed: {document_id}")
    
    # Update window title to indicate unsaved changes
    if self.current_project:
        self.setWindowTitle(f"RebelSCRIBE - {self.current_project.title} *")

def on_document_saved(self, document_id):
    """
    Handle document saved event.
    
    Args:
        document_id: The ID of the saved document.
    """
    logger.debug(f"Document saved: {document_id}")
    
    # Update window title to remove unsaved changes indicator
    if self.current_project:
        self.setWindowTitle(f"RebelSCRIBE - {self.current_project.title}")
    
    # Update status bar
    self.status_bar.showMessage(f"Document saved", 3000)

def on_document_deleted(self, document_id):
    """
    Handle document deleted event.
    
    Args:
        document_id: The ID of the deleted document.
    """
    logger.debug(f"Document deleted: {document_id}")
    
    # Clear editor and inspector if the current document was deleted
    if hasattr(self, 'editor') and self.editor and self.editor.current_document and self.editor.current_document.id == document_id:
        self.editor.set_content("")
        self.editor.current_document = None
        self.editor.last_saved_content = ""
        self.editor._update_status_bar()
    
    if hasattr(self, 'inspector') and self.inspector:
        self.inspector.set_document(None)
    
    # Update status bar
    self.status_bar.showMessage(f"Document deleted", 3000)

def on_project_closed(self):
    """Handle project closed event."""
    logger.debug("Project closed")
    
    # Clear current project
    self.current_project = None
    
    # Clear editor and inspector
    if hasattr(self, 'editor') and self.editor:
        self.editor.set_content("")
        self.editor.current_document = None
        self.editor.last_saved_content = ""
        self.editor._update_status_bar()
    
    if hasattr(self, 'inspector') and self.inspector:
        self.inspector.set_document(None)
    
    # Clear binder view
    if hasattr(self, 'binder_view') and self.binder_view:
        self.binder_view.clear()
    
    # Update window title
    self.setWindowTitle("RebelSCRIBE")
    
    # Update status bar
    self.status_bar.showMessage("Project closed", 3000)

def on_error(self, error_message):
    """
    Handle error event.
    
    Args:
        error_message: The error message.
    """
    logger.error(f"Error: {error_message}")
    
    # Show error message
    self.error_handler.show_error(error_message)
