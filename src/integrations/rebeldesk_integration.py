#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelDESK Integration Module for RebelSCRIBE.

This module provides functionality for integrating RebelSCRIBE with RebelDESK,
enabling documentation management, editing, publishing, version control, and search
capabilities within the RebelDESK IDE.
"""

import os
import sys
import re
import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Add parent directory to path to allow imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.backend.models.documentation import Documentation
from src.backend.services.documentation_manager import DocumentationManager
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class RebelDESKIntegration:
    """
    Integration class for RebelDESK.
    
    This class provides functionality for integrating RebelSCRIBE with RebelDESK,
    enabling documentation management, editing, publishing, version control, and search
    capabilities within the RebelDESK IDE.
    """
    
    def __init__(self, rebelsuite_root: str = None):
        """
        Initialize the RebelDESK integration.
        
        Args:
            rebelsuite_root: The root directory of the RebelSUITE project.
                             If None, it will try to detect it automatically.
        """
        self.doc_manager = DocumentationManager()
        
        # Set RebelSUITE root directory
        if rebelsuite_root:
            self.rebelsuite_root = rebelsuite_root
        else:
            # Try to detect RebelSUITE root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.rebelsuite_root = self._find_rebelsuite_root(current_dir)
            if not self.rebelsuite_root:
                raise ValueError("Could not detect RebelSUITE root directory")
        
        # Set RebelDESK directory
        self.rebeldesk_dir = os.path.join(self.rebelsuite_root, "RebelDESK")
        if not os.path.exists(self.rebeldesk_dir):
            raise ValueError(f"RebelDESK directory not found: {self.rebeldesk_dir}")
        
        logger.info(f"RebelDESK integration initialized with RebelSUITE root: {self.rebelsuite_root}")
    
    def _find_rebelsuite_root(self, start_dir: str) -> Optional[str]:
        """
        Find the RebelSUITE root directory by looking for specific markers.
        
        Args:
            start_dir: The directory to start the search from.
            
        Returns:
            The RebelSUITE root directory, or None if not found.
        """
        current_dir = start_dir
        max_levels = 5  # Maximum number of parent directories to check
        
        for _ in range(max_levels):
            # Check if this is the RebelSUITE root directory
            if os.path.exists(os.path.join(current_dir, "RebelCAD")) and \
               os.path.exists(os.path.join(current_dir, "RebelSCRIBE")) and \
               os.path.exists(os.path.join(current_dir, "RebelSUITE_Integration_Tracking.md")):
                return current_dir
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached the root of the filesystem
                break
            current_dir = parent_dir
        
        return None
    
    def extract_documentation(self, output_dir: str = None) -> List[Documentation]:
        """
        Extract documentation from RebelDESK source code.
        
        Args:
            output_dir: The directory to output the documentation to.
                        If None, it will use the default RebelSCRIBE docs directory.
                        
        Returns:
            A list of Documentation objects.
        """
        logger.info("Extracting documentation from RebelDESK source code")
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.join(self.rebelsuite_root, "RebelSCRIBE", "docs", "rebeldesk")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract documentation from source code
        src_dir = os.path.join(self.rebeldesk_dir, "src")
        
        # Extract documentation from Python files
        python_docs = self._extract_from_directory(
            src_dir,
            Documentation.COMPONENT_DESK,
            Documentation.LANGUAGE_PYTHON
        )
        
        # Generate documentation files
        self._generate_documentation_files(python_docs, output_dir)
        
        logger.info(f"Extracted {len(python_docs)} documentation items from RebelDESK")
        return python_docs
    
    def _extract_from_directory(self, directory: str, component: str, language: str) -> List[Documentation]:
        """
        Extract documentation from all source files in a directory.
        
        Args:
            directory: The directory to extract documentation from.
            component: The component name.
            language: The programming language.
            
        Returns:
            A list of Documentation objects.
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return []
        
        docs = []
        
        # Walk through the directory
        for root, _, files in os.walk(directory):
            for file in files:
                # Check if this is a Python file
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    
                    # Read source code
                    with open(file_path, "r", encoding="utf-8") as f:
                        source_code = f.read()
                    
                    # Create documentation for the file
                    file_name = os.path.basename(file_path)
                    doc = Documentation(
                        title=file_name,
                        type=Documentation.TYPE_CODE,
                        content="",
                        source_code=source_code,
                        language=Documentation.LANGUAGE_PYTHON,
                        component=component,
                        api_version="1.0.0"
                    )
                    
                    # Extract documentation from source code
                    success = doc.extract_documentation_from_code()
                    if not success:
                        logger.warning(f"Failed to extract documentation from: {file_path}")
                    
                    if doc:
                        docs.append(doc)
                    
                    # Extract class and function documentation
                    class_docs, function_docs = self._extract_python_docs(file_path, source_code, component)
                    docs.extend(class_docs)
                    docs.extend(function_docs)
        
        return docs
    
    def _extract_python_docs(self, file_path: str, source_code: str, component: str) -> Tuple[List[Documentation], List[Documentation]]:
        """
        Extract class and function documentation from Python source code.
        
        Args:
            file_path: The path to the Python file.
            source_code: The source code to extract documentation from.
            component: The component name.
            
        Returns:
            A tuple of (class_docs, function_docs).
        """
        class_docs = []
        function_docs = []
        
        # Extract class definitions
        class_matches = re.finditer(r'class\s+(\w+)(?:\(.*?\))?:\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')(?:\s*|$)', source_code, re.DOTALL)
        
        for match in class_matches:
            class_name = match.group(1)
            docstring = match.group(2).strip()
            
            # Create documentation
            doc = Documentation(
                title=class_name,
                type=Documentation.TYPE_CLASS,
                content=docstring,
                source_code=source_code,
                language=Documentation.LANGUAGE_PYTHON,
                component=component,
                api_version="1.0.0"
            )
            
            # Process docstring to extract parameters, returns, etc.
            self._process_python_docstring(doc, docstring)
            
            class_docs.append(doc)
        
        # Extract function definitions
        function_matches = re.finditer(r'def\s+(\w+)\s*\((.*?)\)(?:\s*->.*?)?:\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')(?:\s*|$)', source_code, re.DOTALL)
        
        for match in function_matches:
            function_name = match.group(1)
            parameters = match.group(2).strip()
            docstring = match.group(3).strip()
            
            # Skip if this is a private function (starts with underscore)
            if function_name.startswith('_') and not function_name.startswith('__'):
                continue
            
            # Create documentation
            doc = Documentation(
                title=function_name,
                type=Documentation.TYPE_FUNCTION,
                content=docstring,
                source_code=source_code,
                language=Documentation.LANGUAGE_PYTHON,
                component=component,
                api_version="1.0.0"
            )
            
            # Process docstring to extract parameters, returns, etc.
            self._process_python_docstring(doc, docstring)
            
            # Add parameters from function definition
            if parameters:
                param_list = parameters.split(',')
                for param in param_list:
                    param = param.strip()
                    if param and param != 'self' and param != 'cls':
                        # Check if parameter has a type annotation
                        param_parts = param.split(':')
                        param_name = param_parts[0].strip()
                        
                        # Check if parameter already exists (from docstring)
                        if not doc.has_parameter(param_name):
                            doc.add_parameter(param_name, "")
            
            function_docs.append(doc)
        
        return class_docs, function_docs
    
    def _process_python_docstring(self, doc: Documentation, docstring: str) -> None:
        """
        Process a Python docstring to extract structured information.
        
        Args:
            doc: The Documentation object to update.
            docstring: The docstring to process.
        """
        # Check if this is a Google-style docstring
        if re.search(r'Args:|Returns:|Raises:|Examples:', docstring):
            self._process_google_style_docstring(doc, docstring)
        # Check if this is a NumPy-style docstring
        elif re.search(r'Parameters\s*\n\s*-+|Returns\s*\n\s*-+|Raises\s*\n\s*-+|Examples\s*\n\s*-+', docstring):
            self._process_numpy_style_docstring(doc, docstring)
        # Check if this is a reStructuredText-style docstring
        elif re.search(r':param\s+\w+:|:returns?:|:raises?:|:examples?:', docstring):
            self._process_rest_style_docstring(doc, docstring)
        # Otherwise, just use the docstring as-is
        else:
            doc.content = docstring
    
    def _process_google_style_docstring(self, doc: Documentation, docstring: str) -> None:
        """
        Process a Google-style docstring to extract structured information.
        
        Args:
            doc: The Documentation object to update.
            docstring: The docstring to process.
        """
        # Extract description (text before Args:, Returns:, etc.)
        description_match = re.match(r'(.*?)(?:Args:|Returns:|Raises:|Examples:|$)', docstring, re.DOTALL)
        if description_match:
            doc.content = description_match.group(1).strip()
        
        # Extract parameters
        args_match = re.search(r'Args:(.*?)(?:Returns:|Raises:|Examples:|$)', docstring, re.DOTALL)
        if args_match:
            args_text = args_match.group(1).strip()
            param_matches = re.finditer(r'(\w+)(?:\s*\(.*?\))?\s*:\s*(.*?)(?=\n\s*\w+\s*(?:\(.*?\))?\s*:|$)', args_text, re.DOTALL)
            
            for match in param_matches:
                param_name = match.group(1)
                param_desc = match.group(2).strip()
                doc.add_parameter(param_name, param_desc)
        
        # Extract return value
        returns_match = re.search(r'Returns:(.*?)(?:Raises:|Examples:|$)', docstring, re.DOTALL)
        if returns_match:
            returns_text = returns_match.group(1).strip()
            doc.set_returns(returns_text)
        
        # Extract exceptions
        raises_match = re.search(r'Raises:(.*?)(?:Examples:|$)', docstring, re.DOTALL)
        if raises_match:
            raises_text = raises_match.group(1).strip()
            exception_matches = re.finditer(r'(\w+)(?:\s*\(.*?\))?\s*:\s*(.*?)(?=\n\s*\w+\s*(?:\(.*?\))?\s*:|$)', raises_text, re.DOTALL)
            
            for match in exception_matches:
                exc_type = match.group(1)
                exc_desc = match.group(2).strip()
                doc.add_exception(exc_type, exc_desc)
        
        # Extract examples
        examples_match = re.search(r'Examples:(.*?)$', docstring, re.DOTALL)
        if examples_match:
            examples_text = examples_match.group(1).strip()
            doc.add_example(examples_text)
    
    def _process_numpy_style_docstring(self, doc: Documentation, docstring: str) -> None:
        """
        Process a NumPy-style docstring to extract structured information.
        
        Args:
            doc: The Documentation object to update.
            docstring: The docstring to process.
        """
        # Extract description (text before Parameters, Returns, etc.)
        description_match = re.match(r'(.*?)(?:Parameters\s*\n\s*-+|Returns\s*\n\s*-+|Raises\s*\n\s*-+|Examples\s*\n\s*-+|$)', docstring, re.DOTALL)
        if description_match:
            doc.content = description_match.group(1).strip()
        
        # Extract parameters
        params_match = re.search(r'Parameters\s*\n\s*-+(.*?)(?:Returns\s*\n\s*-+|Raises\s*\n\s*-+|Examples\s*\n\s*-+|$)', docstring, re.DOTALL)
        if params_match:
            params_text = params_match.group(1).strip()
            param_matches = re.finditer(r'(\w+)(?:\s*:\s*.*?)?\s*\n(.*?)(?=\n\s*\w+(?:\s*:\s*.*?)?\s*\n|$)', params_text, re.DOTALL)
            
            for match in param_matches:
                param_name = match.group(1)
                param_desc = match.group(2).strip()
                doc.add_parameter(param_name, param_desc)
        
        # Extract return value
        returns_match = re.search(r'Returns\s*\n\s*-+(.*?)(?:Raises\s*\n\s*-+|Examples\s*\n\s*-+|$)', docstring, re.DOTALL)
        if returns_match:
            returns_text = returns_match.group(1).strip()
            doc.set_returns(returns_text)
        
        # Extract exceptions
        raises_match = re.search(r'Raises\s*\n\s*-+(.*?)(?:Examples\s*\n\s*-+|$)', docstring, re.DOTALL)
        if raises_match:
            raises_text = raises_match.group(1).strip()
            exception_matches = re.finditer(r'(\w+)\s*\n(.*?)(?=\n\s*\w+\s*\n|$)', raises_text, re.DOTALL)
            
            for match in exception_matches:
                exc_type = match.group(1)
                exc_desc = match.group(2).strip()
                doc.add_exception(exc_type, exc_desc)
        
        # Extract examples
        examples_match = re.search(r'Examples\s*\n\s*-+(.*?)$', docstring, re.DOTALL)
        if examples_match:
            examples_text = examples_match.group(1).strip()
            doc.add_example(examples_text)
    
    def _process_rest_style_docstring(self, doc: Documentation, docstring: str) -> None:
        """
        Process a reStructuredText-style docstring to extract structured information.
        
        Args:
            doc: The Documentation object to update.
            docstring: The docstring to process.
        """
        # Extract description (text before :param, :returns, etc.)
        description_match = re.match(r'(.*?)(?::param\s+\w+:|:returns?:|:raises?:|:examples?:|$)', docstring, re.DOTALL)
        if description_match:
            doc.content = description_match.group(1).strip()
        
        # Extract parameters
        param_matches = re.finditer(r':param\s+(\w+):\s*(.*?)(?=:param\s+\w+:|:returns?:|:raises?:|:examples?:|$)', docstring, re.DOTALL)
        for match in param_matches:
            param_name = match.group(1)
            param_desc = match.group(2).strip()
            doc.add_parameter(param_name, param_desc)
        
        # Extract return value
        returns_match = re.search(r':returns?:\s*(.*?)(?::raises?:|:examples?:|$)', docstring, re.DOTALL)
        if returns_match:
            returns_text = returns_match.group(1).strip()
            doc.set_returns(returns_text)
        
        # Extract exceptions
        raises_matches = re.finditer(r':raises?\s+(\w+):\s*(.*?)(?::raises?\s+\w+:|:examples?:|$)', docstring, re.DOTALL)
        for match in raises_matches:
            exc_type = match.group(1)
            exc_desc = match.group(2).strip()
            doc.add_exception(exc_type, exc_desc)
        
        # Extract examples
        examples_match = re.search(r':examples?:\s*(.*?)$', docstring, re.DOTALL)
        if examples_match:
            examples_text = examples_match.group(1).strip()
            doc.add_example(examples_text)
    
    def _generate_documentation_files(self, docs: List[Documentation], output_dir: str) -> None:
        """
        Generate documentation files from Documentation objects.
        
        Args:
            docs: A list of Documentation objects.
            output_dir: The directory to output the documentation to.
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate index.html
        index_html = self._generate_index_html(docs)
        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)
        
        # Generate documentation files
        for doc in docs:
            # Generate HTML
            html = doc.generate_html()
            
            # Write to file
            file_path = os.path.join(output_dir, f"{doc.id}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            # Generate Markdown
            markdown = doc.generate_markdown()
            
            # Write to file
            file_path = os.path.join(output_dir, f"{doc.id}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown)
        
        # Generate search index
        search_index = self._generate_search_index(docs)
        with open(os.path.join(output_dir, "search_index.json"), "w", encoding="utf-8") as f:
            json.dump(search_index, f, indent=2)
    
    def _generate_index_html(self, docs: List[Documentation]) -> str:
        """
        Generate an index.html file for the documentation.
        
        Args:
            docs: A list of Documentation objects.
            
        Returns:
            The generated HTML.
        """
        html = """<!DOCTYPE html>
<html>
<head>
    <title>RebelDESK Documentation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #3498db;
            margin-top: 20px;
        }
        
        .category {
            margin-bottom: 30px;
        }
        
        ul {
            list-style-type: none;
            padding: 0;
        }
        
        li {
            margin-bottom: 5px;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .search {
            margin-bottom: 20px;
        }
        
        #search-input {
            padding: 8px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>RebelDESK Documentation</h1>
    
    <div class="search">
        <input type="text" id="search-input" placeholder="Search documentation...">
    </div>
"""
        
        # Group documentation by type
        docs_by_type = {}
        for doc in docs:
            if doc.type not in docs_by_type:
                docs_by_type[doc.type] = []
            docs_by_type[doc.type].append(doc)
        
        # Add documentation by type
        for doc_type, type_docs in docs_by_type.items():
            # Skip empty categories
            if not type_docs:
                continue
            
            # Get human-readable type name
            type_name = doc_type.capitalize()
            if doc_type == Documentation.TYPE_CLASS:
                type_name = "Classes"
            elif doc_type == Documentation.TYPE_FUNCTION:
                type_name = "Functions"
            elif doc_type == Documentation.TYPE_MODULE:
                type_name = "Modules"
            elif doc_type == Documentation.TYPE_PACKAGE:
                type_name = "Packages"
            elif doc_type == Documentation.TYPE_INTERFACE:
                type_name = "Interfaces"
            elif doc_type == Documentation.TYPE_API:
                type_name = "API Reference"
            elif doc_type == Documentation.TYPE_GUIDE:
                type_name = "Guides"
            elif doc_type == Documentation.TYPE_TUTORIAL:
                type_name = "Tutorials"
            elif doc_type == Documentation.TYPE_REFERENCE:
                type_name = "Reference"
            elif doc_type == Documentation.TYPE_CODE:
                type_name = "Code Documentation"
            
            html += f"""
    <div class="category">
        <h2>{type_name}</h2>
        <ul>
"""
            
            # Sort documentation by title
            type_docs.sort(key=lambda d: d.title)
            
            # Add documentation to HTML
            for doc in type_docs:
                html += f'            <li><a href="{doc.id}.html">{doc.title}</a></li>\n'
            
            html += """        </ul>
    </div>
"""
        
        html += """
    <script>
        // Simple search functionality
        document.getElementById('search-input').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const items = document.querySelectorAll('li');
            
            items.forEach(function(item) {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Show/hide categories based on visible items
            const categories = document.querySelectorAll('.category');
            categories.forEach(function(category) {
                const visibleItems = category.querySelectorAll('li:not([style="display: none;"])');
                if (visibleItems.length === 0) {
                    category.style.display = 'none';
                } else {
                    category.style.display = '';
                }
            });
        });
    </script>
</body>
</html>
"""
        
        return html
    
    def _generate_search_index(self, docs: List[Documentation]) -> Dict[str, Any]:
        """
        Generate a search index for the documentation.
        
        Args:
            docs: A list of Documentation objects.
            
        Returns:
            A dictionary containing the search index.
        """
        search_index = {
            "docs": [],
            "index": {}
        }
        
        # Add documents to search index
        for i, doc in enumerate(docs):
            # Add document
            search_index["docs"].append({
                "id": doc.id,
                "title": doc.title,
                "type": doc.type,
                "content": doc.content,
                "url": f"{doc.id}.html"
            })
            
            # Add terms to index
            terms = set()
            
            # Add title terms
            title_terms = re.findall(r'\w+', doc.title.lower())
            terms.update(title_terms)
            
            # Add content terms
            if doc.content:
                content_terms = re.findall(r'\w+', doc.content.lower())
                terms.update(content_terms)
            
            # Add parameter terms
            for param in doc.parameters:
                param_terms = re.findall(r'\w+', param.name.lower())
                terms.update(param_terms)
                
                if param.description:
                    param_desc_terms = re.findall(r'\w+', param.description.lower())
                    terms.update(param_desc_terms)
            
            # Add return terms
            if doc.returns:
                return_terms = re.findall(r'\w+', doc.returns["description"].lower())
                terms.update(return_terms)
            
            # Add exception terms
            for exc_type, exc_desc in doc.exceptions.items():
                exc_terms = re.findall(r'\w+', exc_type.lower())
                terms.update(exc_terms)
                
                if exc_desc:
                    exc_desc_terms = re.findall(r'\w+', exc_desc.lower())
                    terms.update(exc_desc_terms)
            
            # Add terms to index
            for term in terms:
                if term not in search_index["index"]:
                    search_index["index"][term] = []
                
                if i not in search_index["index"][term]:
                    search_index["index"][term].append(i)
        
        return search_index
    
    def integrate_with_rebeldesk(self) -> bool:
        """
        Integrate RebelSCRIBE with RebelDESK.
        
        This method implements the integration requirements from the RebelSUITE_Integration_Tracking.md file:
        - DESK-SCRIBE-01: Documentation management in DESK
        - DESK-SCRIBE-02: Documentation editing from DESK
        - DESK-SCRIBE-03: Documentation publishing from DESK
        - DESK-SCRIBE-04: Documentation version control
        - DESK-SCRIBE-05: Documentation search from DESK
        
        Returns:
            True if successful, False otherwise.
        """
        logger.info("Integrating RebelSCRIBE with RebelDESK")
        
        try:
            # Extract documentation from RebelDESK source code
            docs = self.extract_documentation()
            
            # Create integration directory in RebelDESK
            integration_dir = os.path.join(self.rebeldesk_dir, "src", "integrations", "rebelscribe")
            os.makedirs(integration_dir, exist_ok=True)
            
            # Create __init__.py
            init_path = os.path.join(integration_dir, "__init__.py")
            with open(init_path, "w", encoding="utf-8") as f:
                f.write('"""RebelSCRIBE integration for RebelDESK."""\n')
            
            # Create integration files
            self._create_documentation_manager(integration_dir)
            self._create_documentation_editor(integration_dir)
            self._create_documentation_browser(integration_dir)
            self._create_version_control(integration_dir)
            
            logger.info("Integration files created successfully")
            return True
        except Exception as e:
            logger.error(f"Error integrating with RebelDESK: {e}", exc_info=True)
            return False
    
    def _create_documentation_manager(self, integration_dir: str) -> None:
        """
        Create the documentation manager module.
        
        Args:
            integration_dir: The integration directory.
        """
        # Copy the documentation manager module
        source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documentation_manager.py")
        target_path = os.path.join(integration_dir, "documentation_manager.py")
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            logger.info(f"Copied documentation manager module to: {target_path}")
        else:
            # Create the documentation manager module
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("""#!/usr/bin/env python3\n""")
