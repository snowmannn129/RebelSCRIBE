#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asset Management Integration Module for RebelSCRIBE.

This module provides integration with the RebelSUITE Unified Asset Management System,
enabling asset browsing, searching, importing, exporting, and management within RebelSCRIBE.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Callable

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTreeView, QFileDialog

# Add the RebelSUITE_Shared_Resources directory to the Python path
shared_resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../RebelSUITE_Shared_Resources'))
if shared_resources_path not in sys.path:
    sys.path.append(shared_resources_path)

# Import the asset management system
from asset_management.python.asset_manager import AssetManager, AssetType, AssetMetadata

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class AssetManagementIntegration(QObject):
    """
    Integration with the RebelSUITE Unified Asset Management System.
    
    This class provides functionality for integrating RebelSCRIBE with the
    RebelSUITE Unified Asset Management System, enabling asset browsing,
    searching, importing, exporting, and management within RebelSCRIBE.
    """
    
    # Signals
    asset_imported = pyqtSignal(str)  # asset_path
    asset_exported = pyqtSignal(str, str)  # asset_path, export_path
    asset_selected = pyqtSignal(str)  # asset_path
    asset_created = pyqtSignal(str)  # asset_path
    asset_updated = pyqtSignal(str)  # asset_path
    asset_deleted = pyqtSignal(str)  # asset_path
    
    def __init__(self, config=None):
        """
        Initialize the asset management integration.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        super().__init__()
        
        # Initialize configuration
        self.config = config or {}
        
        # Initialize state
        self._asset_manager = None
        self._active_assets = {}
        self._current_directory = None
        
        # Initialize capabilities
        self._capabilities = [
            'asset_browsing',
            'asset_searching',
            'asset_importing',
            'asset_exporting',
            'asset_management',
            'asset_conversion',
        ]
        
    def initialize(self):
        """
        Initialize the asset management integration.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info("Initializing asset management integration")
            
            # Get asset root directory from config
            asset_root = self.config.get('asset_root', os.path.join(os.path.expanduser('~'), 'RebelSUITE', 'Assets'))
            
            # Create asset root directory if it doesn't exist
            os.makedirs(asset_root, exist_ok=True)
            
            # Initialize asset manager
            self._asset_manager = AssetManager({
                'rootDirectory': asset_root,
                'thumbnailSize': {'width': 128, 'height': 128},
                'cacheSize': 1000,
                'autoRefresh': True
            })
            
            # Add change listener
            self._asset_manager.add_change_listener(self._handle_asset_changes)
            
            # Load assets
            self._asset_manager.load_directory('')
            
            # Set current directory
            self._current_directory = ''
            
            logger.info("Asset management integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize asset management integration: {e}")
            return False
            
    def shutdown(self):
        """
        Shut down the asset management integration.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info("Shutting down asset management integration")
            
            # Dispose asset manager
            if self._asset_manager:
                self._asset_manager.dispose()
                self._asset_manager = None
            
            # Clear state
            self._active_assets = {}
            self._current_directory = None
            
            logger.info("Asset management integration shut down successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to shut down asset management integration: {e}")
            return False
            
    def is_available(self):
        """
        Check if the asset management system is available.
        
        Returns:
            bool: True if available, False otherwise.
        """
        return self._asset_manager is not None
        
    def execute_command(self, command, args=None):
        """
        Execute a command on the asset management system.
        
        Args:
            command (str): The command to execute.
            args (dict, optional): The command arguments. Defaults to None.
            
        Returns:
            Any: The command result, or None if the command failed.
        """
        try:
            logger.info(f"Executing command {command} on asset management system")
            
            # Handle specific commands
            if command == 'browse_directory':
                return self._browse_directory(args.get('directory', ''))
            elif command == 'search_assets':
                return self._search_assets(args.get('filter', {}))
            elif command == 'import_asset':
                return self._import_asset(args.get('file_path'), args.get('asset_type'))
            elif command == 'export_asset':
                return self._export_asset(args.get('asset_path'), args.get('export_path'), args.get('export_type'))
            elif command == 'create_asset':
                return self._create_asset(args.get('asset_path'), args.get('data'), args.get('metadata'))
            elif command == 'update_asset':
                return self._update_asset(args.get('asset_path'), args.get('data'), args.get('metadata'))
            elif command == 'delete_asset':
                return self._delete_asset(args.get('asset_path'))
            elif command == 'get_asset_metadata':
                return self._get_asset_metadata(args.get('asset_path'))
            elif command == 'get_asset_thumbnail':
                return self._get_asset_thumbnail(args.get('asset_path'))
            elif command == 'convert_asset':
                return self._convert_asset(args.get('source_path'), args.get('target_path'), args.get('options'))
            else:
                logger.warning(f"Unknown command: {command}")
                return None
        except Exception as e:
            logger.error(f"Failed to execute command {command} on asset management system: {e}")
            return None
            
    def _handle_asset_changes(self, changes):
        """
        Handle asset changes.
        
        Args:
            changes (list): The changes.
        """
        try:
            for change in changes:
                if change.type == 'added':
                    # Asset added
                    self._active_assets[change.path] = change.metadata
                    self.asset_created.emit(change.path)
                elif change.type == 'modified':
                    # Asset modified
                    self._active_assets[change.path] = change.metadata
                    self.asset_updated.emit(change.path)
                elif change.type == 'deleted':
                    # Asset deleted
                    if change.path in self._active_assets:
                        del self._active_assets[change.path]
                    self.asset_deleted.emit(change.path)
        except Exception as e:
            logger.error(f"Failed to handle asset changes: {e}")
            
    def _browse_directory(self, directory):
        """
        Browse a directory in the asset management system.
        
        Args:
            directory (str): The directory path.
            
        Returns:
            list: The assets in the directory, or None if browsing failed.
        """
        try:
            logger.info(f"Browsing directory {directory}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Load directory
            assets = self._asset_manager.load_directory(directory)
            
            # Update current directory
            self._current_directory = directory
            
            # Update active assets
            for asset in assets:
                self._active_assets[asset.path] = asset
                
            # Convert assets to dictionaries
            asset_dicts = [asset.to_dict() for asset in assets]
            
            return asset_dicts
        except Exception as e:
            logger.error(f"Failed to browse directory {directory}: {e}")
            return None
            
    def _search_assets(self, filter_dict):
        """
        Search for assets in the asset management system.
        
        Args:
            filter_dict (dict): The filter criteria.
            
        Returns:
            dict: The search results, or None if searching failed.
        """
        try:
            logger.info(f"Searching assets with filter {filter_dict}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Search assets
            results = self._asset_manager.search_assets(filter_dict)
            
            # Convert results to dictionary
            result_dict = {
                'assets': [asset.to_dict() for asset in results['assets']],
                'totalCount': results['totalCount'],
                'page': results['page'],
                'pageSize': results['pageSize'],
            }
            
            return result_dict
        except Exception as e:
            logger.error(f"Failed to search assets: {e}")
            return None
            
    def _import_asset(self, file_path, asset_type=None):
        """
        Import an asset into the asset management system.
        
        Args:
            file_path (str): The file path.
            asset_type (str, optional): The asset type. Defaults to None.
            
        Returns:
            dict: The imported asset metadata, or None if import failed.
        """
        try:
            logger.info(f"Importing asset {file_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Check if file exists
            if not os.path.isfile(file_path):
                logger.warning(f"File {file_path} not found")
                return None
                
            # Get file name and extension
            file_name = os.path.basename(file_path)
            
            # Determine asset path
            asset_path = os.path.join(self._current_directory, file_name)
            
            # Read file data
            with open(file_path, 'rb') as f:
                data = f.read()
                
            # Create metadata
            metadata = {}
            if asset_type:
                metadata['type'] = asset_type
                
            # Create asset
            asset = self._asset_manager.create_asset(asset_path, data, metadata)
            
            if not asset:
                logger.warning(f"Failed to create asset {asset_path}")
                return None
                
            # Update active assets
            self._active_assets[asset_path] = asset
            
            # Emit signal
            self.asset_imported.emit(asset_path)
            
            return asset.to_dict()
        except Exception as e:
            logger.error(f"Failed to import asset {file_path}: {e}")
            return None
            
    def _export_asset(self, asset_path, export_path, export_type=None):
        """
        Export an asset from the asset management system.
        
        Args:
            asset_path (str): The asset path.
            export_path (str): The export path.
            export_type (str, optional): The export type. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info(f"Exporting asset {asset_path} to {export_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return False
                
            # Get asset metadata
            asset = self._asset_manager.get_asset_metadata(asset_path)
            
            if not asset:
                logger.warning(f"Asset {asset_path} not found")
                return False
                
            # Read asset data
            data = self._asset_manager.read_asset_bytes(asset_path)
            
            if not data:
                logger.warning(f"Failed to read asset {asset_path}")
                return False
                
            # Create export directory if it doesn't exist
            export_dir = os.path.dirname(export_path)
            os.makedirs(export_dir, exist_ok=True)
                
            # Write data to export path
            with open(export_path, 'wb') as f:
                f.write(data)
                
            # Emit signal
            self.asset_exported.emit(asset_path, export_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to export asset {asset_path} to {export_path}: {e}")
            return False
            
    def _create_asset(self, asset_path, data, metadata=None):
        """
        Create an asset in the asset management system.
        
        Args:
            asset_path (str): The asset path.
            data (bytes): The asset data.
            metadata (dict, optional): The asset metadata. Defaults to None.
            
        Returns:
            dict: The created asset metadata, or None if creation failed.
        """
        try:
            logger.info(f"Creating asset {asset_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Create asset
            asset = self._asset_manager.create_asset(asset_path, data, metadata)
            
            if not asset:
                logger.warning(f"Failed to create asset {asset_path}")
                return None
                
            # Update active assets
            self._active_assets[asset_path] = asset
            
            # Emit signal
            self.asset_created.emit(asset_path)
            
            return asset.to_dict()
        except Exception as e:
            logger.error(f"Failed to create asset {asset_path}: {e}")
            return None
            
    def _update_asset(self, asset_path, data=None, metadata=None):
        """
        Update an asset in the asset management system.
        
        Args:
            asset_path (str): The asset path.
            data (bytes, optional): The asset data. Defaults to None.
            metadata (dict, optional): The asset metadata. Defaults to None.
            
        Returns:
            dict: The updated asset metadata, or None if update failed.
        """
        try:
            logger.info(f"Updating asset {asset_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Update asset
            asset = self._asset_manager.update_asset(asset_path, data, metadata)
            
            if not asset:
                logger.warning(f"Failed to update asset {asset_path}")
                return None
                
            # Update active assets
            self._active_assets[asset_path] = asset
            
            # Emit signal
            self.asset_updated.emit(asset_path)
            
            return asset.to_dict()
        except Exception as e:
            logger.error(f"Failed to update asset {asset_path}: {e}")
            return None
            
    def _delete_asset(self, asset_path):
        """
        Delete an asset from the asset management system.
        
        Args:
            asset_path (str): The asset path.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info(f"Deleting asset {asset_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return False
                
            # Delete asset
            success = self._asset_manager.delete_asset(asset_path)
            
            if not success:
                logger.warning(f"Failed to delete asset {asset_path}")
                return False
                
            # Remove from active assets
            if asset_path in self._active_assets:
                del self._active_assets[asset_path]
                
            # Emit signal
            self.asset_deleted.emit(asset_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_path}: {e}")
            return False
            
    def _get_asset_metadata(self, asset_path):
        """
        Get metadata for an asset in the asset management system.
        
        Args:
            asset_path (str): The asset path.
            
        Returns:
            dict: The asset metadata, or None if not found.
        """
        try:
            logger.info(f"Getting metadata for asset {asset_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Get asset metadata
            asset = self._asset_manager.get_asset_metadata(asset_path)
            
            if not asset:
                logger.warning(f"Asset {asset_path} not found")
                return None
                
            # Update active assets
            self._active_assets[asset_path] = asset
            
            return asset.to_dict()
        except Exception as e:
            logger.error(f"Failed to get metadata for asset {asset_path}: {e}")
            return None
            
    def _get_asset_thumbnail(self, asset_path):
        """
        Get a thumbnail for an asset in the asset management system.
        
        Args:
            asset_path (str): The asset path.
            
        Returns:
            str: The thumbnail data URL, or None if not available.
        """
        try:
            logger.info(f"Getting thumbnail for asset {asset_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Get asset thumbnail
            thumbnail = self._asset_manager.get_thumbnail(asset_path)
            
            if not thumbnail:
                logger.warning(f"Thumbnail not available for asset {asset_path}")
                return None
                
            return thumbnail
        except Exception as e:
            logger.error(f"Failed to get thumbnail for asset {asset_path}: {e}")
            return None
            
    def _convert_asset(self, source_path, target_path, options=None):
        """
        Convert an asset in the asset management system.
        
        Args:
            source_path (str): The source asset path.
            target_path (str): The target asset path.
            options (dict, optional): The conversion options. Defaults to None.
            
        Returns:
            dict: The conversion result, or None if conversion failed.
        """
        try:
            logger.info(f"Converting asset {source_path} to {target_path}")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Convert asset
            result = self._asset_manager.convert_asset(source_path, target_path, options or {})
            
            if not result.get('success'):
                logger.warning(f"Failed to convert asset {source_path} to {target_path}: {result.get('error')}")
                return result
                
            return result
        except Exception as e:
            logger.error(f"Failed to convert asset {source_path} to {target_path}: {e}")
            return None
            
    def create_asset_browser_widget(self, parent=None):
        """
        Create an asset browser widget.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            
        Returns:
            QWidget: The asset browser widget, or None if creation failed.
        """
        try:
            logger.info("Creating asset browser widget")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Create widget
            widget = AssetBrowserWidget(self._asset_manager, parent)
            
            # Connect signals
            widget.asset_selected.connect(self.asset_selected.emit)
            
            return widget
        except Exception as e:
            logger.error(f"Failed to create asset browser widget: {e}")
            return None
            
    def create_asset_search_widget(self, parent=None):
        """
        Create an asset search widget.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            
        Returns:
            QWidget: The asset search widget, or None if creation failed.
        """
        try:
            logger.info("Creating asset search widget")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Create widget
            widget = AssetSearchWidget(self._asset_manager, parent)
            
            # Connect signals
            widget.asset_selected.connect(self.asset_selected.emit)
            
            return widget
        except Exception as e:
            logger.error(f"Failed to create asset search widget: {e}")
            return None
            
    def create_asset_import_dialog(self, parent=None):
        """
        Create an asset import dialog.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            
        Returns:
            QWidget: The asset import dialog, or None if creation failed.
        """
        try:
            logger.info("Creating asset import dialog")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Create dialog
            dialog = AssetImportDialog(self._asset_manager, parent)
            
            # Connect signals
            dialog.asset_imported.connect(self.asset_imported.emit)
            
            return dialog
        except Exception as e:
            logger.error(f"Failed to create asset import dialog: {e}")
            return None
            
    def create_asset_export_dialog(self, parent=None):
        """
        Create an asset export dialog.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            
        Returns:
            QWidget: The asset export dialog, or None if creation failed.
        """
        try:
            logger.info("Creating asset export dialog")
            
            # Check if asset manager is available
            if not self.is_available():
                logger.warning("Asset management system is not available")
                return None
                
            # Create dialog
            dialog = AssetExportDialog(self._asset_manager, parent)
            
            # Connect signals
            dialog.asset_exported.connect(lambda asset_path, export_path: self.asset_exported.emit(asset_path, export_path))
            
            return dialog
        except Exception as e:
            logger.error(f"Failed to create asset export dialog: {e}")
            return None


class AssetBrowserWidget(QWidget):
    """Asset browser widget."""
    
    # Signals
    asset_selected = pyqtSignal(str)  # asset_path
    
    def __init__(self, asset_manager, parent=None):
        """
        Initialize the asset browser widget.
        
        Args:
            asset_manager (AssetManager): The asset manager.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        
        self.asset_manager = asset_manager
        self.current_directory = ''
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)
        
        # Create back button
        self.back_button = QPushButton('Back')
        self.back_button.clicked.connect(self._on_back_clicked)
        toolbar_layout.addWidget(self.back_button)
        
        # Create path label
        self.path_label = QLabel('/')
        toolbar_layout.addWidget(self.path_label)
        
        # Create spacer
        toolbar_layout.addStretch()
        
        # Create refresh button
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        toolbar_layout.addWidget(self.refresh_button)
        
        # Create tree view
        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)
        
        # Load assets
        self._load_directory('')
        
    def _load_directory(self, directory):
        """
        Load a directory.
        
        Args:
            directory (str): The directory path.
        """
        try:
            # Load directory
            assets = self.asset_manager.load_directory(directory)
            
            # Update current directory
            self.current_directory = directory
            
            # Update path label
            self.path_label.setText(f'/{directory}')
            
            # TODO: Update tree view model
            
        except Exception as e:
            logger.error(f"Failed to load directory {directory}: {e}")
            
    def _on_back_clicked(self):
        """Handle back button clicked."""
        try:
            # Get parent directory
            parent_dir = os.path.dirname(self.current_directory)
            
            # Load parent directory
            self._load_directory(parent_dir)
        except Exception as e:
            logger.error(f"Failed to handle back button clicked: {e}")
            
    def _on_refresh_clicked(self):
        """Handle refresh button clicked."""
        try:
            # Reload current directory
            self._load_directory(self.current_directory)
        except Exception as e:
            logger.error(f"Failed to handle refresh button clicked: {e}")


class AssetSearchWidget(QWidget):
    """Asset search widget."""
    
    # Signals
    asset_selected = pyqtSignal(str)  # asset_path
    
    def __init__(self, asset_manager, parent=None):
        """
        Initialize the asset search widget.
        
        Args:
            asset_manager (AssetManager): The asset manager.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        
        self.asset_manager = asset_manager
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create search bar
        search_layout = QHBoxLayout()
        layout.addLayout(search_layout)
        
        # Create search label
        search_label = QLabel('Search:')
        search_layout.addWidget(search_label)
        
        # Create search input
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        # Create search button
        self.search_button = QPushButton('Search')
        self.search_button.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_button)
        
        # Create filter layout
        filter_layout = QHBoxLayout()
        layout.addLayout(filter_layout)
        
        # Create type label
        type_label = QLabel('Type:')
        filter_layout.addWidget(type_label)
        
        # Create type combo box
        self.type_combo = QComboBox()
        self.type_combo.addItem('All', None)
        self.type_combo.addItem('Texture', AssetType.TEXTURE)
        self.type_combo.addItem('Model', AssetType.MODEL)
        self.type_combo.addItem('Audio', AssetType.AUDIO)
        self.type_combo.addItem('Script', AssetType.SCRIPT)
        self.type_combo.addItem('Document', AssetType.DOCUMENT)
        filter_layout.addWidget(self.type_combo)
        
        # Create spacer
        filter_layout.addStretch()
        
        # Create tree view
        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)
        
    def _on_search(self):
        """Handle search."""
        try:
            # Get search query
            query = self.search_input.text()
            
            # Get selected type
            type_index = self.type_combo.currentIndex()
            asset_type = self.type_combo.itemData(type_index)
            
            # Create filter
            filter_dict = {
                'searchQuery': query
            }
            
            if asset_type:
                filter_dict['types'] = [asset_type]
                
            # Search assets
            results = self.asset_manager.search_assets(filter_dict)
            
            # TODO: Update tree view model
            
        except Exception as e:
            logger.error(f"Failed to handle search: {e}")


class AssetImportDialog(QWidget):
    """Asset import dialog."""
    
    # Signals
    asset_imported = pyqtSignal(str)  # asset_path
    
    def __init__(self, asset_manager, parent=None):
        """
        Initialize the asset import dialog.
        
        Args:
            asset_manager (AssetManager): The asset manager.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        
        self.asset_manager = asset_manager
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create file layout
        file_layout = QHBoxLayout()
        layout.addLayout(file_layout)
        
        # Create file label
        file_label = QLabel('File:')
        file_layout.addWidget(file_label)
        
        # Create file input
        self.file_input = QLineEdit()
        file_layout.addWidget(self.file_input)
        
        # Create browse button
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(self.browse_button)
        
        # Create type layout
        type_layout = QHBoxLayout()
        layout.addLayout(type_layout)
        
        # Create type label
        type_label = QLabel('Type:')
        type_layout.addWidget(type_label)
        
        # Create type combo box
        self.type_combo = QComboBox()
        self.type_combo.addItem('Auto-detect', None)
        self.type_combo.addItem('Texture', AssetType.TEXTURE)
        self.type_combo.addItem('Model', AssetType.MODEL)
        self.type_combo.addItem('Audio', AssetType.AUDIO)
        self.type_combo.addItem('Script', AssetType.SCRIPT)
        self.type_combo.addItem('Document', AssetType.DOCUMENT)
        type_layout.addWidget(self.type_combo)
        
        # Create spacer
        type_layout.addStretch()
        
        # Create button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Create spacer
        button_layout.addStretch()
        
        # Create import button
        self.import_button = QPushButton('Import')
        self.import_button.clicked.connect(self._on_import_clicked)
        button_layout.addWidget(self.import_button)
        
        # Create cancel button
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
    def _on_browse_clicked(self):
        """Handle browse button clicked."""
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(self, 'Select File')
            
            if file_path:
                # Set file input
                self.file_input.setText(file_path)
        except Exception as e:
            logger.error(f"Failed to handle browse button clicked: {e}")
            
    def _on_import_clicked(self):
        """Handle import button clicked."""
        try:
            # Get file path
            file_path = self.file_input.text()
            
            if not file_path:
                logger.warning("No file selected")
                return
                
            # Get selected type
            type_index = self.type_combo.currentIndex()
            asset_type = self.type_combo.itemData(type_index)
            
            # Import asset
            asset = self.asset_manager.import_asset(file_path, asset_type)
            
            if asset:
                # Emit signal
                self.asset_imported.emit(asset.path)
                
                # Close dialog
                self.close()
        except Exception as e:
            logger.error(f"Failed to handle import button clicked: {e}")


class AssetExportDialog(QWidget):
    """Asset export dialog."""
    
    # Signals
    asset_exported = pyqtSignal(str, str)  # asset_path, export_path
    
    def __init__(self, asset_manager, parent=None):
        """
        Initialize the asset export dialog.
        
        Args:
            asset_manager (AssetManager): The asset manager.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        
        self.asset_manager = asset_manager
        self.asset_path = None
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create asset layout
        asset_layout = QHBoxLayout()
        layout.addLayout(asset_layout)
        
        # Create asset label
        asset_label = QLabel('Asset:')
        asset_layout.addWidget(asset_label)
        
        # Create asset input
        self.asset_input = QLineEdit()
        self.asset_input.setReadOnly(True)
        asset_layout.addWidget(self.asset_input)
        
        # Create file layout
        file_layout = QHBoxLayout()
        layout.addLayout(file_layout)
        
        # Create file label
        file_label = QLabel('Export to:')
        file_layout.addWidget(file_label)
        
        # Create file input
        self.file_input = QLineEdit()
        file_layout.addWidget(self.file_input)
        
        # Create browse button
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(self.browse_button)
        
        # Create type layout
        type_layout = QHBoxLayout()
        layout.addLayout(type_layout)
        
        # Create type label
        type_label = QLabel('Type:')
        type_layout.addWidget(type_label)
        
        # Create type combo box
        self.type_combo = QComboBox()
        self.type_combo.addItem('Auto-detect', None)
        self.type_combo.addItem('Texture', 'texture')
        self.type_combo.addItem('Model', 'model')
        self.type_combo.addItem('Audio', 'audio')
        self.type_combo.addItem('Script', 'script')
        self.type_combo.addItem('Document', 'document')
        type_layout.addWidget(self.type_combo)
        
        # Create spacer
        type_layout.addStretch()
        
        # Create button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Create spacer
        button_layout.addStretch()
        
        # Create export button
        self.export_button = QPushButton('Export')
        self.export_button.clicked.connect(self._on_export_clicked)
        button_layout.addWidget(self.export_button)
        
        # Create cancel button
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
    def set_asset(self, asset_path):
        """
        Set the asset to export.
        
        Args:
            asset_path (str): The asset path.
        """
        self.asset_path = asset_path
        self.asset_input.setText(asset_path)
        
        # Set default export path
        file_name = os.path.basename(asset_path)
        self.file_input.setText(os.path.join(os.path.expanduser('~'), file_name))
        
    def _on_browse_clicked(self):
        """Handle browse button clicked."""
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(self, 'Export To')
            
            if file_path:
                # Set file input
                self.file_input.setText(file_path)
        except Exception as e:
            logger.error(f"Failed to handle browse button clicked: {e}")
            
    def _on_export_clicked(self):
        """Handle export button clicked."""
        try:
            # Check if asset is set
            if not self.asset_path:
                logger.warning("No asset selected")
                return
                
            # Get export path
            export_path = self.file_input.text()
            
            if not export_path:
                logger.warning("No export path specified")
                return
                
            # Get selected type
            type_index = self.type_combo.currentIndex()
            export_type = self.type_combo.itemData(type_index)
            
            # Export asset
            success = self.asset_manager.export_asset(self.asset_path, export_path, export_type)
            
            if success:
                # Emit signal
                self.asset_exported.emit(self.asset_path, export_path)
                
                # Close dialog
                self.close()
        except Exception as e:
            logger.error(f"Failed to handle export button clicked: {e}")
