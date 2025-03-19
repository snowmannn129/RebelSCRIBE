# RebelSCRIBE Test Improvement Plan

## Current Testing Issues

After reviewing the current testing approach in RebelSCRIBE, several issues have been identified:

1. **Incomplete Functionality Testing**: Many UI methods and functionality are not being tested, only their presence.
2. **Over-reliance on Mocks**: Integration tests use too many mocks instead of testing actual functionality.
3. **Limited Test Configuration**: The test runner script lacks options for different test types and configurations.
4. **No Continuous Integration**: There's no automated testing on code changes.
5. **Insufficient Edge Case Testing**: Not enough tests for error conditions and edge cases.
6. **No Coverage Requirements**: No defined test coverage thresholds.
7. **Lack of End-to-End Testing**: Missing comprehensive workflow tests that simulate real user behavior.

## Improvement Strategy

### 1. Enhanced Test Framework

#### 1.1 Test Organization

```
src/tests/
├── unit/                  # Unit tests for individual components
│   ├── backend/           # Backend unit tests
│   ├── ui/                # UI unit tests
│   └── utils/             # Utility unit tests
├── integration/           # Integration tests between components
├── functional/            # Functional tests for complete features
├── e2e/                   # End-to-end tests for complete workflows
├── performance/           # Performance and load tests
└── fixtures/              # Test fixtures and data
```

#### 1.2 Test Base Classes

Create base test classes to reduce code duplication:

```python
class BaseUITest(unittest.TestCase):
    """Base class for UI tests with common setup and teardown."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance() or QApplication(sys.argv)
        # Mock common dependencies
        self.mock_config = self._create_mock_config()
        # Other common setup
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Common cleanup
        
    def _create_mock_config(self):
        """Create a standard mock configuration."""
        # Implementation
```

### 2. Comprehensive Test Coverage

#### 2.1 UI Functionality Tests

Expand UI tests to cover actual functionality:

```python
def test_on_save_as(self, qtbot, main_window):
    """Test the save as functionality."""
    # Mock file dialog
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
               return_value=('/path/to/save.rebelscribe', 'RebelSCRIBE Project')):
        # Mock project manager
        main_window.project_manager = MagicMock()
        
        # Call save as method
        main_window._on_save_as()
        
        # Verify project manager was called correctly
        main_window.project_manager.save_project_as.assert_called_once_with('/path/to/save.rebelscribe')
        
        # Verify status bar was updated
        assert "Project saved as" in main_window.status_bar.currentMessage()
```

#### 2.2 Integration Tests with Real Components

Reduce mocking in integration tests:

```python
def test_project_backup_and_restore(self):
    """Test backing up and restoring a project with real components."""
    # Create a project
    project_path = os.path.join(self.test_dir, "backup_project.rebelscribe")
    project = self.project_manager.create_project(
        title="Backup Project",
        author="Test Author",
        path=project_path
    )
    
    # Create real documents
    self.document_manager.set_project_path(os.path.dirname(project_path))
    doc1 = self.document_manager.create_document(
        title="Document 1",
        content="Content 1"
    )
    doc2 = self.document_manager.create_document(
        title="Document 2",
        content="Content 2"
    )
    
    # Save the project
    self.project_manager.current_project = project
    self.project_manager.save_project()
    
    # Create a real backup using the backup service
    backup_path = self.backup_service.create_backup(project_path)
    
    # Verify the backup was created
    self.assertTrue(os.path.exists(backup_path))
    
    # Delete the original project
    os.remove(project_path)
    self.assertFalse(os.path.exists(project_path))
    
    # Restore from backup
    restored_path = self.backup_service.restore_backup(backup_path, self.test_dir)
    
    # Verify the restore was successful
    self.assertTrue(os.path.exists(restored_path))
    
    # Load the restored project
    restored_project = self.project_manager.load_project(restored_path)
    
    # Verify the project details
    self.assertEqual(restored_project.title, "Backup Project")
    self.assertEqual(restored_project.author, "Test Author")
    
    # Verify documents were restored
    documents_dir = os.path.join(os.path.dirname(restored_path), "documents")
    self.assertTrue(os.path.exists(documents_dir))
    
    # Load documents and verify content
    self.document_manager.set_project_path(os.path.dirname(restored_path))
    restored_docs = self.document_manager.get_all_documents()
    
    self.assertEqual(len(restored_docs), 2)
    doc_titles = [doc.title for doc in restored_docs]
    self.assertIn("Document 1", doc_titles)
    self.assertIn("Document 2", doc_titles)
```

#### 2.3 Edge Case and Error Testing

Add tests for error conditions:

```python
def test_load_nonexistent_project(self):
    """Test loading a project that doesn't exist."""
    nonexistent_path = "/path/to/nonexistent.rebelscribe"
    
    # Verify that loading a nonexistent project raises an exception
    with self.assertRaises(FileNotFoundError):
        self.project_manager.load_project(nonexistent_path)

def test_save_without_permissions(self):
    """Test saving a project without write permissions."""
    # Create a project
    project_path = os.path.join(self.test_dir, "no_perms_project.rebelscribe")
    project = self.project_manager.create_project(
        title="No Permissions",
        author="Test Author",
        path=project_path
    )
    
    # Mock os.access to simulate no write permissions
    with patch('os.access', return_value=False):
        # Set as current project
        self.project_manager.current_project = project
        
        # Verify that saving raises a PermissionError
        with self.assertRaises(PermissionError):
            self.project_manager.save_project()
```

### 3. Improved Test Runner

Enhance the test runner script:

```powershell
#!/usr/bin/env pwsh
# RebelSCRIBE Test Runner Script

# Parse command line arguments
param(
    [string]$TestType = "all",  # Options: unit, integration, functional, e2e, all
    [string]$TestPath = "",     # Specific test path to run
    [switch]$Coverage = $false, # Generate coverage report
    [switch]$Verbose = $false,  # Verbose output
    [switch]$Parallel = $false, # Run tests in parallel
    [switch]$FailFast = $false, # Stop on first failure
    [int]$RepeatCount = 1       # Repeat tests multiple times
)

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Set up base command
$command = "pytest"

# Add test type filter
if ($TestPath -ne "") {
    $command += " $TestPath"
}
elseif ($TestType -ne "all") {
    $testDir = "src\tests\$TestType"
    if (Test-Path $testDir) {
        $command += " $testDir"
    }
    else {
        Write-Host "Test type directory not found: $testDir" -ForegroundColor Red
        exit 1
    }
}
else {
    $command += " src\tests"
}

# Add options
if ($Coverage) {
    $command += " --cov=src --cov-report=term --cov-report=html --cov-fail-under=80"
}

if ($Verbose) {
    $command += " -v"
}

if ($Parallel) {
    $command += " -xvs"
}

if ($FailFast) {
    $command += " -x"
}

if ($RepeatCount -gt 1) {
    $command += " --count=$RepeatCount"
}

# Run tests
Write-Host "Running tests: $command" -ForegroundColor Green
Invoke-Expression $command

# Deactivate virtual environment
if (Test-Path function:deactivate) {
    deactivate
}
```

### 4. Continuous Integration Setup

Create a GitHub Actions workflow file:

```yaml
name: RebelSCRIBE Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-qt
    
    - name: Run unit tests
      run: |
        pytest src/tests/unit -v
    
    - name: Run integration tests
      run: |
        pytest src/tests/integration -v
    
    - name: Generate coverage report
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

### 5. Test-Driven Development Process

Implement a test-driven development process:

1. Write tests first for new features
2. Run tests to verify they fail (red)
3. Implement the feature
4. Run tests to verify they pass (green)
5. Refactor code while keeping tests passing

### 6. Performance Testing

Add performance tests:

```python
def test_document_load_performance(self):
    """Test document loading performance."""
    # Create a large document
    large_content = "Lorem ipsum " * 10000  # ~100KB of text
    
    # Create a document
    doc_path = os.path.join(self.test_dir, "large_doc.json")
    doc = Document(title="Large Document", content=large_content)
    
    # Save the document
    with open(doc_path, 'w') as f:
        json.dump(doc.to_dict(), f)
    
    # Measure load time
    start_time = time.time()
    loaded_doc = self.document_manager.load_document(doc_path)
    end_time = time.time()
    
    # Verify load time is acceptable
    load_time = end_time - start_time
    self.assertLess(load_time, 0.1)  # Should load in less than 100ms
```

### 7. UI Automation Testing

Implement UI automation tests:

```python
def test_create_new_project_workflow(self, qtbot):
    """Test the complete workflow of creating a new project."""
    # Launch the application
    main_window = MainWindow()
    qtbot.addWidget(main_window)
    
    # Mock file dialog to return a path for the new project
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
               return_value=('/path/to/new_project.rebelscribe', 'RebelSCRIBE Project')):
        # Click the "New Project" action
        qtbot.mouseClick(main_window.new_project_action.trigger())
        
        # Find the project settings dialog
        dialog = [w for w in QApplication.topLevelWidgets() if isinstance(w, ProjectSettingsDialog)][0]
        
        # Fill in the project details
        qtbot.keyClicks(dialog.title_edit, "New Test Project")
        qtbot.keyClicks(dialog.author_edit, "Test Author")
        
        # Click OK
        qtbot.mouseClick(dialog.button_box.button(QDialogButtonBox.StandardButton.Ok))
        
        # Verify the project was created
        self.assertEqual(main_window.project_manager.current_project.title, "New Test Project")
        self.assertEqual(main_window.project_manager.current_project.author, "Test Author")
        
        # Verify the UI was updated
        self.assertEqual(main_window.windowTitle(), "RebelSCRIBE - New Test Project")
```

## Implementation Plan

### Phase 1: Framework and Organization (Week 1)
- Reorganize test directory structure
- Create base test classes
- Update test runner script

### Phase 2: Increase Test Coverage (Weeks 2-3)
- Add missing unit tests for UI functionality
- Improve integration tests with less mocking
- Add edge case and error condition tests

### Phase 3: Automation and CI (Week 4)
- Set up GitHub Actions for continuous integration
- Implement code coverage requirements
- Create performance tests

### Phase 4: UI and End-to-End Testing (Weeks 5-6)
- Implement UI automation tests
- Create end-to-end workflow tests
- Add regression tests for fixed bugs

## Success Metrics

- **Code Coverage**: Achieve and maintain at least 80% code coverage
- **Test Pass Rate**: Maintain 100% passing tests on the main branch
- **Bug Detection**: 90% of bugs should be caught by tests before reaching production
- **Performance**: All performance tests should pass with defined thresholds
- **Build Time**: Complete test suite should run in under 5 minutes

## Additional Testing for Benchmark Functionality

### 1. UI Component Testing

- Test all UI components in the benchmark dialog
- Verify tab switching and content loading
- Test form inputs and validation
- Verify visualization rendering
- Test progress tracking and display
- Verify error handling and user feedback

### 2. Integration Testing

- Test integration between benchmark dialog and model registry
- Verify model loading and selection
- Test benchmark execution and result storage
- Verify visualization generation from benchmark results
- Test report generation and export

### 3. Performance Testing

- Measure visualization generation time for different dataset sizes
- Test benchmark execution with varying model sizes
- Verify memory usage during benchmark operations
- Test UI responsiveness during long-running operations

### 4. End-to-End Testing

- Test complete benchmarking workflows from model selection to report generation
- Verify data persistence between application sessions
- Test benchmark comparison across multiple models
- Verify visualization export in different formats

### 5. Stress Testing

- Test with large benchmark datasets
- Verify handling of multiple concurrent benchmarks
- Test with limited system resources
- Verify graceful degradation under load

### 6. Accessibility Testing

- Test keyboard navigation in benchmark dialog
- Verify screen reader compatibility
- Test color contrast and readability
- Verify resizing and responsive behavior

## Conclusion

Implementing this test improvement plan will significantly enhance the quality and reliability of the RebelSCRIBE application. By catching issues earlier in the development process, we'll reduce the number of bugs that reach users and improve the overall user experience. The additional testing for benchmark functionality will ensure that this critical feature works correctly and provides accurate results for users evaluating AI models.
