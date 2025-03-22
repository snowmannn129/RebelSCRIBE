#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test module for the Markdown Parser.

This module contains tests for the MarkdownParser class.
"""

import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent.parent.parent.absolute()
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.backend.parsers.markdown_parser import MarkdownParser, MarkdownNode

class TestMarkdownParser(unittest.TestCase):
    """Test case for the MarkdownParser class."""
    
    def setUp(self):
        """Set up the test case."""
        self.parser = MarkdownParser()
    
    def test_parse_heading(self):
        """Test parsing headings."""
        markdown = "# Heading 1\n\n## Heading 2\n\n### Heading 3"
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 3)
        
        self.assertEqual(document.children[0].type, MarkdownNode.TYPE_HEADING)
        self.assertEqual(document.children[0].content, "Heading 1")
        self.assertEqual(document.children[0].attributes["level"], 1)
        
        self.assertEqual(document.children[1].type, MarkdownNode.TYPE_HEADING)
        self.assertEqual(document.children[1].content, "Heading 2")
        self.assertEqual(document.children[1].attributes["level"], 2)
        
        self.assertEqual(document.children[2].type, MarkdownNode.TYPE_HEADING)
        self.assertEqual(document.children[2].content, "Heading 3")
        self.assertEqual(document.children[2].attributes["level"], 3)
    
    def test_parse_paragraph(self):
        """Test parsing paragraphs."""
        markdown = "This is a paragraph.\n\nThis is another paragraph."
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 2)
        
        self.assertEqual(document.children[0].type, MarkdownNode.TYPE_PARAGRAPH)
        self.assertEqual(document.children[0].content, "This is a paragraph.")
        
        self.assertEqual(document.children[1].type, MarkdownNode.TYPE_PARAGRAPH)
        self.assertEqual(document.children[1].content, "This is another paragraph.")
    
    def test_parse_unordered_list(self):
        """Test parsing unordered lists."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        list_node = document.children[0]
        self.assertEqual(list_node.type, MarkdownNode.TYPE_LIST)
        self.assertEqual(list_node.attributes["list_type"], "unordered")
        
        self.assertEqual(len(list_node.children), 3)
        
        self.assertEqual(list_node.children[0].type, MarkdownNode.TYPE_LIST_ITEM)
        self.assertEqual(list_node.children[0].content, "Item 1")
        
        self.assertEqual(list_node.children[1].type, MarkdownNode.TYPE_LIST_ITEM)
        self.assertEqual(list_node.children[1].content, "Item 2")
        
        self.assertEqual(list_node.children[2].type, MarkdownNode.TYPE_LIST_ITEM)
        self.assertEqual(list_node.children[2].content, "Item 3")
    
    def test_parse_ordered_list(self):
        """Test parsing ordered lists."""
        markdown = "1. Item 1\n2. Item 2\n3. Item 3"
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        list_node = document.children[0]
        self.assertEqual(list_node.type, MarkdownNode.TYPE_LIST)
        self.assertEqual(list_node.attributes["list_type"], "ordered")
        
        self.assertEqual(len(list_node.children), 3)
        
        self.assertEqual(list_node.children[0].type, MarkdownNode.TYPE_LIST_ITEM)
        self.assertEqual(list_node.children[0].content, "Item 1")
        self.assertEqual(list_node.children[0].attributes["number"], 1)
        
        self.assertEqual(list_node.children[1].type, MarkdownNode.TYPE_LIST_ITEM)
        self.assertEqual(list_node.children[1].content, "Item 2")
        self.assertEqual(list_node.children[1].attributes["number"], 2)
        
        self.assertEqual(list_node.children[2].type, MarkdownNode.TYPE_LIST_ITEM)
        self.assertEqual(list_node.children[2].content, "Item 3")
        self.assertEqual(list_node.children[2].attributes["number"], 3)
    
    def test_parse_code_block(self):
        """Test parsing code blocks."""
        markdown = "```python\ndef hello():\n    print('Hello, world!')\n```"
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        code_block = document.children[0]
        self.assertEqual(code_block.type, MarkdownNode.TYPE_CODE_BLOCK)
        self.assertEqual(code_block.content, "def hello():\n    print('Hello, world!')")
        self.assertEqual(code_block.attributes["language"], "python")
    
    def test_parse_blockquote(self):
        """Test parsing blockquotes."""
        markdown = "> This is a blockquote.\n> It can span multiple lines."
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        blockquote = document.children[0]
        self.assertEqual(blockquote.type, MarkdownNode.TYPE_BLOCKQUOTE)
        self.assertEqual(blockquote.content, "This is a blockquote.\nIt can span multiple lines.")
    
    def test_parse_horizontal_rule(self):
        """Test parsing horizontal rules."""
        markdown = "---"
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        hr = document.children[0]
        self.assertEqual(hr.type, MarkdownNode.TYPE_HORIZONTAL_RULE)
    
    def test_parse_inline_elements(self):
        """Test parsing inline elements."""
        markdown = "This is **bold** and *italic* text with `code` and a [link](https://example.com)."
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        paragraph = document.children[0]
        self.assertEqual(paragraph.type, MarkdownNode.TYPE_PARAGRAPH)
        self.assertEqual(
            paragraph.content,
            "This is <strong>bold</strong> and <em>italic</em> text with <code>code</code> and a <a href=\"https://example.com\">link</a>."
        )
    
    def test_parse_image(self):
        """Test parsing images."""
        markdown = "![Alt text](https://example.com/image.jpg)"
        document = self.parser.parse(markdown)
        
        self.assertEqual(len(document.children), 1)
        
        paragraph = document.children[0]
        self.assertEqual(paragraph.type, MarkdownNode.TYPE_PARAGRAPH)
        self.assertEqual(
            paragraph.content,
            "<img src=\"https://example.com/image.jpg\" alt=\"Alt text\">"
        )
    
    def test_parse_to_html(self):
        """Test parsing Markdown to HTML."""
        markdown = "# Heading\n\nThis is a paragraph."
        html = self.parser.parse_to_html(markdown)
        
        self.assertEqual(html, "<h1>Heading</h1>\n<p>This is a paragraph.</p>")
    
    def test_parse_to_dict(self):
        """Test parsing Markdown to a dictionary representation."""
        markdown = "# Heading"
        result = self.parser.parse_to_dict(markdown)
        
        self.assertEqual(result["type"], MarkdownNode.TYPE_DOCUMENT)
        self.assertEqual(len(result["children"]), 1)
        self.assertEqual(result["children"][0]["type"], MarkdownNode.TYPE_HEADING)
        self.assertEqual(result["children"][0]["content"], "Heading")
        self.assertEqual(result["children"][0]["attributes"]["level"], 1)
    
    def test_complex_document(self):
        """Test parsing a complex Markdown document."""
        markdown = """# Document Title

This is a paragraph with **bold** and *italic* text.

## Section 1

- Item 1
- Item 2
- Item 3

```python
def hello():
    print('Hello, world!')
```

> This is a blockquote.
> It can span multiple lines.

---

## Section 2

1. First item
2. Second item
3. Third item

![Image](https://example.com/image.jpg)

[Link](https://example.com)
"""
        document = self.parser.parse(markdown)
        
        # Check document structure
        self.assertEqual(document.type, MarkdownNode.TYPE_DOCUMENT)
        self.assertEqual(len(document.children), 11)
        
        # Check heading 1
        self.assertEqual(document.children[0].type, MarkdownNode.TYPE_HEADING)
        self.assertEqual(document.children[0].content, "Document Title")
        self.assertEqual(document.children[0].attributes["level"], 1)
        
        # Check paragraph
        self.assertEqual(document.children[1].type, MarkdownNode.TYPE_PARAGRAPH)
        self.assertEqual(
            document.children[1].content,
            "This is a paragraph with <strong>bold</strong> and <em>italic</em> text."
        )
        
        # Check heading 2
        self.assertEqual(document.children[2].type, MarkdownNode.TYPE_HEADING)
        self.assertEqual(document.children[2].content, "Section 1")
        self.assertEqual(document.children[2].attributes["level"], 2)
        
        # Check unordered list
        self.assertEqual(document.children[3].type, MarkdownNode.TYPE_LIST)
        self.assertEqual(document.children[3].attributes["list_type"], "unordered")
        self.assertEqual(len(document.children[3].children), 3)
        
        # Check code block
        self.assertEqual(document.children[4].type, MarkdownNode.TYPE_CODE_BLOCK)
        self.assertEqual(document.children[4].content, "def hello():\n    print('Hello, world!')")
        self.assertEqual(document.children[4].attributes["language"], "python")
        
        # Check blockquote
        self.assertEqual(document.children[5].type, MarkdownNode.TYPE_BLOCKQUOTE)
        self.assertEqual(document.children[5].content, "This is a blockquote.\nIt can span multiple lines.")
        
        # Check horizontal rule
        self.assertEqual(document.children[6].type, MarkdownNode.TYPE_HORIZONTAL_RULE)
        
        # Check heading 2
        self.assertEqual(document.children[7].type, MarkdownNode.TYPE_HEADING)
        self.assertEqual(document.children[7].content, "Section 2")
        self.assertEqual(document.children[7].attributes["level"], 2)
        
        # Check ordered list
        self.assertEqual(document.children[8].type, MarkdownNode.TYPE_LIST)
        self.assertEqual(document.children[8].attributes["list_type"], "ordered")
        self.assertEqual(len(document.children[8].children), 3)
        
        # Check paragraph with image and link
        self.assertEqual(document.children[9].type, MarkdownNode.TYPE_PARAGRAPH)
        self.assertTrue("<img src=\"https://example.com/image.jpg\" alt=\"Image\">" in document.children[9].content)
        self.assertTrue("<a href=\"https://example.com\">Link</a>" in document.children[9].content)

if __name__ == "__main__":
    unittest.main()
