#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Character Extensions for RebelSCRIBE.

This module adds extension methods to the Character class.
"""

import logging
from typing import Dict, Any

from src.backend.models.character import Character
from src.backend.models.document import Document

logger = logging.getLogger(__name__)

# Add from_document and to_document methods to Character class
def from_document(cls, document: Document) -> 'Character':
    """
    Create a Character instance from a Document.
    
    Args:
        document: The document to convert.
        
    Returns:
        A new Character instance.
    """
    if document.type != Document.TYPE_CHARACTER:
        logger.warning(f"Document type '{document.type}' is not a character document")
    
    # Extract character data from document content and metadata
    character_data = {
        "id": document.id,
        "name": document.title,
        "document_id": document.id
    }
    
    # Add additional fields from metadata
    for field in ["role", "age", "gender", "occupation", "physical_description", 
                  "personality", "background", "goals", "motivations", "conflicts",
                  "relationships", "notes", "arc", "color", "tags", "image_path"]:
        if field in document.metadata:
            character_data[field] = document.metadata.get(field)
    
    # Create character instance
    return cls(**character_data)

def to_document(self, document: Document) -> None:
    """
    Update a Document with Character data.
    
    Args:
        document: The document to update.
    """
    if document.type != Document.TYPE_CHARACTER:
        document.type = Document.TYPE_CHARACTER
        logger.warning(f"Changed document type to '{Document.TYPE_CHARACTER}'")
    
    # Update document title with character name
    document.title = self.name
    
    # Store character data in document metadata
    for field in ["role", "age", "gender", "occupation", "physical_description", 
                  "personality", "background", "goals", "motivations", "conflicts",
                  "relationships", "notes", "arc", "color", "tags", "image_path"]:
        value = getattr(self, field, None)
        if value is not None:
            document.set_metadata(field, value)
    
    logger.debug(f"Updated document '{document.id}' with character data")

# Add methods to Character class
Character.from_document = classmethod(from_document)
Character.to_document = to_document
