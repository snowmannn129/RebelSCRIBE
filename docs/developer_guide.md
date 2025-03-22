# RebelSCRIBE Developer Guide

This guide provides instructions for developing RebelSCRIBE.

## Development Environment

### Prerequisites

- Python 3.8 or higher
- PyQt6
- Other dependencies listed in `requirements.txt`

### Setup

1. Clone the repository:

```bash
git clone https://github.com/rebelsuite/rebelscribe.git
cd rebelscribe
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Install the package in development mode:

```bash
pip install -e .
```

## Project Structure

- `src/`: Source code for RebelSCRIBE.
  - `ui/`: UI components.
  - `utils/`: Utility modules.
- `docs/`: Documentation.
- `tests/`: Tests.
- `examples/`: Example files.
- `config/`: Configuration files.

## Development Workflow

1. Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes.

3. Run the tests:

```bash
pytest
```

4. Run the application:

```bash
python run_hybrid.py
```

5. Commit your changes:

```bash
git add .
git commit -m "Add your feature or fix your bug"
```

6. Push your changes:

```bash
git push origin feature/your-feature-name
```

7. Create a pull request.

## Coding Standards

- Follow PEP 8 for Python code.
- Use type hints.
- Write docstrings for all functions, classes, and modules.
- Write tests for all new features and bug fixes.

## Testing

- Use pytest for testing.
- Run the tests with `pytest`.
- Run the tests with coverage with `pytest --cov=rebelscribe`.

## Documentation

- Use Markdown for documentation.
- Update the documentation when you add or change features.
- Generate API documentation with Sphinx.

## Releasing

1. Update the version number in `setup.py`.
2. Update the changelog.
3. Create a new release on GitHub.
4. Upload the package to PyPI:

```bash
python -m build
twine upload dist/*
```
