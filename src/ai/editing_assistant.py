#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Editing Assistant

This module provides AI-powered editing and improvement features for RebelSCRIBE,
including grammar and style checking, readability analysis, tone consistency checking,
rewriting suggestions, and word choice improvements.
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import statistics

from src.utils.logging_utils import get_logger
from src.ai.ai_service import AIService

logger = get_logger(__name__)


class EditingAssistant:
    """
    Editing assistant for RebelSCRIBE.
    
    This class provides methods for AI-powered editing and improvement,
    including grammar and style checking, readability analysis, tone consistency checking,
    rewriting suggestions, and word choice improvements.
    """
    
    def __init__(self, ai_service: Optional[AIService] = None):
        """
        Initialize the editing assistant.
        
        Args:
            ai_service: The AI service to use. If None, a new instance will be created.
        """
        logger.info("Initializing editing assistant")
        
        # Set AI service
        self.ai_service = ai_service or AIService()
        
        # Default parameters
        self.default_params = {
            "temperature": 0.3,  # Lower temperature for more consistent editing
            "max_tokens": 1500,
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5
        }
        
        logger.debug("Editing assistant initialized")
    
    async def check_grammar_and_style(self, text: str, style_guide: Optional[str] = None,
                                    **kwargs) -> Dict[str, Any]:
        """
        Check grammar and style issues in the text.
        
        Args:
            text: The text to check.
            style_guide: Optional style guide to follow (e.g., "Chicago", "AP", "MLA").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing grammar and style analysis.
        """
        logger.info("Checking grammar and style")
        
        # Prepare prompt
        prompt = "Analyze the following text for grammar and style issues:\n\n"
        prompt += text + "\n\n"
        
        if style_guide:
            prompt += f"Follow the {style_guide} style guide for recommendations.\n\n"
        
        prompt += """
Provide a comprehensive analysis with the following sections:
1. Grammar issues (with line numbers or quotes for context)
2. Style issues (with line numbers or quotes for context)
3. Punctuation issues
4. Word choice suggestions
5. Overall assessment

For each issue, provide:
- The problematic text
- The specific issue
- A suggested correction

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(4000, len(text) // 2)  # Scale with text length
        
        # Generate text
        analysis_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            analysis_text = analysis_text[analysis_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if analysis_text.rfind("}") != -1:
                analysis_text = analysis_text[:analysis_text.rfind("}")+1]
            
            analysis = json.loads(analysis_text)
            logger.debug("Grammar and style analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse grammar analysis JSON: {e}")
            # Create a basic analysis with the raw text
            analysis = {
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def analyze_readability(self, text: str, target_audience: Optional[str] = None,
                                **kwargs) -> Dict[str, Any]:
        """
        Analyze the readability of the text.
        
        Args:
            text: The text to analyze.
            target_audience: Optional target audience (e.g., "young adult", "academic", "general").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing readability analysis.
        """
        logger.info("Analyzing readability")
        
        # Calculate basic readability metrics
        words = text.split()
        word_count = len(words)
        
        # Count sentences (simple approximation)
        sentence_count = len(re.findall(r'[.!?]+', text)) or 1  # Avoid division by zero
        
        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Calculate average sentence length
        avg_sentence_length = word_count / sentence_count
        
        # Prepare prompt
        prompt = "Analyze the readability of the following text:\n\n"
        prompt += text + "\n\n"
        
        if target_audience:
            prompt += f"The target audience is: {target_audience}\n\n"
        
        prompt += f"""
Basic metrics:
- Word count: {word_count}
- Sentence count: {sentence_count}
- Average word length: {avg_word_length:.2f} characters
- Average sentence length: {avg_sentence_length:.2f} words

Provide a comprehensive readability analysis with the following sections:
1. Estimated reading level (e.g., grade level, complexity)
2. Vocabulary assessment (simple vs. complex words)
3. Sentence structure analysis
4. Paragraph structure and flow
5. Suggestions for improving readability
6. Overall assessment

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2000
        
        # Generate text
        analysis_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            analysis_text = analysis_text[analysis_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if analysis_text.rfind("}") != -1:
                analysis_text = analysis_text[:analysis_text.rfind("}")+1]
            
            analysis = json.loads(analysis_text)
            
            # Add basic metrics to the analysis
            analysis["basic_metrics"] = {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": avg_word_length,
                "avg_sentence_length": avg_sentence_length
            }
            
            logger.debug("Readability analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse readability analysis JSON: {e}")
            # Create a basic analysis with the raw text and metrics
            analysis = {
                "basic_metrics": {
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "avg_word_length": avg_word_length,
                    "avg_sentence_length": avg_sentence_length
                },
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def check_tone_consistency(self, text: str, target_tone: Optional[str] = None,
                                   **kwargs) -> Dict[str, Any]:
        """
        Check tone consistency throughout the text.
        
        Args:
            text: The text to check.
            target_tone: Optional target tone (e.g., "formal", "casual", "academic").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing tone consistency analysis.
        """
        logger.info("Checking tone consistency")
        
        # Prepare prompt
        prompt = "Analyze the tone consistency of the following text:\n\n"
        prompt += text + "\n\n"
        
        if target_tone:
            prompt += f"The target tone is: {target_tone}\n\n"
        
        prompt += """
Provide a comprehensive tone analysis with the following sections:
1. Overall tone assessment
2. Tone variations (identify sections with different tones)
3. Consistency issues (with line numbers or quotes for context)
4. Suggestions for maintaining a consistent tone
5. Word choice and phrasing recommendations

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2000
        
        # Generate text
        analysis_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            analysis_text = analysis_text[analysis_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if analysis_text.rfind("}") != -1:
                analysis_text = analysis_text[:analysis_text.rfind("}")+1]
            
            analysis = json.loads(analysis_text)
            logger.debug("Tone consistency analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tone analysis JSON: {e}")
            # Create a basic analysis with the raw text
            analysis = {
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def suggest_rewrites(self, text: str, goal: str, preserve_meaning: bool = True,
                             **kwargs) -> List[Dict[str, str]]:
        """
        Suggest rewrites for the text based on a specific goal.
        
        Args:
            text: The text to rewrite.
            goal: The goal of the rewrite (e.g., "more concise", "more descriptive", "more formal").
            preserve_meaning: Whether to strictly preserve the original meaning.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries containing rewrite suggestions.
        """
        logger.info(f"Suggesting rewrites with goal: {goal}")
        
        # Prepare prompt
        prompt = f"Suggest rewrites for the following text to make it {goal}:\n\n"
        prompt += text + "\n\n"
        
        if preserve_meaning:
            prompt += "Preserve the original meaning as much as possible.\n\n"
        else:
            prompt += "Feel free to be creative while keeping the general idea.\n\n"
        
        prompt += """
Provide 3 different rewrite suggestions, each with:
1. The rewritten text
2. Explanation of changes made
3. How the changes achieve the stated goal

Format the response as a JSON array of rewrite objects, each with "rewritten_text", "explanation", and "goal_achievement" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(4000, len(text) * 3)  # Scale with text length
        
        # Generate text
        rewrites_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            rewrites_text = rewrites_text[rewrites_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if rewrites_text.rfind("]") != -1:
                rewrites_text = rewrites_text[:rewrites_text.rfind("]")+1]
            
            rewrites = json.loads(rewrites_text)
            logger.debug(f"Generated {len(rewrites)} rewrite suggestions")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse rewrites JSON: {e}")
            # Create a basic rewrites list with the raw text
            rewrites = [{
                "rewritten_text": "Failed to parse rewrites",
                "explanation": "JSON parsing error",
                "goal_achievement": "N/A",
                "raw_output": rewrites_text
            }]
        
        return rewrites
    
    async def improve_word_choice(self, text: str, focus: Optional[str] = None,
                                **kwargs) -> Dict[str, Any]:
        """
        Suggest word choice improvements.
        
        Args:
            text: The text to improve.
            focus: Optional focus area (e.g., "vivid descriptions", "emotional impact", "technical precision").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing word choice improvement suggestions.
        """
        logger.info("Suggesting word choice improvements")
        
        # Prepare prompt
        prompt = "Analyze the following text for word choice improvements:\n\n"
        prompt += text + "\n\n"
        
        if focus:
            prompt += f"Focus on improving word choice for {focus}.\n\n"
        
        prompt += """
Provide word choice improvement suggestions with the following sections:
1. Weak or overused words (with alternatives)
2. Vague or imprecise language (with more specific alternatives)
3. Redundant phrases (with concise alternatives)
4. Clichés or idioms (with fresh alternatives)
5. Overall word choice assessment

For each suggestion, provide:
- The original word or phrase
- The suggested replacement(s)
- Why the replacement is better

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2500
        
        # Generate text
        improvements_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            improvements_text = improvements_text[improvements_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if improvements_text.rfind("}") != -1:
                improvements_text = improvements_text[:improvements_text.rfind("}")+1]
            
            improvements = json.loads(improvements_text)
            logger.debug("Word choice improvements generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse word choice improvements JSON: {e}")
            # Create a basic improvements with the raw text
            improvements = {
                "raw_improvements": improvements_text
            }
        
        return improvements
    
    async def edit_text(self, text: str, edit_type: str, intensity: str = "medium",
                      **kwargs) -> Dict[str, str]:
        """
        Edit text according to a specific edit type and intensity.
        
        Args:
            text: The text to edit.
            edit_type: The type of edit (e.g., "grammar", "conciseness", "clarity", "style").
            intensity: The intensity of the edit ("light", "medium", "heavy").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing the edited text and explanation.
        """
        logger.info(f"Editing text with {intensity} {edit_type} edits")
        
        # Prepare prompt
        prompt = f"Edit the following text for {edit_type} with {intensity} intensity:\n\n"
        prompt += text + "\n\n"
        
        prompt += f"""
Apply {intensity} {edit_type} edits to improve the text while preserving the original meaning and voice.

Provide:
1. The edited text
2. A summary of changes made
3. Explanation of how the changes improve the {edit_type}

Format the response as a JSON object with "edited_text", "summary", and "explanation" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(4000, len(text) * 2)  # Scale with text length
        
        # Generate text
        edit_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            edit_text = edit_text[edit_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if edit_text.rfind("}") != -1:
                edit_text = edit_text[:edit_text.rfind("}")+1]
            
            edit = json.loads(edit_text)
            logger.debug("Text edited successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse edit JSON: {e}")
            # Create a basic edit with the raw text
            edit = {
                "edited_text": text,  # Return original text
                "summary": "Failed to parse edit",
                "explanation": "JSON parsing error",
                "raw_output": edit_text
            }
        
        return edit
    
    async def check_repetition(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Check for repetitive words, phrases, and sentence structures.
        
        Args:
            text: The text to check.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing repetition analysis.
        """
        logger.info("Checking for repetition")
        
        # Prepare prompt
        prompt = "Analyze the following text for repetitive elements:\n\n"
        prompt += text + "\n\n"
        
        prompt += """
Identify repetitive elements with the following sections:
1. Repeated words (with frequency and context)
2. Repeated phrases (with frequency and context)
3. Repetitive sentence structures
4. Repetitive paragraph openings
5. Suggestions for reducing repetition

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2000
        
        # Generate text
        repetition_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            repetition_text = repetition_text[repetition_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if repetition_text.rfind("}") != -1:
                repetition_text = repetition_text[:repetition_text.rfind("}")+1]
            
            repetition = json.loads(repetition_text)
            logger.debug("Repetition analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse repetition analysis JSON: {e}")
            # Create a basic repetition with the raw text
            repetition = {
                "raw_analysis": repetition_text
            }
        
        return repetition
    
    async def enhance_descriptions(self, text: str, focus: str = "sensory",
                                 **kwargs) -> Dict[str, str]:
        """
        Enhance descriptions in the text.
        
        Args:
            text: The text to enhance.
            focus: The focus of enhancement (e.g., "sensory", "emotional", "visual", "action").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing the enhanced text and explanation.
        """
        logger.info(f"Enhancing descriptions with focus on {focus}")
        
        # Prepare prompt
        prompt = f"Enhance the descriptions in the following text with a focus on {focus} details:\n\n"
        prompt += text + "\n\n"
        
        prompt += f"""
Improve the {focus} descriptions while maintaining the original style and tone.

Provide:
1. The enhanced text
2. A summary of enhancements made
3. Explanation of how the enhancements improve the {focus} aspects

Format the response as a JSON object with "enhanced_text", "summary", and "explanation" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(4000, len(text) * 2)  # Scale with text length
        
        # Generate text
        enhancement_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            enhancement_text = enhancement_text[enhancement_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if enhancement_text.rfind("}") != -1:
                enhancement_text = enhancement_text[:enhancement_text.rfind("}")+1]
            
            enhancement = json.loads(enhancement_text)
            logger.debug("Descriptions enhanced successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse enhancement JSON: {e}")
            # Create a basic enhancement with the raw text
            enhancement = {
                "enhanced_text": text,  # Return original text
                "summary": "Failed to parse enhancement",
                "explanation": "JSON parsing error",
                "raw_output": enhancement_text
            }
        
        return enhancement
    
    async def close(self):
        """Close the editing assistant and its AI service."""
        logger.info("Closing editing assistant")
        await self.ai_service.close()
