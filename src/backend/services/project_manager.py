#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Manager Service for RebelSCRIBE.

This module provides functionality for creating, loading, saving, and managing projects.
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from ..models.project import Project
from ..models.document import Document
from src.utils import file_utils
from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager

logger = get_logger(__name__)

class ProjectManager:
    """
    Manages writing projects in RebelSCRIBE.
    
    This class provides functionality for creating, loading, saving,
    and managing writing projects, including their documents and metadata.
    """
    
    # Project file extension
    PROJECT_FILE_EXTENSION = ".rebelscribe"
    
    # Project structure
    PROJECT_STRUCTURE = {
        "project.json": "Project metadata",
        "documents/": "Document files",
        "backups/": "Project backups",
        "exports/": "Exported files",
        "templates/": "Project templates",
        "resources/": "Project resources (images, etc.)",
        "settings.json": "Project-specific settings"
    }
    
    # Default project templates
    DEFAULT_TEMPLATES = {
        "novel": {
            "title": "New Novel",
            "description": "A novel project template",
            "structure": [
                {"type": Document.TYPE_FOLDER, "title": "Manuscript"},
                {"type": Document.TYPE_FOLDER, "title": "Characters"},
                {"type": Document.TYPE_FOLDER, "title": "Locations"},
                {"type": Document.TYPE_FOLDER, "title": "Research"},
                {"type": Document.TYPE_FOLDER, "title": "Notes"}
            ]
        },
        "short_story": {
            "title": "New Short Story",
            "description": "A short story project template",
            "structure": [
                {"type": Document.TYPE_FOLDER, "title": "Story"},
                {"type": Document.TYPE_FOLDER, "title": "Characters"},
                {"type": Document.TYPE_FOLDER, "title": "Notes"}
            ]
        },
        "screenplay": {
            "title": "New Screenplay",
            "description": "A screenplay project template",
            "structure": [
                {"type": Document.TYPE_FOLDER, "title": "Screenplay"},
                {"type": Document.TYPE_FOLDER, "title": "Characters"},
                {"type": Document.TYPE_FOLDER, "title": "Scenes"},
                {"type": Document.TYPE_FOLDER, "title": "Notes"}
            ]
        },
        "empty": {
            "title": "Empty Project",
            "description": "An empty project with no predefined structure",
            "structure": []
        }
    }
    
    def __init__(self, config_manager=None):
        """
        Initialize the ProjectManager.
        
        Args:
            config_manager: Optional ConfigManager instance. If None, creates a new one.
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager
        self.current_project: Optional[Project] = None
        self.documents: Dict[str, Document] = {}
        self.root_document_ids: List[str] = []
        self.modified: bool = False
        
        # Ensure data directory exists
        self.data_directory = self.config.get("application", "data_directory")
        if self.data_directory:
            # Expand tilde in data directory path
            self.data_directory = file_utils.expand_path(self.data_directory)
            file_utils.ensure_directory(self.data_directory)
    
    def create_project(self, title: str, author: str = "", description: str = "", 
                      template: str = "novel", path: Optional[str] = None) -> Optional[Project]:
        """
        Create a new project.
        
        Args:
            title: The project title.
            author: The project author.
            description: The project description.
            template: The template to use (novel, short_story, screenplay, empty).
            path: The path to save the project to. If None, uses the default location.
            
        Returns:
            The created project, or None if creation failed.
        """
        try:
            # Create project
            project = Project(
                title=title,
                author=author,
                description=description,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            # Set path if provided, otherwise use default
            if path:
                # Expand tilde in path
                path = file_utils.expand_path(path)
                project.set_path(path)
            else:
                # Create a safe filename from the title
                safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
                filename = f"{safe_title.replace(' ', '_')}{self.PROJECT_FILE_EXTENSION}"
                default_path = os.path.join(self.data_directory, filename)
                project.set_path(default_path)
            
            # Set as current project
            self.current_project = project
            self.documents = {}
            self.root_document_ids = []
            self.modified = True
            
            # Create project structure from template
            self._apply_template(template)
            
            # Save the project
            success = self.save_project()
            if not success:
                logger.error(f"Failed to save new project: {title}")
                return None
            
            logger.info(f"Created new project: {title}")
            return project
        
        except Exception as e:
            logger.error(f"Error creating project: {e}", exc_info=True)
            return None
    
    def _apply_template(self, template_name: str) -> None:
        """
        Apply a template to the current project.
        
        Args:
            template_name: The name of the template to apply.
        """
        if not self.current_project:
            logger.error("No current project to apply template to")
            return
        
        # Get template
        template = self.DEFAULT_TEMPLATES.get(template_name)
        if not template:
            logger.warning(f"Template not found: {template_name}. Using 'empty' template.")
            template = self.DEFAULT_TEMPLATES["empty"]
        
        # Create structure
        for item in template["structure"]:
            doc_type = item.get("type", Document.TYPE_FOLDER)
            title = item.get("title", "Untitled")
            
            document = Document(
                title=title,
                type=doc_type,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            self.documents[document.id] = document
            self.root_document_ids.append(document.id)
    
    def load_project(self, path: str) -> Optional[Project]:
        """
        Load a project from a file.
        
        Args:
            path: The path to the project file.
            
        Returns:
            The loaded project, or None if loading failed.
        """
        try:
            # Expand tilde in path
            path = file_utils.expand_path(path)
            
            # Check if file exists
            if not file_utils.file_exists(path):
                logger.error(f"Project file not found: {path}")
                return None
            
            # Check if it's a directory
            if file_utils.directory_exists(path):
                # If it's a directory, look for project.json inside
                project_json_path = os.path.join(path, "project.json")
                if not file_utils.file_exists(project_json_path):
                    logger.error(f"Project file not found in directory: {project_json_path}")
                    return None
                path = project_json_path
            
            # Load project data
            project_data = file_utils.read_json_file(path)
            if not project_data:
                logger.error(f"Failed to read project data from: {path}")
                return None
            
            # Create project from data
            project = Project.from_dict(project_data)
            project.set_path(path)
            
            # Set as current project
            self.current_project = project
            self.modified = False
            
            # Load documents
            self._load_documents()
            
            logger.info(f"Loaded project: {project.title}")
            return project
        
        except Exception as e:
            logger.error(f"Error loading project: {e}", exc_info=True)
            return None
    
    def _load_documents(self) -> None:
        """Load documents for the current project."""
        if not self.current_project or not self.current_project.path:
            logger.error("No current project or project path")
            return
        
        # Clear current documents
        self.documents = {}
        self.root_document_ids = []
        
        # Get project directory
        project_dir = os.path.dirname(self.current_project.path)
        documents_dir = os.path.join(project_dir, "documents")
        
        # Check if documents directory exists
        if not file_utils.directory_exists(documents_dir):
            logger.warning(f"Documents directory not found: {documents_dir}")
            return
        
        # Load document files
        document_files = file_utils.list_files(documents_dir, "*.json")
        for doc_file in document_files:
            try:
                # Load document data
                doc_data = file_utils.read_json_file(doc_file)
                if not doc_data:
                    logger.warning(f"Failed to read document data from: {doc_file}")
                    continue
                
                # Create document from data
                document = Document.from_dict(doc_data)
                self.documents[document.id] = document
                
                # Add to root documents if it has no parent
                if not document.parent_id:
                    self.root_document_ids.append(document.id)
            
            except Exception as e:
                logger.error(f"Error loading document {doc_file}: {e}", exc_info=True)
    
    def save_project(self) -> bool:
        """
        Save the current project.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.current_project or not self.current_project.path:
            logger.error("No current project or project path")
            return False
        
        try:
            # Update project timestamp
            self.current_project.updated_at = datetime.datetime.now()
            
            # Get project directory
            project_dir = os.path.dirname(self.current_project.path)
            
            # Ensure project directory exists
            file_utils.ensure_directory(project_dir)
            
            # Create project structure if it doesn't exist
            for path, description in self.PROJECT_STRUCTURE.items():
                full_path = os.path.join(project_dir, path)
                if path.endswith("/"):
                    file_utils.ensure_directory(full_path)
            
            # Save project data
            project_data = self.current_project.to_dict()
            success = file_utils.write_json_file(self.current_project.path, project_data)
            if not success:
                logger.error(f"Failed to write project data to: {self.current_project.path}")
                return False
            
            # Save documents
            documents_dir = os.path.join(project_dir, "documents")
            file_utils.ensure_directory(documents_dir)  # Ensure documents directory exists
            
            for doc_id, document in self.documents.items():
                doc_path = os.path.join(documents_dir, f"{doc_id}.json")
                doc_data = document.to_dict()
                success = file_utils.write_json_file(doc_path, doc_data)
                if not success:
                    logger.error(f"Failed to write document data to: {doc_path}")
                    return False
            
            self.modified = False
            logger.info(f"Saved project: {self.current_project.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving project: {e}", exc_info=True)
            return False
    
    def close_project(self) -> bool:
        """
        Close the current project.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.current_project:
            logger.warning("No current project to close")
            return True
        
        try:
            # Save if modified
            if self.modified:
                success = self.save_project()
                if not success:
                    logger.error("Failed to save project before closing")
                    return False
            
            # Clear project data
            self.current_project = None
            self.documents = {}
            self.root_document_ids = []
            self.modified = False
            
            logger.info("Closed project")
            return True
        
        except Exception as e:
            logger.error(f"Error closing project: {e}", exc_info=True)
            return False
    
    def get_project_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available projects.
        
        Returns:
            A list of project metadata dictionaries.
        """
        projects = []
        
        try:
            # Check data directory
            if not self.data_directory or not file_utils.directory_exists(self.data_directory):
                logger.warning(f"Data directory not found: {self.data_directory}")
                return projects
            
            # List project files
            project_files = file_utils.list_files(self.data_directory, f"*{self.PROJECT_FILE_EXTENSION}")
            
            # Load basic project info
            for project_file in project_files:
                try:
                    # Read project data
                    project_data = file_utils.read_json_file(project_file)
                    if not project_data:
                        continue
                    
                    # Extract basic info
                    projects.append({
                        "title": project_data.get("title", "Untitled"),
                        "author": project_data.get("author", ""),
                        "description": project_data.get("description", ""),
                        "created_at": project_data.get("created_at", ""),
                        "updated_at": project_data.get("updated_at", ""),
                        "path": project_file
                    })
                
                except Exception as e:
                    logger.error(f"Error reading project file {project_file}: {e}", exc_info=True)
            
            return projects
        
        except Exception as e:
            logger.error(f"Error getting project list: {e}", exc_info=True)
            return []
    
    def create_document(self, title: str, doc_type: str = Document.TYPE_SCENE,
                       parent_id: Optional[str] = None, content: str = "") -> Optional[Document]:
        """
        Create a new document in the current project.
        
        Args:
            title: The document title.
            doc_type: The document type.
            parent_id: The parent document ID, or None for a root document.
            content: The document content.
            
        Returns:
            The created document, or None if creation failed.
        """
        if not self.current_project:
            logger.error("No current project")
            return None
        
        try:
            # Create document
            document = Document(
                title=title,
                type=doc_type,
                content=content,
                parent_id=parent_id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            # Add to documents
            self.documents[document.id] = document
            
            # Add to parent if specified
            if parent_id and parent_id in self.documents:
                parent = self.documents[parent_id]
                parent.add_child(document.id)
            else:
                # Add to root documents
                self.root_document_ids.append(document.id)
            
            self.modified = True
            logger.info(f"Created document: {title}")
            return document
        
        except Exception as e:
            logger.error(f"Error creating document: {e}", exc_info=True)
            return None
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The document, or None if not found.
        """
        return self.documents.get(document_id)
    
    def update_document(self, document_id: str, **kwargs) -> bool:
        """
        Update a document.
        
        Args:
            document_id: The document ID.
            **kwargs: The document properties to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.current_project:
            logger.error("No current project")
            return False
        
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Update properties
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            # Update timestamp
            document.updated_at = datetime.datetime.now()
            
            self.modified = True
            logger.info(f"Updated document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating document: {e}", exc_info=True)
            return False
    
    def rename_document(self, document_id: str, new_title: str) -> bool:
        """
        Rename a document.
        
        Args:
            document_id: The document ID.
            new_title: The new title for the document.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.current_project:
            logger.error("No current project")
            return False
        
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Update title
            document.title = new_title
            
            # Update timestamp
            document.updated_at = datetime.datetime.now()
            
            self.modified = True
            logger.info(f"Renamed document to: {new_title}")
            return True
        
        except Exception as e:
            logger.error(f"Error renaming document: {e}", exc_info=True)
            return False
    
    def delete_document(self, document_id: str, recursive: bool = True) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: The document ID.
            recursive: Whether to delete child documents recursively.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.current_project:
            logger.error("No current project")
            return False
        
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Get child IDs
            child_ids = document.children_ids.copy()
            
            # Delete children recursively if requested
            if recursive and child_ids:
                for child_id in child_ids:
                    self.delete_document(child_id, recursive)
            
            # Remove from parent
            if document.parent_id and document.parent_id in self.documents:
                parent = self.documents[document.parent_id]
                parent.remove_child(document_id)
            
            # Remove from root documents
            if document_id in self.root_document_ids:
                self.root_document_ids.remove(document_id)
            
            # Remove from documents
            del self.documents[document_id]
            
            self.modified = True
            logger.info(f"Deleted document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            return False
    
    def move_document(self, document_id: str, new_parent_id: Optional[str] = None) -> bool:
        """
        Move a document to a new parent.
        
        Args:
            document_id: The document ID.
            new_parent_id: The new parent document ID, or None to make it a root document.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.current_project:
            logger.error("No current project")
            return False
        
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Remove from current parent
            if document.parent_id and document.parent_id in self.documents:
                parent = self.documents[document.parent_id]
                parent.remove_child(document_id)
            
            # Remove from root documents if it's a root document
            if document_id in self.root_document_ids:
                self.root_document_ids.remove(document_id)
            
            # Add to new parent
            if new_parent_id and new_parent_id in self.documents:
                new_parent = self.documents[new_parent_id]
                new_parent.add_child(document_id)
                document.set_parent(new_parent_id)
            else:
                # Make it a root document
                document.set_parent(None)
                self.root_document_ids.append(document_id)
            
            self.modified = True
            logger.info(f"Moved document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error moving document: {e}", exc_info=True)
            return False
    
    def get_document_tree(self) -> List[Dict[str, Any]]:
        """
        Get the document tree for the current project.
        
        Returns:
            A list of dictionaries representing the document tree.
        """
        if not self.current_project:
            logger.error("No current project")
            return []
        
        tree = []
        
        try:
            # Ensure documents are loaded
            if not self.documents:
                self._load_documents()
            
            # Build tree from root documents
            for doc_id in self.root_document_ids:
                document = self.documents.get(doc_id)
                if document:
                    tree.append(self._build_document_tree_node(document))
            
            return tree
        
        except Exception as e:
            logger.error(f"Error getting document tree: {e}", exc_info=True)
            return []
    
    def _build_document_tree_node(self, document: Document) -> Dict[str, Any]:
        """
        Build a document tree node.
        
        Args:
            document: The document.
            
        Returns:
            A dictionary representing the document tree node.
        """
        node = {
            "id": document.id,
            "title": document.title,
            "type": document.type,
            "children": []
        }
        
        # Add children
        for child_id in document.children_ids:
            child = self.documents.get(child_id)
            if child:
                node["children"].append(self._build_document_tree_node(child))
        
        return node
    
    def create_project_from_template(self, template_path: str, title: str, 
                                    author: str = "", description: str = "",
                                    path: Optional[str] = None) -> Optional[Project]:
        """
        Create a new project from a template file.
        
        Args:
            template_path: The path to the template file.
            title: The project title.
            author: The project author.
            description: The project description.
            path: The path to save the project to. If None, uses the default location.
            
        Returns:
            The created project, or None if creation failed.
        """
        try:
            # Expand tilde in template path
            template_path = file_utils.expand_path(template_path)
            
            # Check if template exists
            if not file_utils.file_exists(template_path):
                logger.error(f"Template file not found: {template_path}")
                return None
            
            # Load template data
            template_data = file_utils.read_json_file(template_path)
            if not template_data:
                logger.error(f"Failed to read template data from: {template_path}")
                return None
            
            # Create project
            project = Project(
                title=title,
                author=author,
                description=description,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            # Set path if provided, otherwise use default
            if path:
                # Expand tilde in path
                path = file_utils.expand_path(path)
                project.set_path(path)
            else:
                # Create a safe filename from the title
                safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
                filename = f"{safe_title.replace(' ', '_')}{self.PROJECT_FILE_EXTENSION}"
                default_path = os.path.join(self.data_directory, filename)
                project.set_path(default_path)
            
            # Set as current project
            self.current_project = project
            self.documents = {}
            self.root_document_ids = []
            self.modified = True
            
            # Create project structure from template
            structure = template_data.get("structure", [])
            self._create_structure_from_template(structure)
            
            # Save the project
            success = self.save_project()
            if not success:
                logger.error(f"Failed to save new project from template: {title}")
                return None
            
            logger.info(f"Created new project from template: {title}")
            return project
        
        except Exception as e:
            logger.error(f"Error creating project from template: {e}", exc_info=True)
            return None
    
    def _create_structure_from_template(self, structure: List[Dict[str, Any]], 
                                       parent_id: Optional[str] = None) -> None:
        """
        Create document structure from template.
        
        Args:
            structure: The structure data from the template.
            parent_id: The parent document ID, or None for root documents.
        """
        for item in structure:
            # Create document
            doc_type = item.get("type", Document.TYPE_FOLDER)
            title = item.get("title", "Untitled")
            content = item.get("content", "")
            
            document = Document(
                title=title,
                type=doc_type,
                content=content,
                parent_id=parent_id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            # Add to documents
            self.documents[document.id] = document
            
            # Add to parent if specified
            if parent_id and parent_id in self.documents:
                parent = self.documents[parent_id]
                parent.add_child(document.id)
            else:
                # Add to root documents
                self.root_document_ids.append(document.id)
            
            # Process children
            children = item.get("children", [])
            if children:
                self._create_structure_from_template(children, document.id)
    
    def export_project_template(self, template_name: str, 
                               template_description: str = "") -> Optional[str]:
        """
        Export the current project as a template.
        
        Args:
            template_name: The name for the template.
            template_description: The description for the template.
            
        Returns:
            The path to the exported template, or None if export failed.
        """
        if not self.current_project:
            logger.error("No current project to export as template")
            return None
        
        try:
            # Create template data
            template_data = {
                "name": template_name,
                "description": template_description or f"Template based on {self.current_project.title}",
                "created_at": datetime.datetime.now().isoformat(),
                "structure": self._build_template_structure()
            }
            
            # Create template directory if it doesn't exist
            templates_dir = os.path.join(self.data_directory, "templates")
            file_utils.ensure_directory(templates_dir)
            
            # Create a safe filename from the template name
            safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in template_name)
            filename = f"{safe_name.replace(' ', '_')}.template.json"
            template_path = os.path.join(templates_dir, filename)
            
            # Save template data
            success = file_utils.write_json_file(template_path, template_data)
            if not success:
                logger.error(f"Failed to write template data to: {template_path}")
                return None
            
            logger.info(f"Exported project template: {template_name}")
            return template_path
        
        except Exception as e:
            logger.error(f"Error exporting project template: {e}", exc_info=True)
            return None
    
    def _build_template_structure(self) -> List[Dict[str, Any]]:
        """
        Build template structure from the current project.
        
        Returns:
            A list of dictionaries representing the template structure.
        """
        structure = []
        
        # Build structure from root documents
        for doc_id in self.root_document_ids:
            document = self.documents.get(doc_id)
            if document:
                structure.append(self._build_template_structure_node(document))
        
        return structure
    
    def _build_template_structure_node(self, document: Document) -> Dict[str, Any]:
        """
        Build a template structure node.
        
        Args:
            document: The document.
            
        Returns:
            A dictionary representing the template structure node.
        """
        node = {
            "title": document.title,
            "type": document.type,
            "content": document.content,
            "children": []
        }
        
        # Add children
        for child_id in document.children_ids:
            child = self.documents.get(child_id)
            if child:
                node["children"].append(self._build_template_structure_node(child))
        
        return node
    
    def get_template_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available templates.
        
        Returns:
            A list of template metadata dictionaries.
        """
        templates = []
        
        # Add built-in templates
        for name, template in self.DEFAULT_TEMPLATES.items():
            templates.append({
                "name": template.get("title", name),
                "description": template.get("description", ""),
                "built_in": True,
                "path": None
            })
        
        try:
            # Check templates directory
            templates_dir = os.path.join(self.data_directory, "templates")
            if not file_utils.directory_exists(templates_dir):
                return templates
            
            # List template files
            template_files = file_utils.list_files(templates_dir, "*.template.json")
            
            # Load template info
            for template_file in template_files:
                try:
                    # Read template data
                    template_data = file_utils.read_json_file(template_file)
                    if not template_data:
                        continue
                    
                    # Extract basic info
                    templates.append({
                        "name": template_data.get("name", "Untitled Template"),
                        "description": template_data.get("description", ""),
                        "created_at": template_data.get("created_at", ""),
                        "built_in": False,
                        "path": template_file
                    })
                
                except Exception as e:
                    logger.error(f"Error reading template file {template_file}: {e}", exc_info=True)
            
            return templates
        
        except Exception as e:
            logger.error(f"Error getting template list: {e}", exc_info=True)
            return templates
