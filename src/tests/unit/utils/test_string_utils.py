#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the string_utils module.

This module contains unit tests for the string utility functions:
- Text cleaning and formatting
- Text analysis (word count, character count, etc.)
- String similarity and comparison
- Validation functions
- Extraction functions
"""

import unittest
from unittest.mock import patch, MagicMock

import pytest
from src.tests.base_test import BaseTest
from src.utils.string_utils import (
    clean_text, truncate_text, slugify, word_count, character_count,
    sentence_count, paragraph_count, extract_keywords, find_similar_strings,
    string_similarity, levenshtein_distance, format_number, format_file_size,
    is_valid_email, is_valid_url, extract_urls, extract_emails
)


class TestStringUtils(BaseTest):
    """Unit tests for the string_utils module."""
    
    def test_clean_text(self):
        """Test cleaning text."""
        # Test with normal text
        text = "  This is a test.  \n  With multiple lines.  \r\n  And different line endings.  \r  "
        expected = "This is a test.\nWith multiple lines.\nAnd different line endings."
        self.assertEqual(clean_text(text), expected)
        
        # Test with empty text
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")
        
        # Test with only whitespace
        self.assertEqual(clean_text("   \n   \r\n   "), "")
        
        # Test with multiple spaces
        self.assertEqual(clean_text("This   has   multiple    spaces."), "This has multiple spaces.")
    
    def test_truncate_text(self):
        """Test truncating text."""
        # Test with text shorter than max length
        text = "Short text"
        self.assertEqual(truncate_text(text, 20), text)
        
        # Test with text longer than max length
        text = "This is a longer text that needs to be truncated"
        expected = "This is a longer..."
        self.assertEqual(truncate_text(text, 20), expected)
        
        # Test with custom suffix
        expected = "This is a longer---"
        self.assertEqual(truncate_text(text, 20, "---"), expected)
        
        # Test with empty text
        self.assertEqual(truncate_text("", 20), "")
        self.assertEqual(truncate_text(None, 20), "")
        
        # Test with max length equal to text length
        text = "Exact length"
        self.assertEqual(truncate_text(text, len(text)), text)
        
        # Test with max length less than suffix length
        text = "Short"
        with self.assertRaises(ValueError):
            truncate_text(text, 2, "...")
    
    def test_slugify(self):
        """Test slugifying text."""
        # Test with normal text
        text = "This is a Test!"
        self.assertEqual(slugify(text), "this-is-a-test")
        
        # Test with special characters and accents
        text = "Héllö Wörld! 123"
        self.assertEqual(slugify(text), "hello-world-123")
        
        # Test with multiple spaces and punctuation
        text = "  Multiple   spaces, and. punctuation!  "
        self.assertEqual(slugify(text), "multiple-spaces-and-punctuation")
        
        # Test with empty text
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify(None), "")
        
        # Test with only special characters
        self.assertEqual(slugify("!@#$%^&*()"), "")
    
    def test_word_count(self):
        """Test counting words."""
        # Test with normal text
        text = "This is a test with seven words."
        self.assertEqual(word_count(text), 7)
        
        # Test with empty text
        self.assertEqual(word_count(""), 0)
        self.assertEqual(word_count(None), 0)
        
        # Test with only whitespace
        self.assertEqual(word_count("   \n   \r\n   "), 0)
        
        # Test with multiple spaces
        self.assertEqual(word_count("This   has   multiple    spaces."), 5)
        
        # Test with multiple lines
        text = "This is line one.\nThis is line two.\nThis is line three."
        self.assertEqual(word_count(text), 12)
    
    def test_character_count(self):
        """Test counting characters."""
        # Test with normal text
        text = "This is a test."
        self.assertEqual(character_count(text), 15)
        
        # Test with empty text
        self.assertEqual(character_count(""), 0)
        self.assertEqual(character_count(None), 0)
        
        # Test with only whitespace
        self.assertEqual(character_count("   \n   \r\n   "), 11)
        
        # Test without whitespace
        text = "This is a test."
        self.assertEqual(character_count(text, include_whitespace=False), 11)
        
        # Test with multiple lines
        text = "This is line one.\nThis is line two."
        self.assertEqual(character_count(text), 33)
        self.assertEqual(character_count(text, include_whitespace=False), 26)
    
    def test_sentence_count(self):
        """Test counting sentences."""
        # Test with normal text
        text = "This is a sentence. This is another sentence! Is this a question? Yes, it is."
        self.assertEqual(sentence_count(text), 4)
        
        # Test with empty text
        self.assertEqual(sentence_count(""), 0)
        self.assertEqual(sentence_count(None), 0)
        
        # Test with only whitespace
        self.assertEqual(sentence_count("   \n   \r\n   "), 0)
        
        # Test with multiple punctuation marks
        text = "Wow!!! This is amazing... Don't you think?!?!"
        self.assertEqual(sentence_count(text), 3)
        
        # Test with no sentence-ending punctuation
        text = "This is not a proper sentence without punctuation"
        self.assertEqual(sentence_count(text), 1)
    
    def test_paragraph_count(self):
        """Test counting paragraphs."""
        # Test with normal text
        text = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
        self.assertEqual(paragraph_count(text), 3)
        
        # Test with empty text
        self.assertEqual(paragraph_count(""), 0)
        self.assertEqual(paragraph_count(None), 0)
        
        # Test with only whitespace
        self.assertEqual(paragraph_count("   \n   \r\n   "), 0)
        
        # Test with single paragraph
        text = "This is a single paragraph with multiple sentences. It has no line breaks."
        self.assertEqual(paragraph_count(text), 1)
        
        # Test with multiple line breaks
        text = "Paragraph one.\n\n\n\nParagraph two."
        self.assertEqual(paragraph_count(text), 2)
    
    def test_extract_keywords(self):
        """Test extracting keywords."""
        # Test with normal text
        text = "This is a test about keyword extraction. Keywords are important for search engines and content analysis."
        keywords = extract_keywords(text)
        self.assertIn("keyword", keywords)
        self.assertIn("extraction", keywords)
        self.assertIn("search", keywords)
        self.assertIn("engines", keywords)
        self.assertIn("content", keywords)
        self.assertIn("analysis", keywords)
        
        # Test with empty text
        self.assertEqual(extract_keywords(""), [])
        self.assertEqual(extract_keywords(None), [])
        
        # Test with min_length
        keywords = extract_keywords(text, min_length=6)
        self.assertIn("keyword", keywords)
        self.assertIn("extraction", keywords)
        self.assertIn("search", keywords)
        self.assertIn("engines", keywords)
        self.assertIn("content", keywords)
        self.assertIn("analysis", keywords)
        self.assertNotIn("test", keywords)  # 'test' is only 4 characters
        
        # Test with max_count
        keywords = extract_keywords(text, max_count=3)
        self.assertEqual(len(keywords), 3)
        
        # Test with stop words
        text = "The and or but if then when at from by for with about"
        self.assertEqual(extract_keywords(text), [])
    
    def test_find_similar_strings(self):
        """Test finding similar strings."""
        # Test with normal strings
        query = "apple"
        strings = ["apple", "apples", "applet", "application", "banana"]
        results = find_similar_strings(query, strings)
        self.assertEqual(results[0][0], "apple")  # Exact match should be first
        self.assertEqual(results[1][0], "apples")  # Close match should be second
        self.assertEqual(results[2][0], "applet")  # Less close match should be third
        
        # Test with empty query
        self.assertEqual(find_similar_strings("", strings), [])
        self.assertEqual(find_similar_strings(None, strings), [])
        
        # Test with empty strings
        self.assertEqual(find_similar_strings(query, []), [])
        self.assertEqual(find_similar_strings(query, None), [])
        
        # Test with threshold
        results = find_similar_strings(query, strings, threshold=0.9)
        self.assertEqual(len(results), 1)  # Only exact match should be above 0.9
        
        # Test with case insensitivity
        query = "APPLE"
        results = find_similar_strings(query, strings)
        self.assertEqual(results[0][0], "apple")  # Should still match despite case difference
    
    def test_string_similarity(self):
        """Test calculating string similarity."""
        # Test with identical strings
        self.assertEqual(string_similarity("apple", "apple"), 1.0)
        
        # Test with similar strings
        self.assertGreater(string_similarity("apple", "apples"), 0.8)
        
        # Test with different strings
        self.assertLess(string_similarity("apple", "banana"), 0.5)
        
        # Test with empty strings
        self.assertEqual(string_similarity("", ""), 1.0)
        self.assertEqual(string_similarity("apple", ""), 0.0)
        self.assertEqual(string_similarity("", "apple"), 0.0)
        self.assertEqual(string_similarity(None, None), 1.0)
        self.assertEqual(string_similarity("apple", None), 0.0)
        self.assertEqual(string_similarity(None, "apple"), 0.0)
        
        # Test with case insensitivity
        self.assertEqual(string_similarity("APPLE", "apple"), 1.0)
    
    def test_levenshtein_distance(self):
        """Test calculating Levenshtein distance."""
        # Test with identical strings
        self.assertEqual(levenshtein_distance("apple", "apple"), 0)
        
        # Test with similar strings
        self.assertEqual(levenshtein_distance("apple", "apples"), 1)  # One insertion
        self.assertEqual(levenshtein_distance("apple", "aple"), 1)    # One deletion
        self.assertEqual(levenshtein_distance("apple", "appke"), 1)   # One substitution
        
        # Test with different strings
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        
        # Test with empty strings
        self.assertEqual(levenshtein_distance("", ""), 0)
        self.assertEqual(levenshtein_distance("apple", ""), 5)
        self.assertEqual(levenshtein_distance("", "apple"), 5)
    
    def test_format_number(self):
        """Test formatting numbers."""
        # Test with small number
        self.assertEqual(format_number(123), "123")
        
        # Test with thousands
        self.assertEqual(format_number(1234), "1,234")
        
        # Test with millions
        self.assertEqual(format_number(1234567), "1,234,567")
        
        # Test with billions
        self.assertEqual(format_number(1234567890), "1,234,567,890")
        
        # Test with zero
        self.assertEqual(format_number(0), "0")
        
        # Test with negative number
        self.assertEqual(format_number(-1234), "-1,234")
    
    def test_format_file_size(self):
        """Test formatting file sizes."""
        # Test with bytes
        self.assertEqual(format_file_size(123), "123 B")
        
        # Test with kilobytes
        self.assertEqual(format_file_size(1234), "1.2 KB")
        
        # Test with megabytes
        self.assertEqual(format_file_size(1234567), "1.2 MB")
        
        # Test with gigabytes
        self.assertEqual(format_file_size(1234567890), "1.15 GB")
        
        # Test with zero
        self.assertEqual(format_file_size(0), "0 B")
    
    def test_is_valid_email(self):
        """Test validating email addresses."""
        # Test with valid emails
        self.assertTrue(is_valid_email("user@example.com"))
        self.assertTrue(is_valid_email("user.name@example.co.uk"))
        self.assertTrue(is_valid_email("user+tag@example.com"))
        self.assertTrue(is_valid_email("user123@example.com"))
        
        # Test with invalid emails
        self.assertFalse(is_valid_email("user@"))
        self.assertFalse(is_valid_email("@example.com"))
        self.assertFalse(is_valid_email("user@example"))
        self.assertFalse(is_valid_email("user@.com"))
        self.assertFalse(is_valid_email("user@example..com"))
        self.assertFalse(is_valid_email("user name@example.com"))
        self.assertFalse(is_valid_email(""))
        self.assertFalse(is_valid_email(None))
    
    def test_is_valid_url(self):
        """Test validating URLs."""
        # Test with valid URLs
        self.assertTrue(is_valid_url("http://example.com"))
        self.assertTrue(is_valid_url("https://example.com"))
        self.assertTrue(is_valid_url("http://example.com/path"))
        self.assertTrue(is_valid_url("http://example.com/path?query=value"))
        self.assertTrue(is_valid_url("http://example.com:8080"))
        self.assertTrue(is_valid_url("ftp://example.com"))
        
        # Test with invalid URLs
        self.assertFalse(is_valid_url("example.com"))
        self.assertFalse(is_valid_url("http://"))
        self.assertFalse(is_valid_url("http:/example.com"))
        self.assertFalse(is_valid_url("http:example.com"))
        self.assertFalse(is_valid_url(""))
        self.assertFalse(is_valid_url(None))
    
    def test_extract_urls(self):
        """Test extracting URLs from text."""
        # Test with normal text
        text = "Visit http://example.com and https://another-example.com/path?query=value for more information."
        urls = extract_urls(text)
        self.assertEqual(len(urls), 2)
        self.assertIn("http://example.com", urls)
        self.assertIn("https://another-example.com/path?query=value", urls)
        
        # Test with no URLs
        self.assertEqual(extract_urls("No URLs here."), [])
        
        # Test with empty text
        self.assertEqual(extract_urls(""), [])
        self.assertEqual(extract_urls(None), [])
        
        # Test with multiple occurrences of the same URL
        text = "Visit http://example.com and http://example.com again."
        urls = extract_urls(text)
        self.assertEqual(len(urls), 2)  # Should find both occurrences
    
    def test_extract_emails(self):
        """Test extracting email addresses from text."""
        # Test with normal text
        text = "Contact user@example.com or another.user@example.co.uk for more information."
        emails = extract_emails(text)
        self.assertEqual(len(emails), 2)
        self.assertIn("user@example.com", emails)
        self.assertIn("another.user@example.co.uk", emails)
        
        # Test with no emails
        self.assertEqual(extract_emails("No emails here."), [])
        
        # Test with empty text
        self.assertEqual(extract_emails(""), [])
        self.assertEqual(extract_emails(None), [])
        
        # Test with multiple occurrences of the same email
        text = "Contact user@example.com or user@example.com again."
        emails = extract_emails(text)
        self.assertEqual(len(emails), 2)  # Should find both occurrences


# Pytest-style tests
class TestStringUtilsPytest:
    """Pytest-style tests for the string_utils module."""
    
    def test_clean_text_pytest(self):
        """Test cleaning text using pytest style."""
        # Test with normal text
        text = "  This is a test.  \n  With multiple lines.  \r\n  And different line endings.  \r  "
        expected = "This is a test.\nWith multiple lines.\nAnd different line endings."
        assert clean_text(text) == expected
        
        # Test with empty text
        assert clean_text("") == ""
        assert clean_text(None) == ""
    
    def test_word_count_pytest(self):
        """Test counting words using pytest style."""
        # Test with normal text
        text = "This is a test with seven words."
        assert word_count(text) == 7
        
        # Test with empty text
        assert word_count("") == 0
        assert word_count(None) == 0
    
    def test_string_similarity_pytest(self):
        """Test calculating string similarity using pytest style."""
        # Test with identical strings
        assert string_similarity("apple", "apple") == 1.0
        
        # Test with similar strings
        assert string_similarity("apple", "apples") > 0.8
        
        # Test with different strings
        assert string_similarity("apple", "banana") < 0.5


if __name__ == '__main__':
    unittest.main()
