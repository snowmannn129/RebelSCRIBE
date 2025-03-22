#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Documentation Methods

This module provides documentation-specific methods for the hybrid version of RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def on_extract_documentation(self):
    """Handle extract documentation action."""
    logger.debug("Extract documentation action triggered")
    
    # Get source file or directory
    source_path, _ = QFileDialog.getOpenFileName(
        self,
        "Select Source File",
        "",
        "All Files (*.*);;Python Files (*.py);;C++ Files (*.cpp *.h);;JavaScript Files (*.js);;TypeScript Files (*.ts)"
    )
    
    if not source_path:
        return
    
    # Get component
    components = [
        "RebelCAD",
        "RebelCODE",
        "RebelENGINE",
        "RebelFLOW",
        "RebelDESK",
        "RebelSCRIBE",
        "Other"
    ]
    component, ok = QInputDialog.getItem(
        self,
        "Extract Documentation",
        "Component:",
        components,
        0,
        False
    )
    
    if not ok:
        return
    
    # Get API version
    api_version, ok = QInputDialog.getText(
        self,
        "Extract Documentation",
        "API version:",
        text="1.0.0"
    )
    
    if not ok:
        return
    
    # Extract documentation
    try:
        doc = self.documentation_manager.extract_documentation_from_file(
            source_path,
            component,
            api_version
        )
        
        if doc:
            self.status_bar.showMessage(f"Documentation extracted from {source_path}", 3000)
        else:
            QMessageBox.warning(
                self,
                "Extract Documentation",
                f"Failed to extract documentation from {source_path}"
            )
    except Exception as e:
        QMessageBox.critical(
            self,
            "Extract Documentation Error",
            f"An error occurred during documentation extraction: {str(e)}"
        )
        self.status_bar.showMessage("Documentation extraction error", 3000)

def on_generate_static_site(self):
    """Handle generate static site action."""
    logger.debug("Generate static site action triggered")
    
    # Get output directory
    output_dir = QFileDialog.getExistingDirectory(
        self,
        "Select Output Directory",
        ""
    )
    
    if not output_dir:
        return
    
    # Generate static site
    try:
        success = self.documentation_manager.generate_static_site(output_dir)
        
        if success:
            self.status_bar.showMessage(f"Static site generated in {output_dir}", 3000)
        else:
            QMessageBox.warning(
                self,
                "Generate Static Site",
                f"Failed to generate static site in {output_dir}"
            )
    except Exception as e:
        QMessageBox.critical(
            self,
            "Generate Static Site Error",
            f"An error occurred during static site generation: {str(e)}"
        )
        self.status_bar.showMessage("Static site generation error", 3000)

def on_integrate_with_component(self):
    """Handle integrate with component action."""
    logger.debug("Integrate with component action triggered")
    
    # Get component
    components = [
        "RebelCAD",
        "RebelCODE",
        "RebelENGINE",
        "RebelFLOW",
        "RebelDESK",
        "RebelSCRIBE"
    ]
    component, ok = QInputDialog.getItem(
        self,
        "Integrate with Component",
        "Component:",
        components,
        0,
        False
    )
    
    if not ok:
        return
    
    # Get source directory
    source_dir = QFileDialog.getExistingDirectory(
        self,
        "Select Source Directory",
        ""
    )
    
    if not source_dir:
        return
    
    # Get output directory
    output_dir = QFileDialog.getExistingDirectory(
        self,
        "Select Output Directory",
        ""
    )
    
    if not output_dir:
        return
    
    # Integrate with component
    try:
        success = self.documentation_manager.integrate_with_component(
            component,
            source_dir,
            output_dir
        )
        
        if success:
            self.status_bar.showMessage(f"Integrated with {component}", 3000)
        else:
            QMessageBox.warning(
                self,
                "Integrate with Component",
                f"Failed to integrate with {component}"
            )
    except Exception as e:
        QMessageBox.critical(
            self,
            "Integrate with Component Error",
            f"An error occurred during integration: {str(e)}"
        )
        self.status_bar.showMessage("Integration error", 3000)
