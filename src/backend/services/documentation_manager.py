#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation Manager Service for RebelSCRIBE.

This module provides functionality for creating, loading, saving, and managing documentation.
It extends the DocumentManager to provide documentation-specific functionality.
"""

import os
import json
import logging
import datetime
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils.logging_utils import get_logger
from src.utils import file_utils
from src.utils.config_manager import ConfigManager

from .document_manager import DocumentManager
from ..models.documentation import Documentation

logger = get_logger(__name__)

class DocumentationManager(DocumentManager):
    """
    Manages documentation in RebelSCRIBE.
    
    This class extends the DocumentManager to provide documentation-specific functionality,
    such as extracting documentation from source code, generating documentation, and
    integrating with other RebelSUITE components.
    """
    
    # Documentation file extension
    DOCUMENTATION_FILE_EXTENSION = ".rsdoc"
    
    # Source code file extensions by language
    SOURCE_FILE_EXTENSIONS = {
        Documentation.LANGUAGE_PYTHON: [".py"],
        Documentation.LANGUAGE_CPP: [".cpp", ".h", ".hpp", ".c", ".cc"],
        Documentation.LANGUAGE_JAVASCRIPT: [".js"],
        Documentation.LANGUAGE_TYPESCRIPT: [".ts"],
        Documentation.LANGUAGE_LUA: [".lua"],
        Documentation.LANGUAGE_GLSL: [".glsl", ".vert", ".frag"],
        Documentation.LANGUAGE_HLSL: [".hlsl", ".fx"],
        Documentation.LANGUAGE_RUST: [".rs"],
        Documentation.LANGUAGE_MARKDOWN: [".md"],
        Documentation.LANGUAGE_JSON: [".json"],
        Documentation.LANGUAGE_YAML: [".yaml", ".yml"]
    }
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the DocumentationManager.
        
        Args:
            project_path: The path to the project directory. If None, documentation will be
                          managed independently of a project.
        """
        # Initialize base DocumentManager
        super().__init__(project_path)
        
        # Initialize documentation-specific attributes
        self.config = ConfigManager()
        
        # Initialize documentation indexes
        self._documentation_component_index: Dict[str, Set[str]] = {}
        self._documentation_language_index: Dict[str, Set[str]] = {}
        self._documentation_api_version_index: Dict[str, Set[str]] = {}
    
    def create_documentation(self, title: str, doc_type: str = Documentation.TYPE_REFERENCE,
                           parent_id: Optional[str] = None, content: str = "",
                           **kwargs) -> Optional[Documentation]:
        """
        Create a new documentation document.
        
        Args:
            title: The document title.
            doc_type: The document type.
            parent_id: The parent document ID, or None for a root document.
            content: The document content.
            **kwargs: Additional documentation-specific attributes.
            
        Returns:
            The created documentation, or None if creation failed.
        """
        try:
            # Create documentation
            documentation = Documentation(
                title=title,
                type=doc_type,
                content=content,
                parent_id=parent_id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                **kwargs
            )
            
            # Add to documents
            self.documents[documentation.id] = documentation
            self.modified_documents.add(documentation.id)
            
            # Add to cache
            self.cache.put_document(documentation.id, documentation)
            
            # Update indexes
            self._update_document_indexes(documentation)
            self._update_documentation_indexes(documentation)
            
            logger.info(f"Created documentation: {title}")
            return documentation
        
        except Exception as e:
            logger.error(f"Error creating documentation: {e}", exc_info=True)
            return None
    
    def _update_documentation_indexes(self, documentation: Documentation) -> None:
        """
        Update documentation-specific indexes.
        
        Args:
            documentation: The documentation to index.
        """
        try:
            # Update component index
            if documentation.component:
                if documentation.component not in self._documentation_component_index:
                    self._documentation_component_index[documentation.component] = set()
                self._documentation_component_index[documentation.component].add(documentation.id)
            
            # Update language index
            if documentation.language:
                if documentation.language not in self._documentation_language_index:
                    self._documentation_language_index[documentation.language] = set()
                self._documentation_language_index[documentation.language].add(documentation.id)
            
            # Update API version index
            if documentation.api_version:
                if documentation.api_version not in self._documentation_api_version_index:
                    self._documentation_api_version_index[documentation.api_version] = set()
                self._documentation_api_version_index[documentation.api_version].add(documentation.id)
        
        except Exception as e:
            logger.error(f"Error updating documentation indexes: {e}", exc_info=True)
    
    def get_documentation(self, document_id: str) -> Optional[Documentation]:
        """
        Get a documentation document by ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The documentation, or None if not found or not a documentation document.
        """
        document = self.get_document(document_id)
        if document and isinstance(document, Documentation):
            return document
        return None
    
    def get_documentation_by_component(self, component: str) -> List[Documentation]:
        """
        Get all documentation for a specific component.
        
        Args:
            component: The component name.
            
        Returns:
            A list of documentation documents for the specified component.
        """
        # Use index for faster lookup
        if component in self._documentation_component_index:
            return [self.get_documentation(doc_id) for doc_id in self._documentation_component_index[component]
                   if self.get_documentation(doc_id) is not None]
        return []
    
    def get_documentation_by_language(self, language: str) -> List[Documentation]:
        """
        Get all documentation for a specific language.
        
        Args:
            language: The language.
            
        Returns:
            A list of documentation documents for the specified language.
        """
        # Use index for faster lookup
        if language in self._documentation_language_index:
            return [self.get_documentation(doc_id) for doc_id in self._documentation_language_index[language]
                   if self.get_documentation(doc_id) is not None]
        return []
    
    def get_documentation_by_api_version(self, api_version: str) -> List[Documentation]:
        """
        Get all documentation for a specific API version.
        
        Args:
            api_version: The API version.
            
        Returns:
            A list of documentation documents for the specified API version.
        """
        # Use index for faster lookup
        if api_version in self._documentation_api_version_index:
            return [self.get_documentation(doc_id) for doc_id in self._documentation_api_version_index[api_version]
                   if self.get_documentation(doc_id) is not None]
        return []
    
    def extract_documentation_from_file(self, file_path: str, component: str = "",
                                      api_version: str = "") -> Optional[Documentation]:
        """
        Extract documentation from a source code file.
        
        Args:
            file_path: The path to the source code file.
            component: The RebelSUITE component this documentation is associated with.
            api_version: The API version this documentation is for.
            
        Returns:
            The extracted documentation, or None if extraction failed.
        """
        try:
            # Check if file exists
            if not file_utils.file_exists(file_path):
                logger.error(f"Source file not found: {file_path}")
                return None
            
            # Determine language from file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            language = None
            
            for lang, extensions in self.SOURCE_FILE_EXTENSIONS.items():
                if file_ext in extensions:
                    language = lang
                    break
            
            if not language:
                logger.error(f"Unsupported file extension: {file_ext}")
                return None
            
            # Read source code
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            
            # Create documentation
            file_name = os.path.basename(file_path)
            documentation = self.create_documentation(
                title=file_name,
                doc_type=Documentation.TYPE_CODE,
                content="",
                source_code=source_code,
                language=language,
                component=component,
                api_version=api_version
            )
            
            if not documentation:
                return None
            
            # Extract documentation from source code
            success = documentation.extract_documentation_from_code()
            if not success:
                logger.warning(f"Failed to extract documentation from: {file_path}")
            
            # Save documentation
            self.save_document(documentation.id)
            
            logger.info(f"Extracted documentation from: {file_path}")
            return documentation
        
        except Exception as e:
            logger.error(f"Error extracting documentation from file: {e}", exc_info=True)
            return None
    
    def extract_documentation_from_directory(self, directory_path: str, component: str = "",
                                           api_version: str = "", recursive: bool = True) -> List[Documentation]:
        """
        Extract documentation from all source code files in a directory.
        
        Args:
            directory_path: The path to the directory.
            component: The RebelSUITE component this documentation is associated with.
            api_version: The API version this documentation is for.
            recursive: Whether to search subdirectories recursively.
            
        Returns:
            A list of extracted documentation documents.
        """
        try:
            # Check if directory exists
            if not file_utils.directory_exists(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return []
            
            # Get all supported file extensions
            supported_extensions = []
            for extensions in self.SOURCE_FILE_EXTENSIONS.values():
                supported_extensions.extend(extensions)
            
            # Find all source code files
            source_files = []
            if recursive:
                for root, _, files in os.walk(directory_path):
                    for file in files:
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext in supported_extensions:
                            source_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(directory_path):
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in supported_extensions:
                        source_files.append(os.path.join(directory_path, file))
            
            # Extract documentation from each file
            documentation_list = []
            for file_path in source_files:
                documentation = self.extract_documentation_from_file(file_path, component, api_version)
                if documentation:
                    documentation_list.append(documentation)
            
            logger.info(f"Extracted documentation from {len(documentation_list)} files in: {directory_path}")
            return documentation_list
        
        except Exception as e:
            logger.error(f"Error extracting documentation from directory: {e}", exc_info=True)
            return []
    
    def generate_markdown_documentation(self, document_id: str) -> str:
        """
        Generate Markdown documentation for a document.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The generated Markdown documentation, or an empty string if generation failed.
        """
        try:
            # Get documentation
            documentation = self.get_documentation(document_id)
            if not documentation:
                logger.error(f"Documentation not found: {document_id}")
                return ""
            
            # Generate Markdown
            markdown = documentation.generate_markdown()
            
            logger.info(f"Generated Markdown documentation for: {documentation.title}")
            return markdown
        
        except Exception as e:
            logger.error(f"Error generating Markdown documentation: {e}", exc_info=True)
            return ""
    
    def generate_html_documentation(self, document_id: str) -> str:
        """
        Generate HTML documentation for a document.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The generated HTML documentation, or an empty string if generation failed.
        """
        try:
            # Get documentation
            documentation = self.get_documentation(document_id)
            if not documentation:
                logger.error(f"Documentation not found: {document_id}")
                return ""
            
            # Generate HTML
            html = documentation.generate_html()
            
            logger.info(f"Generated HTML documentation for: {documentation.title}")
            return html
        
        except Exception as e:
            logger.error(f"Error generating HTML documentation: {e}", exc_info=True)
            return ""
    
    def export_markdown_documentation(self, document_id: str, export_path: str) -> bool:
        """
        Export Markdown documentation for a document to a file.
        
        Args:
            document_id: The document ID.
            export_path: The path to export to.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Generate Markdown
            markdown = self.generate_markdown_documentation(document_id)
            if not markdown:
                return False
            
            # Ensure export directory exists
            export_dir = os.path.dirname(export_path)
            file_utils.ensure_directory(export_dir)
            
            # Write to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            
            logger.info(f"Exported Markdown documentation to: {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting Markdown documentation: {e}", exc_info=True)
            return False
    
    def export_html_documentation(self, document_id: str, export_path: str) -> bool:
        """
        Export HTML documentation for a document to a file.
        
        Args:
            document_id: The document ID.
            export_path: The path to export to.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Generate HTML
            html = self.generate_html_documentation(document_id)
            if not html:
                return False
            
            # Ensure export directory exists
            export_dir = os.path.dirname(export_path)
            file_utils.ensure_directory(export_dir)
            
            # Write to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Exported HTML documentation to: {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting HTML documentation: {e}", exc_info=True)
            return False
    
    def generate_static_site(self, export_dir: str, documents: Optional[List[str]] = None) -> bool:
        """
        Generate a static documentation site.
        
        Args:
            export_dir: The directory to export to.
            documents: A list of document IDs to include, or None for all documents.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure export directory exists
            file_utils.ensure_directory(export_dir)
            
            # Create index.html
            index_html = self._generate_index_html(documents)
            with open(os.path.join(export_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(index_html)
            
            # Create CSS file
            css = self._generate_css()
            with open(os.path.join(export_dir, "style.css"), "w", encoding="utf-8") as f:
                f.write(css)
            
            # Create JavaScript file
            js = self._generate_js()
            with open(os.path.join(export_dir, "script.js"), "w", encoding="utf-8") as f:
                f.write(js)
            
            # Create documentation pages
            if documents is None:
                # Get all documentation documents
                documents = []
                for doc_id, doc in self.documents.items():
                    if isinstance(doc, Documentation):
                        documents.append(doc_id)
            
            # Create documentation directory
            docs_dir = os.path.join(export_dir, "docs")
            file_utils.ensure_directory(docs_dir)
            
            # Generate documentation pages
            for doc_id in documents:
                documentation = self.get_documentation(doc_id)
                if documentation:
                    # Generate HTML
                    html = documentation.generate_html()
                    
                    # Add site header and footer
                    html = html.replace("</head>", f"<link rel='stylesheet' href='../style.css'></head>")
                    html = html.replace("<body>", "<body><header><a href='../index.html'>Home</a></header>")
                    html = html.replace("</body>", "<footer>&copy; 2025 RebelSUITE</footer><script src='../script.js'></script></body>")
                    
                    # Write to file
                    with open(os.path.join(docs_dir, f"{doc_id}.html"), "w", encoding="utf-8") as f:
                        f.write(html)
            
            logger.info(f"Generated static documentation site in: {export_dir}")
            return True
        
        except Exception as e:
            logger.error(f"Error generating static documentation site: {e}", exc_info=True)
            return False
    
    def _generate_index_html(self, documents: Optional[List[str]] = None) -> str:
        """
        Generate the index.html file for the static site.
        
        Args:
            documents: A list of document IDs to include, or None for all documents.
            
        Returns:
            The generated HTML.
        """
        try:
            html = """<!DOCTYPE html>
<html>
<head>
    <title>RebelSUITE Documentation</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>RebelSUITE Documentation</h1>
    </header>
    <main>
        <section class="search">
            <input type="text" id="search-input" placeholder="Search documentation...">
        </section>
        <section class="components">
            <h2>Components</h2>
            <ul>
"""
            
            # Get all components
            components = set()
            for doc_id, doc in self.documents.items():
                if isinstance(doc, Documentation) and doc.component:
                    if documents is None or doc_id in documents:
                        components.add(doc.component)
            
            # Add components to HTML
            for component in sorted(components):
                html += f"                <li><a href='#component-{component}'>{component}</a></li>\n"
            
            html += """            </ul>
        </section>
"""
            
            # Add documentation by component
            for component in sorted(components):
                html += f"        <section id='component-{component}' class='component'>\n"
                html += f"            <h2>{component}</h2>\n"
                html += f"            <ul>\n"
                
                # Get documentation for this component
                component_docs = []
                for doc_id, doc in self.documents.items():
                    if isinstance(doc, Documentation) and doc.component == component:
                        if documents is None or doc_id in documents:
                            component_docs.append(doc)
                
                # Sort by title
                component_docs.sort(key=lambda d: d.title)
                
                # Add documentation to HTML
                for doc in component_docs:
                    html += f"                <li><a href='docs/{doc.id}.html'>{doc.title}</a></li>\n"
                
                html += f"            </ul>\n"
                html += f"        </section>\n"
            
            html += """    </main>
    <footer>
        &copy; 2025 RebelSUITE
    </footer>
    <script src="script.js"></script>
</body>
</html>
"""
            
            return html
        
        except Exception as e:
            logger.error(f"Error generating index.html: {e}", exc_info=True)
            return ""
    
    def _generate_css(self) -> str:
        """
        Generate the CSS file for the static site.
        
        Returns:
            The generated CSS.
        """
        return """/* RebelSUITE Documentation CSS */

/* Global styles */
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem;
    text-align: center;
}

header a {
    color: white;
    text-decoration: none;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

footer {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
}

/* Search */
.search {
    margin-bottom: 2rem;
}

#search-input {
    width: 100%;
    padding: 0.5rem;
    font-size: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

/* Components */
.components {
    margin-bottom: 2rem;
}

.components ul {
    list-style-type: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.components li {
    background-color: #f4f4f4;
    padding: 0.5rem 1rem;
    border-radius: 4px;
}

.components a {
    text-decoration: none;
    color: #2c3e50;
}

/* Component sections */
.component {
    margin-bottom: 2rem;
    padding: 1rem;
    background-color: #f9f9f9;
    border-radius: 4px;
}

.component h2 {
    margin-top: 0;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.5rem;
}

.component ul {
    list-style-type: none;
    padding: 0;
}

.component li {
    margin-bottom: 0.5rem;
}

.component a {
    text-decoration: none;
    color: #3498db;
}

.component a:hover {
    text-decoration: underline;
}

/* Documentation pages */
h1 {
    margin-top: 0;
    color: #2c3e50;
}

h2 {
    color: #3498db;
    margin-top: 2rem;
}

h3 {
    color: #2c3e50;
}

code {
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: monospace;
}

pre {
    background-color: #f4f4f4;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
}

.deprecated {
    background-color: #fff3cd;
    padding: 1rem;
    border-left: 4px solid #ffc107;
    margin-bottom: 1rem;
}

.version {
    color: #666;
    font-style: italic;
    margin-bottom: 1rem;
}

.param-name {
    font-weight: bold;
}

.param-type {
    color: #6c757d;
}
"""
    
    def _generate_js(self) -> str:
        """
        Generate the JavaScript file for the static site.
        
        Returns:
            The generated JavaScript.
        """
        return """// RebelSUITE Documentation JavaScript

// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            // Get all documentation links
            const links = document.querySelectorAll('.component li a');
            
            // Filter links based on search term
            links.forEach(function(link) {
                const text = link.textContent.toLowerCase();
                const listItem = link.parentElement;
                
                if (text.includes(searchTerm)) {
                    listItem.style.display = '';
                } else {
                    listItem.style.display = 'none';
                }
            });
            
            // Show/hide component sections based on visible links
            const components = document.querySelectorAll('.component');
            components.forEach(function(component) {
                const visibleLinks = component.querySelectorAll('li[style="display: none;"]');
                if (visibleLinks.length === component.querySelectorAll('li').length) {
                    component.style.display = 'none';
                } else {
                    component.style.display = '';
                }
            });
        });
    }
});
"""
    
    def integrate_with_component(self, component: str, source_dir: str, output_dir: str) -> bool:
        """
        Integrate with a RebelSUITE component by extracting documentation from its source code.
        
        Args:
            component: The component name.
            source_dir: The source directory of the component.
            output_dir: The output directory for the documentation.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Extract documentation from source code
            documentation_list = self.extract_documentation_from_directory(source_dir, component)
            
            # Generate static site
            doc_ids = [doc.id for doc in documentation_list]
            success = self.generate_static_site(output_dir, doc_ids)
            
            logger.info(f"Integrated with component {component}: {len(documentation_list)} documents")
            return success
        
        except Exception as e:
            logger.error(f"Error integrating with component {component}: {e}", exc_info=True)
            return False
