#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the Content Organization System.

This script demonstrates the functionality of the Content Organization System
by creating test documents, processing them, and performing various operations.
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add src directory to path to allow imports
src_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(src_dir))

from src.backend.models.document import Document
from src.backend.organization.content_organization_system import ContentOrganizationSystem
from src.utils.logging_utils import setup_logging, get_logger

# Set up logging
setup_logging(
    log_file="test_content_organization.log",
    console_output=True,
    file_output=True
)

logger = get_logger(__name__)

def create_test_document(title: str, content: str, doc_type: str = "document", parent_id: str = None) -> Document:
    """
    Create a test document.
    
    Args:
        title: The document title.
        content: The document content.
        doc_type: The document type.
        parent_id: The parent document ID.
        
    Returns:
        The created document.
    """
    document = Document(
        id=str(uuid.uuid4()),
        title=title,
        content=content,
        type=doc_type,
        parent_id=parent_id,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    return document

def main():
    """Main function to test the Content Organization System."""
    logger.info("Starting Content Organization System test")
    
    # Create test directory
    test_dir = os.path.join(src_dir, "test_output")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create Content Organization System
    cos = ContentOrganizationSystem(test_dir)
    
    # Create test documents
    documents = []
    
    # Create root document
    root_doc = create_test_document(
        title="Project Documentation",
        content="""# Project Documentation
        
This is the root document for the project documentation.

## Overview

This project is a comprehensive documentation system that provides tools for creating,
managing, and publishing documentation.

## Features

- Markdown support
- Code documentation extraction
- Hierarchical organization
- Tag-based organization
- Full-text search

## Tags

#documentation #project #overview
""",
        doc_type="folder"
    )
    documents.append(root_doc)
    
    # Create child documents
    child1 = create_test_document(
        title="Installation Guide",
        content="""# Installation Guide
        
This guide provides instructions for installing the software.

## Prerequisites

- Python 3.8 or higher
- Git
- Node.js 14 or higher

## Installation Steps

1. Clone the repository
2. Install dependencies
3. Configure the application
4. Run the application

## Tags

#installation #guide #setup
""",
        doc_type="document",
        parent_id=root_doc.id
    )
    documents.append(child1)
    
    child2 = create_test_document(
        title="API Reference",
        content="""# API Reference
        
This document provides a reference for the API.

## Endpoints

### GET /api/documents

Retrieves a list of documents.

### POST /api/documents

Creates a new document.

### GET /api/documents/{id}

Retrieves a document by ID.

## Tags

#api #reference #documentation
""",
        doc_type="document",
        parent_id=root_doc.id
    )
    documents.append(child2)
    
    child3 = create_test_document(
        title="User Guide",
        content="""# User Guide
        
This guide provides instructions for using the software.

## Getting Started

1. Log in to the application
2. Create a new project
3. Add documents to the project
4. Organize documents

## Features

- Document creation
- Document organization
- Document search
- Document export

## Tags

#user #guide #documentation
""",
        doc_type="document",
        parent_id=root_doc.id
    )
    documents.append(child3)
    
    # Process documents
    logger.info(f"Processing {len(documents)} documents")
    success_count = cos.process_documents(documents)
    logger.info(f"Successfully processed {success_count} documents")
    
    # Save data
    logger.info("Saving data")
    cos.save_data()
    
    # Test search
    logger.info("Testing search")
    search_results = cos.search("API", max_results=5)
    logger.info(f"Found {len(search_results)} results for 'API'")
    for result in search_results:
        logger.info(f"- {result.title} (Score: {result.score:.2f})")
        logger.info(f"  Snippet: {result.snippet}")
    
    # Test tag-based search
    logger.info("Testing tag-based search")
    tag_results = cos.search("documentation", tag_ids=[tag.id for tag in cos.tag_manager.search_tags("api")])
    logger.info(f"Found {len(tag_results)} results for 'documentation' with tag 'api'")
    for result in tag_results:
        logger.info(f"- {result.title} (Score: {result.score:.2f})")
    
    # Test similar documents
    logger.info("Testing similar documents")
    similar_docs = cos.get_similar_documents(child1.id, max_results=2)
    logger.info(f"Found {len(similar_docs)} documents similar to '{child1.title}'")
    for doc in similar_docs:
        logger.info(f"- {doc['title']} (Similarity: {doc['similarity']:.2f})")
    
    # Test hierarchy
    logger.info("Testing hierarchy")
    root_nodes = cos.get_hierarchy_root_nodes()
    logger.info(f"Found {len(root_nodes)} root nodes")
    for node in root_nodes:
        logger.info(f"- {node['name']} ({node['type']})")
        for child in node.get('children', []):
            logger.info(f"  - {child['name']} ({child['type']})")
    
    # Test tags
    logger.info("Testing tags")
    all_tags = cos.get_all_tags()
    logger.info(f"Found {len(all_tags)} tags")
    for tag in all_tags:
        logger.info(f"- {tag['name']}")
        doc_count = len(cos.tag_manager.get_documents_with_tag(tag['id']))
        logger.info(f"  - Used in {doc_count} documents")
    
    # Test statistics
    logger.info("Testing statistics")
    stats = cos.get_statistics()
    logger.info(f"Document count: {stats.get('document_count', 0)}")
    logger.info(f"Term count: {stats.get('term_count', 0)}")
    logger.info(f"Tag count: {stats.get('tag_count', 0)}")
    logger.info(f"Average document length: {stats.get('average_document_length', 0):.2f}")
    logger.info(f"Average tags per document: {stats.get('average_tags_per_document', 0):.2f}")
    
    # Create backup
    logger.info("Creating backup")
    cos.create_backup()
    
    logger.info("Content Organization System test completed successfully")

if __name__ == "__main__":
    main()
