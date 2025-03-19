#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Settings Tabs Package

This package contains the tab widgets for the settings dialog.
"""

from src.ui.settings_tabs.editor_tab import EditorTab
from src.ui.settings_tabs.interface_tab import InterfaceTab
from src.ui.settings_tabs.file_locations_tab import FileLocationsTab
from src.ui.settings_tabs.shortcuts_tab import ShortcutsTab

__all__ = [
    'EditorTab',
    'InterfaceTab',
    'FileLocationsTab',
    'ShortcutsTab'
]
