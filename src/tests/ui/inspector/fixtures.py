#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixtures for inspector view tests.

This module contains fixtures used by the inspector view test modules.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication

from src.ui.inspector.inspector_view import (
    InspectorView, MetadataPanel, CharacterInspector,
    LocationInspector, NotesInspector
)


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to clean up as we're not destroying the app


@pytest.fixture
def metadata_panel(qtbot):
    """Create a MetadataPanel instance for testing."""
    panel = MetadataPanel()
    qtbot.addWidget(panel)
    return panel


@pytest.fixture
def character_inspector(qtbot):
    """Create a CharacterInspector instance for testing."""
    inspector = CharacterInspector()
    qtbot.addWidget(inspector)
    return inspector


@pytest.fixture
def location_inspector(qtbot):
    """Create a LocationInspector instance for testing."""
    inspector = LocationInspector()
    qtbot.addWidget(inspector)
    return inspector


@pytest.fixture
def notes_inspector(qtbot):
    """Create a NotesInspector instance for testing."""
    inspector = NotesInspector()
    qtbot.addWidget(inspector)
    return inspector


@pytest.fixture
def inspector_view(qtbot, monkeypatch):
    """Create an InspectorView instance for testing."""
    # Mock DocumentManager to avoid file operations
    with patch('src.ui.inspector.inspector_view.DocumentManager') as mock_dm:
        # Configure the mock
        mock_instance = mock_dm.return_value
        mock_instance.get_document.return_value = None
        mock_instance.update_document.return_value = True
        
        # Create inspector view
        view = InspectorView()
        qtbot.addWidget(view)
        return view
