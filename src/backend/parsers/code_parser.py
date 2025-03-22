#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Parser for RebelSCRIBE.

This module provides a base class for parsing code files into a structured
representation that can be used for documentation generation.
"""

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class CodeNode:
    """
    Represents a node in the code document tree.
    
    This class is the base class for all code elements.
    """
    
    TYPE_FILE = "file"
    TYPE_CLASS = "class"
    TYPE_FUNCTION = "function"
    TYPE_METHOD = "method"
    TYPE_PROPERTY = "property"
    TYPE_VARIABLE = "variable"
    TYPE_ENUM = "enum"
    TYPE_INTERFACE = "interface"
    TYPE_NAMESPACE = "namespace"
    TYPE_MODULE = "module"
    TYPE_COMMENT = "comment"
    TYPE_DOCSTRING = "docstring"
    TYPE_PARAMETER = "parameter"
    TYPE_RETURN = "return"
    TYPE_EXCEPTION = "exception"
    TYPE_DECORATOR = "decorator"
    TYPE_IMPORT = "import"
    TYPE_EXPORT = "export"
    
    def __init__(self, node_type: str, name: str = "", content: str = "", 
                 children: List["CodeNode"] = None, attributes: Dict[str, Any] = None):
        """
        Initialize a CodeNode.
        
        Args:
            node_type: The type of the node.
            name: The name of the node.
            content: The content of the node.
            children: The children of the node.
            attributes: Additional attributes for the node.
        """
        self.type = node_type
        self.name = name
        self.content = content
        self.children = children or []
        self.attributes = attributes or {}
    
    def add_child(self, child: "CodeNode") -> None:
        """
        Add a child node to this node.
        
        Args:
            child: The child node to add.
        """
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node to a dictionary representation.
        
        Returns:
            A dictionary representation of the node.
        """
        return {
            "type": self.type,
            "name": self.name,
            "content": self.content,
            "children": [child.to_dict() for child in self.children],
            "attributes": self.attributes
        }
    
    def to_html(self) -> str:
        """
        Convert the node to HTML.
        
        Returns:
            The HTML representation of the node.
        """
        if self.type == self.TYPE_FILE:
            return f"""
            <div class="code-file">
                <h1>{self.name}</h1>
                <div class="file-content">
                    {''.join(child.to_html() for child in self.children)}
                </div>
            </div>
            """
        
        elif self.type == self.TYPE_CLASS:
            inheritance = self.attributes.get("inheritance", "")
            inheritance_html = f'<span class="inheritance">extends {inheritance}</span>' if inheritance else ""
            
            return f"""
            <div class="code-class">
                <h2 class="class-name">{self.name} {inheritance_html}</h2>
                <div class="class-description">{self.content}</div>
                <div class="class-content">
                    {''.join(child.to_html() for child in self.children)}
                </div>
            </div>
            """
        
        elif self.type == self.TYPE_FUNCTION or self.type == self.TYPE_METHOD:
            params = self.attributes.get("parameters", [])
            params_html = ", ".join([f'<span class="parameter">{p}</span>' for p in params])
            return_type = self.attributes.get("return_type", "")
            return_html = f' -> <span class="return-type">{return_type}</span>' if return_type else ""
            
            return f"""
            <div class="code-function">
                <h3 class="function-name">{self.name}({params_html}){return_html}</h3>
                <div class="function-description">{self.content}</div>
                <div class="function-content">
                    {''.join(child.to_html() for child in self.children)}
                </div>
            </div>
            """
        
        elif self.type == self.TYPE_PROPERTY or self.type == self.TYPE_VARIABLE:
            var_type = self.attributes.get("var_type", "")
            type_html = f': <span class="var-type">{var_type}</span>' if var_type else ""
            
            return f"""
            <div class="code-variable">
                <h4 class="variable-name">{self.name}{type_html}</h4>
                <div class="variable-description">{self.content}</div>
            </div>
            """
        
        elif self.type == self.TYPE_ENUM:
            return f"""
            <div class="code-enum">
                <h3 class="enum-name">{self.name}</h3>
                <div class="enum-description">{self.content}</div>
                <div class="enum-values">
                    {''.join(child.to_html() for child in self.children)}
                </div>
            </div>
            """
        
        elif self.type == self.TYPE_INTERFACE:
            extends = self.attributes.get("extends", "")
            extends_html = f'<span class="extends">extends {extends}</span>' if extends else ""
            
            return f"""
            <div class="code-interface">
                <h2 class="interface-name">{self.name} {extends_html}</h2>
                <div class="interface-description">{self.content}</div>
                <div class="interface-content">
                    {''.join(child.to_html() for child in self.children)}
                </div>
            </div>
            """
        
        elif self.type == self.TYPE_NAMESPACE or self.type == self.TYPE_MODULE:
            return f"""
            <div class="code-namespace">
                <h2 class="namespace-name">{self.name}</h2>
                <div class="namespace-description">{self.content}</div>
                <div class="namespace-content">
                    {''.join(child.to_html() for child in self.children)}
                </div>
            </div>
            """
        
        elif self.type == self.TYPE_PARAMETER:
            param_type = self.attributes.get("param_type", "")
            type_html = f': <span class="param-type">{param_type}</span>' if param_type else ""
            
            return f"""
            <div class="code-parameter">
                <h5 class="parameter-name">{self.name}{type_html}</h5>
                <div class="parameter-description">{self.content}</div>
            </div>
            """
        
        elif self.type == self.TYPE_RETURN:
            return_type = self.attributes.get("return_type", "")
            type_html = f': <span class="return-type">{return_type}</span>' if return_type else ""
            
            return f"""
            <div class="code-return">
                <h5 class="return-label">Returns{type_html}</h5>
                <div class="return-description">{self.content}</div>
            </div>
            """
        
        elif self.type == self.TYPE_EXCEPTION:
            return f"""
            <div class="code-exception">
                <h5 class="exception-name">{self.name}</h5>
                <div class="exception-description">{self.content}</div>
            </div>
            """
        
        elif self.type == self.TYPE_DECORATOR:
            return f"""
            <div class="code-decorator">
                <span class="decorator-name">@{self.name}</span>
                <div class="decorator-description">{self.content}</div>
            </div>
            """
        
        elif self.type == self.TYPE_IMPORT or self.type == self.TYPE_EXPORT:
            return f"""
            <div class="code-import">
                <span class="import-statement">{self.content}</span>
            </div>
            """
        
        elif self.type == self.TYPE_DOCSTRING or self.type == self.TYPE_COMMENT:
            return f"""
            <div class="code-comment">
                <div class="comment-content">{self.content}</div>
            </div>
            """
        
        else:
            logger.warning(f"Unknown node type: {self.type}")
            return f"""
            <div class="code-unknown">
                <div class="unknown-content">{self.content}</div>
            </div>
            """
    
    def to_markdown(self) -> str:
        """
        Convert the node to Markdown.
        
        Returns:
            The Markdown representation of the node.
        """
        if self.type == self.TYPE_FILE:
            return f"# {self.name}\n\n{''.join(child.to_markdown() for child in self.children)}"
        
        elif self.type == self.TYPE_CLASS:
            inheritance = self.attributes.get("inheritance", "")
            inheritance_md = f" extends {inheritance}" if inheritance else ""
            
            return f"## Class: {self.name}{inheritance_md}\n\n{self.content}\n\n{''.join(child.to_markdown() for child in self.children)}"
        
        elif self.type == self.TYPE_FUNCTION or self.type == self.TYPE_METHOD:
            params = self.attributes.get("parameters", [])
            params_md = ", ".join(params)
            return_type = self.attributes.get("return_type", "")
            return_md = f" -> {return_type}" if return_type else ""
            
            return f"### {'Method' if self.type == self.TYPE_METHOD else 'Function'}: {self.name}({params_md}){return_md}\n\n{self.content}\n\n{''.join(child.to_markdown() for child in self.children)}"
        
        elif self.type == self.TYPE_PROPERTY or self.type == self.TYPE_VARIABLE:
            var_type = self.attributes.get("var_type", "")
            type_md = f": {var_type}" if var_type else ""
            
            return f"#### {'Property' if self.type == self.TYPE_PROPERTY else 'Variable'}: {self.name}{type_md}\n\n{self.content}\n\n"
        
        elif self.type == self.TYPE_ENUM:
            return f"### Enum: {self.name}\n\n{self.content}\n\n{''.join(child.to_markdown() for child in self.children)}"
        
        elif self.type == self.TYPE_INTERFACE:
            extends = self.attributes.get("extends", "")
            extends_md = f" extends {extends}" if extends else ""
            
            return f"## Interface: {self.name}{extends_md}\n\n{self.content}\n\n{''.join(child.to_markdown() for child in self.children)}"
        
        elif self.type == self.TYPE_NAMESPACE or self.type == self.TYPE_MODULE:
            return f"## {'Namespace' if self.type == self.TYPE_NAMESPACE else 'Module'}: {self.name}\n\n{self.content}\n\n{''.join(child.to_markdown() for child in self.children)}"
        
        elif self.type == self.TYPE_PARAMETER:
            param_type = self.attributes.get("param_type", "")
            type_md = f": {param_type}" if param_type else ""
            
            return f"- **{self.name}**{type_md}: {self.content}\n"
        
        elif self.type == self.TYPE_RETURN:
            return_type = self.attributes.get("return_type", "")
            type_md = f": {return_type}" if return_type else ""
            
            return f"**Returns**{type_md}: {self.content}\n\n"
        
        elif self.type == self.TYPE_EXCEPTION:
            return f"**Throws {self.name}**: {self.content}\n\n"
        
        elif self.type == self.TYPE_DECORATOR:
            return f"**Decorator @{self.name}**: {self.content}\n\n"
        
        elif self.type == self.TYPE_IMPORT or self.type == self.TYPE_EXPORT:
            return f"```\n{self.content}\n```\n\n"
        
        elif self.type == self.TYPE_DOCSTRING or self.type == self.TYPE_COMMENT:
            return f"{self.content}\n\n"
        
        else:
            logger.warning(f"Unknown node type: {self.type}")
            return f"{self.content}\n\n"


class CodeParser(ABC):
    """
    Base class for code parsers.
    
    This class defines the interface for all code parsers.
    """
    
    def __init__(self):
        """
        Initialize the CodeParser.
        """
        pass
    
    @abstractmethod
    def parse(self, code_text: str, file_path: Optional[str] = None) -> CodeNode:
        """
        Parse code text into a structured representation.
        
        Args:
            code_text: The code text to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            A CodeNode representing the code.
        """
        pass
    
    def parse_file(self, file_path: str) -> CodeNode:
        """
        Parse a code file into a structured representation.
        
        Args:
            file_path: The path to the file to parse.
            
        Returns:
            A CodeNode representing the code.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_text = f.read()
            
            return self.parse(code_text, file_path)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            
            # Create an empty file node
            file_name = os.path.basename(file_path)
            return CodeNode(CodeNode.TYPE_FILE, name=file_name, content=f"Error parsing file: {str(e)}")
    
    def parse_to_html(self, code_text: str, file_path: Optional[str] = None) -> str:
        """
        Parse code text to HTML.
        
        Args:
            code_text: The code text to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            The HTML representation of the code.
        """
        code_node = self.parse(code_text, file_path)
        return code_node.to_html()
    
    def parse_file_to_html(self, file_path: str) -> str:
        """
        Parse a code file to HTML.
        
        Args:
            file_path: The path to the file to parse.
            
        Returns:
            The HTML representation of the code.
        """
        code_node = self.parse_file(file_path)
        return code_node.to_html()
    
    def parse_to_markdown(self, code_text: str, file_path: Optional[str] = None) -> str:
        """
        Parse code text to Markdown.
        
        Args:
            code_text: The code text to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            The Markdown representation of the code.
        """
        code_node = self.parse(code_text, file_path)
        return code_node.to_markdown()
    
    def parse_file_to_markdown(self, file_path: str) -> str:
        """
        Parse a code file to Markdown.
        
        Args:
            file_path: The path to the file to parse.
            
        Returns:
            The Markdown representation of the code.
        """
        code_node = self.parse_file(file_path)
        return code_node.to_markdown()
    
    def parse_to_dict(self, code_text: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse code text to a dictionary representation.
        
        Args:
            code_text: The code text to parse.
            file_path: Optional path to the file being parsed.
            
        Returns:
            A dictionary representation of the code.
        """
        code_node = self.parse(code_text, file_path)
        return code_node.to_dict()
    
    def parse_file_to_dict(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a code file to a dictionary representation.
        
        Args:
            file_path: The path to the file to parse.
            
        Returns:
            A dictionary representation of the code.
        """
        code_node = self.parse_file(file_path)
        return code_node.to_dict()
