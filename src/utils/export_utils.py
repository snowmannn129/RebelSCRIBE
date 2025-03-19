#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export utilities for RebelSCRIBE.

This module provides utility functions for exporting documents to various formats,
handling templates, processing metadata, and managing batch exports.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union, BinaryIO, Callable
import io
import json
import re
import datetime
import zipfile

# Document processing libraries
try:
    import docx
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from .file_utils import ensure_directory, write_text_file, read_text_file

logger = logging.getLogger(__name__)

# Export format constants
FORMAT_DOCX = "docx"
FORMAT_PDF = "pdf"
FORMAT_MARKDOWN = "md"
FORMAT_HTML = "html"
FORMAT_EPUB = "epub"
FORMAT_TXT = "txt"
FORMAT_RTF = "rtf"
FORMAT_ODT = "odt"
FORMAT_LATEX = "tex"
FORMAT_MOBI = "mobi"
FORMAT_AZW3 = "azw3"
FORMAT_FB2 = "fb2"

# Valid export formats
VALID_FORMATS = {
    FORMAT_DOCX, FORMAT_PDF, FORMAT_MARKDOWN, 
    FORMAT_HTML, FORMAT_EPUB, FORMAT_TXT,
    FORMAT_RTF, FORMAT_ODT, FORMAT_LATEX,
    FORMAT_MOBI, FORMAT_AZW3, FORMAT_FB2
}

# Default export settings
DEFAULT_EXPORT_SETTINGS = {
    "page_size": "letter",
    "margin_top": 1.0,
    "margin_bottom": 1.0,
    "margin_left": 1.0,
    "margin_right": 1.0,
    "font_name": "Times New Roman",
    "font_size": 12,
    "line_spacing": 1.5,
    "paragraph_spacing": 12,
    "include_title_page": True,
    "include_toc": True,
    "include_page_numbers": True,
    "include_header": False,
    "include_footer": True,
    "header_text": "",
    "footer_text": "",
    "scene_separator": "* * *",
    "chapter_start_new_page": True,
    "number_chapters": True,
    "chapter_prefix": "Chapter ",
    "include_synopsis": False,
    "include_notes": False,
    "include_metadata": False
}


# Import additional export formats
try:
    from .export_formats import (
        check_additional_export_dependencies,
        get_additional_available_formats,
        export_to_rtf,
        export_to_odt,
        export_to_latex,
        export_to_epub as ebooklib_export_to_epub,
        export_to_mobi,
        export_to_azw3,
        export_to_fb2,
        FORMAT_RTF,
        FORMAT_ODT,
        FORMAT_LATEX,
        FORMAT_MOBI,
        FORMAT_AZW3,
        FORMAT_FB2,
        ADDITIONAL_FORMATS
    )
    ADDITIONAL_FORMATS_AVAILABLE = True
except ImportError:
    ADDITIONAL_FORMATS_AVAILABLE = False


def check_export_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies for export are available.
    
    Returns:
        Dict[str, bool]: A dictionary mapping format names to availability.
    """
    # Basic formats
    dependencies = {
        FORMAT_DOCX: DOCX_AVAILABLE,
        FORMAT_PDF: PDF_AVAILABLE,
        FORMAT_MARKDOWN: MARKDOWN_AVAILABLE,
        FORMAT_HTML: BS4_AVAILABLE,
        FORMAT_EPUB: BS4_AVAILABLE and MARKDOWN_AVAILABLE,
        FORMAT_TXT: True  # Always available
    }
    
    # Additional formats
    if ADDITIONAL_FORMATS_AVAILABLE:
        additional_dependencies = check_additional_export_dependencies()
        dependencies.update(additional_dependencies)
    
    return dependencies


def get_available_formats() -> List[str]:
    """
    Get a list of available export formats based on installed dependencies.
    
    Returns:
        List[str]: A list of available export formats.
    """
    # Get basic formats
    dependencies = check_export_dependencies()
    available_formats = [format for format, available in dependencies.items() if available]
    
    # Get additional formats
    if ADDITIONAL_FORMATS_AVAILABLE:
        additional_formats = get_additional_available_formats()
        # Avoid duplicates
        for format in additional_formats:
            if format not in available_formats:
                available_formats.append(format)
    
    return available_formats


def validate_export_settings(settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate export settings against expected types and values.
    
    Args:
        settings: The export settings to validate.
        
    Returns:
        Tuple[bool, List[str]]: A tuple containing a boolean indicating if the settings are valid,
                               and a list of error messages if any.
    """
    errors = []
    
    # Define expected types and valid values for each setting
    validations = {
        "page_size": {
            "type": str,
            "valid_values": ["letter", "A4", "legal"]
        },
        "margin_top": {
            "type": (int, float),
            "min": 0.1,
            "max": 3.0
        },
        "margin_bottom": {
            "type": (int, float),
            "min": 0.1,
            "max": 3.0
        },
        "margin_left": {
            "type": (int, float),
            "min": 0.1,
            "max": 3.0
        },
        "margin_right": {
            "type": (int, float),
            "min": 0.1,
            "max": 3.0
        },
        "font_name": {
            "type": str
        },
        "font_size": {
            "type": (int, float),
            "min": 6,
            "max": 72
        },
        "line_spacing": {
            "type": (int, float),
            "min": 1.0,
            "max": 3.0
        },
        "paragraph_spacing": {
            "type": (int, float),
            "min": 0,
            "max": 72
        },
        "include_title_page": {
            "type": bool
        },
        "include_toc": {
            "type": bool
        },
        "include_page_numbers": {
            "type": bool
        },
        "include_header": {
            "type": bool
        },
        "include_footer": {
            "type": bool
        },
        "header_text": {
            "type": str
        },
        "footer_text": {
            "type": str
        },
        "scene_separator": {
            "type": str
        },
        "chapter_start_new_page": {
            "type": bool
        },
        "number_chapters": {
            "type": bool
        },
        "chapter_prefix": {
            "type": str
        },
        "include_synopsis": {
            "type": bool
        },
        "include_notes": {
            "type": bool
        },
        "include_metadata": {
            "type": bool
        }
    }
    
    # Check each setting
    for key, value in settings.items():
        if key not in validations:
            errors.append(f"Unknown setting: {key}")
            continue
        
        validation = validations[key]
        
        # Check type
        if not isinstance(value, validation["type"]):
            errors.append(f"Invalid type for {key}: expected {validation['type']}, got {type(value)}")
            continue  # Skip further validation if type is wrong
        
        # Check valid values if specified
        if "valid_values" in validation and value not in validation["valid_values"]:
            errors.append(f"Invalid value for {key}: {value}. Valid values are: {validation['valid_values']}")
        
        # Check min/max if specified for numeric types
        if isinstance(value, (int, float)):
            if "min" in validation and value < validation["min"]:
                errors.append(f"Value for {key} is too small: {value}. Minimum is {validation['min']}")
            
            if "max" in validation and value > validation["max"]:
                errors.append(f"Value for {key} is too large: {value}. Maximum is {validation['max']}")
    
    return len(errors) == 0, errors


def merge_export_settings(user_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge user-provided export settings with default settings.
    
    Args:
        user_settings: User-provided export settings.
        
    Returns:
        Dict[str, Any]: Merged export settings.
    """
    settings = DEFAULT_EXPORT_SETTINGS.copy()
    if user_settings:
        settings.update(user_settings)
    return settings


def convert_markdown_to_html(markdown_text: str) -> str:
    """
    Convert Markdown text to HTML.
    
    Args:
        markdown_text: The Markdown text to convert.
        
    Returns:
        str: The converted HTML text.
    """
    if not MARKDOWN_AVAILABLE:
        logger.warning("Markdown library not available. Returning plain text.")
        return f"<pre>{markdown_text}</pre>"
    
    try:
        html = markdown.markdown(markdown_text)
        return html
    except Exception as e:
        logger.error(f"Error converting Markdown to HTML: {e}", exc_info=True)
        return f"<pre>{markdown_text}</pre>"


def convert_html_to_plain_text(html_text: str) -> str:
    """
    Convert HTML text to plain text.
    
    Args:
        html_text: The HTML text to convert.
        
    Returns:
        str: The converted plain text.
    """
    if not BS4_AVAILABLE:
        logger.warning("BeautifulSoup library not available. Removing HTML tags with regex.")
        # Simple regex to remove HTML tags
        plain_text = re.sub(r'<[^>]+>', '', html_text)
        return plain_text
    
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text()
    except Exception as e:
        logger.error(f"Error converting HTML to plain text: {e}", exc_info=True)
        # Fallback to regex
        plain_text = re.sub(r'<[^>]+>', '', html_text)
        return plain_text


def create_temp_export_directory() -> str:
    """
    Create a temporary directory for export files.
    
    Returns:
        str: The path to the temporary directory.
    """
    temp_dir = tempfile.mkdtemp(prefix="rebelscribe_export_")
    logger.debug(f"Created temporary export directory: {temp_dir}")
    return temp_dir


def cleanup_temp_export_directory(temp_dir: str) -> bool:
    """
    Clean up a temporary export directory.
    
    Args:
        temp_dir: The path to the temporary directory.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        shutil.rmtree(temp_dir)
        logger.debug(f"Cleaned up temporary export directory: {temp_dir}")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up temporary export directory: {e}", exc_info=True)
        return False


def create_epub_container(output_path: str, content_files: List[Dict[str, Any]], 
                         metadata: Dict[str, Any], cover_image: Optional[str] = None) -> bool:
    """
    Create an EPUB file from HTML content files.
    
    Args:
        output_path: The path to save the EPUB file.
        content_files: A list of dictionaries containing content file information.
                      Each dictionary should have 'id', 'title', and 'content' keys.
        metadata: A dictionary containing metadata for the EPUB.
        cover_image: Optional path to a cover image.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not BS4_AVAILABLE:
        logger.error("BeautifulSoup library not available. Cannot create EPUB.")
        return False
    
    try:
        # Create a temporary directory for EPUB files
        temp_dir = create_temp_export_directory()
        
        # Create EPUB directory structure
        os.makedirs(os.path.join(temp_dir, "META-INF"))
        os.makedirs(os.path.join(temp_dir, "OEBPS"))
        
        # Create container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""
        
        with open(os.path.join(temp_dir, "META-INF", "container.xml"), "w", encoding="utf-8") as f:
            f.write(container_xml)
        
        # Create mimetype file
        with open(os.path.join(temp_dir, "mimetype"), "w", encoding="utf-8") as f:
            f.write("application/epub+zip")
        
        # Create content files
        toc_items = []
        manifest_items = []
        spine_items = []
        
        for i, content_file in enumerate(content_files):
            file_id = content_file.get("id", f"item_{i}")
            file_title = content_file.get("title", f"Chapter {i+1}")
            file_content = content_file.get("content", "")
            
            # Create HTML file
            html_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{file_title}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
</head>
<body>
    <h1>{file_title}</h1>
    {file_content}
</body>
</html>"""
            
            file_path = os.path.join("OEBPS", f"{file_id}.xhtml")
            with open(os.path.join(temp_dir, file_path), "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Add to TOC, manifest, and spine
            toc_items.append(f'<navPoint id="navpoint-{i+1}" playOrder="{i+1}">\n'
                            f'    <navLabel>\n'
                            f'        <text>{file_title}</text>\n'
                            f'    </navLabel>\n'
                            f'    <content src="{file_id}.xhtml"/>\n'
                            f'</navPoint>')
            
            manifest_items.append(f'<item id="{file_id}" href="{file_id}.xhtml" '
                                 f'media-type="application/xhtml+xml"/>')
            
            spine_items.append(f'<itemref idref="{file_id}"/>')
        
        # Add cover image if provided
        cover_item = ""
        if cover_image and os.path.exists(cover_image):
            # Copy cover image to EPUB
            cover_ext = os.path.splitext(cover_image)[1].lower()
            cover_mime = "image/jpeg" if cover_ext in [".jpg", ".jpeg"] else "image/png"
            cover_filename = "cover" + cover_ext
            
            shutil.copy(cover_image, os.path.join(temp_dir, "OEBPS", cover_filename))
            
            # Add cover to manifest
            cover_item = f'<item id="cover-image" href="{cover_filename}" media-type="{cover_mime}" properties="cover-image"/>'
            manifest_items.append(cover_item)
            
            # Create cover HTML
            cover_html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Cover</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
</head>
<body>
    <div style="text-align: center; padding: 0; margin: 0;">
        <img src="{cover_filename}" alt="Cover" style="max-width: 100%; max-height: 100%;"/>
    </div>
</body>
</html>"""
            
            with open(os.path.join(temp_dir, "OEBPS", "cover.xhtml"), "w", encoding="utf-8") as f:
                f.write(cover_html)
            
            # Add cover to manifest and spine
            manifest_items.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.insert(0, '<itemref idref="cover"/>')
            
            # Add to TOC
            toc_items.insert(0, '<navPoint id="navpoint-cover" playOrder="0">\n'
                             '    <navLabel>\n'
                             '        <text>Cover</text>\n'
                             '    </navLabel>\n'
                             '    <content src="cover.xhtml"/>\n'
                             '</navPoint>')
        
        # Create NCX file
        ncx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{metadata.get('identifier', 'unknown')}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{metadata.get('title', 'Unknown Title')}</text>
    </docTitle>
    <docAuthor>
        <text>{metadata.get('creator', 'Unknown Author')}</text>
    </docAuthor>
    <navMap>
        {chr(10).join(toc_items)}
    </navMap>
</ncx>"""
        
        with open(os.path.join(temp_dir, "OEBPS", "toc.ncx"), "w", encoding="utf-8") as f:
            f.write(ncx_content)
        
        # Add NCX to manifest
        manifest_items.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        
        # Create OPF file
        opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{metadata.get('title', 'Unknown Title')}</dc:title>
        <dc:creator>{metadata.get('creator', 'Unknown Author')}</dc:creator>
        <dc:identifier id="BookID">urn:uuid:{metadata.get('identifier', 'unknown')}</dc:identifier>
        <dc:language>{metadata.get('language', 'en')}</dc:language>
        <dc:date>{metadata.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))}</dc:date>
        <dc:publisher>{metadata.get('publisher', 'RebelSCRIBE')}</dc:publisher>
        <dc:description>{metadata.get('description', '')}</dc:description>
        <meta property="dcterms:modified">{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
    </metadata>
    <manifest>
        {chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
        {chr(10).join(spine_items)}
    </spine>
</package>"""
        
        with open(os.path.join(temp_dir, "OEBPS", "content.opf"), "w", encoding="utf-8") as f:
            f.write(opf_content)
        
        # Create EPUB file (ZIP with specific order)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
            # mimetype must be first and uncompressed
            epub.write(os.path.join(temp_dir, "mimetype"), "mimetype", compress_type=zipfile.ZIP_STORED)
            
            # Add all other files
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "mimetype":
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    epub.write(file_path, arcname)
        
        # Clean up
        cleanup_temp_export_directory(temp_dir)
        
        logger.info(f"Created EPUB file: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating EPUB file: {e}", exc_info=True)
        # Clean up
        try:
            cleanup_temp_export_directory(temp_dir)
        except:
            pass
        return False


def apply_template(template: str, data: Dict[str, Any]) -> str:
    """
    Apply a template with data.
    
    Args:
        template: The template string with placeholders in the format {{variable}}.
        data: A dictionary of data to fill the template.
        
    Returns:
        str: The filled template.
    """
    result = template
    
    # Replace placeholders
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    return result


def load_template(template_path: str) -> Optional[str]:
    """
    Load a template from a file.
    
    Args:
        template_path: The path to the template file.
        
    Returns:
        Optional[str]: The template string, or None if the file could not be loaded.
    """
    return read_text_file(template_path)


def batch_export(items: List[Any], export_function: Callable, 
                output_dir: str, format: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """
    Batch export multiple items.
    
    Args:
        items: A list of items to export.
        export_function: A function that takes an item, output path, format, and settings,
                        and returns a boolean indicating success.
        output_dir: The directory to export to.
        format: The export format.
        settings: Export settings.
        
    Returns:
        Dict[str, bool]: A dictionary mapping item IDs to export success.
    """
    results = {}
    
    # Ensure output directory exists
    ensure_directory(output_dir)
    
    # Export each item
    for item in items:
        try:
            item_id = getattr(item, "id", str(id(item)))
            item_title = getattr(item, "title", f"Item_{item_id}")
            
            # Create a safe filename
            safe_title = re.sub(r'[^\w\-_.]', '_', item_title)
            output_path = os.path.join(output_dir, f"{safe_title}.{format}")
            
            # Export the item
            success = export_function(item, output_path, format, settings)
            results[item_id] = success
            
            if success:
                logger.info(f"Exported item {item_id} to {output_path}")
            else:
                logger.error(f"Failed to export item {item_id}")
        
        except Exception as e:
            item_id = getattr(item, "id", str(id(item)))
            logger.error(f"Error exporting item {item_id}: {e}", exc_info=True)
            results[item_id] = False
    
    return results


def extract_metadata(content: str) -> Dict[str, str]:
    """
    Extract metadata from content.
    
    This function looks for metadata in the format:
    ---
    key: value
    another_key: another value
    ---
    
    Args:
        content: The content to extract metadata from.
        
    Returns:
        Dict[str, str]: A dictionary of metadata.
    """
    metadata = {}
    
    # Look for metadata block
    match = re.search(r'---\s+(.*?)\s+---', content, re.DOTALL)
    if not match:
        return metadata
    
    # Extract metadata
    metadata_block = match.group(1)
    for line in metadata_block.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Look for key-value pairs
        key_value_match = re.match(r'([^:]+):\s*(.*)', line)
        if key_value_match:
            key = key_value_match.group(1).strip()
            value = key_value_match.group(2).strip()
            metadata[key] = value
    
    return metadata


def remove_metadata(content: str) -> str:
    """
    Remove metadata block from content.
    
    Args:
        content: The content to remove metadata from.
        
    Returns:
        str: The content without metadata.
    """
    # Remove metadata block
    return re.sub(r'---\s+(.*?)\s+---', '', content, flags=re.DOTALL).strip()


def get_page_size(page_size_name: str) -> Tuple[float, float]:
    """
    Get page dimensions for a named page size.
    
    Args:
        page_size_name: The name of the page size (e.g., "letter", "A4").
        
    Returns:
        Tuple[float, float]: The page width and height in points.
    """
    page_sizes = {
        "letter": (8.5 * 72, 11 * 72),  # 8.5 x 11 inches
        "a4": (595, 842),               # 210 x 297 mm
        "legal": (8.5 * 72, 14 * 72),   # 8.5 x 14 inches
        "tabloid": (11 * 72, 17 * 72),  # 11 x 17 inches
        "a3": (842, 1191),              # 297 x 420 mm
        "a5": (420, 595)                # 148 x 210 mm
    }
    
    page_size_name = page_size_name.lower()
    if page_size_name in page_sizes:
        return page_sizes[page_size_name]
    else:
        logger.warning(f"Unknown page size: {page_size_name}. Using letter size.")
        return page_sizes["letter"]
