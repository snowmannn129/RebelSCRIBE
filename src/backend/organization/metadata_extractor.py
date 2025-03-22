#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Extractor for RebelSCRIBE.

This module provides functionality for extracting metadata from various content types,
including Markdown documents, code files, and other document formats.
"""

import re
import os
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime
import yaml

from src.utils.logging_utils import get_logger
from src.backend.parsers.markdown_parser import MarkdownParser

logger = get_logger(__name__)

class MetadataExtractor:
    """
    Extracts metadata from various content types.
    
    This class provides functionality for extracting metadata from Markdown documents,
    code files, and other document formats.
    """
    
    def __init__(self):
        """Initialize the MetadataExtractor."""
        self.markdown_parser = MarkdownParser()
        
        # Regular expressions for extracting metadata
        self.markdown_metadata_regex = re.compile(r'---\s+(.*?)\s+---', re.DOTALL)
        self.code_metadata_regex = re.compile(r'/\*\*\s+(.*?)\s+\*\*/', re.DOTALL)
        self.python_docstring_regex = re.compile(r'"""(.*?)"""', re.DOTALL)
        
        # Metadata field mappings
        self.field_mappings = {
            'title': ['title', 'name', 'heading'],
            'author': ['author', 'creator', 'by'],
            'date': ['date', 'created', 'published'],
            'description': ['description', 'summary', 'abstract'],
            'tags': ['tags', 'keywords', 'categories'],
            'version': ['version', 'ver', 'v'],
            'status': ['status', 'state'],
            'language': ['language', 'lang'],
            'license': ['license', 'copyright'],
            'publisher': ['publisher', 'published by']
        }
    
    def extract_from_markdown(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from Markdown content.
        
        Args:
            content: The Markdown content to extract metadata from.
            
        Returns:
            A dictionary of metadata.
        """
        metadata = {}
        
        try:
            # Look for YAML frontmatter
            match = self.markdown_metadata_regex.search(content)
            if match:
                yaml_content = match.group(1)
                try:
                    # Parse YAML
                    yaml_metadata = yaml.safe_load(yaml_content)
                    if isinstance(yaml_metadata, dict):
                        metadata.update(yaml_metadata)
                except Exception as e:
                    logger.warning(f"Error parsing YAML frontmatter: {e}")
            
            # Extract metadata from document structure
            if not metadata.get('title'):
                # Try to extract title from first heading
                heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if heading_match:
                    metadata['title'] = heading_match.group(1).strip()
            
            # Extract tags from content
            if not metadata.get('tags'):
                # Look for hashtags
                hashtags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                if hashtags:
                    metadata['tags'] = list(set(hashtags))
            
            # Extract date from content
            if not metadata.get('date'):
                # Look for date patterns
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
                if date_match:
                    metadata['date'] = date_match.group(1)
            
            # Extract word count and reading time
            word_count = len(re.findall(r'\b\w+\b', content))
            metadata['word_count'] = word_count
            metadata['reading_time'] = max(1, round(word_count / 200))  # Assuming 200 words per minute
            
            # Extract links
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            if links:
                metadata['links'] = [{'text': text, 'url': url} for text, url in links]
            
            # Extract images
            images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
            if images:
                metadata['images'] = [{'alt': alt, 'url': url} for alt, url in images]
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata from Markdown: {e}", exc_info=True)
            return metadata
    
    def extract_from_code(self, content: str, file_extension: str) -> Dict[str, Any]:
        """
        Extract metadata from code content.
        
        Args:
            content: The code content to extract metadata from.
            file_extension: The file extension (e.g., 'py', 'js', 'cpp').
            
        Returns:
            A dictionary of metadata.
        """
        metadata = {}
        
        try:
            # Extract based on file type
            if file_extension == 'py':
                # Python files
                match = self.python_docstring_regex.search(content)
                if match:
                    docstring = match.group(1).strip()
                    metadata['description'] = docstring
                    
                    # Extract parameters
                    param_matches = re.findall(r'Args:\s+(.*?)(?:\n\s*\n|\n\s*Returns:|\n\s*Raises:|\Z)', docstring, re.DOTALL)
                    if param_matches:
                        params_text = param_matches[0]
                        params = re.findall(r'(\w+):\s+([^\n]+)', params_text)
                        if params:
                            metadata['parameters'] = {name: desc.strip() for name, desc in params}
                    
                    # Extract return value
                    return_matches = re.findall(r'Returns:\s+(.*?)(?:\n\s*\n|\n\s*Raises:|\Z)', docstring, re.DOTALL)
                    if return_matches:
                        metadata['returns'] = return_matches[0].strip()
                    
                    # Extract exceptions
                    raises_matches = re.findall(r'Raises:\s+(.*?)(?:\n\s*\n|\Z)', docstring, re.DOTALL)
                    if raises_matches:
                        raises_text = raises_matches[0]
                        raises = re.findall(r'(\w+):\s+([^\n]+)', raises_text)
                        if raises:
                            metadata['raises'] = {name: desc.strip() for name, desc in raises}
            
            elif file_extension in ['js', 'ts']:
                # JavaScript/TypeScript files
                # Extract JSDoc comments
                jsdoc_matches = re.findall(r'/\*\*\s+(.*?)\s+\*/', content, re.DOTALL)
                if jsdoc_matches:
                    jsdoc = jsdoc_matches[0]
                    
                    # Clean up JSDoc comment
                    jsdoc = re.sub(r'\n\s*\*\s*', '\n', jsdoc)
                    metadata['description'] = jsdoc.strip()
                    
                    # Extract parameters
                    param_matches = re.findall(r'@param\s+{([^}]+)}\s+(\w+)\s+([^\n]+)', jsdoc)
                    if param_matches:
                        metadata['parameters'] = {name: {'type': type, 'description': desc.strip()} 
                                                for type, name, desc in param_matches}
                    
                    # Extract return value
                    return_matches = re.findall(r'@returns?\s+{([^}]+)}\s+([^\n]+)', jsdoc)
                    if return_matches:
                        metadata['returns'] = {'type': return_matches[0][0], 'description': return_matches[0][1].strip()}
                    
                    # Extract other tags
                    for tag in ['author', 'version', 'since', 'deprecated', 'example']:
                        tag_matches = re.findall(fr'@{tag}\s+([^\n]+)', jsdoc)
                        if tag_matches:
                            metadata[tag] = tag_matches[0].strip()
            
            elif file_extension in ['cpp', 'h', 'hpp']:
                # C++ files
                # Extract Doxygen comments
                doxygen_matches = re.findall(r'/\*\*\s+(.*?)\s+\*/', content, re.DOTALL)
                if doxygen_matches:
                    doxygen = doxygen_matches[0]
                    
                    # Clean up Doxygen comment
                    doxygen = re.sub(r'\n\s*\*\s*', '\n', doxygen)
                    metadata['description'] = doxygen.strip()
                    
                    # Extract parameters
                    param_matches = re.findall(r'@param\s+(\w+)\s+([^\n]+)', doxygen)
                    if param_matches:
                        metadata['parameters'] = {name: desc.strip() for name, desc in param_matches}
                    
                    # Extract return value
                    return_matches = re.findall(r'@return\s+([^\n]+)', doxygen)
                    if return_matches:
                        metadata['returns'] = return_matches[0].strip()
                    
                    # Extract other tags
                    for tag in ['author', 'version', 'date', 'brief', 'details']:
                        tag_matches = re.findall(fr'@{tag}\s+([^\n]+)', doxygen)
                        if tag_matches:
                            metadata[tag] = tag_matches[0].strip()
            
            # Extract common metadata
            # Try to extract class/function name
            if file_extension == 'py':
                class_match = re.search(r'class\s+(\w+)', content)
                if class_match:
                    metadata['class'] = class_match.group(1)
                
                func_match = re.search(r'def\s+(\w+)', content)
                if func_match:
                    metadata['function'] = func_match.group(1)
            
            elif file_extension in ['js', 'ts']:
                class_match = re.search(r'class\s+(\w+)', content)
                if class_match:
                    metadata['class'] = class_match.group(1)
                
                func_match = re.search(r'function\s+(\w+)', content)
                if func_match:
                    metadata['function'] = func_match.group(1)
            
            elif file_extension in ['cpp', 'h', 'hpp']:
                class_match = re.search(r'class\s+(\w+)', content)
                if class_match:
                    metadata['class'] = class_match.group(1)
                
                func_match = re.search(r'(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*0)?\s*(?:{\s*)?$', content, re.MULTILINE)
                if func_match:
                    metadata['function'] = func_match.group(1)
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata from code: {e}", exc_info=True)
            return metadata
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a file.
        
        Args:
            file_path: The path to the file.
            
        Returns:
            A dictionary of metadata.
        """
        metadata = {}
        
        try:
            # Get file information
            file_stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1].lstrip('.').lower()
            
            # Add file metadata
            metadata['file_name'] = file_name
            metadata['file_extension'] = file_extension
            metadata['file_size'] = file_stat.st_size
            metadata['created_at'] = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            metadata['modified_at'] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract content-specific metadata
            if file_extension in ['md', 'markdown']:
                content_metadata = self.extract_from_markdown(content)
                metadata.update(content_metadata)
            
            elif file_extension in ['py', 'js', 'ts', 'cpp', 'h', 'hpp']:
                content_metadata = self.extract_from_code(content, file_extension)
                metadata.update(content_metadata)
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata from file: {e}", exc_info=True)
            return metadata
    
    def normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize metadata by mapping fields to standard names.
        
        Args:
            metadata: The metadata to normalize.
            
        Returns:
            Normalized metadata.
        """
        normalized = {}
        
        try:
            # Copy metadata
            normalized.update(metadata)
            
            # Normalize fields
            for standard_field, aliases in self.field_mappings.items():
                # Skip if standard field already exists
                if standard_field in normalized:
                    continue
                
                # Check aliases
                for alias in aliases:
                    if alias in normalized:
                        normalized[standard_field] = normalized[alias]
                        break
            
            # Normalize tags
            if 'tags' in normalized and isinstance(normalized['tags'], str):
                # Split comma-separated tags
                normalized['tags'] = [tag.strip() for tag in normalized['tags'].split(',')]
            
            # Normalize date
            if 'date' in normalized and isinstance(normalized['date'], str):
                try:
                    # Try to parse date
                    date_str = normalized['date']
                    # Try different formats
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            normalized['date'] = date_obj.isoformat()
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.warning(f"Error normalizing date: {e}")
            
            return normalized
        
        except Exception as e:
            logger.error(f"Error normalizing metadata: {e}", exc_info=True)
            return metadata
