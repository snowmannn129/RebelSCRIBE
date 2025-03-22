#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation model for RebelSCRIBE.

This module defines the Documentation class which represents a documentation document in the system.
It extends the base Document class to provide documentation-specific functionality.
"""

import datetime
import json
import uuid
import re
from typing import Dict, List, Optional, Any, Union, Set

import logging
logger = logging.getLogger(__name__)

from .document import Document

class Documentation(Document):
    """
    Represents a documentation document in the system.
    
    This class extends the base Document class to provide documentation-specific functionality,
    such as code documentation extraction, API documentation, and integration with other
    RebelSUITE components.
    
    Attributes:
        All attributes from Document, plus:
        source_code: The source code associated with the documentation.
        language: The programming language of the source code.
        component: The RebelSUITE component this documentation is associated with.
        api_version: The API version this documentation is for.
        examples: Code examples associated with the documentation.
        see_also: References to related documentation.
        parameters: Documentation for function/method parameters.
        returns: Documentation for function/method return values.
        exceptions: Documentation for exceptions that can be raised.
        deprecated: Whether the documented item is deprecated.
        since_version: The version when the documented item was introduced.
        authors: The authors of the documented item.
    """
    # Documentation types
    TYPE_API = "api"
    TYPE_GUIDE = "guide"
    TYPE_TUTORIAL = "tutorial"
    TYPE_REFERENCE = "reference"
    TYPE_CODE = "code"
    TYPE_FUNCTION = "function"
    TYPE_CLASS = "class"
    TYPE_MODULE = "module"
    TYPE_PACKAGE = "package"
    TYPE_INTERFACE = "interface"
    
    # RebelSUITE components
    COMPONENT_CAD = "RebelCAD"
    COMPONENT_CODE = "RebelCODE"
    COMPONENT_ENGINE = "RebelENGINE"
    COMPONENT_FLOW = "RebelFLOW"
    COMPONENT_DESK = "RebelDESK"
    COMPONENT_SCRIBE = "RebelSCRIBE"
    COMPONENT_SUITE = "RebelSUITE"
    
    # Programming languages
    LANGUAGE_PYTHON = "python"
    LANGUAGE_CPP = "cpp"
    LANGUAGE_JAVASCRIPT = "javascript"
    LANGUAGE_TYPESCRIPT = "typescript"
    LANGUAGE_LUA = "lua"
    LANGUAGE_GLSL = "glsl"
    LANGUAGE_HLSL = "hlsl"
    LANGUAGE_RUST = "rust"
    LANGUAGE_MARKDOWN = "markdown"
    LANGUAGE_JSON = "json"
    LANGUAGE_YAML = "yaml"
    
    def __init__(self, id: str = None, title: str = "", content: str = "", 
                 type: str = None, parent_id: str = None, created_at: datetime.datetime = None, 
                 updated_at: datetime.datetime = None, **kwargs):
        """Initialize a new Documentation document."""
        # Set default type if not provided or not a valid documentation type
        doc_type = type
        if not doc_type or doc_type not in [self.TYPE_API, self.TYPE_GUIDE, self.TYPE_TUTORIAL, 
                                          self.TYPE_REFERENCE, self.TYPE_CODE, self.TYPE_FUNCTION,
                                          self.TYPE_CLASS, self.TYPE_MODULE, self.TYPE_PACKAGE,
                                          self.TYPE_INTERFACE, Document.TYPE_FOLDER]:
            doc_type = self.TYPE_REFERENCE
        
        # Initialize base Document
        super().__init__(id=id, title=title, content=content, type=doc_type, 
                        parent_id=parent_id, created_at=created_at, updated_at=updated_at, **kwargs)
        
        # Initialize documentation-specific attributes
        self.source_code = kwargs.get('source_code', "")
        self.language = kwargs.get('language', self.LANGUAGE_PYTHON)
        self.component = kwargs.get('component', "")
        self.api_version = kwargs.get('api_version', "")
        self.examples = kwargs.get('examples', [])
        self.see_also = kwargs.get('see_also', [])
        self.parameters = kwargs.get('parameters', {})
        self.returns = kwargs.get('returns', {})
        self.exceptions = kwargs.get('exceptions', {})
        self.deprecated = kwargs.get('deprecated', False)
        self.since_version = kwargs.get('since_version', "")
        self.authors = kwargs.get('authors', [])
    
    def set_source_code(self, source_code: str) -> None:
        """
        Set the source code associated with the documentation.
        
        Args:
            source_code: The source code.
        """
        self.source_code = source_code
        self.updated_at = datetime.datetime.now()
    
    def set_language(self, language: str) -> None:
        """
        Set the programming language of the source code.
        
        Args:
            language: The programming language.
        """
        self.language = language
        self.updated_at = datetime.datetime.now()
    
    def set_component(self, component: str) -> None:
        """
        Set the RebelSUITE component this documentation is associated with.
        
        Args:
            component: The RebelSUITE component.
        """
        self.component = component
        self.updated_at = datetime.datetime.now()
    
    def set_api_version(self, api_version: str) -> None:
        """
        Set the API version this documentation is for.
        
        Args:
            api_version: The API version.
        """
        self.api_version = api_version
        self.updated_at = datetime.datetime.now()
    
    def add_example(self, example: str) -> None:
        """
        Add a code example to the documentation.
        
        Args:
            example: The code example.
        """
        self.examples.append(example)
        self.updated_at = datetime.datetime.now()
    
    def remove_example(self, index: int) -> None:
        """
        Remove a code example from the documentation.
        
        Args:
            index: The index of the example to remove.
        """
        if 0 <= index < len(self.examples):
            self.examples.pop(index)
            self.updated_at = datetime.datetime.now()
    
    def add_see_also(self, reference: str) -> None:
        """
        Add a reference to related documentation.
        
        Args:
            reference: The reference to add.
        """
        if reference not in self.see_also:
            self.see_also.append(reference)
            self.updated_at = datetime.datetime.now()
    
    def remove_see_also(self, reference: str) -> None:
        """
        Remove a reference to related documentation.
        
        Args:
            reference: The reference to remove.
        """
        if reference in self.see_also:
            self.see_also.remove(reference)
            self.updated_at = datetime.datetime.now()
    
    def add_parameter(self, name: str, description: str, param_type: str = "") -> None:
        """
        Add documentation for a function/method parameter.
        
        Args:
            name: The parameter name.
            description: The parameter description.
            param_type: The parameter type.
        """
        self.parameters[name] = {
            "description": description,
            "type": param_type
        }
        self.updated_at = datetime.datetime.now()
    
    def remove_parameter(self, name: str) -> None:
        """
        Remove documentation for a function/method parameter.
        
        Args:
            name: The parameter name.
        """
        if name in self.parameters:
            del self.parameters[name]
            self.updated_at = datetime.datetime.now()
    
    def set_returns(self, description: str, return_type: str = "") -> None:
        """
        Set documentation for function/method return values.
        
        Args:
            description: The return value description.
            return_type: The return value type.
        """
        self.returns = {
            "description": description,
            "type": return_type
        }
        self.updated_at = datetime.datetime.now()
    
    def add_exception(self, exception_type: str, description: str) -> None:
        """
        Add documentation for an exception that can be raised.
        
        Args:
            exception_type: The exception type.
            description: The exception description.
        """
        self.exceptions[exception_type] = description
        self.updated_at = datetime.datetime.now()
    
    def remove_exception(self, exception_type: str) -> None:
        """
        Remove documentation for an exception.
        
        Args:
            exception_type: The exception type.
        """
        if exception_type in self.exceptions:
            del self.exceptions[exception_type]
            self.updated_at = datetime.datetime.now()
    
    def set_deprecated(self, deprecated: bool, reason: str = "") -> None:
        """
        Set whether the documented item is deprecated.
        
        Args:
            deprecated: Whether the item is deprecated.
            reason: The reason for deprecation.
        """
        self.deprecated = deprecated
        if deprecated and reason:
            self.set_metadata("deprecation_reason", reason)
        self.updated_at = datetime.datetime.now()
    
    def set_since_version(self, since_version: str) -> None:
        """
        Set the version when the documented item was introduced.
        
        Args:
            since_version: The version.
        """
        self.since_version = since_version
        self.updated_at = datetime.datetime.now()
    
    def add_author(self, author: str) -> None:
        """
        Add an author of the documented item.
        
        Args:
            author: The author name.
        """
        if author not in self.authors:
            self.authors.append(author)
            self.updated_at = datetime.datetime.now()
    
    def remove_author(self, author: str) -> None:
        """
        Remove an author of the documented item.
        
        Args:
            author: The author name.
        """
        if author in self.authors:
            self.authors.remove(author)
            self.updated_at = datetime.datetime.now()
    
    def extract_documentation_from_code(self) -> bool:
        """
        Extract documentation from source code.
        
        This method analyzes the source code and extracts documentation from comments,
        docstrings, and other sources based on the programming language.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.source_code:
            logger.warning("No source code to extract documentation from")
            return False
        
        try:
            # Extract documentation based on language
            if self.language == self.LANGUAGE_PYTHON:
                return self._extract_python_documentation()
            elif self.language == self.LANGUAGE_CPP:
                return self._extract_cpp_documentation()
            elif self.language in [self.LANGUAGE_JAVASCRIPT, self.LANGUAGE_TYPESCRIPT]:
                return self._extract_js_documentation()
            elif self.language == self.LANGUAGE_LUA:
                return self._extract_lua_documentation()
            else:
                logger.warning(f"Documentation extraction not implemented for language: {self.language}")
                return False
        
        except Exception as e:
            logger.error(f"Error extracting documentation: {e}", exc_info=True)
            return False
    
    def _extract_python_documentation(self) -> bool:
        """
        Extract documentation from Python source code.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            import ast
            
            # Parse the source code
            tree = ast.parse(self.source_code)
            
            # Extract module docstring
            if (len(tree.body) > 0 and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Str)):
                self.content = tree.body[0].value.s.strip()
            
            # Extract class/function definitions
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    # Extract name
                    name = node.name
                    
                    # Extract docstring
                    docstring = ast.get_docstring(node)
                    if docstring:
                        # Parse docstring for parameters, returns, etc.
                        self._parse_python_docstring(docstring)
                    
                    # Set type based on node type
                    if isinstance(node, ast.ClassDef):
                        self.type = self.TYPE_CLASS
                    else:
                        self.type = self.TYPE_FUNCTION
                    
                    # Set title if not already set
                    if not self.title:
                        self.title = name
                    
                    # Only process the first class/function for now
                    break
            
            return True
        
        except Exception as e:
            logger.error(f"Error extracting Python documentation: {e}", exc_info=True)
            return False
    
    def _parse_python_docstring(self, docstring: str) -> None:
        """
        Parse a Python docstring to extract structured information.
        
        Args:
            docstring: The docstring to parse.
        """
        # Simple parsing for now, can be enhanced with more sophisticated parsing
        lines = docstring.split('\n')
        
        # Extract main description
        description_lines = []
        i = 0
        while i < len(lines) and not (lines[i].strip().startswith('Args:') or 
                                     lines[i].strip().startswith('Parameters:') or
                                     lines[i].strip().startswith('Returns:') or
                                     lines[i].strip().startswith('Raises:') or
                                     lines[i].strip().startswith('Exceptions:')):
            if lines[i].strip():
                description_lines.append(lines[i].strip())
            i += 1
        
        # Set content to description
        if description_lines:
            self.content = '\n'.join(description_lines)
        
        # Parse parameters
        in_params = False
        current_param = None
        param_desc = []
        
        for line in lines:
            line = line.strip()
            
            # Check for parameter section
            if line.startswith('Args:') or line.startswith('Parameters:'):
                in_params = True
                continue
            
            # Check for returns section
            if line.startswith('Returns:'):
                in_params = False
                returns_desc = []
                i = lines.index(line) + 1
                while i < len(lines) and not (lines[i].strip().startswith('Raises:') or
                                             lines[i].strip().startswith('Exceptions:')):
                    if lines[i].strip():
                        returns_desc.append(lines[i].strip())
                    i += 1
                
                if returns_desc:
                    self.set_returns('\n'.join(returns_desc))
                continue
            
            # Check for exceptions section
            if line.startswith('Raises:') or line.startswith('Exceptions:'):
                in_params = False
                i = lines.index(line) + 1
                while i < len(lines) and lines[i].strip():
                    exception_line = lines[i].strip()
                    # Parse exception line (e.g., "ValueError: If x is negative")
                    if ':' in exception_line:
                        exc_type, exc_desc = exception_line.split(':', 1)
                        self.add_exception(exc_type.strip(), exc_desc.strip())
                    i += 1
                continue
            
            # Parse parameter
            if in_params:
                if line and not line.startswith(' ') and ':' in line:
                    # Save previous parameter
                    if current_param and param_desc:
                        self.add_parameter(current_param, '\n'.join(param_desc))
                    
                    # Start new parameter
                    current_param, param_desc_str = line.split(':', 1)
                    current_param = current_param.strip()
                    param_desc = [param_desc_str.strip()] if param_desc_str.strip() else []
                
                elif line and current_param:
                    # Continue parameter description
                    param_desc.append(line)
        
        # Save last parameter
        if in_params and current_param and param_desc:
            self.add_parameter(current_param, '\n'.join(param_desc))
    
    def _extract_cpp_documentation(self) -> bool:
        """
        Extract documentation from C++ source code.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Extract class documentation
            class_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*class\s+(\w+)', self.source_code)
            if class_match:
                self.type = self.TYPE_CLASS
                self.title = class_match.group(2)
                
                # Process the comment text
                comment_text = class_match.group(1)
                self._process_cpp_comment(comment_text)
                
                return True
            
            # Extract enum documentation
            enum_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*enum\s+(?:class\s+)?(\w+)', self.source_code)
            if enum_match:
                self.type = self.TYPE_CLASS  # Using CLASS type for enums
                self.title = enum_match.group(2)
                
                # Process the comment text
                comment_text = enum_match.group(1)
                self._process_cpp_comment(comment_text)
                
                return True
            
            # Extract struct documentation
            struct_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*struct\s+(\w+)', self.source_code)
            if struct_match:
                self.type = self.TYPE_CLASS  # Using CLASS type for structs
                self.title = struct_match.group(2)
                
                # Process the comment text
                comment_text = struct_match.group(1)
                self._process_cpp_comment(comment_text)
                
                return True
            
            # Extract function documentation
            func_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:\w+(?:::\w+)*\s+)?(\w+)\s*\(', self.source_code)
            if func_match:
                self.type = self.TYPE_FUNCTION
                self.title = func_match.group(2)
                
                # Process the comment text
                comment_text = func_match.group(1)
                self._process_cpp_comment(comment_text)
                
                return True
            
            # Extract method documentation (inside class)
            method_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:\w+(?:::\w+)*\s+)?(\w+)\s*\(', self.source_code)
            if method_match:
                self.type = self.TYPE_FUNCTION
                self.title = method_match.group(2)
                
                # Process the comment text
                comment_text = method_match.group(1)
                self._process_cpp_comment(comment_text)
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error extracting C++ documentation: {e}", exc_info=True)
            return False
    
    def _process_cpp_comment(self, comment_text: str) -> None:
        """
        Process a C++ comment to extract structured information.
        
        Args:
            comment_text: The comment text to process.
        """
        # Clean up the comment text by removing leading asterisks and spaces
        lines = comment_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading asterisks and spaces
            cleaned_line = re.sub(r'^\s*\*\s?', '', line)
            cleaned_lines.append(cleaned_line)
        
        # Join cleaned lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Extract class/brief description
        brief_match = re.search(r'@brief\s+(.*?)(?=\n\n|\n@|\Z)', cleaned_text, re.DOTALL)
        if brief_match:
            self.content = brief_match.group(1).strip()
        
        # Extract detailed description (text between @brief and the next tag)
        detail_match = re.search(r'@brief\s+.*?\n\n(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if detail_match:
            detailed_desc = detail_match.group(1).strip()
            if self.content:
                self.content += '\n\n' + detailed_desc
            else:
                self.content = detailed_desc
        
        # Extract parameters
        param_matches = re.finditer(r'@param\s+(\w+)\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in param_matches:
            param_name = match.group(1)
            param_desc = match.group(2).strip()
            self.add_parameter(param_name, param_desc)
        
        # Extract return value
        return_match = re.search(r'@return(?:s)?\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if return_match:
            return_desc = return_match.group(1).strip()
            self.set_returns(return_desc)
        
        # Extract throws/exceptions
        throws_matches = re.finditer(r'@throws\s+(\w+)\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in throws_matches:
            exc_type = match.group(1)
            exc_desc = match.group(2).strip()
            self.add_exception(exc_type, exc_desc)
        
        # Extract deprecated
        deprecated_match = re.search(r'@deprecated\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if deprecated_match:
            reason = deprecated_match.group(1).strip()
            self.set_deprecated(True, reason)
        
        # Extract since version
        since_match = re.search(r'@since\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if since_match:
            since_version = since_match.group(1).strip()
            self.set_since_version(since_version)
        
        # Extract authors
        author_matches = re.finditer(r'@author\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in author_matches:
            author = match.group(1).strip()
            self.add_author(author)
        
        # Extract see also
        see_matches = re.finditer(r'@see\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in see_matches:
            reference = match.group(1).strip()
            self.add_see_also(reference)
    
    def _extract_js_documentation(self) -> bool:
        """
        Extract documentation from JavaScript/TypeScript source code.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Simple regex-based extraction for now
            # Extract class documentation
            class_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*class\s+(\w+)', self.source_code)
            if class_match:
                self.type = self.TYPE_CLASS
                self.title = class_match.group(2)
                self.content = class_match.group(1).strip()
                return True
            
            # Extract function documentation
            func_match = re.search(r'/\*\*\s*([\s\S]*?)\s*\*/\s*(?:function\s+)?(\w+)\s*\(', self.source_code)
            if func_match:
                self.type = self.TYPE_FUNCTION
                self.title = func_match.group(2)
                self.content = func_match.group(1).strip()
                
                # Extract parameters
                param_matches = re.finditer(r'@param\s+{([^}]*)}\s+(\w+)\s+(.*?)(?=@|\*/)', func_match.group(1))
                for match in param_matches:
                    self.add_parameter(match.group(2), match.group(3).strip(), match.group(1))
                
                # Extract return value
                return_match = re.search(r'@returns?\s+{([^}]*)}\s+(.*?)(?=@|\*/)', func_match.group(1))
                if return_match:
                    self.set_returns(return_match.group(2).strip(), return_match.group(1))
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error extracting JavaScript/TypeScript documentation: {e}", exc_info=True)
            return False
    
    def _extract_lua_documentation(self) -> bool:
        """
        Extract documentation from Lua source code.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Simple regex-based extraction for now
            # Extract function documentation
            func_match = re.search(r'---\s*([\s\S]*?)\s*\n\s*function\s+(\w+)[.:]?(\w+)?\s*\(', self.source_code)
            if func_match:
                self.type = self.TYPE_FUNCTION
                self.title = func_match.group(2)
                if func_match.group(3):
                    self.title += "." + func_match.group(3)
                self.content = func_match.group(1).strip()
                
                # Extract parameters
                param_matches = re.finditer(r'@param\s+(\w+)\s+(.*?)(?=@|\n---)', func_match.group(1))
                for match in param_matches:
                    self.add_parameter(match.group(1), match.group(2).strip())
                
                # Extract return value
                return_match = re.search(r'@return\s+(.*?)(?=@|\n---)', func_match.group(1))
                if return_match:
                    self.set_returns(return_match.group(1).strip())
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error extracting Lua documentation: {e}", exc_info=True)
            return False
    
    def generate_markdown(self) -> str:
        """
        Generate Markdown documentation.
        
        Returns:
            str: The generated Markdown documentation.
        """
        try:
            markdown = f"# {self.title}\n\n"
            
            # Add API version if available
            if self.api_version:
                markdown += f"**API Version:** {self.api_version}\n\n"
            
            # Add component if available
            if self.component:
                markdown += f"**Component:** {self.component}\n\n"
            
            # Add deprecation notice if deprecated
            if self.deprecated:
                reason = self.get_metadata("deprecation_reason", "")
                markdown += f"> **Deprecated**"
                if reason:
                    markdown += f": {reason}"
                markdown += "\n\n"
            
            # Add since version if available
            if self.since_version:
                markdown += f"*Since version {self.since_version}*\n\n"
            
            # Add main content
            if self.content:
                markdown += f"{self.content}\n\n"
            
            # Add parameters if available
            if self.parameters:
                markdown += "## Parameters\n\n"
                for name, param in self.parameters.items():
                    param_type = f" `{param['type']}`" if param.get('type') else ""
                    markdown += f"- **{name}**{param_type}: {param['description']}\n"
                markdown += "\n"
            
            # Add return value if available
            if self.returns:
                markdown += "## Returns\n\n"
                return_type = f" `{self.returns['type']}`" if self.returns.get('type') else ""
                markdown += f"{return_type}: {self.returns['description']}\n\n"
            
            # Add exceptions if available
            if self.exceptions:
                markdown += "## Exceptions\n\n"
                for exc_type, exc_desc in self.exceptions.items():
                    markdown += f"- **{exc_type}**: {exc_desc}\n"
                markdown += "\n"
            
            # Add examples if available
            if self.examples:
                markdown += "## Examples\n\n"
                for i, example in enumerate(self.examples):
                    markdown += f"### Example {i+1}\n\n"
                    markdown += f"```{self.language}\n{example}\n```\n\n"
            
            # Add see also if available
            if self.see_also:
                markdown += "## See Also\n\n"
                for reference in self.see_also:
                    markdown += f"- {reference}\n"
                markdown += "\n"
            
            # Add authors if available
            if self.authors:
                markdown += "## Authors\n\n"
                for author in self.authors:
                    markdown += f"- {author}\n"
                markdown += "\n"
            
            return markdown
        
        except Exception as e:
            logger.error(f"Error generating Markdown: {e}", exc_info=True)
            return ""
    
    def generate_html(self) -> str:
        """
        Generate HTML documentation.
        
        Returns:
            str: The generated HTML documentation.
        """
        try:
            html = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{self.title}</title>\n"
            html += "<style>\n"
            html += "body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }\n"
            html += "h1 { color: #333; }\n"
            html += "h2 { color: #444; margin-top: 20px; }\n"
            html += "code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }\n"
            html += "pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }\n"
            html += ".deprecated { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin-bottom: 20px; }\n"
            html += ".version { color: #666; font-style: italic; margin-bottom: 20px; }\n"
            html += ".param-name { font-weight: bold; }\n"
            html += ".param-type { color: #6c757d; }\n"
            html += "</style>\n"
            html += "</head>\n<body>\n"
            
            # Add title
            html += f"<h1>{self.title}</h1>\n"
            
            # Add API version and component
            if self.api_version or self.component:
                html += "<p>"
                if self.api_version:
                    html += f"<strong>API Version:</strong> {self.api_version}"
                    if self.component:
                        html += " | "
                if self.component:
                    html += f"<strong>Component:</strong> {self.component}"
                html += "</p>\n"
            
            # Add deprecation notice if deprecated
            if self.deprecated:
                reason = self.get_metadata("deprecation_reason", "")
                html += f"<div class='deprecated'><strong>Deprecated</strong>"
                if reason:
                    html += f": {reason}"
                html += "</div>\n"
            
            # Add since version if available
            if self.since_version:
                html += f"<p class='version'>Since version {self.since_version}</p>\n"
            
            # Add main content
            if self.content:
                # Format content with paragraphs
                paragraphs = self.content.split('\n\n')
                html += "<div>\n"
                for paragraph in paragraphs:
                    if paragraph.strip():
                        html += f"<p>{paragraph.strip()}</p>\n"
                html += "</div>\n"
            
            # Add parameters if available
            if self.parameters:
                html += "<h2>Parameters</h2>\n<ul>\n"
                for name, param in self.parameters.items():
                    param_type = f" <span class='param-type'>{param['type']}</span>" if param.get('type') else ""
                    html += f"<li><span class='param-name'>{name}</span>{param_type}: {param['description']}</li>\n"
                html += "</ul>\n"
            
            # Add return value if available
            if self.returns:
                html += "<h2>Returns</h2>\n"
                return_type = f" <span class='param-type'>{self.returns['type']}</span>" if self.returns.get('type') else ""
                html += f"<p>{return_type}: {self.returns['description']}</p>\n"
            
            # Add exceptions if available
            if self.exceptions:
                html += "<h2>Exceptions</h2>\n<ul>\n"
                for exc_type, exc_desc in self.exceptions.items():
                    html += f"<li><strong>{exc_type}</strong>: {exc_desc}</li>\n"
                html += "</ul>\n"
            
            # Add examples if available
            if self.examples:
                html += "<h2>Examples</h2>\n"
                for i, example in enumerate(self.examples):
                    html += f"<h3>Example {i+1}</h3>\n"
                    html += f"<pre><code>{example}</code></pre>\n"
            
            # Add see also if available
            if self.see_also:
                html += "<h2>See Also</h2>\n<ul>\n"
                for reference in self.see_also:
                    html += f"<li>{reference}</li>\n"
                html += "</ul>\n"
            
            # Add authors if available
            if self.authors:
                html += "<h2>Authors</h2>\n<ul>\n"
                for author in self.authors:
                    html += f"<li>{author}</li>\n"
                html += "</ul>\n"
            
            html += "</body>\n</html>"
            return html
        
        except Exception as e:
            logger.error(f"Error generating HTML: {e}", exc_info=True)
            return ""
    
    def is_api(self) -> bool:
        """Check if the document is an API documentation."""
        return self.type == self.TYPE_API
    
    def is_guide(self) -> bool:
        """Check if the document is a guide."""
        return self.type == self.TYPE_GUIDE
    
    def is_tutorial(self) -> bool:
        """Check if the document is a tutorial."""
        return self.type == self.TYPE_TUTORIAL
    
    def is_reference(self) -> bool:
        """Check if the document is a reference."""
        return self.type == self.TYPE_REFERENCE
    
    def is_code(self) -> bool:
        """Check if the document is a code documentation."""
        return self.type == self.TYPE_CODE
    
    def is_function(self) -> bool:
        """Check if the document is a function documentation."""
        return self.type == self.TYPE_FUNCTION
    
    def is_class(self) -> bool:
        """Check if the document is a class documentation."""
        return self.type == self.TYPE_CLASS
    
    def is_module(self) -> bool:
        """Check if the document is a module documentation."""
        return self.type == self.TYPE_MODULE
    
    def is_package(self) -> bool:
        """Check if the document is a package documentation."""
        return self.type == self.TYPE_PACKAGE
    
    def is_interface(self) -> bool:
        """Check if the document is an interface documentation."""
        return self.type == self.TYPE_INTERFACE
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the documentation to a dictionary.
        
        Returns:
            A dictionary representation of the documentation.
        """
        # Get base document dictionary
        doc_dict = super().to_dict()
        
        # Add documentation-specific attributes
        doc_dict.update({
            "source_code": self.source_code,
            "language": self.language,
            "component": self.component,
            "api_version": self.api_version,
            "examples": self.examples,
            "see_also": self.see_also,
            "parameters": self.parameters,
            "returns": self.returns,
            "exceptions": self.exceptions,
            "deprecated": self.deprecated,
            "since_version": self.since_version,
            "authors": self.authors
        })
        
        return doc_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Documentation':
        """
        Create a documentation from a dictionary.
        
        Args:
            data: The dictionary containing the documentation data.
            
        Returns:
            The created documentation.
        """
        # Create documentation instance
        doc = cls(
            id=data.get("id"),
            title=data.get("title", ""),
            content=data.get("content", ""),
            type=data.get("type"),
            parent_id=data.get("parent_id"),
            created_at=datetime.datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Set documentation-specific attributes
        if "source_code" in data:
            doc.source_code = data["source_code"]
        if "language" in data:
            doc.language = data["language"]
        if "component" in data:
            doc.component = data["component"]
        if "api_version" in data:
            doc.api_version = data["api_version"]
        if "examples" in data:
            doc.examples = data["examples"]
        if "see_also" in data:
            doc.see_also = data["see_also"]
        if "parameters" in data:
            doc.parameters = data["parameters"]
        if "returns" in data:
            doc.returns = data["returns"]
        if "exceptions" in data:
            doc.exceptions = data["exceptions"]
        if "deprecated" in data:
            doc.deprecated = data["deprecated"]
        if "since_version" in data:
            doc.since_version = data["since_version"]
        if "authors" in data:
            doc.authors = data["authors"]
        
        # Set additional attributes from base Document
        if "children_ids" in data:
            doc.children_ids = data["children_ids"]
        if "order" in data:
            doc.order = data["order"]
        if "word_count" in data:
            doc.word_count = data["word_count"]
        if "character_count" in data:
            doc.character_count = data["character_count"]
        if "tags" in data:
            doc.tags = data["tags"]
        if "metadata" in data:
            doc.metadata = data["metadata"]
        if "is_included_in_compile" in data:
            doc.is_included_in_compile = data["is_included_in_compile"]
        if "synopsis" in data:
            doc.synopsis = data["synopsis"]
        if "status" in data:
            doc.status = data["status"]
        if "color" in data:
            doc.color = data["color"]
        
        return doc
