#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note Extensions for RebelSCRIBE.

This module adds extension methods to the Note class.
"""

import logging
from typing import Dict, Any

from src.backend.models.note import Note
from src.backend.models.document import Document

logger = logging.getLogger(__name__)

# Add from_document and to_document methods to Note class
def from_document(cls, document: Document) -> 'Note':
    """
    Create a Note instance from a Document.
    
    Args:
        document: The document to convert.
        
    Returns:
        A new Note instance.
    """
    if document.type != Document.TYPE_NOTE:
        logger.warning(f"Document type '{document.type}' is not a note document")
    
    # Extract note data from document content and metadata
    note_data = {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "document_id": document.id
    }
    
    # Add additional fields from metadata
    for field in ["category", "priority", "status", "color", "tags"]:
        if field in document.metadata:
            note_data[field] = document.metadata.get(field)
    
    # Create note instance
    return cls(**note_data)

def to_document(self, document: Document) -> None:
    """
    Update a Document with Note data.
    
    Args:
        document: The document to update.
    """
    if document.type != Document.TYPE_NOTE:
        document.type = Document.TYPE_NOTE
        logger.warning(f"Changed document type to '{Document.TYPE_NOTE}'")
    
    # Update document title with note title
    document.title = self.title
    
    # Update document content with note content
    document.set_content(self.content)
    
    # Store note data in document metadata
    for field in ["category", "priority", "status", "color", "tags"]:
        value = getattr(self, field, None)
        if value is not None:
            document.set_metadata(field, value)
    
    logger.debug(f"Updated document '{document.id}' with note data")

# Add methods to Note class
Note.from_document = classmethod(from_document)
Note.to_document = to_document
