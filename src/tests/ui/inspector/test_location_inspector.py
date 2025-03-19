#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the LocationInspector component.

This module contains tests for the LocationInspector class.
"""

from unittest.mock import MagicMock
import pytest
from PyQt6.QtCore import Qt

from src.ui.inspector.inspector_view import LocationInspector
from src.backend.models.location import Location
from src.tests.ui.inspector.fixtures import app, location_inspector


class TestLocationInspector:
    """Test cases for the LocationInspector class."""
    
    def test_init(self, location_inspector):
        """Test initialization of the location inspector."""
        # Check that components are created
        assert location_inspector.name_edit is not None
        assert location_inspector.type_combo is not None
        
        # Check that fields are disabled initially
        assert not location_inspector.name_edit.isEnabled()
        assert not location_inspector.type_combo.isEnabled()
    
    def test_set_location(self, location_inspector):
        """Test setting a location."""
        # Create mock location
        mock_location = MagicMock(spec=Location)
        mock_location.name = "New York"
        mock_location.type = "City"
        
        # Set location
        location_inspector.set_location(mock_location)
        
        # Check that fields are enabled
        assert location_inspector.name_edit.isEnabled()
        assert location_inspector.type_combo.isEnabled()
        
        # Check field values
        assert location_inspector.name_edit.text() == "New York"
        assert location_inspector.type_combo.currentText() == "City"
        
        # Clear location
        location_inspector.set_location(None)
        
        # Check that fields are disabled
        assert not location_inspector.name_edit.isEnabled()
        assert not location_inspector.type_combo.isEnabled()
        
        # Check field values are cleared
        assert location_inspector.name_edit.text() == ""
        assert location_inspector.type_combo.currentIndex() == 0
    
    def test_location_changed_signals(self, qtbot, location_inspector):
        """Test location changed signals."""
        # Create mock location
        mock_location = MagicMock(spec=Location)
        mock_location.name = "New York"
        mock_location.type = "City"
        
        # Set location
        location_inspector.set_location(mock_location)
        
        # Mock location_changed signal
        location_inspector.location_changed = MagicMock()
        
        # Change name
        location_inspector.name_edit.setText("Los Angeles")
        location_inspector.location_changed.emit.assert_called_with("name", "Los Angeles")
        
        # Change type
        location_inspector.type_combo.setCurrentText("Town")
        location_inspector.location_changed.emit.assert_called_with("type", "Town")
