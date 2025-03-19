#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Character Assistant

This module provides AI-powered character development features for RebelSCRIBE,
including character profile generation, development suggestions, consistency checking,
relationship mapping, and dialogue style analysis.
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Union, Tuple, Set

from src.utils.logging_utils import get_logger
from src.ai.ai_service import AIService
from src.backend.models.character import Character

logger = get_logger(__name__)


class CharacterAssistant:
    """
    Character assistant for RebelSCRIBE.
    
    This class provides methods for AI-powered character development,
    including profile generation, development suggestions, consistency checking,
    relationship mapping, and dialogue style analysis.
    """
    
    def __init__(self, ai_service: Optional[AIService] = None):
        """
        Initialize the character assistant.
        
        Args:
            ai_service: The AI service to use. If None, a new instance will be created.
        """
        logger.info("Initializing character assistant")
        
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
        
        logger.debug("Character assistant initialized")
    
    async def generate_character_profile(self, name: str, role: str, genre: str, 
                                        age: Optional[int] = None, gender: Optional[str] = None,
                                        detail_level: str = "medium", **kwargs) -> Dict[str, Any]:
        """
        Generate a character profile.
        
        Args:
            name: The character's name.
            role: The character's role (e.g., "protagonist", "antagonist", "supporting").
            genre: The genre of the story.
            age: The character's age (optional).
            gender: The character's gender (optional).
            detail_level: The level of detail ("brief", "medium", "detailed").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing the character profile.
        """
        logger.info(f"Generating {detail_level} character profile for {name}")
        
        # Prepare prompt
        prompt = f"""Generate a {detail_level} character profile for a {role} character named {name} in a {genre} story.
"""
        
        if age is not None:
            prompt += f"The character is {age} years old.\n"
        
        if gender:
            prompt += f"The character's gender is {gender}.\n"
        
        prompt += f"""
Include the following sections:
1. Physical appearance
2. Personality traits
3. Background/history
4. Motivations and goals
5. Strengths and weaknesses
6. Quirks and habits
7. Speech patterns
8. Relationships with other characters (general)

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 1500 if detail_level == "brief" else 2000 if detail_level == "medium" else 3000
        
        # Generate text
        profile_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            profile_text = profile_text[profile_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if profile_text.rfind("}") != -1:
                profile_text = profile_text[:profile_text.rfind("}")+1]
            
            profile = json.loads(profile_text)
            logger.debug("Character profile generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse character profile JSON: {e}")
            # Create a basic profile with the raw text
            profile = {
                "name": name,
                "role": role,
                "genre": genre,
                "raw_profile": profile_text
            }
        
        return profile
    
    async def generate_development_suggestions(self, character_profile: Dict[str, Any], 
                                             story_context: str, num_suggestions: int = 5, **kwargs) -> List[str]:
        """
        Generate character development suggestions.
        
        Args:
            character_profile: The character's profile.
            story_context: The context of the story.
            num_suggestions: The number of suggestions to generate.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of character development suggestions.
        """
        logger.info(f"Generating {num_suggestions} character development suggestions")
        
        # Extract character info
        name = character_profile.get("name", "the character")
        
        # Prepare prompt
        prompt = f"""Based on the following character profile and story context, generate {num_suggestions} suggestions for developing the character further.

Character Profile:
"""
        
        # Add profile details
        for key, value in character_profile.items():
            if key != "raw_profile" and isinstance(value, str):
                prompt += f"{key}: {value}\n"
        
        prompt += f"""
Story Context:
{story_context}

Provide {num_suggestions} specific, actionable suggestions for developing this character further. Each suggestion should include:
1. A brief description of the development opportunity
2. How it connects to the existing character traits
3. How it could impact the story

Format each suggestion as a numbered item.

Character Development Suggestions:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2048, num_suggestions * 300)
        
        # Generate text
        suggestions_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse suggestions
        suggestions = []
        pattern = r"(?:^|\n)(?:\d+\.\s*|\-\s*)(.*?)(?=\n\d+\.|\n\-|\Z)"
        matches = re.finditer(pattern, suggestions_text, re.DOTALL)
        
        for match in matches:
            suggestion = match.group(1).strip()
            if suggestion:
                suggestions.append(suggestion)
        
        # If parsing failed, just split by newlines and clean up
        if not suggestions:
            suggestions = [line.strip() for line in suggestions_text.split("\n") if line.strip()]
        
        # Ensure we have the requested number of suggestions
        suggestions = suggestions[:num_suggestions]
        
        logger.debug(f"Generated {len(suggestions)} character development suggestions")
        return suggestions
    
    async def check_character_consistency(self, character_profile: Dict[str, Any], 
                                        character_actions: List[str], **kwargs) -> Dict[str, Any]:
        """
        Check character consistency across actions/dialogue.
        
        Args:
            character_profile: The character's profile.
            character_actions: List of character actions or dialogue to check.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary with consistency analysis.
        """
        logger.info("Checking character consistency")
        
        # Extract character info
        name = character_profile.get("name", "the character")
        
        # Prepare prompt
        prompt = f"""Analyze the consistency of the character {name} based on their profile and their actions/dialogue in the story.

Character Profile:
"""
        
        # Add profile details
        for key, value in character_profile.items():
            if key != "raw_profile" and isinstance(value, str):
                prompt += f"{key}: {value}\n"
        
        prompt += f"""
Character Actions/Dialogue:
"""
        
        # Add actions/dialogue
        for i, action in enumerate(character_actions, 1):
            prompt += f"{i}. {action}\n"
        
        prompt += f"""
Provide a consistency analysis with the following sections:
1. Overall consistency rating (1-10)
2. Consistent elements (what actions align with the character profile)
3. Inconsistent elements (what actions seem out of character)
4. Suggestions for improving consistency

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 1500
        
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
            logger.debug("Character consistency analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse consistency analysis JSON: {e}")
            # Create a basic analysis with the raw text
            analysis = {
                "character_name": name,
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def map_character_relationships(self, characters: List[Dict[str, Any]], 
                                        story_context: str, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """
        Map relationships between characters.
        
        Args:
            characters: List of character profiles.
            story_context: The context of the story.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary mapping character names to their relationships.
        """
        logger.info(f"Mapping relationships between {len(characters)} characters")
        
        # Prepare prompt
        prompt = f"""Analyze the relationships between the following characters based on their profiles and the story context.

Characters:
"""
        
        # Add character summaries
        for i, character in enumerate(characters, 1):
            name = character.get("name", f"Character {i}")
            prompt += f"{i}. {name}: "
            
            # Add brief character description
            if "personality_traits" in character:
                prompt += f"{character['personality_traits']} "
            if "role" in character:
                prompt += f"({character['role']}) "
            
            prompt += "\n"
        
        prompt += f"""
Story Context:
{story_context}

For each character, identify their relationships with all other characters. Include:
1. The nature of the relationship (e.g., friend, enemy, mentor, etc.)
2. The dynamics of the relationship (e.g., power dynamics, emotional connection)
3. Potential for conflict or alliance
4. How the relationship might evolve

Format the response as a JSON object where keys are character names and values are arrays of relationship objects.
Each relationship object should have: "target" (the other character's name), "relationship_type", "dynamics", "conflict_potential", and "evolution".
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(4000, len(characters) * len(characters) * 100)
        
        # Generate text
        relationships_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            relationships_text = relationships_text[relationships_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if relationships_text.rfind("}") != -1:
                relationships_text = relationships_text[:relationships_text.rfind("}")+1]
            
            relationships = json.loads(relationships_text)
            logger.debug("Character relationships mapped and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse relationships JSON: {e}")
            # Create a basic relationships map with the raw text
            relationships = {
                "raw_relationships": relationships_text
            }
        
        return relationships
    
    async def analyze_dialogue_style(self, character_profile: Dict[str, Any], 
                                    dialogue_samples: List[str], **kwargs) -> Dict[str, Any]:
        """
        Analyze a character's dialogue style.
        
        Args:
            character_profile: The character's profile.
            dialogue_samples: List of dialogue samples from the character.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary with dialogue style analysis.
        """
        logger.info("Analyzing character dialogue style")
        
        # Extract character info
        name = character_profile.get("name", "the character")
        
        # Prepare prompt
        prompt = f"""Analyze the dialogue style of the character {name} based on their profile and dialogue samples.

Character Profile:
"""
        
        # Add profile details
        for key, value in character_profile.items():
            if key != "raw_profile" and isinstance(value, str):
                prompt += f"{key}: {value}\n"
        
        prompt += f"""
Dialogue Samples:
"""
        
        # Add dialogue samples
        for i, sample in enumerate(dialogue_samples, 1):
            prompt += f'{i}. "{sample}"\n'
        
        prompt += f"""
Provide a dialogue style analysis with the following sections:
1. Vocabulary and word choice
2. Sentence structure and length
3. Speech patterns and verbal tics
4. Emotional expression
5. Formality level
6. Cultural or educational influences
7. Consistency with character profile
8. Suggestions for making dialogue more distinctive

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 1500
        
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
            logger.debug("Dialogue style analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dialogue analysis JSON: {e}")
            # Create a basic analysis with the raw text
            analysis = {
                "character_name": name,
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def generate_character_arc(self, character_profile: Dict[str, Any], 
                                   story_context: str, num_stages: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate a character arc with multiple stages.
        
        Args:
            character_profile: The character's profile.
            story_context: The context of the story.
            num_stages: The number of stages in the character arc.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries representing stages in the character arc.
        """
        logger.info(f"Generating {num_stages}-stage character arc")
        
        # Extract character info
        name = character_profile.get("name", "the character")
        
        # Prepare prompt
        prompt = f"""Create a {num_stages}-stage character arc for {name} based on their profile and the story context.

Character Profile:
"""
        
        # Add profile details
        for key, value in character_profile.items():
            if key != "raw_profile" and isinstance(value, str):
                prompt += f"{key}: {value}\n"
        
        prompt += f"""
Story Context:
{story_context}

Design a {num_stages}-stage character arc that shows meaningful growth and development.
For each stage, include:
1. The character's state at this stage
2. Key events or catalysts
3. Internal and external conflicts
4. Changes from the previous stage
5. Impact on the story

Format the response as a JSON array of stage objects, each with the above sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(3000, num_stages * 400)
        
        # Generate text
        arc_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            arc_text = arc_text[arc_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if arc_text.rfind("]") != -1:
                arc_text = arc_text[:arc_text.rfind("]")+1]
            
            arc = json.loads(arc_text)
            logger.debug("Character arc generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse character arc JSON: {e}")
            # Create a basic arc with the raw text
            arc = [{"stage": i+1, "description": f"Stage {i+1}"} for i in range(num_stages)]
            arc.append({"raw_arc": arc_text})
        
        return arc
    
    async def generate_backstory(self, character_profile: Dict[str, Any], 
                               detail_level: str = "medium", focus_areas: Optional[List[str]] = None, 
                               **kwargs) -> str:
        """
        Generate a detailed backstory for a character.
        
        Args:
            character_profile: The character's profile.
            detail_level: The level of detail ("brief", "medium", "detailed").
            focus_areas: Specific areas to focus on (e.g., "childhood", "relationships", "trauma").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            The generated backstory.
        """
        logger.info(f"Generating {detail_level} character backstory")
        
        # Extract character info
        name = character_profile.get("name", "the character")
        
        # Prepare prompt
        prompt = f"""Generate a {detail_level} backstory for the character {name} based on their profile.

Character Profile:
"""
        
        # Add profile details
        for key, value in character_profile.items():
            if key != "raw_profile" and isinstance(value, str):
                prompt += f"{key}: {value}\n"
        
        if focus_areas:
            prompt += f"\nFocus particularly on these aspects of the character's past: {', '.join(focus_areas)}.\n"
        
        prompt += f"""
The backstory should be coherent with the existing profile and add depth to the character.
It should explain how the character developed their current traits, motivations, and relationships.

Backstory:
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 1000 if detail_level == "brief" else 2000 if detail_level == "medium" else 3000
        
        # Generate text
        backstory = await self.ai_service.generate_text(prompt, **params)
        
        logger.debug("Character backstory generated")
        return backstory.strip()
    
    async def generate_character_flaws(self, character_profile: Dict[str, Any], 
                                     num_flaws: int = 3, story_impact: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate character flaws that create interesting story opportunities.
        
        Args:
            character_profile: The character's profile.
            num_flaws: The number of flaws to generate.
            story_impact: Whether to include how each flaw impacts the story.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries representing character flaws.
        """
        logger.info(f"Generating {num_flaws} character flaws")
        
        # Extract character info
        name = character_profile.get("name", "the character")
        
        # Prepare prompt
        prompt = f"""Generate {num_flaws} interesting and meaningful character flaws for {name} based on their profile.

Character Profile:
"""
        
        # Add profile details
        for key, value in character_profile.items():
            if key != "raw_profile" and isinstance(value, str):
                prompt += f"{key}: {value}\n"
        
        prompt += f"""
For each flaw, include:
1. A name or short description of the flaw
2. How this flaw manifests in the character's behavior
3. The underlying cause or origin of this flaw
"""
        
        if story_impact:
            prompt += "4. How this flaw could create interesting conflicts or story opportunities\n"
        
        prompt += f"""
The flaws should be consistent with the character's existing traits but add complexity and depth.
Format the response as a JSON array of flaw objects, each with the above sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(2000, num_flaws * 300)
        
        # Generate text
        flaws_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            flaws_text = flaws_text[flaws_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if flaws_text.rfind("]") != -1:
                flaws_text = flaws_text[:flaws_text.rfind("]")+1]
            
            flaws = json.loads(flaws_text)
            logger.debug("Character flaws generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse character flaws JSON: {e}")
            # Create a basic flaws list with the raw text
            flaws = [{"flaw": f"Flaw {i+1}"} for i in range(num_flaws)]
            flaws.append({"raw_flaws": flaws_text})
        
        return flaws
    
    async def close(self):
        """Close the character assistant and its AI service."""
        logger.info("Closing character assistant")
        await self.ai_service.close()
