# RebelSCRIBE

RebelSCRIBE is an AI-powered novel writing program inspired by Scrivener.

## Features

- Organize your writing projects with a hierarchical binder
- Write and edit in a distraction-free environment
- Track your writing progress and statistics
- AI-powered assistance for character development, plot generation, and more
- GPU acceleration support for NVIDIA (CUDA), AMD (ROCm), and Apple Silicon (Metal)
- Export your work to various formats (DOCX, PDF, Markdown, HTML)
- Cloud storage integration for backup and synchronization

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone or download this repository
2. Run the setup script to create a virtual environment and install dependencies:

```powershell
.\setup.ps1
```

### Running the Application

To start RebelSCRIBE, run:

```powershell
.\run.ps1
```

### Running Tests

To run the test suite:

```powershell
.\run_tests.ps1
```

For test coverage report:

```powershell
.\run_tests.ps1 -Coverage
```

## Project Structure

- `src/` - Source code
  - `ai/` - AI integration components
  - `backend/` - Backend logic and data models
  - `ui/` - User interface components
  - `utils/` - Utility functions
  - `tests/` - Test suite
- `documents/` - Document storage
- `exports/` - Exported documents
- `resources/` - Application resources
- `templates/` - Project templates
- `backups/` - Local backups

## License

This project is licensed under the MIT License - see the LICENSE file for details.
