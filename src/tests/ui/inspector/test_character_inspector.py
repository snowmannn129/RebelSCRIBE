#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the CharacterInspector component.

This module contains tests for the CharacterInspector class.
"""

from unittest.mock import MagicMock
import pytest
from PyQt6.QtCore import Qt

from src.ui.inspector.inspector_view import CharacterInspector
from src.backend.models.character import Character
from src.tests.ui.inspector.fixtures import app, character_inspector


class TestCharacterInspector:
    """Test cases for the CharacterInspector class."""
    
    def test_init(self, character_inspector):
        """Test initialization of the character inspector."""
        # Check that components are created
        assert character_inspector.name_edit is not None
        assert character_inspector.role_combo is not None
        assert character_inspector.age_spin is not None
        
        # Check that fields are disabled initially
        assert not character_inspector.name_edit.isEnabled()
        assert not character_inspector.role_combo.isEnabled()
        assert not character_inspector.age_spin.isEnabled()
    
    def test_set_character(self, character_inspector):
        """Test setting a character."""
        # Create mock character
        mock_character = MagicMock(spec=Character)
        mock_character.name = "John Doe"
        mock_character.role = "Protagonist"
        mock_character.age = 30
        
        # Set character
        character_inspector.set_character(mock_character)
        
        # Check that fields are enabled
        assert character_inspector.name_edit.isEnabled()
        assert character_inspector.role_combo.isEnabled()
        assert character_inspector.age_spin.isEnabled()
        
        # Check field values
        assert character_inspector.name_edit.text() == "John Doe"
        assert character_inspector.role_combo.currentText() == "Protagonist"
        assert character_inspector.age_spin.value() == 30
        
        # Clear character
        character_inspector.set_character(None)
        
        # Check that fields are disabled
        assert not character_inspector.name_edit.isEnabled()
        assert not character_inspector.role_combo.isEnabled()
        assert not character_inspector.age_spin.isEnabled()
        
        # Check field values are cleared
        assert character_inspector.name_edit.text() == ""
        assert character_inspector.role_combo.currentIndex() == 0
        assert character_inspector.age_spin.value() == 0
    
    def test_character_changed_signals(self, qtbot, character_inspector):
        """Test character changed signals."""
        # Create mock character
        mock_character = MagicMock(spec=Character)
        mock_character.name = "John Doe"
        mock_character.role = "Protagonist"
        mock_character.age = 30
        
        # Set character
        character_inspector.set_character(mock_character)
        
        # Mock character_changed signal
        character_inspector.character_changed = MagicMock()
        
        # Change name
        character_inspector.name_edit.setText("Jane Doe")
        character_inspector.character_changed.emit.assert_called_with("name", "Jane Doe")
        
        # Change role
        character_inspector.role_combo.setCurrentText("Antagonist")
        character_inspector.character_changed.emit.assert_called_with("role", "Antagonist")
        
        # Change age
        character_inspector.age_spin.setValue(35)
        character_inspector.character_changed.emit.assert_called_with("age", 35)
