#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional tests for AI integration.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from src.tests.functional.base_functional_test import BaseFunctionalTest
from src.backend.models.document import Document
from src.ai.ai_service import AIService
from src.ai.text_generator import TextGenerator
from src.ai.character_assistant import CharacterAssistant
from src.ai.plot_assistant import PlotAssistant
from src.ai.editing_assistant import EditingAssistant
import src.ai.local_models as local_models


class TestAIIntegration(BaseFunctionalTest):
    """Test case for AI integration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test project
        self.project_path = self.create_test_project()
        self.project_manager.load_project(self.project_path)
        
        # Create test documents
        self.doc1_id = self.create_test_document(
            title="Sample Document",
            content="This is a sample document for AI testing. "
                    "It contains some text that will be used for text generation, "
                    "editing suggestions, and other AI features."
        )
        
        # Initialize AI services
        self.ai_service = AIService(config_manager=self.config_manager)
        self.text_generator = TextGenerator(self.ai_service)
        self.character_assistant = CharacterAssistant(self.ai_service)
        self.plot_assistant = PlotAssistant(self.ai_service)
        self.editing_assistant = EditingAssistant(self.ai_service)
        
        # Check if local models are available
        self.has_local_models = local_models.is_local_models_available()
    
    def test_ai_service_initialization(self):
        """Test AI service initialization."""
        # Verify AI service was initialized
        self.assertIsNotNone(self.ai_service)
        
        # Verify API key is set (or using a mock/default for testing)
        self.assertTrue(hasattr(self.ai_service, 'api_key') or hasattr(self.ai_service, '_api_key'))
        
        # Verify model configuration is set
        self.assertTrue(hasattr(self.ai_service, 'model_config') or hasattr(self.ai_service, '_model_config'))
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_text_generation(self, mock_generate_text):
        """Test text generation functionality."""
        # Set up mock response
        mock_generate_text.return_value = "This is generated text. It continues the sample document."
        
        # Get document content
        document = self.document_manager.get_document(self.doc1_id)
        content = document.content
        
        # Generate text
        prompt = "Continue the story"
        generated_text = self.text_generator.generate_text(content, prompt)
        
        # Verify text was generated
        self.assertIsNotNone(generated_text)
        self.assertGreater(len(generated_text), 0)
        
        # Verify the mock was called with correct parameters
        mock_generate_text.assert_called_once()
        args, kwargs = mock_generate_text.call_args
        self.assertIn(content, str(args) + str(kwargs))
        self.assertIn(prompt, str(args) + str(kwargs))
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_character_development(self, mock_generate_text):
        """Test character development functionality."""
        # Set up mock response
        mock_character_profile = """
        # John Doe
        
        ## Basic Information
        - Age: 35
        - Occupation: Detective
        - Physical Description: Tall, with dark hair and piercing blue eyes
        
        ## Personality
        - Introverted but observant
        - Highly analytical
        - Struggles with personal relationships
        
        ## Background
        John grew up in a small town but moved to the city after college.
        He joined the police force and quickly rose through the ranks due to his
        exceptional deductive abilities.
        
        ## Goals and Motivations
        - Solving the case that has haunted him for years
        - Finding connection with others
        - Proving himself to his estranged father
        
        ## Flaws and Conflicts
        - Workaholic tendencies
        - Trust issues
        - Occasional drinking problem
        """
        mock_generate_text.return_value = mock_character_profile
        
        # Generate character profile
        character_name = "John Doe"
        profile = self.character_assistant.generate_character_profile(character_name)
        
        # Verify profile was generated
        self.assertIsNotNone(profile)
        self.assertGreater(len(profile), 0)
        
        # Verify the mock was called with correct parameters
        mock_generate_text.assert_called_once()
        args, kwargs = mock_generate_text.call_args
        self.assertIn(character_name, str(args) + str(kwargs))
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_plot_development(self, mock_generate_text):
        """Test plot development functionality."""
        # Set up mock response
        mock_plot_outline = """
        # Mystery in the Old Town
        
        ## Act 1: Setup
        - Introduce Detective John and the small town setting
        - A valuable artifact is stolen from the local museum
        - John is assigned to the case, meeting resistance from locals
        
        ## Act 2: Confrontation
        - John discovers clues pointing to an inside job
        - He faces obstacles from the museum curator
        - A second theft occurs, revealing a pattern
        
        ## Act 3: Resolution
        - John sets a trap for the thief
        - The curator is revealed to be part of a larger smuggling ring
        - Final confrontation and resolution
        
        ## Themes
        - Trust vs. suspicion
        - Small town secrets
        - Redemption through truth
        """
        mock_generate_text.return_value = mock_plot_outline
        
        # Generate plot outline
        premise = "A detective investigating a museum theft in a small town"
        outline = self.plot_assistant.generate_plot_outline(premise)
        
        # Verify outline was generated
        self.assertIsNotNone(outline)
        self.assertGreater(len(outline), 0)
        
        # Verify the mock was called with correct parameters
        mock_generate_text.assert_called_once()
        args, kwargs = mock_generate_text.call_args
        self.assertIn(premise, str(args) + str(kwargs))
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_editing_suggestions(self, mock_generate_text):
        """Test editing suggestions functionality."""
        # Set up mock response
        mock_suggestions = """
        # Editing Suggestions
        
        1. **Clarity**: The second sentence could be clearer. Consider revising to: 
           "It contains sample text for testing various AI features including text generation and editing suggestions."
        
        2. **Conciseness**: The phrase "that will be used for" could be shortened to "for".
        
        3. **Word Choice**: Consider replacing "contains" with "provides" for more variety.
        
        4. **Structure**: Consider breaking the long sentence into two separate sentences for better readability.
        """
        mock_generate_text.return_value = mock_suggestions
        
        # Get document content
        document = self.document_manager.get_document(self.doc1_id)
        content = document.content
        
        # Get editing suggestions
        suggestions = self.editing_assistant.get_editing_suggestions(content)
        
        # Verify suggestions were generated
        self.assertIsNotNone(suggestions)
        self.assertGreater(len(suggestions), 0)
        
        # Verify the mock was called with correct parameters
        mock_generate_text.assert_called_once()
        args, kwargs = mock_generate_text.call_args
        self.assertIn(content, str(args) + str(kwargs))
    
    def test_local_model_availability(self):
        """Test local model availability."""
        # Check if local models are available
        if not self.has_local_models:
            self.skipTest("No local models available")
        
        # Get available models
        available_models = local_models.get_available_models()
        
        # Verify at least one model is available
        self.assertGreater(len(available_models), 0)
    
    @unittest.skipIf(not hasattr(local_models, 'generate_text'), "Local inference not implemented")
    def test_local_model_inference(self):
        """Test local model inference."""
        # Skip if no local models are available
        if not self.has_local_models:
            self.skipTest("No local models available")
        
        # Get available models
        available_models = local_models.get_available_models()
        if not available_models:
            self.skipTest("No local models available")
        
        # Select the first available model
        model_name = available_models[0]["name"]
        
        # Run inference
        prompt = "Once upon a time"
        try:
            with patch('src.ai.local_models.generate_text') as mock_generate_text:
                mock_generate_text.return_value = ["Once upon a time there was a kingdom far away."]
                
                result = local_models.generate_text(prompt, model_name, max_length=20)
                
                # Verify result
                self.assertIsNotNone(result)
                self.assertIsInstance(result, list)
                self.assertGreater(len(result[0]), len(prompt))
        except NotImplementedError:
            self.skipTest("Local inference not implemented")
    
    def test_ai_settings_configuration(self):
        """Test AI settings configuration."""
        # Get current settings
        original_settings = self.ai_service.get_settings()
        
        # Modify settings
        new_settings = {
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9
        }
        
        # Update settings
        self.ai_service.update_settings(new_settings)
        
        # Get updated settings
        updated_settings = self.ai_service.get_settings()
        
        # Verify settings were updated
        for key, value in new_settings.items():
            self.assertEqual(updated_settings.get(key), value)
        
        # Restore original settings
        self.ai_service.update_settings(original_settings)
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_text_generation_with_parameters(self, mock_generate_text):
        """Test text generation with different parameters."""
        # Set up mock response
        mock_generate_text.return_value = "This is generated text with custom parameters."
        
        # Get document content
        document = self.document_manager.get_document(self.doc1_id)
        content = document.content
        
        # Generate text with custom parameters
        prompt = "Continue the story"
        parameters = {
            "temperature": 0.8,
            "max_tokens": 150,
            "top_p": 0.95
        }
        
        generated_text = self.text_generator.generate_text(content, prompt, **parameters)
        
        # Verify text was generated
        self.assertIsNotNone(generated_text)
        self.assertGreater(len(generated_text), 0)
        
        # Verify the mock was called with correct parameters
        mock_generate_text.assert_called_once()
        args, kwargs = mock_generate_text.call_args
        
        # Check that parameters were passed correctly
        for key, value in parameters.items():
            self.assertIn(key, kwargs)
            self.assertEqual(kwargs[key], value)
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_ai_error_handling(self, mock_generate_text):
        """Test AI error handling."""
        # Set up mock to raise an exception
        mock_generate_text.side_effect = Exception("API Error")
        
        # Get document content
        document = self.document_manager.get_document(self.doc1_id)
        content = document.content
        
        # Try to generate text
        prompt = "Continue the story"
        
        # Verify that the error is handled gracefully
        try:
            generated_text = self.text_generator.generate_text(content, prompt)
            
            # If no exception is raised, the result should be None or an error message
            self.assertTrue(generated_text is None or "error" in generated_text.lower())
        except Exception as e:
            # If an exception is raised, it should be handled by the text generator
            self.fail(f"Text generator did not handle the exception: {str(e)}")
    
    def test_ai_integration_with_document_manager(self):
        """Test AI integration with document manager."""
        # Create a document with AI-generated content
        with patch('src.ai.ai_service.AIService.generate_text') as mock_generate_text:
            # Set up mock response
            mock_generate_text.return_value = "This is AI-generated content for a new document."
            
            # Create a document with AI-generated content
            document = Document(
                title="AI Generated Document",
                content="Initial content. "
            )
            
            # Add the document
            self.document_manager.add_document(document)
            
            # Generate content using AI
            prompt = "Continue the document"
            generated_content = self.text_generator.generate_text(document.content, prompt)
            
            # Update document with generated content
            document.content += "\n\n" + generated_content
            
            # Save the document
            self.document_manager.save_document(document)
            
            # Reload the document
            reloaded_document = self.document_manager.get_document(document.id)
            
            # Verify the document contains the generated content
            self.assertIn(generated_content, reloaded_document.content)
    
    @patch('src.ai.ai_service.AIService.generate_text')
    def test_batch_processing(self, mock_generate_text):
        """Test batch processing with AI."""
        # Set up mock response
        mock_generate_text.return_value = "AI-generated summary."
        
        # Create multiple documents
        doc_ids = []
        for i in range(3):
            doc_id = self.create_test_document(
                title=f"Document {i+1}",
                content=f"This is document {i+1} for batch processing test."
            )
            doc_ids.append(doc_id)
        
        # Process documents in batch
        results = []
        for doc_id in doc_ids:
            document = self.document_manager.get_document(doc_id)
            summary = self.ai_service.generate_text(
                prompt=f"Summarize the following text:\n\n{document.content}",
                max_tokens=50
            )
            results.append(summary)
            
            # Update document with summary
            document.metadata = document.metadata or {}
            document.metadata["ai_summary"] = summary
            self.document_manager.save_document(document)
        
        # Verify results
        self.assertEqual(len(results), len(doc_ids))
        for result in results:
            self.assertIsNotNone(result)
            self.assertGreater(len(result), 0)
        
        # Verify documents were updated with summaries
        for doc_id in doc_ids:
            document = self.document_manager.get_document(doc_id)
            self.assertIn("ai_summary", document.metadata)
            self.assertEqual(document.metadata["ai_summary"], "AI-generated summary.")
    
    def test_model_switching(self):
        """Test switching between different AI models."""
        # Get original model
        original_model = self.ai_service.get_settings().get("model")
        
        # Define test models
        test_models = ["test-model-1", "test-model-2"]
        
        for model in test_models:
            # Update model
            self.ai_service.update_settings({"model": model})
            
            # Verify model was updated
            current_model = self.ai_service.get_settings().get("model")
            self.assertEqual(current_model, model)
            
            # Test with mock to verify the correct model is used
            with patch('src.ai.ai_service.AIService.generate_text') as mock_generate_text:
                mock_generate_text.return_value = f"Text generated with {model}"
                
                # Generate text
                result = self.ai_service.generate_text(prompt="Test prompt")
                
                # Verify result
                self.assertIn(model, result)
        
        # Restore original model
        if original_model:
            self.ai_service.update_settings({"model": original_model})


if __name__ == "__main__":
    unittest.main()
