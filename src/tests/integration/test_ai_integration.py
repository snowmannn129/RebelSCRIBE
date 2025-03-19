#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI integration tests for RebelSCRIBE.

This module contains tests that verify the integration of AI components
with the rest of the application.
"""

import os
import tempfile
import unittest
import shutil
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.backend.models.project import Project
from src.backend.models.document import Document
from src.backend.services.project_manager import ProjectManager
from src.backend.services.document_manager import DocumentManager
from src.ai.ai_service import AIService
from src.ai.text_generator import TextGenerator
from src.ai.character_assistant import CharacterAssistant
from src.ai.plot_assistant import PlotAssistant
from src.ai.editing_assistant import EditingAssistant
from src.utils.config_manager import ConfigManager


class TestAIIntegration(unittest.TestCase):
    """Tests for AI integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test configuration
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.config = ConfigManager(self.config_path)
        
        # Set up the project manager
        self.project_manager = ProjectManager(self.config)
        
        # Set up the document manager with project path
        with patch('src.backend.services.document_manager.ConfigManager') as mock_config_manager:
            mock_config_instance = MagicMock()
            mock_config_instance.get.side_effect = lambda section, key=None, default=None: {
                'application': {'data_directory': self.test_dir},
                'documents': {'max_versions': 5}
            }.get(section, {}).get(key, default)
            mock_config_manager.return_value = mock_config_instance
            self.document_manager = DocumentManager(self.test_dir)
        
        # Set up the AI service
        self.ai_service = AIService(self.config)
        
        # Set up the text generator
        self.text_generator = TextGenerator(self.config)
        
        # Set up the character assistant
        self.character_assistant = CharacterAssistant(self.config)
        
        # Set up the plot assistant
        self.plot_assistant = PlotAssistant(self.config)
        
        # Set up the editing assistant
        self.editing_assistant = EditingAssistant(self.config)
        
        # Create a test project
        self.project_path = os.path.join(self.test_dir, "test_project.rebelscribe")
        self.project = self.project_manager.create_project(
            title="Test Project",
            author="Test Author",
            path=self.project_path
        )
        
        # Create a test document
        self.document = self.document_manager.create_document(
            title="Test Document",
            content="This is a test document for AI integration."
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_text_generation_integration(self):
        """Test integration of text generation with document management."""
        # Mock the text generator to return a predictable response
        with patch.object(self.text_generator, 'continue_story', return_value=" This is AI-generated text."):
            # Generate text
            generated_text = asyncio.run(self.text_generator.continue_story(
                context=self.document.content,
                length=50
            ))
            
            # Update the document with the generated text
            self.document.content += generated_text
            self.document_manager.save_document(self.document)
            
            # Reload the document to verify changes were saved
            reloaded_document = self.document_manager.get_document(self.document.id)
            self.assertEqual(
                reloaded_document.content,
                "This is a test document for AI integration. This is AI-generated text."
            )
    
    def test_character_assistant_integration(self):
        """Test integration of character assistant with document management."""
        # Mock the character assistant to return a predictable response
        character_data = {
            "name": "John Smith",
            "age": 35,
            "description": "A detective with a troubled past.",
            "motivation": "To solve the case and redeem himself.",
            "traits": ["intelligent", "persistent", "cynical"]
        }
        
        with patch.object(self.character_assistant, 'generate_character_profile', return_value=character_data):
            # Generate a character
            character = asyncio.run(self.character_assistant.generate_character_profile(
                name="John Smith",
                role="protagonist",
                genre="mystery"
            ))
            
            # Create a character document
            character_doc = self.document_manager.create_document(
                title=f"Character: {character['name']}",
                content=f"Name: {character['name']}\n"
                        f"Age: {character['age']}\n"
                        f"Description: {character['description']}\n"
                        f"Motivation: {character['motivation']}\n"
                        f"Traits: {', '.join(character['traits'])}"
            )
            
            # Verify the character document was created
            self.assertIsNotNone(character_doc)
            self.assertEqual(character_doc.title, "Character: John Smith")
            self.assertIn("A detective with a troubled past.", character_doc.content)
            
            # Reload the document to verify changes were saved
            reloaded_doc = self.document_manager.get_document(character_doc.id)
            self.assertEqual(reloaded_doc.title, "Character: John Smith")
            self.assertIn("A detective with a troubled past.", reloaded_doc.content)
    
    def test_plot_assistant_integration(self):
        """Test integration of plot assistant with document management."""
        # Mock the plot assistant to return a predictable response
        plot_data = {
            "title": "The Mystery of the Missing Diamond",
            "premise": "A valuable diamond goes missing from a museum, and a detective must solve the case.",
            "setting": "Modern-day New York City",
            "plot_points": [
                "The diamond is stolen during a high-profile exhibition.",
                "The detective is assigned to the case.",
                "The detective discovers that the security system was compromised.",
                "The detective identifies the thief as an inside job.",
                "The detective confronts the culprit and recovers the diamond."
            ]
        }
        
        with patch.object(self.plot_assistant, 'generate_plot_outline', return_value=plot_data):
            # Generate a plot
            plot = asyncio.run(self.plot_assistant.generate_plot_outline(
                premise="A valuable diamond goes missing from a museum",
                genre="mystery",
                num_acts=3
            ))
            
            # Create a plot document
            plot_doc = self.document_manager.create_document(
                title=f"Plot: {plot['title']}",
                content=f"Title: {plot['title']}\n"
                        f"Premise: {plot['premise']}\n"
                        f"Setting: {plot['setting']}\n"
                        f"Plot Points:\n" + "\n".join([f"- {point}" for point in plot['plot_points']])
            )
            
            # Verify the plot document was created
            self.assertIsNotNone(plot_doc)
            self.assertEqual(plot_doc.title, "Plot: The Mystery of the Missing Diamond")
            self.assertIn("A valuable diamond goes missing from a museum", plot_doc.content)
            
            # Reload the document to verify changes were saved
            reloaded_doc = self.document_manager.get_document(plot_doc.id)
            self.assertEqual(reloaded_doc.title, "Plot: The Mystery of the Missing Diamond")
            self.assertIn("A valuable diamond goes missing from a museum", reloaded_doc.content)
    
    def test_editing_assistant_integration(self):
        """Test integration of editing assistant with document management."""
        # Create a document with some issues
        document_with_issues = self.document_manager.create_document(
            title="Document with Issues",
            content="This document has has some issues. There are repeated words and typos."
        )
        
        # Mock the editing assistant to return a predictable response
        edited_content = {
            "edited_text": "This document has some issues. There are repeated words and typos.",
            "summary": "Fixed repeated word",
            "explanation": "Removed the repeated word 'has'"
        }
        
        with patch.object(self.editing_assistant, 'edit_text', return_value=edited_content):
            # Edit the document
            result = asyncio.run(self.editing_assistant.edit_text(
                text=document_with_issues.content,
                edit_type="grammar"
            ))
            
            # Extract the edited text
            edited_text = result["edited_text"]
            
            # Update the document with the edited text
            document_with_issues.content = edited_text
            self.document_manager.save_document(document_with_issues)
            
            # Create a suggestions document
            suggestions_doc = self.document_manager.create_document(
                title=f"Editing Suggestions for: {document_with_issues.title}",
                content=f"Editing Suggestions:\n- {result['summary']}\n  {result['explanation']}"
            )
            
            # Verify the document was updated
            reloaded_doc = self.document_manager.get_document(document_with_issues.id)
            self.assertEqual(reloaded_doc.content, edited_text)
            
            # Verify the suggestions document was created
            self.assertIsNotNone(suggestions_doc)
            self.assertEqual(suggestions_doc.title, "Editing Suggestions for: Document with Issues")
            self.assertIn("Fixed repeated word", suggestions_doc.content)
    
    def test_ai_settings_integration(self):
        """Test integration of AI settings with AI services."""
        # Update AI settings in the configuration
        self.config.set("ai", "model", "gpt-4")
        self.config.set("ai", "temperature", 0.7)
        self.config.set("ai", "max_tokens", 1000)
        self.config.save_config()
        
        # Create a new AI service with the updated configuration
        new_ai_service = AIService(self.config)
        
        # Mock the AI service's generate_text method
        with patch.object(new_ai_service, '_make_request') as mock_make_request:
            # Set up the mock to return a simple response
            mock_response = {"text": "This is a test response"}
            mock_make_request.return_value = mock_response
            
            # Call the generate_text method
            asyncio.run(new_ai_service.generate_text("Test prompt"))
            
            # Verify the method was called
            mock_make_request.assert_called_once()
            
            # Check that the configuration was used correctly
            # We can't directly verify the config values since they're used internally,
            # but we can check that the method was called with the expected parameters
            args, kwargs = mock_make_request.call_args
            self.assertEqual(args[0].value, "completion")  # First arg should be AIModelType.COMPLETION
    
    def test_ai_service_error_handling(self):
        """Test error handling in AI service integration."""
        # Mock the text generator to raise an exception
        with patch.object(self.text_generator, 'continue_story', side_effect=Exception("API error")):
            # Try to generate text
            with self.assertRaises(Exception):
                asyncio.run(self.text_generator.continue_story(
                    context=self.document.content,
                    length=50
                ))
            
            # Verify the document wasn't changed
            reloaded_document = self.document_manager.get_document(self.document.id)
            self.assertEqual(
                reloaded_document.content,
                "This is a test document for AI integration."
            )


if __name__ == '__main__':
    unittest.main()
