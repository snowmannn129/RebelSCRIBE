#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Index for RebelSCRIBE.

This module provides functionality for indexing and searching content.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime
import uuid
from collections import defaultdict
import math

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class SearchResult:
    """
    Represents a search result.
    
    This class provides functionality for representing a search result, including
    the document ID, score, and highlighted text.
    """
    
    def __init__(self, document_id: str, score: float, title: str, snippet: str,
               highlights: List[Tuple[int, int]] = None):
        """
        Initialize a SearchResult.
        
        Args:
            document_id: The ID of the document.
            score: The relevance score of the result.
            title: The title of the document.
            snippet: A snippet of text from the document.
            highlights: A list of (start, end) tuples indicating highlighted text.
        """
        self.document_id = document_id
        self.score = score
        self.title = title
        self.snippet = snippet
        self.highlights = highlights or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the search result to a dictionary representation.
        
        Returns:
            A dictionary representation of the search result.
        """
        return {
            'document_id': self.document_id,
            'score': self.score,
            'title': self.title,
            'snippet': self.snippet,
            'highlights': self.highlights
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """
        Create a search result from a dictionary representation.
        
        Args:
            data: The dictionary representation of the search result.
            
        Returns:
            A SearchResult instance.
        """
        return cls(
            document_id=data['document_id'],
            score=data['score'],
            title=data['title'],
            snippet=data['snippet'],
            highlights=data.get('highlights', [])
        )


class SearchIndex:
    """
    Manages indexing and searching of content.
    
    This class provides functionality for indexing and searching content, including
    full-text search, metadata search, and tag-based search.
    """
    
    def __init__(self):
        """Initialize the SearchIndex."""
        # Inverted index: term -> {document_id -> [positions]}
        self.inverted_index: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        
        # Document metadata: document_id -> metadata
        self.document_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Document term counts: document_id -> {term -> count}
        self.document_term_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Document lengths: document_id -> length
        self.document_lengths: Dict[str, int] = {}
        
        # Total number of documents
        self.document_count = 0
        
        # Total number of terms
        self.term_count = 0
        
        # Stop words
        self.stop_words = set([
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
            'at', 'from', 'by', 'for', 'with', 'about', 'against', 'between',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'of', 'in', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
            'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren',
            'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
            'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won',
            'wouldn', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
            'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
            'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who',
            'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
            'does', 'did', 'doing', 'as', 'until', 'while', 'of', 'because',
            'such', 'that', 'until', 'while', 'at', 'by', 'for', 'with', 'about',
            'against', 'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
            'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very'
        ])
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms.
        
        Args:
            text: The text to tokenize.
            
        Returns:
            A list of terms.
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace non-alphanumeric characters with spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into terms
        terms = text.split()
        
        # Remove stop words
        terms = [term for term in terms if term not in self.stop_words]
        
        return terms
    
    def index_document(self, document_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Index a document.
        
        Args:
            document_id: The ID of the document.
            text: The text of the document.
            metadata: Additional metadata for the document.
        """
        # Tokenize text
        terms = self.tokenize(text)
        
        # Update document count if this is a new document
        if document_id not in self.document_metadata:
            self.document_count += 1
        
        # Update document metadata
        self.document_metadata[document_id] = metadata or {}
        
        # Update document length
        self.document_lengths[document_id] = len(terms)
        
        # Clear existing index entries for this document
        for term in self.inverted_index:
            if document_id in self.inverted_index[term]:
                del self.inverted_index[term][document_id]
        
        # Clear existing term counts for this document
        if document_id in self.document_term_counts:
            self.document_term_counts[document_id] = defaultdict(int)
        
        # Index terms
        for position, term in enumerate(terms):
            # Add to inverted index
            self.inverted_index[term][document_id].append(position)
            
            # Update term count
            self.document_term_counts[document_id][term] += 1
            
            # Update total term count
            self.term_count += 1
    
    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the index.
        
        Args:
            document_id: The ID of the document to remove.
            
        Returns:
            True if successful, False otherwise.
        """
        # Check if document exists
        if document_id not in self.document_metadata:
            logger.warning(f"Document not found in index: {document_id}")
            return False
        
        # Remove from inverted index
        for term in list(self.inverted_index.keys()):
            if document_id in self.inverted_index[term]:
                # Update total term count
                self.term_count -= len(self.inverted_index[term][document_id])
                
                # Remove document from term
                del self.inverted_index[term][document_id]
                
                # Remove term if no documents left
                if not self.inverted_index[term]:
                    del self.inverted_index[term]
        
        # Remove from document term counts
        if document_id in self.document_term_counts:
            del self.document_term_counts[document_id]
        
        # Remove from document lengths
        if document_id in self.document_lengths:
            del self.document_lengths[document_id]
        
        # Remove from document metadata
        del self.document_metadata[document_id]
        
        # Update document count
        self.document_count -= 1
        
        return True
    
    def search(self, query: str, max_results: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for documents matching a query.
        
        Args:
            query: The search query.
            max_results: The maximum number of results to return.
            metadata_filter: A dictionary of metadata key-value pairs to filter by.
            
        Returns:
            A list of search results.
        """
        # Tokenize query
        query_terms = self.tokenize(query)
        
        # Calculate document scores
        scores = self._calculate_scores(query_terms)
        
        # Filter by metadata
        if metadata_filter:
            filtered_scores = {}
            for document_id, score in scores.items():
                if document_id in self.document_metadata:
                    metadata = self.document_metadata[document_id]
                    match = True
                    for key, value in metadata_filter.items():
                        if key not in metadata or metadata[key] != value:
                            match = False
                            break
                    
                    if match:
                        filtered_scores[document_id] = score
            
            scores = filtered_scores
        
        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Limit results
        sorted_results = sorted_results[:max_results]
        
        # Create search results
        results = []
        for document_id, score in sorted_results:
            # Get document metadata
            metadata = self.document_metadata.get(document_id, {})
            
            # Get document title
            title = metadata.get('title', document_id)
            
            # Get document snippet
            snippet = self._get_snippet(document_id, query_terms)
            
            # Create search result
            result = SearchResult(
                document_id=document_id,
                score=score,
                title=title,
                snippet=snippet
            )
            
            results.append(result)
        
        return results
    
    def _calculate_scores(self, query_terms: List[str]) -> Dict[str, float]:
        """
        Calculate document scores for a query.
        
        Args:
            query_terms: The terms in the query.
            
        Returns:
            A dictionary mapping document IDs to scores.
        """
        scores = defaultdict(float)
        
        # Calculate TF-IDF scores
        for term in query_terms:
            if term in self.inverted_index:
                # Calculate IDF
                idf = math.log(self.document_count / len(self.inverted_index[term]))
                
                for document_id, positions in self.inverted_index[term].items():
                    # Calculate TF
                    tf = len(positions) / self.document_lengths[document_id]
                    
                    # Calculate TF-IDF
                    tf_idf = tf * idf
                    
                    # Add to score
                    scores[document_id] += tf_idf
        
        return scores
    
    def _get_snippet(self, document_id: str, query_terms: List[str], snippet_length: int = 150) -> str:
        """
        Get a snippet of text from a document.
        
        Args:
            document_id: The ID of the document.
            query_terms: The terms in the query.
            snippet_length: The maximum length of the snippet.
            
        Returns:
            A snippet of text from the document.
        """
        # Get document metadata
        metadata = self.document_metadata.get(document_id, {})
        
        # Get document content
        content = metadata.get('content', '')
        
        # If no content, return empty snippet
        if not content:
            return ''
        
        # Find positions of query terms in content
        positions = []
        for term in query_terms:
            if term in self.inverted_index and document_id in self.inverted_index[term]:
                positions.extend(self.inverted_index[term][document_id])
        
        # If no positions found, return start of content
        if not positions:
            return content[:snippet_length] + '...'
        
        # Find best position for snippet
        best_position = min(positions)
        
        # Calculate snippet start and end
        start = max(0, best_position - snippet_length // 2)
        end = min(len(content), start + snippet_length)
        
        # Adjust start if end is at content end
        if end == len(content):
            start = max(0, end - snippet_length)
        
        # Get snippet
        snippet = content[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = '...' + snippet
        
        if end < len(content):
            snippet = snippet + '...'
        
        return snippet
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The document metadata, or None if not found.
        """
        return self.document_metadata.get(document_id)
    
    def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a document.
        
        Args:
            document_id: The ID of the document.
            metadata: The new metadata for the document.
            
        Returns:
            True if successful, False otherwise.
        """
        # Check if document exists
        if document_id not in self.document_metadata:
            logger.warning(f"Document not found in index: {document_id}")
            return False
        
        # Update metadata
        self.document_metadata[document_id].update(metadata)
        
        return True
    
    def get_term_frequency(self, term: str, document_id: str) -> int:
        """
        Get the frequency of a term in a document.
        
        Args:
            term: The term to get the frequency of.
            document_id: The ID of the document.
            
        Returns:
            The frequency of the term in the document.
        """
        if document_id not in self.document_term_counts:
            return 0
        
        return self.document_term_counts[document_id].get(term, 0)
    
    def get_document_frequency(self, term: str) -> int:
        """
        Get the number of documents containing a term.
        
        Args:
            term: The term to get the document frequency of.
            
        Returns:
            The number of documents containing the term.
        """
        if term not in self.inverted_index:
            return 0
        
        return len(self.inverted_index[term])
    
    def get_similar_documents(self, document_id: str, max_results: int = 10) -> List[Tuple[str, float]]:
        """
        Get documents similar to a document.
        
        Args:
            document_id: The ID of the document.
            max_results: The maximum number of results to return.
            
        Returns:
            A list of (document_id, similarity) tuples.
        """
        # Check if document exists
        if document_id not in self.document_term_counts:
            logger.warning(f"Document not found in index: {document_id}")
            return []
        
        # Get document terms
        document_terms = self.document_term_counts[document_id]
        
        # Calculate similarity scores
        scores = defaultdict(float)
        for other_id in self.document_metadata:
            # Skip the document itself
            if other_id == document_id:
                continue
            
            # Get other document terms
            other_terms = self.document_term_counts[other_id]
            
            # Calculate cosine similarity
            similarity = self._calculate_cosine_similarity(document_terms, other_terms)
            
            # Add to scores
            scores[other_id] = similarity
        
        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Limit results
        sorted_results = sorted_results[:max_results]
        
        return sorted_results
    
    def _calculate_cosine_similarity(self, terms1: Dict[str, int], terms2: Dict[str, int]) -> float:
        """
        Calculate the cosine similarity between two term frequency dictionaries.
        
        Args:
            terms1: The first term frequency dictionary.
            terms2: The second term frequency dictionary.
            
        Returns:
            The cosine similarity between the two dictionaries.
        """
        # Calculate dot product
        dot_product = 0
        for term, count in terms1.items():
            if term in terms2:
                dot_product += count * terms2[term]
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(count * count for count in terms1.values()))
        magnitude2 = math.sqrt(sum(count * count for count in terms2.values()))
        
        # Calculate cosine similarity
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the search index to a dictionary representation.
        
        Returns:
            A dictionary representation of the search index.
        """
        return {
            'inverted_index': {term: dict(docs) for term, docs in self.inverted_index.items()},
            'document_metadata': self.document_metadata,
            'document_term_counts': {doc_id: dict(terms) for doc_id, terms in self.document_term_counts.items()},
            'document_lengths': self.document_lengths,
            'document_count': self.document_count,
            'term_count': self.term_count
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load the search index from a dictionary representation.
        
        Args:
            data: The dictionary representation of the search index.
        """
        # Clear existing data
        self.inverted_index = defaultdict(lambda: defaultdict(list))
        self.document_metadata = {}
        self.document_term_counts = defaultdict(lambda: defaultdict(int))
        self.document_lengths = {}
        self.document_count = 0
        self.term_count = 0
        
        # Load inverted index
        for term, docs in data.get('inverted_index', {}).items():
            for doc_id, positions in docs.items():
                self.inverted_index[term][doc_id] = positions
        
        # Load document metadata
        self.document_metadata = data.get('document_metadata', {})
        
        # Load document term counts
        for doc_id, terms in data.get('document_term_counts', {}).items():
            for term, count in terms.items():
                self.document_term_counts[doc_id][term] = count
        
        # Load document lengths
        self.document_lengths = data.get('document_lengths', {})
        
        # Load document count
        self.document_count = data.get('document_count', 0)
        
        # Load term count
        self.term_count = data.get('term_count', 0)
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Save the search index to a file.
        
        Args:
            file_path: The path to save the search index to.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert to dictionary
            data = self.to_dict()
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving search index to file: {e}", exc_info=True)
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load the search index from a file.
        
        Args:
            file_path: The path to load the search index from.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Search index file not found: {file_path}")
                return False
            
            # Read from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load from dictionary
            self.from_dict(data)
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading search index from file: {e}", exc_info=True)
            return False
