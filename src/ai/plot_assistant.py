#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Plot Assistant

This module provides AI-powered plot development features for RebelSCRIBE,
including plot outline generation, plot hole detection, plot twist suggestions,
story arc analysis, and pacing recommendations.
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Union, Tuple, Set

from src.utils.logging_utils import get_logger
from src.ai.ai_service import AIService

logger = get_logger(__name__)


class PlotAssistant:
    """
    Plot assistant for RebelSCRIBE.
    
    This class provides methods for AI-powered plot development,
    including outline generation, plot hole detection, plot twist suggestions,
    story arc analysis, and pacing recommendations.
    """
    
    def __init__(self, ai_service: Optional[AIService] = None):
        """
        Initialize the plot assistant.
        
        Args:
            ai_service: The AI service to use. If None, a new instance will be created.
        """
        logger.info("Initializing plot assistant")
        
        # Set AI service
        self.ai_service = ai_service or AIService()
        
        # Default parameters
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 1500,
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5
        }
        
        logger.debug("Plot assistant initialized")
    
    async def generate_plot_outline(self, premise: str, genre: str, num_acts: int = 3,
                                  characters: Optional[List[Dict[str, Any]]] = None,
                                  settings: Optional[List[str]] = None,
                                  themes: Optional[List[str]] = None,
                                  detail_level: str = "medium", **kwargs) -> Dict[str, Any]:
        """
        Generate a plot outline.
        
        Args:
            premise: The basic premise or concept for the story.
            genre: The genre of the story.
            num_acts: The number of acts in the story structure.
            characters: List of character profiles (optional).
            settings: List of settings or locations (optional).
            themes: List of themes to explore (optional).
            detail_level: The level of detail ("brief", "medium", "detailed").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing the plot outline.
        """
        logger.info(f"Generating {detail_level} plot outline with {num_acts} acts")
        
        # Prepare prompt
        prompt = f"""Generate a {detail_level} plot outline for a {genre} story with the following premise:
"{premise}"

Structure the outline with {num_acts} acts.
"""
        
        if characters:
            prompt += "\nMain Characters:\n"
            for i, character in enumerate(characters, 1):
                name = character.get("name", f"Character {i}")
                role = character.get("role", "")
                prompt += f"{i}. {name} - {role}\n"
        
        if settings:
            prompt += f"\nSettings: {', '.join(settings)}\n"
        
        if themes:
            prompt += f"\nThemes to explore: {', '.join(themes)}\n"
        
        prompt += f"""
For each act, include:
1. The main events and plot points
2. Character development and arcs
3. Conflicts and obstacles
4. Key revelations or twists
5. Emotional beats and tone

Format the response as a JSON object with the following structure:
{{
  "title": "Suggested title",
  "logline": "One-sentence summary",
  "acts": [
    {{
      "act_number": 1,
      "title": "Act title",
      "summary": "Brief summary",
      "events": ["Event 1", "Event 2", ...],
      "character_arcs": {{"Character Name": "Development in this act", ...}},
      "conflicts": ["Conflict 1", "Conflict 2", ...],
      "revelations": ["Revelation 1", "Revelation 2", ...],
      "emotional_beats": ["Beat 1", "Beat 2", ...]
    }},
    ...
  ],
  "themes": ["Theme 1", "Theme 2", ...],
  "potential_subplots": ["Subplot 1", "Subplot 2", ...]
}}
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 1500 if detail_level == "brief" else 2500 if detail_level == "medium" else 4000
        
        # Generate text
        outline_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening brace
            outline_text = outline_text[outline_text.find("{"):]
            # Remove any non-JSON text after the closing brace
            if outline_text.rfind("}") != -1:
                outline_text = outline_text[:outline_text.rfind("}")+1]
            
            outline = json.loads(outline_text)
            logger.debug("Plot outline generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plot outline JSON: {e}")
            # Create a basic outline with the raw text
            outline = {
                "premise": premise,
                "genre": genre,
                "raw_outline": outline_text
            }
        
        return outline
    
    async def detect_plot_holes(self, plot_outline: Dict[str, Any], 
                              story_content: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Detect potential plot holes and inconsistencies.
        
        Args:
            plot_outline: The plot outline.
            story_content: The actual story content (optional).
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries describing potential plot holes.
        """
        logger.info("Detecting plot holes")
        
        # Prepare prompt
        prompt = "Analyze the following plot outline for potential plot holes, inconsistencies, and logical problems:\n\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        if story_content:
            prompt += f"\n\nAdditional story content:\n{story_content}\n"
        
        prompt += """
Identify any plot holes, logical inconsistencies, or narrative problems. For each issue, provide:
1. A description of the plot hole or inconsistency
2. Why it's problematic for the story
3. Possible solutions to fix it

Format the response as a JSON array of plot hole objects, each with "description", "problem", and "solutions" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2000
        
        # Generate text
        holes_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            holes_text = holes_text[holes_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if holes_text.rfind("]") != -1:
                holes_text = holes_text[:holes_text.rfind("]")+1]
            
            plot_holes = json.loads(holes_text)
            logger.debug(f"Detected {len(plot_holes)} plot holes")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plot holes JSON: {e}")
            # Create a basic plot holes list with the raw text
            plot_holes = [{
                "description": "Failed to parse plot holes",
                "problem": "JSON parsing error",
                "solutions": ["Review the raw output"],
                "raw_output": holes_text
            }]
        
        return plot_holes
    
    async def suggest_plot_twists(self, plot_outline: Dict[str, Any], 
                                num_twists: int = 3, twist_type: Optional[str] = None,
                                placement: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Suggest potential plot twists.
        
        Args:
            plot_outline: The plot outline.
            num_twists: The number of twist suggestions to generate.
            twist_type: The type of twist (e.g., "revelation", "betrayal", "reversal").
            placement: Where in the story to place the twist (e.g., "midpoint", "climax").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries describing potential plot twists.
        """
        logger.info(f"Generating {num_twists} plot twist suggestions")
        
        # Prepare prompt
        prompt = f"Based on the following plot outline, suggest {num_twists} potential plot twists"
        
        if twist_type:
            prompt += f" involving {twist_type}"
        
        if placement:
            prompt += f" at the {placement} of the story"
        
        prompt += ":\n\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        prompt += f"""

For each plot twist suggestion, provide:
1. A brief description of the twist
2. How it would impact the story and characters
3. How to set it up earlier in the story (foreshadowing)
4. Why it would be effective and surprising

The twists should be surprising but believable within the context of the story.
Format the response as a JSON array of twist objects, each with "description", "impact", "setup", and "effectiveness" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(3000, num_twists * 500)
        
        # Generate text
        twists_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            twists_text = twists_text[twists_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if twists_text.rfind("]") != -1:
                twists_text = twists_text[:twists_text.rfind("]")+1]
            
            plot_twists = json.loads(twists_text)
            logger.debug(f"Generated {len(plot_twists)} plot twist suggestions")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plot twists JSON: {e}")
            # Create a basic plot twists list with the raw text
            plot_twists = [{
                "description": f"Plot Twist {i+1}",
                "raw_output": twists_text
            } for i in range(num_twists)]
        
        return plot_twists
    
    async def analyze_story_arc(self, plot_outline: Dict[str, Any], 
                              story_content: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze the story arc for pacing, tension, and emotional impact.
        
        Args:
            plot_outline: The plot outline.
            story_content: The actual story content (optional).
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary containing the story arc analysis.
        """
        logger.info("Analyzing story arc")
        
        # Prepare prompt
        prompt = "Analyze the following plot outline for story arc, pacing, tension, and emotional impact:\n\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        if story_content:
            prompt += f"\n\nAdditional story content:\n{story_content}\n"
        
        prompt += """
Provide a comprehensive analysis of the story arc with the following sections:
1. Overall arc structure and effectiveness
2. Pacing analysis (identifying slow or rushed sections)
3. Tension graph (how tension rises and falls throughout the story)
4. Emotional impact assessment
5. Key turning points and their effectiveness
6. Recommendations for improvement

Format the response as a JSON object with these sections as keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2500
        
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
            logger.debug("Story arc analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse story arc analysis JSON: {e}")
            # Create a basic analysis with the raw text
            analysis = {
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def recommend_pacing_adjustments(self, plot_outline: Dict[str, Any], 
                                         story_content: Optional[str] = None,
                                         target_pacing: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Recommend pacing adjustments for the story.
        
        Args:
            plot_outline: The plot outline.
            story_content: The actual story content (optional).
            target_pacing: The desired pacing style (e.g., "fast", "balanced", "deliberate").
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries containing pacing recommendations.
        """
        logger.info("Generating pacing recommendations")
        
        # Prepare prompt
        prompt = "Analyze the pacing of the following plot outline"
        
        if target_pacing:
            prompt += f" and recommend adjustments to achieve a {target_pacing} pacing style"
        
        prompt += ":\n\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        if story_content:
            prompt += f"\n\nAdditional story content:\n{story_content}\n"
        
        prompt += """
Provide specific recommendations for adjusting the pacing of the story. For each recommendation, include:
1. The section or element that needs adjustment
2. The current pacing issue (too slow, too fast, uneven)
3. Specific changes to improve the pacing
4. How this change would affect the overall story

Format the response as a JSON array of recommendation objects, each with "section", "issue", "changes", and "effect" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = 2000
        
        # Generate text
        recommendations_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            recommendations_text = recommendations_text[recommendations_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if recommendations_text.rfind("]") != -1:
                recommendations_text = recommendations_text[:recommendations_text.rfind("]")+1]
            
            recommendations = json.loads(recommendations_text)
            logger.debug(f"Generated {len(recommendations)} pacing recommendations")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pacing recommendations JSON: {e}")
            # Create a basic recommendations list with the raw text
            recommendations = [{
                "section": "Overall story",
                "raw_output": recommendations_text
            }]
        
        return recommendations
    
    async def generate_subplot_ideas(self, plot_outline: Dict[str, Any], 
                                   characters: Optional[List[Dict[str, Any]]] = None,
                                   num_subplots: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate subplot ideas that complement the main plot.
        
        Args:
            plot_outline: The plot outline.
            characters: List of character profiles (optional).
            num_subplots: The number of subplot ideas to generate.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries containing subplot ideas.
        """
        logger.info(f"Generating {num_subplots} subplot ideas")
        
        # Prepare prompt
        prompt = f"Based on the following plot outline, generate {num_subplots} subplot ideas that would complement and enhance the main story:\n\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        if characters:
            prompt += "\n\nMain Characters:\n"
            for i, character in enumerate(characters, 1):
                name = character.get("name", f"Character {i}")
                role = character.get("role", "")
                prompt += f"{i}. {name} - {role}\n"
        
        prompt += f"""

For each subplot idea, provide:
1. A title or brief description
2. The characters involved
3. How it connects to the main plot
4. Key events or beats in the subplot
5. How it enhances themes or character development

The subplots should feel integrated with the main story while adding depth and complexity.
Format the response as a JSON array of subplot objects, each with "title", "characters", "connection", "events", and "enhancement" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(3000, num_subplots * 500)
        
        # Generate text
        subplots_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            subplots_text = subplots_text[subplots_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if subplots_text.rfind("]") != -1:
                subplots_text = subplots_text[:subplots_text.rfind("]")+1]
            
            subplots = json.loads(subplots_text)
            logger.debug(f"Generated {len(subplots)} subplot ideas")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse subplot ideas JSON: {e}")
            # Create a basic subplots list with the raw text
            subplots = [{
                "title": f"Subplot {i+1}",
                "raw_output": subplots_text
            } for i in range(num_subplots)]
        
        return subplots
    
    async def analyze_theme_development(self, plot_outline: Dict[str, Any], 
                                      themes: List[str], **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze how themes are developed throughout the story.
        
        Args:
            plot_outline: The plot outline.
            themes: List of themes to analyze.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A dictionary mapping themes to their development analysis.
        """
        logger.info(f"Analyzing development of {len(themes)} themes")
        
        # Prepare prompt
        prompt = f"Analyze how the following themes are developed throughout this plot outline:\n\nThemes: {', '.join(themes)}\n\nPlot Outline:\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        prompt += f"""

For each theme, analyze:
1. How the theme is introduced
2. Key moments where the theme is developed or explored
3. How characters embody or interact with the theme
4. The theme's progression throughout the story
5. The final statement or conclusion about the theme
6. Suggestions for strengthening the theme's development

Format the response as a JSON object where keys are theme names and values are arrays of analysis objects.
Each analysis object should have "aspect" (e.g., "introduction", "key_moments", etc.) and "analysis" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(3000, len(themes) * 500)
        
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
            logger.debug("Theme development analysis generated and parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse theme analysis JSON: {e}")
            # Create a basic analysis with the raw text
            analysis = {
                theme: [{"aspect": "raw_analysis", "analysis": analysis_text}] for theme in themes
            }
        
        return analysis
    
    async def generate_scene_ideas(self, plot_outline: Dict[str, Any], 
                                 plot_point: str, num_ideas: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate scene ideas for a specific plot point.
        
        Args:
            plot_outline: The plot outline.
            plot_point: The plot point to generate scene ideas for.
            num_ideas: The number of scene ideas to generate.
            **kwargs: Additional parameters for the AI request.
            
        Returns:
            A list of dictionaries containing scene ideas.
        """
        logger.info(f"Generating {num_ideas} scene ideas for plot point: {plot_point}")
        
        # Prepare prompt
        prompt = f"Based on the following plot outline, generate {num_ideas} different scene ideas for this plot point: \"{plot_point}\"\n\n"
        
        # Add plot outline
        if "raw_outline" in plot_outline:
            prompt += plot_outline["raw_outline"]
        else:
            prompt += json.dumps(plot_outline, indent=2)
        
        prompt += f"""

For each scene idea, provide:
1. A brief description of the scene
2. The setting and atmosphere
3. Characters involved and their objectives
4. Key actions, dialogue, or moments
5. How it advances the plot or character development
6. The emotional tone or impact

Format the response as a JSON array of scene objects, each with "description", "setting", "characters", "key_moments", "advancement", and "tone" keys.
"""
        
        # Set parameters
        params = self.default_params.copy()
        params.update(kwargs)
        params["max_tokens"] = min(3000, num_ideas * 500)
        
        # Generate text
        scenes_text = await self.ai_service.generate_text(prompt, **params)
        
        # Parse JSON
        try:
            # Clean up the text to ensure it's valid JSON
            # Remove any non-JSON text before the opening bracket
            scenes_text = scenes_text[scenes_text.find("["):]
            # Remove any non-JSON text after the closing bracket
            if scenes_text.rfind("]") != -1:
                scenes_text = scenes_text[:scenes_text.rfind("]")+1]
            
            scenes = json.loads(scenes_text)
            logger.debug(f"Generated {len(scenes)} scene ideas")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scene ideas JSON: {e}")
            # Create a basic scenes list with the raw text
            scenes = [{
                "description": f"Scene Idea {i+1}",
                "raw_output": scenes_text
            } for i in range(num_ideas)]
        
        return scenes
    
    async def close(self):
        """Close the plot assistant and its AI service."""
        logger.info("Closing plot assistant")
        await self.ai_service.close()
