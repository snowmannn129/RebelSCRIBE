#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional export formats for RebelSCRIBE.

This module provides utility functions for exporting documents to various formats
beyond the basic ones provided in export_utils.py, including:
- RTF (Rich Text Format)
- ODT (OpenDocument Text)
- LaTeX
- MOBI (Mobipocket)
- AZW3 (Kindle Format)
- FB2 (FictionBook)
"""

import os
import logging
import tempfile
import shutil
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, BinaryIO

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import pylatex
    from pylatex import Document as LaTeXDocument
    from pylatex import Section, Subsection, Command
    from pylatex.utils import italic, NoEscape
    LATEX_AVAILABLE = True
except ImportError:
    LATEX_AVAILABLE = False

try:
    from odf.opendocument import OpenDocumentText
    from odf.style import Style, TextProperties, ParagraphProperties, PageLayout
    from odf.style import PageLayoutProperties, MasterPage
    from odf.text import H, P, Span
    ODT_AVAILABLE = True
except ImportError:
    ODT_AVAILABLE = False

try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False

# Export format constants
FORMAT_RTF = "rtf"
FORMAT_ODT = "odt"
FORMAT_LATEX = "tex"
FORMAT_MOBI = "mobi"
FORMAT_AZW3 = "azw3"
FORMAT_FB2 = "fb2"

# Valid export formats
ADDITIONAL_FORMATS = {
    FORMAT_RTF, FORMAT_ODT, FORMAT_LATEX, 
    FORMAT_MOBI, FORMAT_AZW3, FORMAT_FB2
}


def check_additional_export_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies for additional export formats are available.
    
    Returns:
        Dict[str, bool]: A dictionary mapping format names to availability.
    """
    # Check for Calibre CLI tools for MOBI/AZW3 conversion
    calibre_available = False
    try:
        # Try to run ebook-convert with --version to check if it's installed
        result = subprocess.run(
            ["ebook-convert", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        calibre_available = result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        calibre_available = False
    
    return {
        FORMAT_RTF: True,  # Basic RTF can be implemented without external dependencies
        FORMAT_ODT: ODT_AVAILABLE,
        FORMAT_LATEX: LATEX_AVAILABLE,
        FORMAT_MOBI: calibre_available and EBOOKLIB_AVAILABLE,
        FORMAT_AZW3: calibre_available and EBOOKLIB_AVAILABLE,
        FORMAT_FB2: EBOOKLIB_AVAILABLE
    }


def get_additional_available_formats() -> List[str]:
    """
    Get a list of available additional export formats based on installed dependencies.
    
    Returns:
        List[str]: A list of available export formats.
    """
    dependencies = check_additional_export_dependencies()
    return [format for format, available in dependencies.items() if available]


def export_to_rtf(content: str, title: str, author: Optional[str] = None, 
                 output_path: str = None, settings: Optional[Dict[str, Any]] = None) -> Union[str, bool]:
    """
    Export content to RTF format.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the RTF file. If None, returns the RTF content as a string.
        settings: Export settings.
        
    Returns:
        Union[str, bool]: The RTF content as a string if output_path is None, 
                         otherwise True if successful, False otherwise.
    """
    try:
        # Default settings
        default_settings = {
            "font_name": "Times New Roman",
            "font_size": 12,
            "line_spacing": 1.5,
            "paragraph_spacing": 12,
            "margin_top": 1.0,
            "margin_bottom": 1.0,
            "margin_left": 1.0,
            "margin_right": 1.0
        }
        
        # Merge with provided settings
        if settings:
            default_settings.update(settings)
        
        # Convert font size to half-points (RTF uses half-points)
        font_size_half_points = int(default_settings["font_size"] * 2)
        
        # Start RTF document
        rtf = r"{\rtf1\ansi\ansicpg1252\deff0\deflang1033"
        
        # Font table
        rtf += r"{\fonttbl{\f0\froman\fcharset0 " + default_settings["font_name"] + ";}}"
        
        # Document info
        rtf += r"{\info"
        rtf += r"{\title " + title + "}"
        if author:
            rtf += r"{\author " + author + "}"
        rtf += r"{\createtime " + str(int(datetime.datetime.now().timestamp())) + "}"
        rtf += r"}"
        
        # Document formatting
        rtf += r"\viewkind4\uc1\pard\sa" + str(int(default_settings["paragraph_spacing"] * 20))
        rtf += r"\sl" + str(int(default_settings["line_spacing"] * 240))
        rtf += r"\slmult1"
        rtf += r"\margt" + str(int(default_settings["margin_top"] * 1440))
        rtf += r"\margb" + str(int(default_settings["margin_bottom"] * 1440))
        rtf += r"\margl" + str(int(default_settings["margin_left"] * 1440))
        rtf += r"\margr" + str(int(default_settings["margin_right"] * 1440))
        rtf += r"\f0\fs" + str(font_size_half_points)
        
        # Title
        rtf += r"\pard\qc\b\fs" + str(font_size_half_points + 12) + " " + title + r"\par"
        
        # Author
        if author:
            rtf += r"\pard\qc\b0\fs" + str(font_size_half_points) + " by " + author + r"\par"
        
        # Add a blank line after title/author
        rtf += r"\pard\par"
        
        # Content
        rtf += r"\pard\qj "  # Justified text
        
        # Process paragraphs
        paragraphs = content.split("\n\n")
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                # Escape special characters: \, {, }
                paragraph = paragraph.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                
                # Replace line breaks with RTF line breaks
                paragraph = paragraph.replace("\n", "\\line ")
                
                rtf += paragraph
                
                # Add paragraph mark except for the last paragraph
                if i < len(paragraphs) - 1:
                    rtf += r"\par"
        
        # Close RTF document
        rtf += r"}"
        
        # Save to file or return as string
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rtf)
            logger.info(f"Exported content to RTF: {output_path}")
            return True
        else:
            return rtf
    
    except Exception as e:
        logger.error(f"Error exporting to RTF: {e}", exc_info=True)
        if output_path:
            return False
        else:
            return ""


def export_to_odt(content: str, title: str, author: Optional[str] = None,
                 output_path: str = None, settings: Optional[Dict[str, Any]] = None) -> bool:
    """
    Export content to ODT format.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the ODT file.
        settings: Export settings.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not ODT_AVAILABLE:
        logger.error("ODT export requires the odfpy library.")
        return False
    
    try:
        # Default settings
        default_settings = {
            "font_name": "Times New Roman",
            "font_size": 12,
            "line_spacing": 1.5,
            "paragraph_spacing": 12,
            "margin_top": 1.0,
            "margin_bottom": 1.0,
            "margin_left": 1.0,
            "margin_right": 1.0
        }
        
        # Merge with provided settings
        if settings:
            default_settings.update(settings)
        
        # Create ODT document
        doc = OpenDocumentText()
        
        # Set document metadata
        doc.setMeta("title", title)
        if author:
            doc.setMeta("creator", author)
        doc.setMeta("creation-date", datetime.datetime.now().isoformat())
        
        # Create styles
        # Page layout style
        page_layout = PageLayout(name="PageLayout")
        page_layout_props = PageLayoutProperties(
            margintop=f"{default_settings['margin_top']}in",
            marginbottom=f"{default_settings['margin_bottom']}in",
            marginleft=f"{default_settings['margin_left']}in",
            marginright=f"{default_settings['margin_right']}in"
        )
        page_layout.addElement(page_layout_props)
        doc.automaticstyles.addElement(page_layout)
        
        # Master page
        master_page = MasterPage(name="Standard", pagelayoutname=page_layout)
        doc.masterstyles.addElement(master_page)
        
        # Title style
        title_style = Style(name="Title", family="paragraph")
        title_style.addElement(ParagraphProperties(textalign="center"))
        title_style.addElement(TextProperties(
            fontfamily=default_settings["font_name"],
            fontsize=f"{default_settings['font_size'] + 6}pt",
            fontweight="bold"
        ))
        doc.styles.addElement(title_style)
        
        # Author style
        author_style = Style(name="Author", family="paragraph")
        author_style.addElement(ParagraphProperties(textalign="center"))
        author_style.addElement(TextProperties(
            fontfamily=default_settings["font_name"],
            fontsize=f"{default_settings['font_size']}pt"
        ))
        doc.styles.addElement(author_style)
        
        # Normal text style
        text_style = Style(name="Text", family="paragraph")
        text_style.addElement(ParagraphProperties(
            textalign="justify",
            lineheight=f"{default_settings['line_spacing'] * 100}%",
            margintop=f"{default_settings['paragraph_spacing'] / 2}pt",
            marginbottom=f"{default_settings['paragraph_spacing'] / 2}pt"
        ))
        text_style.addElement(TextProperties(
            fontfamily=default_settings["font_name"],
            fontsize=f"{default_settings['font_size']}pt"
        ))
        doc.styles.addElement(text_style)
        
        # Add title
        title_para = H(outlinelevel=1, stylename="Title")
        title_para.addText(title)
        doc.text.addElement(title_para)
        
        # Add author
        if author:
            author_para = P(stylename="Author")
            author_para.addText(f"by {author}")
            doc.text.addElement(author_para)
        
        # Add a blank line
        doc.text.addElement(P())
        
        # Add content
        paragraphs = content.split("\n\n")
        for paragraph in paragraphs:
            if paragraph.strip():
                p = P(stylename="Text")
                p.addText(paragraph.strip())
                doc.text.addElement(p)
        
        # Save document
        doc.save(output_path)
        logger.info(f"Exported content to ODT: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting to ODT: {e}", exc_info=True)
        return False


def export_to_latex(content: str, title: str, author: Optional[str] = None,
                   output_path: str = None, settings: Optional[Dict[str, Any]] = None) -> Union[str, bool]:
    """
    Export content to LaTeX format.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the LaTeX file. If None, returns the LaTeX content as a string.
        settings: Export settings.
        
    Returns:
        Union[str, bool]: The LaTeX content as a string if output_path is None, 
                         otherwise True if successful, False otherwise.
    """
    if not LATEX_AVAILABLE and output_path is not None:
        logger.error("LaTeX export requires the pylatex library for file output.")
        return False
    
    try:
        # Default settings
        default_settings = {
            "document_class": "book",
            "font_size": 12,
            "paper_size": "letterpaper",
            "margin_top": 1.0,
            "margin_bottom": 1.0,
            "margin_left": 1.0,
            "margin_right": 1.0,
            "line_spacing": 1.5,
            "include_toc": True
        }
        
        # Merge with provided settings
        if settings:
            default_settings.update(settings)
        
        if LATEX_AVAILABLE and output_path is not None:
            # Use PyLaTeX to create the document
            geometry_options = {
                "tmargin": f"{default_settings['margin_top']}in",
                "bmargin": f"{default_settings['margin_bottom']}in",
                "lmargin": f"{default_settings['margin_left']}in",
                "rmargin": f"{default_settings['margin_right']}in"
            }
            
            doc = LaTeXDocument(
                documentclass=default_settings["document_class"],
                fontsize=f"{default_settings['font_size']}pt",
                geometry_options=geometry_options,
                document_options=default_settings["paper_size"]
            )
            
            # Add packages
            doc.packages.append(pylatex.Package("setspace"))
            doc.packages.append(pylatex.Package("parskip"))
            doc.packages.append(pylatex.Package("titlesec"))
            
            # Set line spacing
            doc.append(Command("setstretch", default_settings["line_spacing"]))
            
            # Add title and author
            doc.preamble.append(Command("title", title))
            if author:
                doc.preamble.append(Command("author", author))
            doc.preamble.append(Command("date", datetime.datetime.now().strftime("%B %d, %Y")))
            
            # Begin document
            doc.append(NoEscape(r"\maketitle"))
            
            # Add table of contents if requested
            if default_settings["include_toc"]:
                doc.append(NoEscape(r"\tableofcontents"))
                doc.append(NoEscape(r"\newpage"))
            
            # Add content
            paragraphs = content.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    doc.append(paragraph.strip())
                    doc.append(NoEscape(r"\par"))
            
            # Generate LaTeX file
            doc.generate_tex(output_path.replace(".tex", ""))
            logger.info(f"Exported content to LaTeX: {output_path}")
            return True
        
        else:
            # Manual LaTeX generation as a string
            latex = f"""\\documentclass[{default_settings['font_size']}pt,{default_settings['paper_size']}]{{{default_settings['document_class']}}}

\\usepackage[
    top={default_settings['margin_top']}in,
    bottom={default_settings['margin_bottom']}in,
    left={default_settings['margin_left']}in,
    right={default_settings['margin_right']}in
]{{geometry}}
\\usepackage{{setspace}}
\\usepackage{{parskip}}
\\usepackage{{titlesec}}

\\setstretch{{{default_settings['line_spacing']}}}

\\title{{{title}}}
"""
            
            if author:
                latex += f"\\author{{{author}}}\n"
            
            latex += f"\\date{{{datetime.datetime.now().strftime('%B %d, %Y')}}}\n\n"
            latex += "\\begin{document}\n\n"
            latex += "\\maketitle\n\n"
            
            # Add table of contents if requested
            if default_settings["include_toc"]:
                latex += "\\tableofcontents\n\n"
                latex += "\\newpage\n\n"
            
            # Add content
            paragraphs = content.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    # Escape special LaTeX characters: \, {, }, &, %, $, #, _, ^, ~
                    escaped = paragraph.strip()
                    escaped = escaped.replace("\\", "\\textbackslash{}")
                    escaped = escaped.replace("{", "\\{").replace("}", "\\}")
                    escaped = escaped.replace("&", "\\&").replace("%", "\\%")
                    escaped = escaped.replace("$", "\\$").replace("#", "\\#")
                    escaped = escaped.replace("_", "\\_").replace("^", "\\^")
                    escaped = escaped.replace("~", "\\~")
                    
                    latex += f"{escaped}\n\n"
            
            latex += "\\end{document}"
            
            # Save to file or return as string
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(latex)
                logger.info(f"Exported content to LaTeX: {output_path}")
                return True
            else:
                return latex
    
    except Exception as e:
        logger.error(f"Error exporting to LaTeX: {e}", exc_info=True)
        if output_path:
            return False
        else:
            return ""


def export_to_epub(content: str, title: str, author: Optional[str] = None, 
                  output_path: str = None, settings: Optional[Dict[str, Any]] = None,
                  cover_image: Optional[str] = None) -> bool:
    """
    Export content to EPUB format using ebooklib.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the EPUB file.
        settings: Export settings.
        cover_image: Optional path to a cover image.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not EBOOKLIB_AVAILABLE:
        logger.error("EPUB export requires the ebooklib library.")
        return False
    
    try:
        # Create a new EPUB book
        book = epub.EpubBook()
        
        # Set metadata
        book.set_title(title)
        if author:
            book.add_author(author)
        
        # Set language
        book.set_language('en')
        
        # Add cover image if provided
        if cover_image and os.path.exists(cover_image):
            book.set_cover("cover.jpg", open(cover_image, 'rb').read())
        
        # Create chapters
        chapters = []
        
        # If content is very long, split it into multiple chapters
        paragraphs = content.split("\n\n")
        chapter_size = 50  # paragraphs per chapter
        
        if len(paragraphs) > chapter_size:
            # Split into multiple chapters
            for i in range(0, len(paragraphs), chapter_size):
                chapter_num = i // chapter_size + 1
                chapter_title = f"Chapter {chapter_num}"
                chapter_content = "\n\n".join(paragraphs[i:i+chapter_size])
                
                # Create chapter
                chapter = epub.EpubHtml(
                    title=chapter_title,
                    file_name=f'chapter_{chapter_num}.xhtml',
                    lang='en'
                )
                
                # Add content to chapter
                chapter.content = f"<h1>{chapter_title}</h1>\n"
                for para in chapter_content.split("\n\n"):
                    if para.strip():
                        chapter.content += f"<p>{para.strip()}</p>\n"
                
                # Add chapter to book
                book.add_item(chapter)
                chapters.append(chapter)
        else:
            # Single chapter
            chapter = epub.EpubHtml(
                title=title,
                file_name='chapter_1.xhtml',
                lang='en'
            )
            
            # Add content to chapter
            chapter.content = f"<h1>{title}</h1>\n"
            for para in paragraphs:
                if para.strip():
                    chapter.content += f"<p>{para.strip()}</p>\n"
            
            # Add chapter to book
            book.add_item(chapter)
            chapters.append(chapter)
        
        # Define CSS style
        style = """
        @namespace epub "http://www.idpf.org/2007/ops";
        body {
            font-family: Times New Roman, serif;
            line-height: 1.5;
            text-align: justify;
            margin: 1em;
        }
        h1 {
            text-align: center;
            margin: 1em 0;
        }
        p {
            margin: 0.5em 0;
            text-indent: 1.5em;
        }
        """
        
        # Add CSS file
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        # Add navigation files
        book.toc = chapters
        book.spine = ['nav'] + chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Write EPUB file
        epub.write_epub(output_path, book, {})
        logger.info(f"Exported content to EPUB: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting to EPUB: {e}", exc_info=True)
        return False


def convert_epub_to_mobi(epub_path: str, mobi_path: str) -> bool:
    """
    Convert EPUB to MOBI format using Calibre's ebook-convert tool.
    
    Args:
        epub_path: The path to the EPUB file.
        mobi_path: The path to save the MOBI file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Check if ebook-convert is available
        try:
            subprocess.run(
                ["ebook-convert", "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            logger.error("Calibre's ebook-convert tool is not available.")
            return False
        
        # Convert EPUB to MOBI
        result = subprocess.run(
            ["ebook-convert", epub_path, mobi_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"Error converting EPUB to MOBI: {result.stderr}")
            return False
        
        logger.info(f"Converted EPUB to MOBI: {mobi_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error converting EPUB to MOBI: {e}", exc_info=True)
        return False


def convert_epub_to_azw3(epub_path: str, azw3_path: str) -> bool:
    """
    Convert EPUB to AZW3 format using Calibre's ebook-convert tool.
    
    Args:
        epub_path: The path to the EPUB file.
        azw3_path: The path to save the AZW3 file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Check if ebook-convert is available
        try:
            subprocess.run(
                ["ebook-convert", "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            logger.error("Calibre's ebook-convert tool is not available.")
            return False
        
        # Convert EPUB to AZW3
        result = subprocess.run(
            ["ebook-convert", epub_path, azw3_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"Error converting EPUB to AZW3: {result.stderr}")
            return False
        
        logger.info(f"Converted EPUB to AZW3: {azw3_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error converting EPUB to AZW3: {e}", exc_info=True)
        return False


def export_to_fb2(content: str, title: str, author: Optional[str] = None,
                 output_path: str = None, settings: Optional[Dict[str, Any]] = None) -> bool:
    """
    Export content to FB2 (FictionBook) format.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the FB2 file.
        settings: Export settings.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create FB2 XML content
        fb2_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:xlink="http://www.w3.org/1999/xlink">
  <description>
    <title-info>
      <genre>prose</genre>
      <author>
        <first-name>{author.split()[0] if author and ' ' in author else ''}</first-name>
        <last-name>{author.split()[-1] if author and ' ' in author else author or 'Unknown'}</last-name>
      </author>
      <book-title>{title}</book-title>
      <annotation>
        <p>Created with RebelSCRIBE</p>
      </annotation>
      <date>{datetime.datetime.now().strftime('%Y-%m-%d')}</date>
      <lang>en</lang>
    </title-info>
    <document-info>
      <author>
        <first-name>{author.split()[0] if author and ' ' in author else ''}</first-name>
        <last-name>{author.split()[-1] if author and ' ' in author else author or 'Unknown'}</last-name>
      </author>
      <program-used>RebelSCRIBE</program-used>
      <date>{datetime.datetime.now().strftime('%Y-%m-%d')}</date>
      <id>{hash(title + (author or '') + str(datetime.datetime.now()))}</id>
      <version>1.0</version>
    </document-info>
  </description>
  <body>
    <title>
      <p>{title}</p>
    </title>
"""
        
        # Add content
        paragraphs = content.split("\n\n")
        for paragraph in paragraphs:
            if paragraph.strip():
                # Escape XML special characters
                escaped = paragraph.strip()
                escaped = escaped.replace("&", "&amp;")
                escaped = escaped.replace("<", "&lt;")
                escaped = escaped.replace(">", "&gt;")
                escaped = escaped.replace("\"", "&quot;")
                escaped = escaped.replace("'", "&apos;")
                
                fb2_content += f"    <p>{escaped}</p>\n"
        
        # Close FB2 document
        fb2_content += "  </body>\n</FictionBook>"
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(fb2_content)
        
        logger.info(f"Exported content to FB2: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting to FB2: {e}", exc_info=True)
        return False


def export_to_mobi(content: str, title: str, author: Optional[str] = None,
                  output_path: str = None, settings: Optional[Dict[str, Any]] = None,
                  cover_image: Optional[str] = None) -> bool:
    """
    Export content to MOBI format by first creating an EPUB and then converting it.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the MOBI file.
        settings: Export settings.
        cover_image: Optional path to a cover image.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not EBOOKLIB_AVAILABLE:
        logger.error("MOBI export requires the ebooklib library.")
        return False
    
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="rebelscribe_export_")
        
        # Create temporary EPUB file
        epub_path = os.path.join(temp_dir, "temp.epub")
        
        # Export to EPUB first
        if not export_to_epub(content, title, author, epub_path, settings, cover_image):
            logger.error("Failed to create temporary EPUB file for MOBI conversion.")
            shutil.rmtree(temp_dir)
            return False
        
        # Convert EPUB to MOBI
        if not convert_epub_to_mobi(epub_path, output_path):
            logger.error("Failed to convert EPUB to MOBI.")
            shutil.rmtree(temp_dir)
            return False
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        logger.info(f"Exported content to MOBI: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting to MOBI: {e}", exc_info=True)
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        return False


def export_to_azw3(content: str, title: str, author: Optional[str] = None,
                  output_path: str = None, settings: Optional[Dict[str, Any]] = None,
                  cover_image: Optional[str] = None) -> bool:
    """
    Export content to AZW3 format by first creating an EPUB and then converting it.
    
    Args:
        content: The content to export.
        title: The document title.
        author: The document author.
        output_path: The path to save the AZW3 file.
        settings: Export settings.
        cover_image: Optional path to a cover image.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not EBOOKLIB_AVAILABLE:
        logger.error("AZW3 export requires the ebooklib library.")
        return False
    
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="rebelscribe_export_")
        
        # Create temporary EPUB file
        epub_path = os.path.join(temp_dir, "temp.epub")
        
        # Export to EPUB first
        if not export_to_epub(content, title, author, epub_path, settings, cover_image):
            logger.error("Failed to create temporary EPUB file for AZW3 conversion.")
            shutil.rmtree(temp_dir)
            return False
        
        # Convert EPUB to AZW3
        if not convert_epub_to_azw3(epub_path, output_path):
            logger.error("Failed to convert EPUB to AZW3.")
            shutil.rmtree(temp_dir)
            return False
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        logger.info(f"Exported content to AZW3: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting to AZW3: {e}", exc_info=True)
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        return False
