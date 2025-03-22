#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ Parser for RebelSCRIBE.

This module provides functionality for parsing C++ files into a structured
representation that can be used for documentation generation.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils.logging_utils import get_logger
from .code_parser import CodeParser, CodeNode

logger = get_logger(__name__)

class CppParser(CodeParser):
    """
    Parser for C++ files.
    
    This class provides functionality for parsing C++ files into a structured
    representation that can be used for documentation generation.
    """
    
    def __init__(self):
        """
        Initialize the CppParser.
        """
        super().__init__()
        
        # Regular expressions for parsing C++ code
        self.include_regex = re.compile(r'^\s*#include\s+[<"]([^>"]+)[>"]\s*$')
        self.namespace_start_regex = re.compile(r'^\s*namespace\s+([a-zA-Z0-9_:]+)\s*{?\s*$')
        self.namespace_end_regex = re.compile(r'^\s*}\s*(?://\s*namespace\s+([a-zA-Z0-9_:]+))?\s*$')
        self.class_regex = re.compile(r'^\s*(?:class|struct|enum(?:\s+class)?)\s+([a-zA-Z0-9_]+)(?:\s*:\s*([^{]+))?\s*{?\s*$')
        self.class_end_regex = re.compile(r'^\s*};\s*$')
        self.function_regex = re.compile(r'^\s*(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:explicit\s+)?(?:constexpr\s+)?(?:([a-zA-Z0-9_:]+(?:<[^>]*>)?)\s+)?([a-zA-Z0-9_~]+)\s*\(([^)]*)\)(?:\s*(?:const|override|final|noexcept))?\s*(?:{\s*|\s*=\s*[^;]+;|;)\s*$')
        self.variable_regex = re.compile(r'^\s*(?:static\s+)?(?:const\s+)?(?:constexpr\s+)?([a-zA-Z0-9_:]+(?:<[^>]*>)?)\s+([a-zA-Z0-9_]+)(?:\s*=\s*[^;]+)?;\s*$')
        self.enum_value_regex = re.compile(r'^\s*([a-zA-Z0-9_]+)(?:\s*=\s*[^,]+)?,?\s*(?://\s*(.*))?$')
        self.comment_start_regex = re.compile(r'^\s*/\*\*\s*$')
        self.comment_line_regex = re.compile(r'^\s*\*\s*(.*)$')
        self.comment_end_regex = re.compile(r'^\s*\*/\s*$')
        self.single_line_comment_regex = re.compile(r'^\s*///\s*(.*)$')
        self.param_regex = re.compile(r'@param\s+([a-zA-Z0-9_]+)(?:\s+\[([^\]]+)\])?\s+(.+)$')
        self.return_regex = re.compile(r'@return(?:\s+\[([^\]]+)\])?\s+(.+)$')
        self.throws_regex = re.compile(r'@throws\s+([a-zA-Z0-9_:]+)(?:\s+(.+))?$')
        self.brief_regex = re.compile(r'@brief\s+(.+)$')
        self.details_regex = re.compile(r'@details\s+(.+)$')
        
    def parse(self, code_text: str, file_path: Optional[str] = None) -> CodeNode:
        """
        Parse C++ code into a structured representation.
        
        Args:
            code_text: The C++ code to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            A CodeNode representing the C++ code.
        """
        try:
            # Create file node
            file_name = os.path.basename(file_path) if file_path else "unknown.cpp"
            file_node = CodeNode(CodeNode.TYPE_FILE, name=file_name)
            
            # Split into lines
            lines = code_text.split('\n')
            
            # State variables
            current_comment = []
            in_comment = False
            current_namespace = []
            namespace_stack = []
            class_stack = []
            
            # Process lines
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Check for include directive
                include_match = self.include_regex.match(line)
                if include_match:
                    include_node = CodeNode(
                        CodeNode.TYPE_IMPORT,
                        name=include_match.group(1),
                        content=line.strip()
                    )
                    file_node.add_child(include_node)
                    i += 1
                    continue
                
                # Check for namespace start
                namespace_start_match = self.namespace_start_regex.match(line)
                if namespace_start_match:
                    namespace_name = namespace_start_match.group(1)
                    current_namespace.append(namespace_name)
                    
                    # Create namespace node
                    namespace_node = CodeNode(
                        CodeNode.TYPE_NAMESPACE,
                        name="::".join(current_namespace)
                    )
                    
                    # Add to parent
                    if namespace_stack:
                        namespace_stack[-1].add_child(namespace_node)
                    else:
                        file_node.add_child(namespace_node)
                    
                    namespace_stack.append(namespace_node)
                    i += 1
                    continue
                
                # Check for namespace end
                namespace_end_match = self.namespace_end_regex.match(line)
                if namespace_end_match and namespace_stack:
                    namespace_stack.pop()
                    if current_namespace:
                        current_namespace.pop()
                    i += 1
                    continue
                
                # Check for class/struct/enum definition
                class_match = self.class_regex.match(line)
                if class_match:
                    class_name = class_match.group(1)
                    inheritance = class_match.group(2).strip() if class_match.group(2) else ""
                    
                    # Check if this is an enum
                    is_enum = "enum" in line
                    
                    # Create class node
                    class_node = CodeNode(
                        CodeNode.TYPE_ENUM if is_enum else CodeNode.TYPE_CLASS,
                        name=class_name,
                        attributes={"inheritance": inheritance}
                    )
                    
                    # Add comment if available
                    if current_comment:
                        class_node.content = self._process_comment(current_comment)
                        current_comment = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(class_node)
                    elif namespace_stack:
                        namespace_stack[-1].add_child(class_node)
                    else:
                        file_node.add_child(class_node)
                    
                    class_stack.append(class_node)
                    i += 1
                    
                    # If this is an enum, process enum values
                    if is_enum:
                        while i < len(lines) and not self.class_end_regex.match(lines[i]):
                            enum_value_match = self.enum_value_regex.match(lines[i])
                            if enum_value_match:
                                enum_name = enum_value_match.group(1)
                                enum_desc = enum_value_match.group(2) or ""
                                
                                enum_value_node = CodeNode(
                                    CodeNode.TYPE_VARIABLE,
                                    name=enum_name,
                                    content=enum_desc
                                )
                                class_node.add_child(enum_value_node)
                            
                            i += 1
                    
                    continue
                
                # Check for class end
                class_end_match = self.class_end_regex.match(line)
                if class_end_match and class_stack:
                    class_stack.pop()
                    i += 1
                    continue
                
                # Check for function definition
                function_match = self.function_regex.match(line)
                if function_match:
                    return_type = function_match.group(1) or ""
                    function_name = function_match.group(2)
                    parameters_str = function_match.group(3)
                    
                    # Parse parameters
                    parameters = []
                    if parameters_str.strip():
                        for param in parameters_str.split(','):
                            param = param.strip()
                            if param:
                                # Extract parameter name (last word before any default value)
                                param_parts = param.split('=')[0].strip().split()
                                if param_parts:
                                    param_name = param_parts[-1].strip('&*')
                                    param_type = ' '.join(param_parts[:-1])
                                    parameters.append(f"{param_name}: {param_type}")
                    
                    # Determine if this is a method or constructor
                    is_method = class_stack and function_name != class_stack[-1].name and function_name != f"~{class_stack[-1].name}"
                    is_constructor = class_stack and (function_name == class_stack[-1].name or function_name == f"~{class_stack[-1].name}")
                    
                    # Create function node
                    function_node = CodeNode(
                        CodeNode.TYPE_METHOD if is_method or is_constructor else CodeNode.TYPE_FUNCTION,
                        name=function_name,
                        attributes={
                            "parameters": parameters,
                            "return_type": return_type
                        }
                    )
                    
                    # Add comment if available
                    if current_comment:
                        function_node.content = self._process_comment(current_comment)
                        
                        # Extract parameter and return documentation
                        self._extract_comment_details(current_comment, function_node)
                        
                        current_comment = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(function_node)
                    elif namespace_stack:
                        namespace_stack[-1].add_child(function_node)
                    else:
                        file_node.add_child(function_node)
                    
                    i += 1
                    continue
                
                # Check for variable definition
                variable_match = self.variable_regex.match(line)
                if variable_match:
                    var_type = variable_match.group(1)
                    var_name = variable_match.group(2)
                    
                    # Create variable node
                    variable_node = CodeNode(
                        CodeNode.TYPE_PROPERTY if class_stack else CodeNode.TYPE_VARIABLE,
                        name=var_name,
                        attributes={"var_type": var_type}
                    )
                    
                    # Add comment if available
                    if current_comment:
                        variable_node.content = self._process_comment(current_comment)
                        current_comment = []
                    
                    # Add to parent
                    if class_stack:
                        class_stack[-1].add_child(variable_node)
                    elif namespace_stack:
                        namespace_stack[-1].add_child(variable_node)
                    else:
                        file_node.add_child(variable_node)
                    
                    i += 1
                    continue
                
                # Check for comment start
                comment_start_match = self.comment_start_regex.match(line)
                if comment_start_match:
                    in_comment = True
                    current_comment = []
                    i += 1
                    continue
                
                # Check for comment line
                if in_comment:
                    comment_line_match = self.comment_line_regex.match(line)
                    if comment_line_match:
                        current_comment.append(comment_line_match.group(1))
                        i += 1
                        continue
                
                # Check for comment end
                comment_end_match = self.comment_end_regex.match(line)
                if comment_end_match:
                    in_comment = False
                    i += 1
                    continue
                
                # Check for single line comment
                single_line_comment_match = self.single_line_comment_regex.match(line)
                if single_line_comment_match:
                    current_comment.append(single_line_comment_match.group(1))
                    i += 1
                    continue
                
                # Move to next line
                i += 1
            
            return file_node
        except Exception as e:
            logger.error(f"Failed to parse C++ code: {e}")
            
            # Create an empty file node
            file_name = os.path.basename(file_path) if file_path else "unknown.cpp"
            return CodeNode(CodeNode.TYPE_FILE, name=file_name, content=f"Error parsing C++ code: {str(e)}")
    
    def _process_comment(self, comment_lines: List[str]) -> str:
        """
        Process a comment.
        
        Args:
            comment_lines: The lines of the comment.
            
        Returns:
            The processed comment.
        """
        if not comment_lines:
            return ""
        
        # Process Doxygen tags
        processed_lines = []
        i = 0
        while i < len(comment_lines):
            line = comment_lines[i]
            
            # Check for brief tag
            brief_match = self.brief_regex.match(line)
            if brief_match:
                processed_lines.append(brief_match.group(1))
                i += 1
                continue
            
            # Check for details tag
            details_match = self.details_regex.match(line)
            if details_match:
                processed_lines.append(details_match.group(1))
                i += 1
                continue
            
            # Skip param, return, and throws tags
            if (self.param_regex.match(line) or 
                self.return_regex.match(line) or 
                self.throws_regex.match(line)):
                i += 1
                continue
            
            # Add line
            processed_lines.append(line)
            i += 1
        
        # Join lines
        return '\n'.join(processed_lines)
    
    def _extract_comment_details(self, comment_lines: List[str], parent_node: CodeNode) -> None:
        """
        Extract parameter, return, and throws documentation from a comment.
        
        Args:
            comment_lines: The lines of the comment.
            parent_node: The parent node to add the extracted nodes to.
        """
        for line in comment_lines:
            # Check for param tag
            param_match = self.param_regex.match(line)
            if param_match:
                param_name = param_match.group(1)
                param_type = param_match.group(2) or ""
                param_desc = param_match.group(3)
                
                param_node = CodeNode(
                    CodeNode.TYPE_PARAMETER,
                    name=param_name,
                    content=param_desc,
                    attributes={"param_type": param_type}
                )
                parent_node.add_child(param_node)
                continue
            
            # Check for return tag
            return_match = self.return_regex.match(line)
            if return_match:
                return_type = return_match.group(1) or ""
                return_desc = return_match.group(2)
                
                return_node = CodeNode(
                    CodeNode.TYPE_RETURN,
                    content=return_desc,
                    attributes={"return_type": return_type}
                )
                parent_node.add_child(return_node)
                continue
            
            # Check for throws tag
            throws_match = self.throws_regex.match(line)
            if throws_match:
                exception_name = throws_match.group(1)
                exception_desc = throws_match.group(2) or ""
                
                exception_node = CodeNode(
                    CodeNode.TYPE_EXCEPTION,
                    name=exception_name,
                    content=exception_desc
                )
                parent_node.add_child(exception_node)
                continue
