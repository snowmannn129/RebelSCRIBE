#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Organization System for RebelSCRIBE.

This package provides functionality for organizing and managing content in RebelSCRIBE.
"""

from .content_organization_system import ContentOrganizationSystem
from .metadata_extractor import MetadataExtractor
from .content_hierarchy import ContentHierarchy
from .tag_manager import TagManager
from .search_index import SearchIndex

__all__ = [
    'ContentOrganizationSystem',
    'MetadataExtractor',
    'ContentHierarchy',
    'TagManager',
    'SearchIndex'
]
