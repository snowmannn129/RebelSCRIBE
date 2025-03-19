#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Inspector View.

This module imports and runs tests for the InspectorView class and its components.
"""

# Import the test modules
from src.tests.ui.inspector.fixtures import *
from src.tests.ui.inspector.test_metadata_panel import TestMetadataPanel
from src.tests.ui.inspector.test_character_inspector import TestCharacterInspector
from src.tests.ui.inspector.test_location_inspector import TestLocationInspector
from src.tests.ui.inspector.test_notes_inspector import TestNotesInspector
from src.tests.ui.inspector.test_inspector_view import TestInspectorView

# This file serves as an entry point for running all inspector view tests
# The actual test implementations have been moved to separate modules in the inspector directory
