# RebelSCRIBE AI Module

This module provides AI-powered features for RebelSCRIBE, including text generation, character development, plot assistance, and editing suggestions.

## Components

### AIService (`ai_service.py`)

The core service that handles communication with AI providers.

- Supports multiple AI providers (OpenAI, Anthropic, Google, local models)
- Manages API keys and authentication
- Handles request formatting and response parsing
- Implements error handling and rate limiting
- Tracks usage statistics

```python
from ai.ai_service import AIService, AIProvider, AIModelType

# Create AI service
ai_service = AIService()

# Set provider (if you have API keys)
ai_service.set_provider(AIProvider.OPENAI)

# Generate text
response = await ai_service.generate_text("Write a short story about a robot.")

# Generate embeddings
embedding = await ai_service.generate_embedding("Semantic search vector")

# Close the service when done
await ai_service.close()
```

### TextGenerator (`text_generator.py`)

Provides text generation capabilities for creative writing.

- Story continuation
- Dialogue generation
- Description enhancement
- Scene generation
- Creative prompts

```python
from ai.text_generator import TextGenerator

# Create text generator
text_generator = TextGenerator()

# Generate story continuation
continuation = await text_generator.continue_story(
    context="Once upon a time in a distant galaxy...",
    length=500,
    style="descriptive"
)

# Generate dialogue
dialogue = await text_generator.generate_dialogue(
    characters=["Captain", "First Officer"],
    context="The spaceship is about to enter a dangerous nebula.",
    tone="tense"
)

# Close the generator when done
await text_generator.close()
```

### CharacterAssistant (`character_assistant.py`)

Provides AI-powered character development features.

- Character profile generation
- Character development suggestions
- Character consistency checking
- Character relationship mapping
- Character dialogue style analysis

```python
from ai.character_assistant import CharacterAssistant

# Create character assistant
character_assistant = CharacterAssistant()

# Generate character profile
profile = await character_assistant.generate_character_profile(
    name="Alex Chen",
    role="protagonist",
    genre="science fiction",
    age=32,
    gender="non-binary"
)

# Generate character development suggestions
suggestions = await character_assistant.generate_development_suggestions(
    character_profile=profile,
    story_context="Alex is a brilliant scientist who discovers a way to communicate with parallel universes."
)

# Close the assistant when done
await character_assistant.close()
```

### PlotAssistant (`plot_assistant.py`)

Provides AI-powered plot development features.

- Plot outline generation
- Plot hole detection
- Plot twist suggestions
- Story arc analysis
- Pacing recommendations

```python
from ai.plot_assistant import PlotAssistant

# Create plot assistant
plot_assistant = PlotAssistant()

# Generate plot outline
outline = await plot_assistant.generate_plot_outline(
    premise="A scientist discovers a way to communicate with parallel universes.",
    genre="science fiction thriller",
    num_acts=3
)

# Detect plot holes
plot_holes = await plot_assistant.detect_plot_holes(
    plot_outline=outline
)

# Close the assistant when done
await plot_assistant.close()
```

### EditingAssistant (`editing_assistant.py`)

Provides AI-powered editing and improvement features.

- Grammar and style checking
- Readability analysis
- Tone consistency checking
- Rewriting suggestions
- Word choice improvements

```python
from ai.editing_assistant import EditingAssistant

# Create editing assistant
editing_assistant = EditingAssistant()

# Check grammar and style
analysis = await editing_assistant.check_grammar_and_style(
    text="The scientist were excited about there discovery.",
    style_guide="Chicago"
)

# Analyze readability
readability = await editing_assistant.analyze_readability(
    text="The quantum fluctuations in the subatomic particles caused a cascading effect...",
    target_audience="general"
)

# Close the assistant when done
await editing_assistant.close()
```

## Examples

See the `examples/ai_examples.py` script for complete examples of how to use each component.

## API Keys

To use external AI providers, you need to set up API keys:

1. **OpenAI**: Set the `OPENAI_API_KEY` environment variable or add it to the configuration file.
2. **Anthropic**: Set the `ANTHROPIC_API_KEY` environment variable or add it to the configuration file.
3. **Google**: Set the `GOOGLE_API_KEY` environment variable or add it to the configuration file.

## Configuration

The AI module can be configured in the `config.yaml` file:

```yaml
ai:
  provider: openai  # Default provider (openai, anthropic, google, local)
  api_keys:
    openai: "your-api-key"  # Optional, can use environment variable instead
    anthropic: "your-api-key"
    google: "your-api-key"
  models:
    openai:
      completion: "gpt-4-turbo"
      chat: "gpt-4-turbo"
      embedding: "text-embedding-3-small"
    anthropic:
      completion: "claude-3-opus-20240229"
      chat: "claude-3-opus-20240229"
  rate_limits:
    openai: 10  # Requests per second
    anthropic: 5
    google: 10
```

## Local Models (Optional)

For offline use or to reduce API costs, you can set up local models:

1. Install the required dependencies: `pip install llama-cpp-python sentence-transformers`
2. Download model weights (see documentation for links)
3. Configure the local model in `config.yaml`
4. Set the provider to `local`: `ai_service.set_provider(AIProvider.LOCAL)`
