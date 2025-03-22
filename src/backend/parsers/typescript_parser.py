#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TypeScript/JavaScript Parser for RebelSCRIBE.

This module provides functionality for parsing TypeScript and JavaScript files into a structured
representation that can be used for documentation generation.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils.logging_utils import get_logger
from .code_parser import CodeParser, CodeNode

logger = get_logger(__name__)

class TypeScriptParser(CodeParser):
    """
    Parser for TypeScript and JavaScript files.
    
    This class provides functionality for parsing TypeScript and JavaScript files into a structured
    representation that can be used for documentation generation.
    """
    
    def __init__(self):
        """
        Initialize the TypeScriptParser.
        """
        super().__init__()
        
        # Regular expressions for parsing TypeScript/JavaScript code
        self.import_regex = re.compile(r'^\s*import\s+(?:{([^}]+)}|([a-zA-Z0-9_$]+)|(?:\*\s+as\s+([a-zA-Z0-9_$]+)))\s+from\s+[\'"]([^\'"]+)[\'"];\s*$')
        self.export_regex = re.compile(r'^\s*export\s+(?:default\s+)?(?:class|interface|enum|function|const|let|var)\s+([a-zA-Z0-9_$]+)')
        self.class_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?(?:\s+implements\s+([a-zA-Z0-9_$.,\s]+))?\s*{?\s*$')
        self.interface_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?interface\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.,\s]+))?\s*{?\s*$')
        self.enum_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?enum\s+([a-zA-Z0-9_$]+)\s*{?\s*$')
        self.function_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)(?:\s*:\s*([a-zA-Z0-9_$<>[\].,\s|]+))?\s*{?\s*$')
        self.arrow_function_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s+)?\(([^)]*)\)(?:\s*:\s*([a-zA-Z0-9_$<>[\].,\s|]+))?\s*=>\s*{?\s*$')
        self.method_regex = re.compile(r'^\s*(?:public|private|protected|static|readonly|async)?\s*(?:public|private|protected|static|readonly|async)?\s*([a-zA-Z0-9_$]+)\s*\(([^)]*)\)(?:\s*:\s*([a-zA-Z0-9_$<>[\].,\s|]+))?\s*{?\s*$')
        self.property_regex = re.compile(r'^\s*(?:public|private|protected|static|readonly)?\s*(?:public|private|protected|static|readonly)?\s*([a-zA-Z0-9_$]+)\s*(?::\s*([a-zA-Z0-9_$<>[\].,\s|]+))?\s*(?:=\s*[^;]+)?;\s*$')
        self.variable_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)(?:\s*:\s*([a-zA-Z0-9_$<>[\].,\s|]+))?(?:\s*=\s*[^;]+)?;?\s*$')
        self.enum_value_regex = re.compile(r'^\s*([a-zA-Z0-9_$]+)(?:\s*=\s*[^,]+)?,?\s*(?://\s*(.*))?$')
        self.jsdoc_start_regex = re.compile(r'^\s*/\*\*\s*$')
        self.jsdoc_line_regex = re.compile(r'^\s*\*\s*(.*)$')
        self.jsdoc_end_regex = re.compile(r'^\s*\*/\s*$')
        self.jsdoc_param_regex = re.compile(r'@param\s+(?:{([^}]+)}\s+)?([a-zA-Z0-9_$]+)(?:\s+-\s+(.+))?$')
        self.jsdoc_returns_regex = re.compile(r'@returns?\s+(?:{([^}]+)}\s+)?(.+)?$')
        self.jsdoc_throws_regex = re.compile(r'@throws?\s+(?:{([^}]+)}\s+)?(.+)?$')
        self.jsdoc_description_regex = re.compile(r'@description\s+(.+)$')
        self.jsdoc_example_regex = re.compile(r'@example\s+(.+)$')
        self.jsdoc_deprecated_regex = re.compile(r'@deprecated\s+(.+)?$')
        self.jsdoc_since_regex = re.compile(r'@since\s+(.+)$')
        self.jsdoc_see_regex = re.compile(r'@see\s+(.+)$')
        self.jsdoc_todo_regex = re.compile(r'@todo\s+(.+)$')
        
    def parse(self, code_text: str, file_path: Optional[str] = None) -> CodeNode:
        """
        Parse TypeScript/JavaScript code into a structured representation.
        
        Args:
            code_text: The TypeScript/JavaScript code to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            A CodeNode representing the TypeScript/JavaScript code.
        """
        try:
            # Create file node
            file_name = os.path.basename(file_path) if file_path else "unknown.ts"
            file_node = CodeNode(CodeNode.TYPE_FILE, name=file_name)
            
            # Split into lines
            lines = code_text.split('\n')
            
            # State variables
            current_jsdoc = []
            in_jsdoc = False
            class_stack = []
            
            # Process lines
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Check for import statement
                import_match = self.import_regex.match(line)
                if import_match:
                    imports = import_match.group(1) or import_match.group(2) or import_match.group(3)
                    module = import_match.group(4)
                    
                    import_node = CodeNode(
                        CodeNode.TYPE_IMPORT,
                        name=module,
                        content=line.strip()
                    )
                    file_node.add_child(import_node)
                    i += 1
                    continue
                
                # Check for variable definition first (to catch exported variables)
                variable_match = self.variable_regex.match(line)
                if variable_match:
                    variable_name = variable_match.group(1)
                    variable_type = variable_match.group(2) or ""
                    
                    # Create variable node
                    variable_node = CodeNode(
                        CodeNode.TYPE_VARIABLE,
                        name=variable_name,
                        attributes={"var_type": variable_type}
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        variable_node.content = self._process_jsdoc(current_jsdoc)
                        current_jsdoc = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(variable_node)
                    else:
                        file_node.add_child(variable_node)
                    
                    i += 1
                    continue
                
                # Check for export statement
                export_match = self.export_regex.match(line)
                if export_match and not self.class_regex.match(line) and not self.interface_regex.match(line) and not self.enum_regex.match(line) and not self.function_regex.match(line):
                    export_name = export_match.group(1)
                    
                    export_node = CodeNode(
                        CodeNode.TYPE_EXPORT,
                        name=export_name,
                        content=line.strip()
                    )
                    file_node.add_child(export_node)
                    i += 1
                    continue
                
                # Check for class definition
                class_match = self.class_regex.match(line)
                if class_match:
                    class_name = class_match.group(1)
                    extends = class_match.group(2) or ""
                    implements = class_match.group(3) or ""
                    
                    inheritance = []
                    if extends:
                        inheritance.append(f"extends {extends}")
                    if implements:
                        inheritance.append(f"implements {implements}")
                    
                    inheritance_str = " ".join(inheritance)
                    
                    # Create class node
                    class_node = CodeNode(
                        CodeNode.TYPE_CLASS,
                        name=class_name,
                        attributes={"inheritance": inheritance_str}
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        class_node.content = self._process_jsdoc(current_jsdoc)
                        current_jsdoc = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(class_node)
                    else:
                        file_node.add_child(class_node)
                    
                    class_stack.append(class_node)
                    i += 1
                    continue
                
                # Check for interface definition
                interface_match = self.interface_regex.match(line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    extends = interface_match.group(2) or ""
                    
                    # Create interface node
                    interface_node = CodeNode(
                        CodeNode.TYPE_INTERFACE,
                        name=interface_name,
                        attributes={"extends": extends}
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        interface_node.content = self._process_jsdoc(current_jsdoc)
                        current_jsdoc = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(interface_node)
                    else:
                        file_node.add_child(interface_node)
                    
                    class_stack.append(interface_node)
                    i += 1
                    continue
                
                # Check for enum definition
                enum_match = self.enum_regex.match(line)
                if enum_match:
                    enum_name = enum_match.group(1)
                    
                    # Create enum node
                    enum_node = CodeNode(
                        CodeNode.TYPE_ENUM,
                        name=enum_name
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        enum_node.content = self._process_jsdoc(current_jsdoc)
                        current_jsdoc = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(enum_node)
                    else:
                        file_node.add_child(enum_node)
                    
                    class_stack.append(enum_node)
                    i += 1
                    
                    # Process enum values
                    while i < len(lines) and not lines[i].strip().endswith('}'):
                        enum_value_match = self.enum_value_regex.match(lines[i])
                        if enum_value_match:
                            enum_value_name = enum_value_match.group(1)
                            enum_value_desc = enum_value_match.group(2) or ""
                            
                            enum_value_node = CodeNode(
                                CodeNode.TYPE_VARIABLE,
                                name=enum_value_name,
                                content=enum_value_desc
                            )
                            enum_node.add_child(enum_value_node)
                        
                        i += 1
                    
                    # Skip closing brace
                    if i < len(lines) and lines[i].strip().endswith('}'):
                        i += 1
                    
                    class_stack.pop()
                    continue
                
                # Check for function definition
                function_match = self.function_regex.match(line)
                if function_match:
                    function_name = function_match.group(1)
                    parameters_str = function_match.group(2)
                    return_type = function_match.group(3) or ""
                    
                    # Parse parameters
                    parameters = []
                    if parameters_str.strip():
                        for param in parameters_str.split(','):
                            param = param.strip()
                            if param:
                                # Extract parameter name and type
                                param_parts = param.split(':')
                                param_name = param_parts[0].strip()
                                param_type = param_parts[1].strip() if len(param_parts) > 1 else ""
                                
                                if param_type:
                                    parameters.append(f"{param_name}: {param_type}")
                                else:
                                    parameters.append(param_name)
                    
                    # Create function node
                    function_node = CodeNode(
                        CodeNode.TYPE_FUNCTION,
                        name=function_name,
                        attributes={
                            "parameters": parameters,
                            "return_type": return_type
                        }
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        function_node.content = self._process_jsdoc(current_jsdoc)
                        
                        # Extract parameter and return documentation
                        self._extract_jsdoc_details(current_jsdoc, function_node)
                        
                        current_jsdoc = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(function_node)
                    else:
                        file_node.add_child(function_node)
                    
                    i += 1
                    continue
                
                # Check for arrow function
                arrow_function_match = self.arrow_function_regex.match(line)
                if arrow_function_match:
                    function_name = arrow_function_match.group(1)
                    parameters_str = arrow_function_match.group(2)
                    return_type = arrow_function_match.group(3) or ""
                    
                    # Parse parameters
                    parameters = []
                    if parameters_str.strip():
                        for param in parameters_str.split(','):
                            param = param.strip()
                            if param:
                                # Extract parameter name and type
                                param_parts = param.split(':')
                                param_name = param_parts[0].strip()
                                param_type = param_parts[1].strip() if len(param_parts) > 1 else ""
                                
                                if param_type:
                                    parameters.append(f"{param_name}: {param_type}")
                                else:
                                    parameters.append(param_name)
                    
                    # Create function node
                    function_node = CodeNode(
                        CodeNode.TYPE_FUNCTION,
                        name=function_name,
                        attributes={
                            "parameters": parameters,
                            "return_type": return_type
                        }
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        function_node.content = self._process_jsdoc(current_jsdoc)
                        
                        # Extract parameter and return documentation
                        self._extract_jsdoc_details(current_jsdoc, function_node)
                        
                        current_jsdoc = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(function_node)
                    else:
                        file_node.add_child(function_node)
                    
                    i += 1
                    continue
                
                # Check for method definition
                method_match = self.method_regex.match(line)
                if method_match and class_stack:
                    method_name = method_match.group(1)
                    parameters_str = method_match.group(2)
                    return_type = method_match.group(3) or ""
                    
                    # Parse parameters
                    parameters = []
                    if parameters_str.strip():
                        for param in parameters_str.split(','):
                            param = param.strip()
                            if param:
                                # Extract parameter name and type
                                param_parts = param.split(':')
                                param_name = param_parts[0].strip()
                                param_type = param_parts[1].strip() if len(param_parts) > 1 else ""
                                
                                if param_type:
                                    parameters.append(f"{param_name}: {param_type}")
                                else:
                                    parameters.append(param_name)
                    
                    # Create method node
                    method_node = CodeNode(
                        CodeNode.TYPE_METHOD,
                        name=method_name,
                        attributes={
                            "parameters": parameters,
                            "return_type": return_type
                        }
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        method_node.content = self._process_jsdoc(current_jsdoc)
                        
                        # Extract parameter and return documentation
                        self._extract_jsdoc_details(current_jsdoc, method_node)
                        
                        current_jsdoc = []
                    
                    # Add to parent
                    class_stack[-1].add_child(method_node)
                    
                    i += 1
                    continue
                
                # Check for property definition
                property_match = self.property_regex.match(line)
                if property_match and class_stack:
                    property_name = property_match.group(1)
                    property_type = property_match.group(2) or ""
                    
                    # Create property node
                    property_node = CodeNode(
                        CodeNode.TYPE_PROPERTY,
                        name=property_name,
                        attributes={"var_type": property_type}
                    )
                    
                    # Add JSDoc if available
                    if current_jsdoc:
                        property_node.content = self._process_jsdoc(current_jsdoc)
                        current_jsdoc = []
                    
                    # Add to parent
                    class_stack[-1].add_child(property_node)
                    
                    i += 1
                    continue
                
                # Variable check is now before export check
                
                # Check for JSDoc start
                jsdoc_start_match = self.jsdoc_start_regex.match(line)
                if jsdoc_start_match:
                    in_jsdoc = True
                    current_jsdoc = []
                    i += 1
                    continue
                
                # Check for JSDoc line
                if in_jsdoc:
                    jsdoc_line_match = self.jsdoc_line_regex.match(line)
                    if jsdoc_line_match:
                        current_jsdoc.append(jsdoc_line_match.group(1))
                        i += 1
                        continue
                
                # Check for JSDoc end
                jsdoc_end_match = self.jsdoc_end_regex.match(line)
                if jsdoc_end_match:
                    in_jsdoc = False
                    i += 1
                    continue
                
                # Check for end of class/interface
                if class_stack and line.strip() == '}':
                    class_stack.pop()
                    i += 1
                    continue
                
                # Move to next line
                i += 1
            
            return file_node
        except Exception as e:
            logger.error(f"Failed to parse TypeScript/JavaScript code: {e}")
            
            # Create an empty file node
            file_name = os.path.basename(file_path) if file_path else "unknown.ts"
            return CodeNode(CodeNode.TYPE_FILE, name=file_name, content=f"Error parsing TypeScript/JavaScript code: {str(e)}")
    
    def _process_jsdoc(self, jsdoc_lines: List[str]) -> str:
        """
        Process a JSDoc comment.
        
        Args:
            jsdoc_lines: The lines of the JSDoc comment.
            
        Returns:
            The processed JSDoc comment.
        """
        if not jsdoc_lines:
            return ""
        
        # Process JSDoc tags
        processed_lines = []
        i = 0
        while i < len(jsdoc_lines):
            line = jsdoc_lines[i]
            
            # Check for description tag
            description_match = self.jsdoc_description_regex.match(line)
            if description_match:
                processed_lines.append(description_match.group(1))
                i += 1
                continue
            
            # Skip param, returns, and throws tags
            if (self.jsdoc_param_regex.match(line) or 
                self.jsdoc_returns_regex.match(line) or 
                self.jsdoc_throws_regex.match(line)):
                i += 1
                continue
            
            # Check for example tag
            example_match = self.jsdoc_example_regex.match(line)
            if example_match:
                processed_lines.append(f"Example: {example_match.group(1)}")
                i += 1
                continue
            
            # Check for deprecated tag
            deprecated_match = self.jsdoc_deprecated_regex.match(line)
            if deprecated_match:
                reason = deprecated_match.group(1) or ""
                processed_lines.append(f"Deprecated: {reason}")
                i += 1
                continue
            
            # Check for since tag
            since_match = self.jsdoc_since_regex.match(line)
            if since_match:
                processed_lines.append(f"Since: {since_match.group(1)}")
                i += 1
                continue
            
            # Check for see tag
            see_match = self.jsdoc_see_regex.match(line)
            if see_match:
                processed_lines.append(f"See: {see_match.group(1)}")
                i += 1
                continue
            
            # Check for todo tag
            todo_match = self.jsdoc_todo_regex.match(line)
            if todo_match:
                processed_lines.append(f"TODO: {todo_match.group(1)}")
                i += 1
                continue
            
            # Add line
            processed_lines.append(line)
            i += 1
        
        # Join lines
        return '\n'.join(processed_lines)
    
    def _extract_jsdoc_details(self, jsdoc_lines: List[str], parent_node: CodeNode) -> None:
        """
        Extract parameter, return, and throws documentation from a JSDoc comment.
        
        Args:
            jsdoc_lines: The lines of the JSDoc comment.
            parent_node: The parent node to add the extracted nodes to.
        """
        for line in jsdoc_lines:
            # Check for param tag
            param_match = self.jsdoc_param_regex.match(line)
            if param_match:
                param_type = param_match.group(1) or ""
                param_name = param_match.group(2)
                param_desc = param_match.group(3) or ""
                
                param_node = CodeNode(
                    CodeNode.TYPE_PARAMETER,
                    name=param_name,
                    content=param_desc,
                    attributes={"param_type": param_type}
                )
                parent_node.add_child(param_node)
                continue
            
            # Check for returns tag
            returns_match = self.jsdoc_returns_regex.match(line)
            if returns_match:
                return_type = returns_match.group(1) or ""
                return_desc = returns_match.group(2) or ""
                
                return_node = CodeNode(
                    CodeNode.TYPE_RETURN,
                    content=return_desc,
                    attributes={"return_type": return_type}
                )
                parent_node.add_child(return_node)
                continue
            
            # Check for throws tag
            throws_match = self.jsdoc_throws_regex.match(line)
            if throws_match:
                exception_type = throws_match.group(1) or ""
                exception_desc = throws_match.group(2) or ""
                
                exception_node = CodeNode(
                    CodeNode.TYPE_EXCEPTION,
                    name=exception_type,
                    content=exception_desc
                )
                parent_node.add_child(exception_node)
                continue
