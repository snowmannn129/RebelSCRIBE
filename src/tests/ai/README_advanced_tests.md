# Advanced AI Tests for RebelSCRIBE

This directory contains advanced tests for the AI module in RebelSCRIBE, focusing on edge cases, error handling, and advanced features.

## Purpose

The advanced tests complement the basic tests by:

1. Testing edge cases and error conditions
2. Verifying thread safety and asynchronous operations
3. Testing model caching and management
4. Verifying callback mechanisms
5. Testing dependency checking and graceful degradation

## Test Files

- `test_local_models_advanced.py`: Advanced tests for the local_models module
- `test_llama_support.py`: Tests for the Llama model support functionality
- `test_mistral_support.py`: Tests for the Mistral model support functionality
- `test_phi_support.py`: Tests for the Phi model support functionality
- `test_falcon_support.py`: Tests for the Falcon model support functionality
- `test_mpt_support.py`: Tests for the MPT model support functionality
- `test_adapter_support.py`: Tests for the adapter-based fine-tuning functionality
- `test_progress_callbacks.py`: Tests for the progress tracking and callback functionality

## Running the Tests

### Using the Run Script

The easiest way to run the advanced tests is to use the provided run script:

```bash
# From the project root directory
python src/run_advanced_ai_tests.py
```

### Using PowerShell Script

For Windows users, a PowerShell script is provided:

```powershell
# From the project root directory
.\run_advanced_ai_tests.ps1
```

### Options

Both scripts support the following options:

#### Main Options
- `--pytest`: Use pytest instead of unittest (recommended for more detailed output)
- `-v, --verbose`: Show more detailed output
- `--cov`: Generate coverage report (only works with pytest)
- `--cov-report`: Coverage report format (term, html, xml, or all)

#### Test Selection
- `--test-file`: Run specific test file (e.g., test_llama_support.py)
- `--test-class`: Run specific test class (e.g., TestLlamaSupport)
- `--test-method`: Run specific test method (e.g., test_load_model)
- `--model`: Run tests for specific model (local, llama, mistral, phi, falcon, mpt, adapter, progress, or all)

#### Additional Options
- `--fail-fast`: Stop on first failure
- `--repeat`: Repeat tests multiple times
- `--output`: Save test output to file

### Examples

Run all tests with unittest:
```powershell
.\run_advanced_ai_tests.ps1
```

Run all tests with pytest and generate coverage report:
```powershell
.\run_advanced_ai_tests.ps1 -pytest -coverage
```

Run only Llama model tests:
```powershell
.\run_advanced_ai_tests.ps1 -model llama
```

Run only progress callbacks tests:
```powershell
.\run_advanced_ai_tests.ps1 -model progress
```

Run a specific test class:
```powershell
.\run_advanced_ai_tests.ps1 -testClass TestLlamaSupport
```

Run a specific test method:
```powershell
.\run_advanced_ai_tests.ps1 -testMethod test_load_model
```

Run tests with verbose output and save to file:
```powershell
.\run_advanced_ai_tests.ps1 -verbose -output test_results.txt
```

Run tests with pytest, coverage, and fail-fast:
```powershell
.\run_advanced_ai_tests.ps1 -pytest -coverage -failFast
```

### Running Directly with pytest

You can also run the tests directly with pytest:

```bash
# From the project root directory
pytest src/tests/ai/test_local_models_advanced.py -v
```

For coverage report:

```bash
pytest src/tests/ai/test_local_models_advanced.py -v --cov=src/ai --cov-report=term --cov-report=html
```

## Test Structure

The advanced tests are organized into two classes:

1. `TestLocalModelsAdvanced`: Traditional unittest-style tests
2. `TestLocalModelsAdvancedPytest`: Pytest-style tests using fixtures

Each test focuses on a specific aspect of the AI modules, with an emphasis on edge cases and error handling.

## Adding New Tests

When adding new advanced tests:

1. Follow the existing pattern of testing edge cases and error conditions
2. Use appropriate mocking to isolate the code being tested
3. Add both unittest-style and pytest-style tests when possible
4. Update the progress.md file to reflect the new tests

## Related Files

- `src/ai/enhancement_plan.md`: Plan for future enhancements to the AI module
- `src/ai/local_models.py`: The local models module
- `src/ai/llama_support.py`: The Llama model support module
- `src/ai/mistral_support.py`: The Mistral model support module
- `src/ai/phi_support.py`: The Phi model support module
- `src/ai/falcon_support.py`: The Falcon model support module
- `src/ai/mpt_support.py`: The MPT model support module
- `src/ai/adapter_support.py`: The adapter-based fine-tuning module
- `src/ai/progress_callbacks.py`: The progress tracking and callback module
- `src/ai/examples/progress_callbacks_example.py`: Example usage of progress callbacks
- `src/tests/ai/test_local_models.py`: Basic tests for the local_models module
