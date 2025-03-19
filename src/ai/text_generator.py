#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Text Generator

This module provides text generation capabilities for RebelSCRIBE,
including story continuation, dialogue generation, description enhancement,
scene generation, and creative prompts.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Union, Tuple

from src.utils.logging_utils import get_logger
from src.ai.ai_service import AIService

logger = get_logger(__name__)


class TextGenerator:
    """
    Text generator for RebelSCRIBE.
    
    This class provides methods for generating various types of text content
    using AI models, including story continuation, dialogue generation,
    description enhancement, scene generation, and creative prompts.
    """
    
    def __init__(self, ai_service: Optional[AIService] = None):
        """
        Initialize the text generator.
        
        Args:
            ai_service: The AI service to use. If None, a new instance will be created.
        """
        logger.info("Initializing text generator")
        
        # Set AI service
        self.ai_service = ai_service or AIService()
        
        # Default parameters
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5
        }
        
        logger.debug("Text generator initialized")
    
    async def continue_story(self, context: str, length: int = 500, style: Optional[str] = None, **kwargs) -> str:
        """
        Generate a continuation of a story.
        
        Args:
            context: The existing story context.
            length: The approximate length of the continuation in words.
            style: The writing style to use (e.g., "descriptive", "action-oriented", "dialogue-heavy").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated story continuation.
        """
        logger.info("Generating story continuation")
        
        # Prepare prompt
        prompt = f"""Continue the following story in a natural and engaging way. 
The continuation should be approximately {length} words.
"""
        
        if style:
            prompt += f"Write in a {style} style.\n"
        
        prompt += f"\nStory so far:\n{context}\n\nContinuation:"
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, int(length * 1.5))  # Estimate tokens from words
        
        # Generate text
        continuation = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Story continuation generated")
        return continuation.strip()
    
    async def generate_dialogue(self, characters: List[str], context: str, tone: Optional[str] = None, 
                               length: int = 300, **kwargs) -> str:
        """
        Generate dialogue between characters.
        
        Args:
            characters: List of character names.
            context: The context for the dialogue.
            tone: The tone of the dialogue (e.g., "tense", "humorous", "romantic").
            length: The approximate length of the dialogue in words.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated dialogue.
        """
        logger.info("Generating dialogue")
        
        # Prepare prompt
        prompt = f"""Generate a dialogue between {', '.join(characters[:-1])}{"" if len(characters) <= 1 else " and "}{characters[-1] if characters else ""}.
"""
        
        if tone:
            prompt += f"The tone should be {tone}.\n"
        
        prompt += f"""
Context: {context}

The dialogue should be approximately {length} words and should be formatted as:
CHARACTER: Dialogue text.
CHARACTER: Response.

Dialogue:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, int(length * 1.5))  # Estimate tokens from words
        
        # Generate text
        dialogue = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Dialogue generated")
        return dialogue.strip()
    
    async def enhance_description(self, original_text: str, enhancement_type: str = "sensory", 
                                 length_factor: float = 1.5, **kwargs) -> str:
        """
        Enhance a description with more details.
        
        Args:
            original_text: The original description.
            enhancement_type: The type of enhancement ("sensory", "emotional", "technical", "atmospheric").
            length_factor: How much longer the enhanced description should be (1.0 = same length).
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The enhanced description.
        """
        logger.info(f"Enhancing description with {enhancement_type} details")
        
        # Prepare prompt
        prompt = f"""Enhance the following description with more {enhancement_type} details.
The enhanced version should be approximately {length_factor:.1f}x the length of the original.

Original description:
{original_text}

Enhanced description:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, int(len(original_text.split()) * length_factor * 1.5))
        
        # Generate text
        enhanced = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Description enhanced")
        return enhanced.strip()
    
    async def generate_scene(self, setting: str, characters: List[str], mood: str, 
                            plot_points: Optional[List[str]] = None, length: int = 500, **kwargs) -> str:
        """
        Generate a complete scene.
        
        Args:
            setting: The setting for the scene.
            characters: List of characters in the scene.
            mood: The mood or atmosphere of the scene.
            plot_points: Key plot points to include.
            length: The approximate length of the scene in words.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated scene.
        """
        logger.info("Generating scene")
        
        # Prepare prompt
        prompt = f"""Generate a scene with the following elements:

Setting: {setting}
Characters: {', '.join(characters)}
Mood: {mood}
"""
        
        if plot_points:
            prompt += f"Plot points to include:\n"
            for i, point in enumerate(plot_points, 1):
                prompt += f"{i}. {point}\n"
        
        prompt += f"\nThe scene should be approximately {length} words and include both narrative and dialogue.\n\nScene:"
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, int(length * 1.5))  # Estimate tokens from words
        
        # Generate text
        scene = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Scene generated")
        return scene.strip()
    
    async def generate_creative_prompt(self, genre: Optional[str] = None, theme: Optional[str] = None, 
                                      elements: Optional[List[str]] = None, **kwargs) -> str:
        """
        Generate a creative writing prompt.
        
        Args:
            genre: The genre for the prompt.
            theme: The theme for the prompt.
            elements: Specific elements to include.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated creative prompt.
        """
        logger.info("Generating creative prompt")
        
        # Prepare prompt
        prompt = "Generate an inspiring and detailed creative writing prompt"
        
        if genre:
            prompt += f" in the {genre} genre"
        
        if theme:
            prompt += f" exploring the theme of {theme}"
        
        prompt += "."
        
        if elements:
            prompt += f" Include the following elements: {', '.join(elements)}."
        
        prompt += "\n\nCreative Writing Prompt:"
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 500  # Shorter for prompts
        
        # Generate text
        creative_prompt = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Creative prompt generated")
        return creative_prompt.strip()
    
    async def rewrite_text(self, original_text: str, style: str, preserve_meaning: bool = True, **kwargs) -> str:
        """
        Rewrite text in a different style while preserving meaning.
        
        Args:
            original_text: The original text.
            style: The target style (e.g., "formal", "casual", "poetic", "technical").
            preserve_meaning: Whether to strictly preserve the original meaning.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The rewritten text.
        """
        logger.info(f"Rewriting text in {style} style")
        
        # Prepare prompt
        prompt = f"""Rewrite the following text in a {style} style.
{"Preserve the original meaning as much as possible." if preserve_meaning else "Feel free to be creative while keeping the general idea."}

Original text:
{original_text}

Rewritten text:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, int(len(original_text.split()) * 1.5))
        
        # Generate text
        rewritten = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Text rewritten")
        return rewritten.strip()
    
    async def generate_character_dialogue(self, character_description: str, situation: str, 
                                         length: int = 200, **kwargs) -> str:
        """
        Generate dialogue for a specific character.
        
        Args:
            character_description: Description of the character.
            situation: The situation the character is in.
            length: The approximate length of the dialogue in words.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated character dialogue.
        """
        logger.info("Generating character dialogue")
        
        # Prepare prompt
        prompt = f"""Generate dialogue for a character with the following description:
{character_description}

The character is in this situation:
{situation}

The dialogue should be approximately {length} words and should sound authentic to this character's voice and personality.

Dialogue:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(1024, int(length * 1.5))  # Estimate tokens from words
        
        # Generate text
        dialogue = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Character dialogue generated")
        return dialogue.strip()
    
    async def generate_plot_twist(self, story_context: str, intensity: str = "medium", 
                                 foreshadowing: bool = True, **kwargs) -> str:
        """
        Generate a plot twist for a story.
        
        Args:
            story_context: The context of the story so far.
            intensity: The intensity of the twist ("mild", "medium", "major").
            foreshadowing: Whether to include suggestions for foreshadowing.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated plot twist, with optional foreshadowing suggestions.
        """
        logger.info(f"Generating {intensity} plot twist")
        
        # Prepare prompt
        prompt = f"""Based on the following story context, generate a {intensity} plot twist that would be surprising yet believable.

Story context:
{story_context}

{"Also include suggestions for how this twist could be foreshadowed earlier in the story." if foreshadowing else ""}

Plot twist:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 1000
        
        # Generate text
        twist = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Plot twist generated")
        return twist.strip()
    
    async def brainstorm_ideas(self, topic: str, number: int = 5, depth: str = "medium", **kwargs) -> List[str]:
        """
        Brainstorm ideas related to a topic.
        
        Args:
            topic: The topic to brainstorm about.
            number: The number of ideas to generate.
            depth: The depth of exploration ("brief", "medium", "detailed").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of brainstormed ideas.
        """
        logger.info(f"Brainstorming {number} ideas about {topic}")
        
        # Prepare prompt
        prompt = f"""Brainstorm {number} {depth} ideas related to the following topic:

Topic: {topic}

Format each idea with a number and a brief description. For {depth} depth, each idea should be a paragraph of appropriate length.

Ideas:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, number * (100 if depth == "brief" else 200 if depth == "medium" else 400))
        
        # Generate text
        ideas_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse ideas
        ideas = []
        pattern = r"(?:^|\n)(?:\d+\.\s*|\-\s*)(.*?)(?=\n\d+\.|\n\-|\Z)"
        matches = re.finditer(pattern, ideas_text, re.DOTALL)
        
        for match in matches:
            idea = match.group(1).strip()
            if idea:
                ideas.append(idea)
        
        # If parsing failed, just split by newlines and clean up
        if not ideas:
            ideas = [line.strip() for line in ideas_text.split("\n") if line.strip()]
        
        # Ensure we have the requested number of ideas
        ideas = ideas[:number]
        
        logger.debug(f"Generated {len(ideas)} ideas")
        return ideas
    
    async def close(self):
        """Close the text generator and its AI service."""
        logger.info("Closing text generator")
        await self.ai_service.close()
