# Adapter Tests

This directory contains tests for the adapter support module, which provides functionality for fine-tuning large language models using adapter methods like LoRA, QLoRA, and Prefix Tuning.

## Running the Tests

There are two ways to run the adapter tests:

1. Using the Python script: `src/run_adapter_tests.py`
2. Using the PowerShell script: `run_adapter_tests.ps1`

Both scripts provide the same functionality and options.

### Command-Line Options

The following command-line options are available:

| Option | Description |
|--------|-------------|
| `--test-class` | Run only tests from the specified class (TestAdapterInfo or TestAdapterManager) |
| `--test-method` | Run only the specified test method |
| `--verbose`, `-v` | Verbosity level (0=quiet, 1=normal, 2=verbose) |
| `--output`, `-o` | File to write test output to |
| `--repeat` | Number of times to repeat the tests |
| `--fail-fast`, `-f` | Stop on first failure |

### Examples

#### Run all adapter tests

```bash
python src/run_adapter_tests.py
```

```powershell
.\run_adapter_tests.ps1
```

#### Run only TestAdapterInfo tests

```bash
python src/run_adapter_tests.py --test-class TestAdapterInfo
```

```powershell
.\run_adapter_tests.ps1 -TestClass TestAdapterInfo
```

#### Run a specific test method

```bash
python src/run_adapter_tests.py --test-method test_init
```

```powershell
.\run_adapter_tests.ps1 -TestMethod test_init
```

#### Run tests with high verbosity

```bash
python src/run_adapter_tests.py --verbose 2
```

```powershell
.\run_adapter_tests.ps1 -Verbose 2
```

#### Run tests and save output to a file

```bash
python src/run_adapter_tests.py --output test_results.txt
```

```powershell
.\run_adapter_tests.ps1 -Output test_results.txt
```

#### Run tests multiple times for stability testing

```bash
python src/run_adapter_tests.py --repeat 3
```

```powershell
.\run_adapter_tests.ps1 -Repeat 3
```

#### Stop on first failure for quicker debugging

```bash
python src/run_adapter_tests.py --fail-fast
```

```powershell
.\run_adapter_tests.ps1 -FailFast
```

## Test Classes

### TestAdapterInfo

Tests for the `AdapterInfo` class, which stores information about an adapter.

### TestAdapterManager

Tests for the `AdapterManager` class, which manages model adapters like LoRA, QLoRA, and Prefix Tuning.

## Adding New Tests

To add new tests for the adapter support module:

1. Add new test methods to the existing test classes in `test_adapter_support.py`.
2. Ensure that test method names start with `test_`.
3. Run the tests to verify that the new tests pass.

## Troubleshooting

If you encounter issues running the tests:

1. Make sure you have all the required dependencies installed.
2. Check that the virtual environment is activated (if using one).
3. Verify that the test files are in the correct location.
4. Try running with higher verbosity (`--verbose 2`) to get more detailed output.
5. Check the test output for specific error messages.

## Integration with CI/CD

These tests can be integrated into a CI/CD pipeline by running the Python script with appropriate options. For example:

```yaml
- name: Run adapter tests
  run: python src/run_adapter_tests.py --verbose 2 --fail-fast
```

This will run the tests with high verbosity and stop on the first failure, which is useful for CI/CD pipelines.
