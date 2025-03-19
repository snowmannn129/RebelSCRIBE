# RebelSCRIBE Development Procedure

## Backup Standard

RebelSCRIBE follows the RebelSUITE backup standard. Backups are created after major milestones:
- Phase completions
- Release types (Alpha, Beta, Full)
- Major development advancements
- Scheduled dates

Backups are stored as ZIP files in `C:\Users\snowm\Desktop\VSCode\Backup` with the naming format:
`RebelSCRIBE_(mmddyyyy)_(current time).zip`

To create a backup, run:
```powershell
.\backup_project.ps1 -ProgramName "RebelSCRIBE" -MilestoneType "<milestone type>"
```

Backup history is documented below in chronological order.

## 1. Development Environment & Execution
- RebelSCRIBE is developed in VSCode on Windows 11 using PowerShell
- Built using Python for core functionality and PyQt/Tauri for UI
- All development follows a test-driven approach with rigorous validation
- All UI elements must be rigorously tested and functional before submission
- All modules must connect properly before requesting approval

## 2. Project Structure
RebelSCRIBE follows a modular structure:

```
RebelSCRIBE/
├── src/                 # Source code
│   ├── core/            # Core functionality
│   │   ├── parser/      # Markdown and code parsing
│   │   ├── generator/   # Documentation generation
│   │   ├── metadata/    # Metadata extraction and management
│   │   ├── search/      # Search functionality
│   │   ├── versioning/  # Version tracking
│   ├── ai/              # AI-assisted features
│   │   ├── summarizer/  # Content summarization
│   │   ├── analyzer/    # Documentation quality analysis
│   │   ├── generator/   # Content generation
│   │   ├── nlp/         # Natural language processing
│   ├── ui/              # User interface components
│   │   ├── browser/     # Documentation browser
│   │   ├── editor/      # Content editor
│   │   ├── preview/     # Preview system
│   │   ├── export/      # Export functionality
│   │   ├── themes/      # Theme support
│   ├── integration/     # Integration with other RebelSUITE components
│   │   ├── cad/         # RebelCAD integration
│   │   ├── code/        # RebelCODE integration
│   │   ├── engine/      # RebelENGINE integration
│   │   ├── flow/        # RebelFLOW integration
│   │   ├── desk/        # RebelDESK integration
│   ├── utils/           # Utility functions
│   │   ├── logging/     # Logging utilities
│   │   ├── file/        # File operations
│   │   ├── config/      # Configuration management
│   ├── main.py          # Program entry point
├── tests/               # Test files
│   ├── core/            # Core tests
│   ├── ai/              # AI tests
│   ├── ui/              # UI tests
│   ├── integration/     # Integration tests
│   ├── utils/           # Utility tests
├── docs/                # Documentation
│   ├── user-guide/      # User guide
│   ├── developer-guide/ # Developer documentation
│   ├── api/             # API documentation
│   ├── best-practices/  # Documentation best practices
├── scripts/             # Development scripts
│   ├── build.ps1        # Build script
│   ├── test.ps1         # Test script
│   ├── deploy.ps1       # Deployment script
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
├── RebelSCRIBE_Progress_Tracker.md  # Progress tracking
```

## 3. Functional Testing & UI Verification
RebelSCRIBE follows a rigorous testing process:

### Unit Tests for Core Components
- Each function/class must have unit tests before submission
- Tests should cover edge cases, exceptions, and normal behavior
- Store all test scripts in tests/ directory
- Use pytest for Python testing

### UI Component Testing
- Ensure all buttons, menus, and inputs work
- Verify UI elements correctly trigger backend functions
- Use automated UI testing frameworks
- Create visual regression tests for UI components

### Integration Testing
- After every UI implementation:
  - Test every event handler (button clicks, keyboard shortcuts)
  - Ensure UI updates reflect backend actions
  - Simulate user input to test flow
  - Test documentation generation and viewing

### Functional Feature Testing
- Write test scenarios for every feature:
  - Documentation Generation: Test parsing, extraction, and generation
  - Content Management: Test organization, metadata, and search
  - AI Integration: Test summarization, analysis, and generation
  - Integration: Test integration with other RebelSUITE components
  - UI: Test browser, editor, preview, and export

### Regression Testing
- Do not break previous features when adding new code
- Before approving new code, re-run all tests
- Maintain a test suite that can be run automatically

## 4. Python Coding Standards & Best Practices
- Follow PEP 8 style guide for Python code
- Use consistent naming conventions:
  - CamelCase for class names
  - snake_case for function and variable names
  - UPPER_SNAKE_CASE for constants
- Each file should be ≤ 300-500 lines
- If a file exceeds this, split it into multiple modules
- Use docstrings for all functions and classes

Example:
```python
def parse_markdown(content: str) -> Dict[str, Any]:
    """
    Parse markdown content and extract structured data.
    
    Args:
        content: The markdown content to parse
        
    Returns:
        A dictionary containing the parsed structure
        
    Raises:
        ParseError: If the markdown cannot be parsed
    """
    try:
        # Implementation
        return parsed_data
    except Exception as e:
        logger.error(f"Failed to parse markdown: {str(e)}")
        raise ParseError(f"Failed to parse markdown: {str(e)}") from e
```

- Use proper error handling:
```python
try:
    content = file_utils.read_file(file_path)
    parsed_data = parse_markdown(content)
    return parsed_data
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    return None
except ParseError as e:
    logger.error(f"Parse error: {str(e)}")
    return None
```

- Use logging instead of print statements:
```python
import logging
logger = logging.getLogger(__name__)
# ...
logger.debug("Markdown parser initialized")
logger.error(f"Failed to parse file: {str(e)}")
```

## 5. Managing Development Complexity
- Only implement one feature/component per development session
- Keep functions short and modular
- Use type hints for better code organization
- Implement proper error handling and logging
- Track dependencies in requirements.txt
- Use virtual environments for development

## 6. Core Features & Modules
RebelSCRIBE has the following core modules:

### Core Module (src/core/)
- Markdown and code parsing
- Documentation generation
- Metadata extraction and management
- Search functionality
- Version tracking

### AI Module (src/ai/)
- Content summarization
- Documentation quality analysis
- Content generation
- Natural language processing

### UI Module (src/ui/)
- Documentation browser
- Content editor
- Preview system
- Export functionality
- Theme support

### Integration Module (src/integration/)
- RebelCAD integration
- RebelCODE integration
- RebelENGINE integration
- RebelFLOW integration
- RebelDESK integration

### Utils Module (src/utils/)
- Logging utilities
- File operations
- Configuration management

## 7. Automation for Testing
- Run All Tests Automatically:
```powershell
pytest tests/
```

- Run Tests with Coverage:
```powershell
pytest --cov=src tests/
```

- Run UI Tests:
```powershell
pytest tests/ui/
```

- Run Linting:
```powershell
flake8 src/
```

- Run Type Checking:
```powershell
mypy src/
```

## 8. Development Workflow
- Task Breakdown:
  1. Break large tasks into smaller steps
  2. Create detailed implementation plan
  3. Write tests first (Test-Driven Development)
  4. Implement the feature
  5. Verify with tests
  6. Document the implementation

- Approval Workflow:
  1. Generate code and tests
  2. Test thoroughly before requesting approval
  3. Ensure UI elements properly connect to the backend
  4. Once approved, update progress tracker
  5. Move to the next task

## 9. Best Practices for Development
- Use Git for version control:
```powershell
git add .
git commit -m "Implemented markdown parser with code block support"
```

- Create GitHub issues for tracking:
```powershell
.\scripts\create_github_issue.ps1 -title "Fix performance issue in search functionality" -body "Search becomes slow with large documentation sets" -labels "bug,performance,high-priority"
```

- Keep modules focused:
  - No single file should exceed 500 lines
  - Split complex functionality into multiple files
  - Use proper abstraction and encapsulation

- Ensure proper resource management:
  - Clean up resources properly
  - Use context managers for resource management
  - Monitor memory usage

- Optimize performance:
  - Use efficient data structures
  - Implement caching for expensive operations
  - Use asynchronous processing for long-running tasks
  - Implement proper indexing for search functionality

## 10. Progress Tracking
- Update RebelSCRIBE_Progress_Tracker.md after completing each task
- Run progress update script:
```powershell
.\scripts\update_progress.ps1
```

- Generate GitHub issues from progress tracker:
```powershell
.\scripts\generate_github_issues.ps1
```

- Update GitHub issues status:
```powershell
.\scripts\update_github_issues.ps1
```

## 11. Integration with RebelSUITE
- Define clear integration points with other RebelSUITE components:
  - RebelCAD: Generate documentation for CAD models and operations
  - RebelCODE: Integrate with code documentation and API references
  - RebelENGINE: Document game assets and engine features
  - RebelFLOW: Document workflows and node systems
  - RebelDESK: Share common UI components and themes

- Implement shared data formats and APIs
- Create plugin interfaces for cross-application functionality
- Establish unified documentation standards across the suite

## Final Notes
- Your goal is to develop a comprehensive documentation and content management system
- Every UI element must be tested for functionality before requesting approval
- All features must be verified using unit, UI, and integration tests
- Do NOT generate untested or disconnected UI components
- DO ensure all modules connect properly before moving to the next task
