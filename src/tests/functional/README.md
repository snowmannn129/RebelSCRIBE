# Functional Tests for RebelSCRIBE

This directory contains functional tests for the RebelSCRIBE application. Functional tests focus on testing complete features from a user's perspective, ensuring that the application behaves as expected when multiple components interact.

## Purpose

Functional tests bridge the gap between unit tests (which test individual components in isolation) and end-to-end tests (which test the entire application). They test specific features or workflows that involve multiple components working together, but without necessarily testing the entire application.

## Test Organization

Functional tests are organized by feature or workflow:

- `test_document_management.py`: Tests for document creation, editing, and management
- `test_project_management.py`: Tests for project creation, loading, and saving
- `test_search_functionality.py`: Tests for search features
- `test_export_functionality.py`: Tests for export features
- `test_ai_integration.py`: Tests for AI-powered features
- `test_cloud_storage.py`: Tests for cloud storage integration

## Running Functional Tests

To run all functional tests:

```powershell
.\run_tests_enhanced.ps1 -TestType functional
```

To run a specific functional test:

```powershell
.\run_tests_enhanced.ps1 -TestPath src\tests\functional\test_document_management.py
```

## Writing Functional Tests

When writing functional tests:

1. Focus on testing complete features or workflows
2. Test the feature from a user's perspective
3. Use real components instead of mocks when possible
4. Set up the necessary state before the test
5. Clean up after the test to avoid affecting other tests

Example:

```python
def test_document_creation_and_editing(self):
    """Test creating a document and editing its content."""
    # Set up
    project = self.project_manager.create_project(
        title="Test Project",
        author="Test Author",
        path=os.path.join(self.test_dir, "test_project.rebelscribe")
    )
    self.project_manager.current_project = project
    
    # Create a document
    document = self.document_manager.create_document(
        title="Test Document",
        content="Initial content"
    )
    
    # Edit the document
    document.content = "Updated content"
    self.document_manager.save_document(document)
    
    # Verify the document was saved correctly
    loaded_document = self.document_manager.load_document(document.id)
    self.assertEqual(loaded_document.title, "Test Document")
    self.assertEqual(loaded_document.content, "Updated content")
