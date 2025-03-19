#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location Extensions for RebelSCRIBE.

This module adds extension methods to the Location class.
"""

import logging
from typing import Dict, Any

from src.backend.models.location import Location
from src.backend.models.document import Document

logger = logging.getLogger(__name__)

# Add from_document and to_document methods to Location class
def from_document(cls, document: Document) -> 'Location':
    """
    Create a Location instance from a Document.
    
    Args:
        document: The document to convert.
        
    Returns:
        A new Location instance.
    """
    if document.type != Document.TYPE_LOCATION:
        logger.warning(f"Document type '{document.type}' is not a location document")
    
    # Extract location data from document content and metadata
    location_data = {
        "id": document.id,
        "name": document.title,
        "document_id": document.id,
        "description": document.content
    }
    
    # Add additional fields from metadata
    for field in ["type", "address", "coordinates", "scenes", "color", "tags", "image_path"]:
        if field in document.metadata:
            location_data[field] = document.metadata.get(field)
    
    # Create location instance
    return cls(**location_data)

def to_document(self, document: Document) -> None:
    """
    Update a Document with Location data.
    
    Args:
        document: The document to update.
    """
    if document.type != Document.TYPE_LOCATION:
        document.type = Document.TYPE_LOCATION
        logger.warning(f"Changed document type to '{Document.TYPE_LOCATION}'")
    
    # Update document title with location name
    document.title = self.name
    
    # Update document content with location description
    if hasattr(self, "description") and self.description:
        document.set_content(self.description)
    
    # Store location data in document metadata
    for field in ["type", "address", "coordinates", "scenes", "color", "tags", "image_path"]:
        value = getattr(self, field, None)
        if value is not None:
            document.set_metadata(field, value)
    
    logger.debug(f"Updated document '{document.id}' with location data")

# Add methods to Location class
Location.from_document = classmethod(from_document)
Location.to_document = to_document
