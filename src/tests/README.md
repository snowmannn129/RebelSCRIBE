# RebelSCRIBE Testing Framework

This directory contains the testing framework for the RebelSCRIBE application. The tests are organized into different categories to ensure comprehensive coverage of the application's functionality.

## Test Organization

The tests are organized into the following directories:

- **unit/**: Unit tests for individual components
  - **backend/**: Backend unit tests
  - **ui/**: UI unit tests
  - **utils/**: Utility unit tests
- **integration/**: Integration tests between components
- **e2e/**: End-to-end tests for complete workflows
- **performance/**: Performance and load tests
- **fixtures/**: Test fixtures and data

## Running Tests

### Using the Enhanced Test Runner

The enhanced test runner (`run_tests_enhanced.ps1`) provides a flexible way to run tests with various options:

```powershell
# Run all tests
.\run_tests_enhanced.ps1

# Run specific test types
.\run_tests_enhanced.ps1 -TestType unit
.\run_tests_enhanced.ps1 -TestType integration
.\run_tests_enhanced.ps1 -TestType e2e
.\run_tests_enhanced.ps1 -TestType performance

# Run with coverage report
.\run_tests_enhanced.ps1 -Coverage

# Run with verbose output
.\run_tests_enhanced.ps1 -Verbose

# Run tests in parallel
.\run_tests_enhanced.ps1 -Parallel

# Stop on first failure
.\run_tests_enhanced.ps1 -FailFast

# Run tests multiple times
.\run_tests_enhanced.ps1 -RepeatCount 3

# Set coverage threshold
.\run_tests_enhanced.ps1 -Coverage -CoverageThreshold 90

# Output test results to a file
.\run_tests_enhanced.ps1 -OutputFile test_results.xml

# Run a specific test file
.\run_tests_enhanced.ps1 -TestPath src/tests/unit/test_specific_file.py
```

### Using pytest Directly

You can also run tests directly using pytest:

```powershell
# Run all tests
pytest src/tests

# Run specific test types
pytest src/tests/unit
pytest src/tests/integration
pytest src/tests/e2e
pytest src/tests/performance

# Run with coverage report
pytest --cov=src --cov-report=term --cov-report=html

# Run a specific test file
pytest src/tests/unit/test_specific_file.py

# Run a specific test function
pytest src/tests/unit/test_specific_file.py::TestClass::test_function
```

## Writing Tests

### Base Test Classes

To reduce code duplication, use the base test classes provided:

```python
from src.tests.base_test import BaseTest
from src.tests.ui.base_ui_test import BaseUITest

class TestMyFeature(BaseTest):
    """Tests for my feature."""
    
    def test_something(self):
        """Test something."""
        # Test implementation
```

### Unit Tests

Unit tests should focus on testing individual components in isolation:

```python
def test_document_creation(self):
    """Test creating a document."""
    doc = Document(title="Test Document", content="Test content")
    
    assert doc.title == "Test Document"
    assert doc.content == "Test content"
```

### Integration Tests

Integration tests should focus on testing the interaction between components:

```python
def test_document_manager_with_project_manager(self):
    """Test document manager working with project manager."""
    # Create a project
    project = self.project_manager.create_project(
        title="Test Project",
        author="Test Author",
        path=self.test_project_path
    )
    
    # Set project path for document manager
    self.document_manager.set_project_path(os.path.dirname(self.test_project_path))
    
    # Create a document
    doc = self.document_manager.create_document(
        title="Test Document",
        content="Test content"
    )
    
    # Save the project
    self.project_manager.current_project = project
    self.project_manager.save_project()
    
    # Verify the document was saved
    assert os.path.exists(doc.path)
```

### End-to-End Tests

End-to-end tests should simulate real user workflows:

```python
def test_create_project_add_documents_export(self, qtbot, app, setup, monkeypatch):
    """
    Test the complete workflow of:
    1. Creating a new project
    2. Adding documents
    3. Editing documents
    4. Exporting the project
    """
    # Test implementation
```

### Performance Tests

Performance tests should measure the performance of critical operations:

```python
def test_document_load_performance(self, setup, benchmark):
    """Test document loading performance."""
    # Create a document
    doc = self.document_manager.create_document(
        title="Load Performance Test",
        content="This is a test document for load performance testing."
    )
    
    # Save the document to get its path
    self.document_manager.save_document(doc)
    doc_path = doc.path
    
    def load_document():
        return self.document_manager.load_document(doc_path)
    
    # Benchmark document loading
    result = benchmark(load_document)
    
    # Verify the document was loaded
    assert result is not None
    assert result.title == "Load Performance Test"
```

## Continuous Integration

The project uses GitHub Actions for continuous integration. The workflow is defined in `.github/workflows/tests.yml` and includes:

1. Running unit tests
2. Running integration tests
3. Generating a coverage report
4. Running performance tests
5. Checking code formatting and linting

## Test Coverage

The project aims to maintain at least 80% code coverage. You can view the coverage report by running:

```powershell
.\run_tests_enhanced.ps1 -Coverage
```

Then open `coverage_report/index.html` in your browser.

## Best Practices

1. **Test-Driven Development**: Write tests before implementing features
2. **Isolation**: Ensure tests are isolated and don't depend on each other
3. **Mocking**: Use mocks for external dependencies
4. **Fixtures**: Use fixtures for common setup and teardown
5. **Naming**: Use clear and descriptive test names
6. **Assertions**: Use specific assertions to make failures clear
7. **Coverage**: Aim for high test coverage, especially for critical code paths
8. **Performance**: Keep tests fast to run
9. **Maintenance**: Keep tests up to date with code changes
