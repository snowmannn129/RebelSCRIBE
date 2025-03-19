# RebelSCRIBE UI Tests

This directory contains tests for the RebelSCRIBE user interface components. The tests ensure that all UI components are present, functional, and properly integrated.

## Test Files

### Component Tests

- `test_main_window.py`: Tests for the main window components
- `test_binder_view.py`: Tests for the binder view
- `test_editor_view.py`: Tests for the editor view
- `test_inspector_view.py`: Tests for the inspector view

### Dialog Tests

- `test_adapter_config_dialog.py`: Tests for the adapter configuration dialog
- `test_training_visualization_dialog.py`: Tests for the training visualization dialog
- `test_benchmark_dialog.py`: Tests for the benchmark dialog
- `test_batch_benchmark_dialog.py`: Tests for the batch benchmark dialog
- `test_ai_settings_dialog.py`: Tests for the AI settings dialog
- `test_export_dialog.py`: Tests for the export dialog
- `test_project_settings_dialog.py`: Tests for the project settings dialog
- `test_cloud_storage_dialog.py`: Tests for the cloud storage dialog

### Integration Tests

- `test_adapter_training_integration.py`: Tests for the integration between adapter configuration and training visualization
- `test_main_window_ai_actions.py`: Tests for the AI actions in the main window

### Comprehensive Tests

- `test_comprehensive_ui.py`: Comprehensive tests for all UI components, including:
  - Component presence tests
  - Component functionality tests
  - Integration tests
  - Edge case tests

## Running the Tests

### Running Individual Test Files

To run an individual test file, use the following command:

```bash
python -m unittest src/tests/ui/test_file.py
```

For example, to run the main window tests:

```bash
python -m unittest src/tests/ui/test_main_window.py
```

### Running All UI Tests

To run all UI tests, use the provided PowerShell script:

```powershell
.\run_all_ui_tests.ps1
```

This script will run all UI tests and save the results to a file in the `test_results` directory.

### Running Comprehensive UI Tests

To run only the comprehensive UI tests, use the provided PowerShell script:

```powershell
.\run_comprehensive_ui_tests.ps1
```

## Test Structure

Each test file follows a similar structure:

1. Import necessary modules
2. Create a test class that inherits from `unittest.TestCase`
3. Implement `setUpClass` to create a QApplication instance
4. Implement `setUp` to create the UI component being tested
5. Implement `tearDown` to clean up after each test
6. Implement test methods for each aspect of the UI component

Example:

```python
import unittest
from PyQt6.QtWidgets import QApplication
from src.ui.component import Component

class TestComponent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
    
    def setUp(self):
        self.component = Component()
    
    def tearDown(self):
        self.component.close()
    
    def test_component_init(self):
        self.assertIsNotNone(self.component)
```

## Test Coverage

The UI tests cover the following areas:

- **Component Presence**: Tests that all UI components are present
- **Component Functionality**: Tests that all UI components function as expected
- **Integration**: Tests that different UI components work together correctly
- **Edge Cases**: Tests that the UI handles edge cases correctly

## Adding New Tests

When adding new UI components to RebelSCRIBE, follow these steps to add tests:

1. Create a new test file in the `src/tests/ui` directory
2. Follow the test structure outlined above
3. Implement tests for all aspects of the UI component
4. Add the new test file to the comprehensive UI tests if appropriate

## Comprehensive Test Plan

For a detailed overview of the UI testing strategy, see the `comprehensive_ui_test_plan.md` file in the root directory.
