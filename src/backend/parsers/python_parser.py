#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Parser for RebelSCRIBE.

This module provides functionality for parsing Python files into a structured
representation that can be used for documentation generation.
"""

import os
import re
import ast
import inspect
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union, cast

from src.utils.logging_utils import get_logger
from .code_parser import CodeParser, CodeNode

logger = get_logger(__name__)

class PythonParser(CodeParser):
    """
    Parser for Python files.
    
    This class provides functionality for parsing Python files into a structured
    representation that can be used for documentation generation.
    """
    
    def __init__(self):
        """
        Initialize the PythonParser.
        """
        super().__init__()
        
        # Regular expressions for parsing docstrings
        self.param_regex = re.compile(r'^\s*(?:Args?|Parameters?|Params?):\s*$')
        self.param_item_regex = re.compile(r'^\s*([a-zA-Z0-9_]+)(?:\s*\(([^)]+)\))?\s*:\s*(.+)$')
        self.return_regex = re.compile(r'^\s*(?:Returns?|Return type):\s*$')
        self.return_item_regex = re.compile(r'^\s*(?:\(([^)]+)\))?\s*(.+)$')
        self.raises_regex = re.compile(r'^\s*(?:Raises?|Exceptions?|Yields?):\s*$')
        self.raises_item_regex = re.compile(r'^\s*([a-zA-Z0-9_]+)(?:\s*\(([^)]+)\))?\s*:\s*(.+)$')
        self.example_regex = re.compile(r'^\s*(?:Examples?|Usage):\s*$')
        self.note_regex = re.compile(r'^\s*(?:Notes?|Warning|Attention|Important|Tip):\s*$')
        
    def parse(self, code_text: str, file_path: Optional[str] = None) -> CodeNode:
        """
        Parse Python code into a structured representation.
        
        Args:
            code_text: The Python code to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            A CodeNode representing the Python code.
        """
        try:
            # Parse the code using ast
            tree = ast.parse(code_text)
            
            # Create file node
            file_name = os.path.basename(file_path) if file_path else "unknown.py"
            file_node = CodeNode(CodeNode.TYPE_FILE, name=file_name)
            
            # Extract module docstring
            if (len(tree.body) > 0 and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                docstring = tree.body[0].value.value
                file_node.content = self._process_docstring(docstring)
            
            # Process imports
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for name in node.names:
                        import_node = CodeNode(
                            CodeNode.TYPE_IMPORT,
                            name=name.name,
                            content=f"import {name.name}"
                        )
                        file_node.add_child(import_node)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join(name.name for name in node.names)
                    import_node = CodeNode(
                        CodeNode.TYPE_IMPORT,
                        name=module,
                        content=f"from {module} import {names}"
                    )
                    file_node.add_child(import_node)
            
            # Process classes and functions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_node = self._process_class(node)
                    file_node.add_child(class_node)
                elif isinstance(node, ast.FunctionDef):
                    function_node = self._process_function(node)
                    file_node.add_child(function_node)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_node = self._process_variable(target, node.value)
                            file_node.add_child(var_node)
            
            return file_node
        except Exception as e:
            logger.error(f"Failed to parse Python code: {e}")
            
            # Create an empty file node
            file_name = os.path.basename(file_path) if file_path else "unknown.py"
            return CodeNode(CodeNode.TYPE_FILE, name=file_name, content=f"Error parsing Python code: {str(e)}")
    
    def _process_class(self, node: ast.ClassDef) -> CodeNode:
        """
        Process a class definition.
        
        Args:
            node: The AST node representing the class.
            
        Returns:
            A CodeNode representing the class.
        """
        # Get class name
        class_name = node.name
        
        # Get inheritance
        inheritance = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                inheritance.append(base.id)
            elif isinstance(base, ast.Attribute):
                inheritance.append(self._get_attribute_name(base))
        
        inheritance_str = ", ".join(inheritance)
        
        # Create class node
        class_node = CodeNode(
            CodeNode.TYPE_CLASS,
            name=class_name,
            attributes={"inheritance": inheritance_str}
        )
        
        # Extract docstring
        if (len(node.body) > 0 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            class_node.content = self._process_docstring(docstring)
        
        # Process methods and class variables
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_node = self._process_method(item)
                class_node.add_child(method_node)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        var_node = self._process_variable(target, item.value, is_property=True)
                        class_node.add_child(var_node)
        
        return class_node
    
    def _process_function(self, node: ast.FunctionDef) -> CodeNode:
        """
        Process a function definition.
        
        Args:
            node: The AST node representing the function.
            
        Returns:
            A CodeNode representing the function.
        """
        # Get function name
        function_name = node.name
        
        # Get parameters
        parameters = []
        for arg in node.args.args:
            param_name = arg.arg
            
            # Get type annotation if available
            param_type = ""
            if arg.annotation:
                param_type = self._get_annotation_name(arg.annotation)
            
            if param_type:
                parameters.append(f"{param_name}: {param_type}")
            else:
                parameters.append(param_name)
        
        # Get return type
        return_type = ""
        if node.returns:
            return_type = self._get_annotation_name(node.returns)
        
        # Create function node
        function_node = CodeNode(
            CodeNode.TYPE_FUNCTION,
            name=function_name,
            attributes={
                "parameters": parameters,
                "return_type": return_type
            }
        )
        
        # Extract docstring
        if (len(node.body) > 0 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            function_node.content = self._process_docstring(docstring)
            
            # Extract parameter and return documentation
            self._extract_docstring_details(docstring, function_node)
        
        # Process decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorator_node = CodeNode(
                    CodeNode.TYPE_DECORATOR,
                    name=decorator.id
                )
                function_node.add_child(decorator_node)
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                decorator_node = CodeNode(
                    CodeNode.TYPE_DECORATOR,
                    name=decorator.func.id
                )
                function_node.add_child(decorator_node)
        
        return function_node
    
    def _process_method(self, node: ast.FunctionDef) -> CodeNode:
        """
        Process a method definition.
        
        Args:
            node: The AST node representing the method.
            
        Returns:
            A CodeNode representing the method.
        """
        # Get method name
        method_name = node.name
        
        # Get parameters
        parameters = []
        for arg in node.args.args:
            param_name = arg.arg
            
            # Skip 'self' parameter
            if param_name == 'self':
                continue
            
            # Get type annotation if available
            param_type = ""
            if arg.annotation:
                param_type = self._get_annotation_name(arg.annotation)
            
            if param_type:
                parameters.append(f"{param_name}: {param_type}")
            else:
                parameters.append(param_name)
        
        # Get return type
        return_type = ""
        if node.returns:
            return_type = self._get_annotation_name(node.returns)
        
        # Create method node
        method_node = CodeNode(
            CodeNode.TYPE_METHOD,
            name=method_name,
            attributes={
                "parameters": parameters,
                "return_type": return_type
            }
        )
        
        # Extract docstring
        if (len(node.body) > 0 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            method_node.content = self._process_docstring(docstring)
            
            # Extract parameter and return documentation
            self._extract_docstring_details(docstring, method_node)
        
        # Process decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorator_name = decorator.id
                
                # Check for property decorator
                if decorator_name == 'property':
                    method_node.type = CodeNode.TYPE_PROPERTY
                
                decorator_node = CodeNode(
                    CodeNode.TYPE_DECORATOR,
                    name=decorator_name
                )
                method_node.add_child(decorator_node)
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                decorator_node = CodeNode(
                    CodeNode.TYPE_DECORATOR,
                    name=decorator.func.id
                )
                method_node.add_child(decorator_node)
        
        return method_node
    
    def _process_variable(self, target: ast.Name, value: ast.AST, is_property: bool = False) -> CodeNode:
        """
        Process a variable assignment.
        
        Args:
            target: The AST node representing the variable name.
            value: The AST node representing the variable value.
            is_property: Whether the variable is a class property.
            
        Returns:
            A CodeNode representing the variable.
        """
        # Get variable name
        var_name = target.id
        
        # Get variable type if available
        var_type = ""
        if isinstance(value, ast.Constant):
            var_type = type(value.value).__name__
        elif isinstance(value, ast.List):
            var_type = "list"
        elif isinstance(value, ast.Dict):
            var_type = "dict"
        elif isinstance(value, ast.Set):
            var_type = "set"
        elif isinstance(value, ast.Tuple):
            var_type = "tuple"
        
        # Create variable node
        var_node = CodeNode(
            CodeNode.TYPE_PROPERTY if is_property else CodeNode.TYPE_VARIABLE,
            name=var_name,
            attributes={"var_type": var_type}
        )
        
        return var_node
    
    def _process_docstring(self, docstring: str) -> str:
        """
        Process a docstring.
        
        Args:
            docstring: The docstring to process.
            
        Returns:
            The processed docstring.
        """
        if not docstring:
            return ""
        
        # Remove leading/trailing whitespace
        docstring = docstring.strip()
        
        # Split into lines
        lines = docstring.split('\n')
        
        # Remove common indentation
        if len(lines) > 1:
            # Find minimum indentation
            min_indent = float('inf')
            for line in lines[1:]:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)
            
            # Remove indentation
            if min_indent < float('inf'):
                for i in range(1, len(lines)):
                    if lines[i].strip():
                        lines[i] = lines[i][min_indent:]
        
        # Join lines
        return '\n'.join(lines)
    
    def _extract_docstring_details(self, docstring: str, parent_node: CodeNode) -> None:
        """
        Extract parameter and return documentation from a docstring.
        
        Args:
            docstring: The docstring to process.
            parent_node: The parent node to add the extracted nodes to.
        """
        if not docstring:
            return
        
        # Split into lines
        lines = docstring.split('\n')
        
        # Process lines
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for parameters section
            if self.param_regex.match(line):
                i += 1
                while i < len(lines) and lines[i].strip():
                    param_match = self.param_item_regex.match(lines[i])
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
                    
                    i += 1
                continue
            
            # Check for returns section
            if self.return_regex.match(line):
                i += 1
                return_desc = []
                while i < len(lines) and lines[i].strip():
                    return_match = self.return_item_regex.match(lines[i])
                    if return_match:
                        return_type = return_match.group(1) or ""
                        return_desc.append(return_match.group(2))
                    else:
                        return_desc.append(lines[i].strip())
                    
                    i += 1
                
                return_node = CodeNode(
                    CodeNode.TYPE_RETURN,
                    content='\n'.join(return_desc),
                    attributes={"return_type": return_type if 'return_type' in locals() else ""}
                )
                parent_node.add_child(return_node)
                continue
            
            # Check for raises section
            if self.raises_regex.match(line):
                i += 1
                while i < len(lines) and lines[i].strip():
                    raises_match = self.raises_item_regex.match(lines[i])
                    if raises_match:
                        exception_name = raises_match.group(1)
                        exception_desc = raises_match.group(3)
                        
                        exception_node = CodeNode(
                            CodeNode.TYPE_EXCEPTION,
                            name=exception_name,
                            content=exception_desc
                        )
                        parent_node.add_child(exception_node)
                    
                    i += 1
                continue
            
            i += 1
    
    def _get_annotation_name(self, node: ast.AST) -> str:
        """
        Get the name of a type annotation.
        
        Args:
            node: The AST node representing the annotation.
            
        Returns:
            The name of the annotation.
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.Subscript):
            value_name = self._get_annotation_name(node.value)
            if isinstance(node.slice, ast.Index):
                if isinstance(node.slice.value, ast.Name):
                    return f"{value_name}[{node.slice.value.id}]"
                elif isinstance(node.slice.value, ast.Tuple):
                    elts = []
                    for elt in node.slice.value.elts:
                        if isinstance(elt, ast.Name):
                            elts.append(elt.id)
                    return f"{value_name}[{', '.join(elts)}]"
            return value_name
        elif isinstance(node, ast.Constant) and node.value is None:
            return "None"
        else:
            return str(node)
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """
        Get the full name of an attribute.
        
        Args:
            node: The AST node representing the attribute.
            
        Returns:
            The full name of the attribute.
        """
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr
