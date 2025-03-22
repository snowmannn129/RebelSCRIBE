# RebelSCRIBE

RebelSCRIBE is a hybrid documentation and novel writing program that combines the functionality of a documentation management system with a novel writing program.

## Features

- **Documentation Management**: Extract documentation from source code, generate documentation in various formats, and integrate with other RebelSUITE components.
- **Novel Writing**: Create and manage novel projects, with support for chapters, scenes, characters, and more.
- **AI-Assisted Content Creation**: Generate text, character profiles, and plot outlines using AI.
- **Unified Interface**: Switch between documentation and novel writing modes with a tabbed interface.
- **Theme Customization**: Customize the appearance of the application with themes.
- **Cross-Platform**: Works on Windows, macOS, and Linux.

## Installation

### Prerequisites

- Python 3.8 or higher
- PyQt6
- Other dependencies listed in `requirements.txt`

### Install from Source

1. Clone the repository:

```bash
git clone https://github.com/rebelsuite/rebelscribe.git
cd rebelscribe
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python run_hybrid.py
```

### Install with pip

```bash
pip install rebelscribe
```

## Usage

### Documentation Management

RebelSCRIBE can extract documentation from source code and generate documentation in various formats.

#### Extracting Documentation

1. Open the Documentation tab.
2. Click on "Extract Documentation" in the Documentation menu.
3. Select the source file or directory.
4. Select the component.
5. Enter the API version.
6. Click "Extract".

#### Generating Static Site

1. Open the Documentation tab.
2. Click on "Generate Static Site" in the Documentation menu.
3. Select the output directory.
4. Click "Generate".

#### Integrating with Component

1. Open the Documentation tab.
2. Click on "Integrate with Component" in the Documentation menu.
3. Select the component.
4. Select the source directory.
5. Select the output directory.
6. Click "Integrate".

### Novel Writing

RebelSCRIBE can be used to create and manage novel projects.

#### Creating a New Novel

1. Open the Novel Writing tab.
2. Click on "New" in the File menu.
3. Enter the novel title.
4. Click "Create".

#### Adding Chapters and Scenes

1. Open the Novel Writing tab.
2. Right-click on the novel in the binder view.
3. Select "Add Chapter" or "Add Scene".
4. Enter the chapter or scene title.
5. Click "Add".

#### Writing Content

1. Open the Novel Writing tab.
2. Select a chapter or scene in the binder view.
3. Write content in the editor.
4. Click "Save" in the File menu to save the novel.

### AI-Assisted Content Creation

RebelSCRIBE can generate text, character profiles, and plot outlines using AI.

#### Generating Text

1. Open the Novel Writing tab.
2. Select a chapter or scene in the binder view.
3. Click on "Generate Text" in the AI menu.
4. Enter the prompt.
5. Click "Generate".

#### Creating Character Profiles

1. Open the Novel Writing tab.
2. Right-click on the novel in the binder view.
3. Select "Add Character".
4. Enter the character name.
5. Click "Add".
6. Select the character in the binder view.
7. Click on "Generate Character Profile" in the AI menu.
8. Enter the prompt.
9. Click "Generate".

#### Creating Plot Outlines

1. Open the Novel Writing tab.
2. Right-click on the novel in the binder view.
3. Select "Add Plot Outline".
4. Enter the plot outline title.
5. Click "Add".
6. Select the plot outline in the binder view.
7. Click on "Generate Plot Outline" in the AI menu.
8. Enter the prompt.
9. Click "Generate".

## Integration with RebelSUITE

RebelSCRIBE integrates with other RebelSUITE components to provide a comprehensive documentation and content management solution.

### Integration with RebelCAD

RebelSCRIBE can extract documentation from RebelCAD source code and generate documentation for RebelCAD components.

### Integration with RebelCODE

RebelSCRIBE can extract documentation from RebelCODE source code and generate documentation for RebelCODE components.

### Integration with RebelENGINE

RebelSCRIBE can extract documentation from RebelENGINE source code and generate documentation for RebelENGINE components.

### Integration with RebelFLOW

RebelSCRIBE can extract documentation from RebelFLOW source code and generate documentation for RebelFLOW components.

### Integration with RebelDESK

RebelSCRIBE can extract documentation from RebelDESK source code and generate documentation for RebelDESK components.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the UI framework
- OpenAI, Anthropic, and Meta for the AI models
- Markdown and Sphinx for the documentation generation
