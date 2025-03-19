#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - AI Examples

This script demonstrates how to use the AI components in RebelSCRIBE.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.ai_service import AIService, AIProvider, AIModelType
from ai.text_generator import TextGenerator
from ai.character_assistant import CharacterAssistant
from ai.plot_assistant import PlotAssistant
from ai.editing_assistant import EditingAssistant

from utils.logging_utils import get_logger

logger = get_logger(__name__)


async def demonstrate_ai_service():
    """Demonstrate the AI service."""
    print("\n=== AI Service Example ===")
    
    # Create AI service
    ai_service = AIService()
    
    # Set provider (if you have API keys)
    try:
        # Try to use OpenAI (requires API key)
        ai_service.set_provider(AIProvider.OPENAI)
        print(f"Using provider: {ai_service.provider.value}")
    except Exception as e:
        print(f"Could not set OpenAI provider: {e}")
        print("Using default provider")
    
    # Generate text
    prompt = "Write a short paragraph about a writer using an AI assistant."
    print(f"Prompt: {prompt}")
    
    try:
        response = await ai_service.generate_text(prompt, max_tokens=100)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error generating text: {e}")
    
    # Close the service
    await ai_service.close()


async def demonstrate_text_generator():
    """Demonstrate the text generator."""
    print("\n=== Text Generator Example ===")
    
    # Create text generator
    text_generator = TextGenerator()
    
    # Generate story continuation
    context = """
    Sarah stared at the blank page on her screen. She had been trying to start her novel for weeks, 
    but the words wouldn't come. Just as she was about to give up for the day, her computer made 
    an unusual sound.
    """
    
    print("Story context:")
    print(context)
    
    try:
        continuation = await text_generator.continue_story(
            context=context,
            length=150,
            style="suspenseful"
        )
        
        print("\nGenerated continuation:")
        print(continuation)
    except Exception as e:
        print(f"Error generating story continuation: {e}")
    
    # Generate dialogue
    try:
        dialogue = await text_generator.generate_dialogue(
            characters=["Sarah", "AI Assistant"],
            context="Sarah is frustrated with her writer's block, and her AI assistant is trying to help.",
            tone="humorous",
            length=150
        )
        
        print("\nGenerated dialogue:")
        print(dialogue)
    except Exception as e:
        print(f"Error generating dialogue: {e}")
    
    # Close the text generator
    await text_generator.close()


async def demonstrate_character_assistant():
    """Demonstrate the character assistant."""
    print("\n=== Character Assistant Example ===")
    
    # Create character assistant
    character_assistant = CharacterAssistant()
    
    # Generate character profile
    try:
        profile = await character_assistant.generate_character_profile(
            name="Alex Chen",
            role="protagonist",
            genre="science fiction",
            age=32,
            gender="non-binary",
            detail_level="medium"
        )
        
        print("Generated character profile:")
        for key, value in profile.items():
            if key != "raw_profile" and isinstance(value, str):
                print(f"{key}: {value}")
        print()
    except Exception as e:
        print(f"Error generating character profile: {e}")
    
    # Generate character development suggestions
    try:
        story_context = "Alex is a brilliant scientist who discovers a way to communicate with parallel universes."
        
        suggestions = await character_assistant.generate_development_suggestions(
            character_profile=profile,
            story_context=story_context,
            num_suggestions=2
        )
        
        print("Character development suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
        print()
    except Exception as e:
        print(f"Error generating character development suggestions: {e}")
    
    # Close the character assistant
    await character_assistant.close()


async def demonstrate_plot_assistant():
    """Demonstrate the plot assistant."""
    print("\n=== Plot Assistant Example ===")
    
    # Create plot assistant
    plot_assistant = PlotAssistant()
    
    # Generate plot outline
    try:
        premise = "A scientist discovers a way to communicate with parallel universes, but soon realizes that something is crossing over."
        
        outline = await plot_assistant.generate_plot_outline(
            premise=premise,
            genre="science fiction thriller",
            num_acts=3,
            detail_level="brief"
        )
        
        print("Generated plot outline:")
        print(f"Title: {outline.get('title', 'Untitled')}")
        print(f"Logline: {outline.get('logline', 'No logline')}")
        
        acts = outline.get("acts", [])
        for act in acts:
            print(f"\nAct {act.get('act_number', '?')}: {act.get('title', 'Untitled')}")
            print(f"Summary: {act.get('summary', 'No summary')}")
        print()
    except Exception as e:
        print(f"Error generating plot outline: {e}")
    
    # Generate plot twist suggestions
    try:
        twists = await plot_assistant.suggest_plot_twists(
            plot_outline=outline,
            num_twists=1,
            twist_type="revelation"
        )
        
        print("Plot twist suggestion:")
        for twist in twists:
            print(f"Description: {twist.get('description', 'No description')}")
            print(f"Impact: {twist.get('impact', 'No impact')}")
        print()
    except Exception as e:
        print(f"Error generating plot twist suggestions: {e}")
    
    # Close the plot assistant
    await plot_assistant.close()


async def demonstrate_editing_assistant():
    """Demonstrate the editing assistant."""
    print("\n=== Editing Assistant Example ===")
    
    # Create editing assistant
    editing_assistant = EditingAssistant()
    
    # Sample text with issues
    text = """
    Sarah stared at the blank page on her screen. She had been trying to start her novel for weeks, 
    but the words wouldn't come. She was frustrated. She was about to give up for the day, when her 
    computer made an unusual sound. It was strange. She was confused.
    """
    
    print("Original text:")
    print(text)
    
    # Analyze readability
    try:
        readability = await editing_assistant.analyze_readability(
            text=text,
            target_audience="general"
        )
        
        print("\nReadability analysis:")
        metrics = readability.get("basic_metrics", {})
        print(f"Word count: {metrics.get('word_count', 0)}")
        print(f"Sentence count: {metrics.get('sentence_count', 0)}")
        print(f"Average sentence length: {metrics.get('avg_sentence_length', 0):.2f} words")
    except Exception as e:
        print(f"Error analyzing readability: {e}")
    
    # Improve word choice
    try:
        improvements = await editing_assistant.improve_word_choice(
            text=text,
            focus="emotional impact"
        )
        
        print("\nWord choice improvement suggestions:")
        if "weak_or_overused_words" in improvements:
            for item in improvements["weak_or_overused_words"][:2]:  # Show first 2 suggestions
                if isinstance(item, dict):
                    print(f"Original: {item.get('original', '')}")
                    print(f"Suggestion: {item.get('suggestion', '')}")
    except Exception as e:
        print(f"Error improving word choice: {e}")
    
    # Edit text
    try:
        edit = await editing_assistant.edit_text(
            text=text,
            edit_type="conciseness",
            intensity="medium"
        )
        
        print("\nEdited text:")
        print(edit.get("edited_text", "No edited text"))
    except Exception as e:
        print(f"Error editing text: {e}")
    
    # Close the editing assistant
    await editing_assistant.close()


async def main():
    """Run all demonstrations."""
    print("RebelSCRIBE AI Components Demonstration")
    print("======================================")
    
    try:
        await demonstrate_ai_service()
        await demonstrate_text_generator()
        await demonstrate_character_assistant()
        await demonstrate_plot_assistant()
        await demonstrate_editing_assistant()
    except Exception as e:
        print(f"Error in demonstration: {e}")


if __name__ == "__main__":
    # Check if API keys are set
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: No API keys found in environment variables.")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to use the respective services.")
        print("Some examples may not work without API keys.")
        print()
    
    # Run the demonstration
    asyncio.run(main())
