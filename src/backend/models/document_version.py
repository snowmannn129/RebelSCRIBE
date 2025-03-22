#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Version model for RebelSCRIBE.

This module defines the DocumentVersion class which represents a version of a document in the system.
"""

import datetime
import uuid
from typing import Dict, Any, Optional

import logging
logger = logging.getLogger(__name__)

class DocumentVersion:
    """
    Represents a version of a document in the system.
    
    Attributes:
        id: The unique identifier for the version.
        document_id: The ID of the document this version belongs to.
        content: The content of the document at this version.
        title: The title of the document at this version.
        created_at: The creation date of the version.
        created_by: The user who created the version.
        comment: A comment describing the changes in this version.
        version_number: The version number.
        metadata: Additional metadata for the version.
    """
    
    def __init__(self, document_id: str, content: str, title: str, 
                 created_by: Optional[str] = None, comment: Optional[str] = None,
                 version_number: int = 1, id: Optional[str] = None, 
                 created_at: Optional[datetime.datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new DocumentVersion.
        
        Args:
            document_id: The ID of the document this version belongs to.
            content: The content of the document at this version.
            title: The title of the document at this version.
            created_by: The user who created the version.
            comment: A comment describing the changes in this version.
            version_number: The version number.
            id: The unique identifier for the version. If None, a new UUID will be generated.
            created_at: The creation date of the version. If None, the current time will be used.
            metadata: Additional metadata for the version.
        """
        self.id = id if id else str(uuid.uuid4())
        self.document_id = document_id
        self.content = content
        self.title = title
        self.created_at = created_at if created_at else datetime.datetime.now()
        self.created_by = created_by
        self.comment = comment
        self.version_number = version_number
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        """Return a string representation of the document version."""
        return f"DocumentVersion(title='{self.title}', version={self.version_number}, created_at={self.created_at})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the document version to a dictionary.
        
        Returns:
            A dictionary representation of the document version.
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "comment": self.comment,
            "version_number": self.version_number,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentVersion':
        """
        Create a document version from a dictionary.
        
        Args:
            data: The dictionary containing the document version data.
            
        Returns:
            The created document version.
        """
        created_at = datetime.datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        
        return cls(
            id=data.get("id"),
            document_id=data.get("document_id", ""),
            content=data.get("content", ""),
            title=data.get("title", ""),
            created_at=created_at,
            created_by=data.get("created_by"),
            comment=data.get("comment"),
            version_number=data.get("version_number", 1),
            metadata=data.get("metadata", {})
        )
