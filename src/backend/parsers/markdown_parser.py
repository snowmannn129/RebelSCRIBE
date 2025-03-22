#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Parser for RebelSCRIBE.

This module provides functionality for parsing Markdown documents into a structured
representation that can be used by the rest of the system.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class MarkdownNode:
    """
    Represents a node in the Markdown document tree.
    
    This class is the base class for all Markdown elements.
    """
    
    TYPE_DOCUMENT = "document"
    TYPE_HEADING = "heading"
    TYPE_PARAGRAPH = "paragraph"
    TYPE_LIST = "list"
    TYPE_LIST_ITEM = "list_item"
    TYPE_CODE_BLOCK = "code_block"
    TYPE_BLOCKQUOTE = "blockquote"
    TYPE_HORIZONTAL_RULE = "horizontal_rule"
    TYPE_TABLE = "table"
    TYPE_TABLE_ROW = "table_row"
    TYPE_TABLE_CELL = "table_cell"
    TYPE_IMAGE = "image"
    TYPE_LINK = "link"
    TYPE_EMPHASIS = "emphasis"
    TYPE_STRONG = "strong"
    TYPE_CODE = "code"
    TYPE_STRIKETHROUGH = "strikethrough"
    TYPE_HTML = "html"
    TYPE_TEXT = "text"
    
    def __init__(self, node_type: str, content: str = "", children: List["MarkdownNode"] = None, 
                attributes: Dict[str, Any] = None):
        """
        Initialize a MarkdownNode.
        
        Args:
            node_type: The type of the node.
            content: The content of the node.
            children: The children of the node.
            attributes: Additional attributes for the node.
        """
        self.type = node_type
        self.content = content
        self.children = children or []
        self.attributes = attributes or {}
    
    def add_child(self, child: "MarkdownNode") -> None:
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
        if self.type == self.TYPE_DOCUMENT:
            return "\n".join(child.to_html() for child in self.children)
        
        elif self.type == self.TYPE_HEADING:
            level = self.attributes.get("level", 1)
            return f"<h{level}>{self.content}</h{level}>"
        
        elif self.type == self.TYPE_PARAGRAPH:
            return f"<p>{self.content}</p>"
        
        elif self.type == self.TYPE_LIST:
            list_type = self.attributes.get("list_type", "unordered")
            tag = "ul" if list_type == "unordered" else "ol"
            items = "\n".join(child.to_html() for child in self.children)
            return f"<{tag}>\n{items}\n</{tag}>"
        
        elif self.type == self.TYPE_LIST_ITEM:
            return f"<li>{self.content}</li>"
        
        elif self.type == self.TYPE_CODE_BLOCK:
            language = self.attributes.get("language", "")
            return f'<pre><code class="language-{language}">{self.content}</code></pre>'
        
        elif self.type == self.TYPE_BLOCKQUOTE:
            return f"<blockquote>{self.content}</blockquote>"
        
        elif self.type == self.TYPE_HORIZONTAL_RULE:
            return "<hr>"
        
        elif self.type == self.TYPE_TABLE:
            rows = "\n".join(child.to_html() for child in self.children)
            return f"<table>\n{rows}\n</table>"
        
        elif self.type == self.TYPE_TABLE_ROW:
            cells = "\n".join(child.to_html() for child in self.children)
            return f"<tr>\n{cells}\n</tr>"
        
        elif self.type == self.TYPE_TABLE_CELL:
            is_header = self.attributes.get("is_header", False)
            tag = "th" if is_header else "td"
            return f"<{tag}>{self.content}</{tag}>"
        
        elif self.type == self.TYPE_IMAGE:
            src = self.attributes.get("src", "")
            alt = self.attributes.get("alt", "")
            return f'<img src="{src}" alt="{alt}">'
        
        elif self.type == self.TYPE_LINK:
            href = self.attributes.get("href", "")
            return f'<a href="{href}">{self.content}</a>'
        
        elif self.type == self.TYPE_EMPHASIS:
            return f"<em>{self.content}</em>"
        
        elif self.type == self.TYPE_STRONG:
            return f"<strong>{self.content}</strong>"
        
        elif self.type == self.TYPE_CODE:
            return f"<code>{self.content}</code>"
        
        elif self.type == self.TYPE_STRIKETHROUGH:
            return f"<del>{self.content}</del>"
        
        elif self.type == self.TYPE_HTML:
            return self.content
        
        elif self.type == self.TYPE_TEXT:
            return self.content
        
        else:
            logger.warning(f"Unknown node type: {self.type}")
            return self.content
    
    def to_markdown(self) -> str:
        """
        Convert the node back to Markdown.
        
        Returns:
            The Markdown representation of the node.
        """
        if self.type == self.TYPE_DOCUMENT:
            return "\n\n".join(child.to_markdown() for child in self.children)
        
        elif self.type == self.TYPE_HEADING:
            level = self.attributes.get("level", 1)
            return f"{'#' * level} {self.content}"
        
        elif self.type == self.TYPE_PARAGRAPH:
            return self.content
        
        elif self.type == self.TYPE_LIST:
            return "\n".join(child.to_markdown() for child in self.children)
        
        elif self.type == self.TYPE_LIST_ITEM:
            list_type = self.attributes.get("list_type", "unordered")
            prefix = "- " if list_type == "unordered" else f"{self.attributes.get('number', 1)}. "
            return f"{prefix}{self.content}"
        
        elif self.type == self.TYPE_CODE_BLOCK:
            language = self.attributes.get("language", "")
            return f"```{language}\n{self.content}\n```"
        
        elif self.type == self.TYPE_BLOCKQUOTE:
            lines = self.content.split("\n")
            return "\n".join(f"> {line}" for line in lines)
        
        elif self.type == self.TYPE_HORIZONTAL_RULE:
            return "---"
        
        elif self.type == self.TYPE_TABLE:
            # This is a simplified implementation
            return "\n".join(child.to_markdown() for child in self.children)
        
        elif self.type == self.TYPE_TABLE_ROW:
            return " | ".join(child.to_markdown() for child in self.children)
        
        elif self.type == self.TYPE_TABLE_CELL:
            return self.content
        
        elif self.type == self.TYPE_IMAGE:
            src = self.attributes.get("src", "")
            alt = self.attributes.get("alt", "")
            return f"![{alt}]({src})"
        
        elif self.type == self.TYPE_LINK:
            href = self.attributes.get("href", "")
            return f"[{self.content}]({href})"
        
        elif self.type == self.TYPE_EMPHASIS:
            return f"*{self.content}*"
        
        elif self.type == self.TYPE_STRONG:
            return f"**{self.content}**"
        
        elif self.type == self.TYPE_CODE:
            return f"`{self.content}`"
        
        elif self.type == self.TYPE_STRIKETHROUGH:
            return f"~~{self.content}~~"
        
        elif self.type == self.TYPE_HTML:
            return self.content
        
        elif self.type == self.TYPE_TEXT:
            return self.content
        
        else:
            logger.warning(f"Unknown node type: {self.type}")
            return self.content


class MarkdownParser:
    """
    Parser for Markdown documents.
    
    This class provides functionality for parsing Markdown documents into a structured
    representation that can be used by the rest of the system.
    """
    
    def __init__(self):
        """
        Initialize the MarkdownParser.
        """
        # Regular expressions for parsing
        self.heading_regex = re.compile(r'^(#{1,6})\s+(.+)$')
        self.horizontal_rule_regex = re.compile(r'^([-*_])\s*\1\s*\1\s*[\1\s]*$')
        self.unordered_list_regex = re.compile(r'^([-*+])\s+(.+)$')
        self.ordered_list_regex = re.compile(r'^(\d+)[.)]\s+(.+)$')
        self.code_block_regex = re.compile(r'^```(\w*)$')
        self.blockquote_regex = re.compile(r'^>\s*(.*)$')
        self.image_regex = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.link_regex = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.emphasis_regex = re.compile(r'(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)')
        self.strong_regex = re.compile(r'\*\*([^*]+)\*\*')
        self.code_regex = re.compile(r'`([^`]+)`')
        self.strikethrough_regex = re.compile(r'~~([^~]+)~~')
        
        # State variables
        self.in_code_block = False
        self.code_block_language = ""
        self.code_block_content = []
    
    def parse(self, markdown_text: str) -> MarkdownNode:
        """
        Parse a Markdown document into a structured representation.
        
        Args:
            markdown_text: The Markdown text to parse.
            
        Returns:
            A MarkdownNode representing the document.
        """
        # Create document node
        document = MarkdownNode(MarkdownNode.TYPE_DOCUMENT)
        
        # Split into lines
        lines = markdown_text.split("\n")
        
        # Process lines
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Check if we're in a code block
            if self.in_code_block:
                if line.strip() == "```":
                    # End of code block
                    self.in_code_block = False
                    code_block = MarkdownNode(
                        MarkdownNode.TYPE_CODE_BLOCK,
                        "\n".join(self.code_block_content),
                        attributes={"language": self.code_block_language}
                    )
                    document.add_child(code_block)
                    self.code_block_content = []
                else:
                    # Add line to code block
                    self.code_block_content.append(line)
                i += 1
                continue
            
            # Check for code block start
            code_block_match = self.code_block_regex.match(line)
            if code_block_match:
                self.in_code_block = True
                self.code_block_language = code_block_match.group(1)
                i += 1
                continue
            
            # Check for heading
            heading_match = self.heading_regex.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                heading = MarkdownNode(
                    MarkdownNode.TYPE_HEADING,
                    content,
                    attributes={"level": level}
                )
                document.add_child(heading)
                i += 1
                continue
            
            # Check for horizontal rule
            hr_match = self.horizontal_rule_regex.match(line)
            if hr_match:
                hr = MarkdownNode(MarkdownNode.TYPE_HORIZONTAL_RULE)
                document.add_child(hr)
                i += 1
                continue
            
            # Check for unordered list
            ul_match = self.unordered_list_regex.match(line)
            if ul_match:
                list_node = MarkdownNode(
                    MarkdownNode.TYPE_LIST,
                    attributes={"list_type": "unordered"}
                )
                
                # Process list items
                while i < len(lines) and (ul_match := self.unordered_list_regex.match(lines[i])):
                    content = ul_match.group(2)
                    item = MarkdownNode(
                        MarkdownNode.TYPE_LIST_ITEM,
                        content,
                        attributes={"list_type": "unordered"}
                    )
                    list_node.add_child(item)
                    i += 1
                
                document.add_child(list_node)
                continue
            
            # Check for ordered list
            ol_match = self.ordered_list_regex.match(line)
            if ol_match:
                list_node = MarkdownNode(
                    MarkdownNode.TYPE_LIST,
                    attributes={"list_type": "ordered"}
                )
                
                # Process list items
                number = 1
                while i < len(lines) and (ol_match := self.ordered_list_regex.match(lines[i])):
                    content = ol_match.group(2)
                    item = MarkdownNode(
                        MarkdownNode.TYPE_LIST_ITEM,
                        content,
                        attributes={"list_type": "ordered", "number": number}
                    )
                    list_node.add_child(item)
                    number += 1
                    i += 1
                
                document.add_child(list_node)
                continue
            
            # Check for blockquote
            bq_match = self.blockquote_regex.match(line)
            if bq_match:
                blockquote_lines = []
                
                # Process blockquote lines
                while i < len(lines) and (bq_match := self.blockquote_regex.match(lines[i])):
                    blockquote_lines.append(bq_match.group(1))
                    i += 1
                
                blockquote = MarkdownNode(
                    MarkdownNode.TYPE_BLOCKQUOTE,
                    "\n".join(blockquote_lines)
                )
                document.add_child(blockquote)
                continue
            
            # If we get here, it's a paragraph
            paragraph_lines = []
            while i < len(lines) and lines[i].strip():
                paragraph_lines.append(lines[i])
                i += 1
            
            paragraph_text = " ".join(paragraph_lines)
            
            # Process inline elements
            paragraph_text = self._process_inline_elements(paragraph_text)
            
            paragraph = MarkdownNode(MarkdownNode.TYPE_PARAGRAPH, paragraph_text)
            document.add_child(paragraph)
            
            # Skip any empty lines after the paragraph
            while i < len(lines) and not lines[i].strip():
                i += 1
        
        return document
    
    def _process_inline_elements(self, text: str) -> str:
        """
        Process inline Markdown elements.
        
        Args:
            text: The text to process.
            
        Returns:
            The processed text with HTML tags for inline elements.
        """
        # Process images
        text = self.image_regex.sub(r'<img src="\2" alt="\1">', text)
        
        # Process links
        text = self.link_regex.sub(r'<a href="\2">\1</a>', text)
        
        # Process strong
        text = self.strong_regex.sub(r'<strong>\1</strong>', text)
        
        # Process emphasis
        text = self.emphasis_regex.sub(r'<em>\1</em>', text)
        
        # Process code
        text = self.code_regex.sub(r'<code>\1</code>', text)
        
        # Process strikethrough
        text = self.strikethrough_regex.sub(r'<del>\1</del>', text)
        
        return text
    
    def parse_to_html(self, markdown_text: str) -> str:
        """
        Parse Markdown text to HTML.
        
        Args:
            markdown_text: The Markdown text to parse.
            
        Returns:
            The HTML representation of the Markdown text.
        """
        document = self.parse(markdown_text)
        return document.to_html()
    
    def parse_to_dict(self, markdown_text: str) -> Dict[str, Any]:
        """
        Parse Markdown text to a dictionary representation.
        
        Args:
            markdown_text: The Markdown text to parse.
            
        Returns:
            A dictionary representation of the Markdown text.
        """
        document = self.parse(markdown_text)
        return document.to_dict()
