# Enhanced Error Handler

The Enhanced Error Handler is a comprehensive error handling system for RebelSCRIBE that provides advanced features for error management, notification, and tracking.

## Features

- **Error Severity Categorization**: Errors are categorized by severity (INFO, WARNING, ERROR, CRITICAL)
- **Automatic Severity Detection**: Automatically determines severity based on error type
- **Different UI Treatments**: Different UI treatments based on error severity
- **Customizable Notification System**: Non-blocking notifications for less severe errors
- **Error History**: Maintains a history of errors with filtering by severity, component, and time
- **Error Export**: Export error history to JSON, CSV, or plain text
- **Callback System**: Register callbacks for specialized error handling
- **Error Aggregation**: Aggregates similar errors to reduce notification spam
- **Rate Limiting**: Limits the frequency of error notifications
- **Component Registration**: Register components for better error categorization

## Architecture

The enhanced error handler consists of several components:

1. **EnhancedErrorHandler**: The main error handler class that provides all the enhanced features
2. **ErrorHandlerIntegration**: Integration layer that provides backward compatibility with the original error handler
3. **error_handler_init.py**: Initialization module that configures the enhanced error handler

## Usage

### Basic Usage

```python
from src.ui.error_handler_integration import get_integrated_error_handler

# Get error handler instance
error_handler = get_integrated_error_handler(parent)

# Handle a simple error
error_handler.handle_error(
    error_type="MyErrorType",
    error_message="Something went wrong",
    parent=parent
)

# Handle an exception
try:
    # Some code that might raise an exception
    result = 1 / 0
except Exception as e:
    error_handler.handle_exception(
        exception=e,
        context="Division operation",
        parent=parent
    )
```

### Advanced Usage

#### Using Error Severity

```python
from src.ui.enhanced_error_handler import ErrorSeverity
from src.ui.error_handler_integration import get_integrated_error_handler

# Get error handler instance
error_handler = get_integrated_error_handler(parent)

# Handle an error with specific severity
error_handler.handle_error(
    error_type="MyErrorType",
    error_message="Something went wrong",
    severity=ErrorSeverity.WARNING,
    parent=parent
)
```

#### Component Registration

```python
from src.ui.error_handler_integration import get_integrated_error_handler

# Get error handler instance
error_handler = get_integrated_error_handler(parent)

# Register components
error_handler.register_component(
    component_name="MyComponent",
    metadata={"description": "My Component"}
)

error_handler.register_component(
    component_name="MyComponent.SubComponent",
    parent_component="MyComponent",
    metadata={"description": "My Sub-Component"}
)

# Handle an error with component
error_handler.handle_error(
    error_type="MyErrorType",
    error_message="Something went wrong",
    component="MyComponent.SubComponent",
    parent=parent
)
```

#### Error Callbacks

```python
from src.ui.enhanced_error_handler import ErrorSeverity, ErrorRecord
from src.ui.error_handler_integration import get_integrated_error_handler

# Get error handler instance
error_handler = get_integrated_error_handler(parent)

# Define callback function
def my_error_callback(error_record: ErrorRecord):
    print(f"Error occurred: {error_record.error_type} - {error_record.error_message}")
    # Do something with the error

# Register callback
callback_id = error_handler.set_error_callback(
    error_type="MyErrorType",
    severity=ErrorSeverity.ERROR,
    component="MyComponent",
    callback=my_error_callback
)

# Later, remove the callback if needed
error_handler.remove_error_callback(callback_id)
```

#### Error History

```python
from src.ui.enhanced_error_handler import ErrorSeverity
from src.ui.error_handler_integration import get_integrated_error_handler

# Get error handler instance
error_handler = get_integrated_error_handler(parent)

# Get error history
errors = error_handler.get_error_history(
    severity=ErrorSeverity.ERROR,
    component="MyComponent",
    limit=10
)

# Export error history
error_handler.export_error_history(
    file_path="error_history.json",
    format="json",
    include_system_info=True,
    anonymize=False
)

# Clear error history
error_handler.clear_error_history()
```

## Integration with Existing Code

The enhanced error handler is designed to be backward compatible with the original error handler. The integration layer provides the same interface as the original error handler, so existing code that uses the original error handler will continue to work without changes.

To use the enhanced error handler in existing code, simply replace the import statement:

```python
# Original import
from src.ui.error_handler import get_error_handler

# New import
from src.ui.error_handler_integration import get_integrated_error_handler as get_error_handler
```

Alternatively, you can use the `replace_error_handler` function to replace the original error handler with the enhanced one globally:

```python
from src.ui.error_handler_init import initialize_error_handler

# Initialize and replace the error handler
initialize_error_handler()
```

## Configuration

The enhanced error handler can be configured through the application's configuration system. The following configuration options are available:

### UI Treatments

```yaml
error_handler:
  ui_treatments:
    INFO:
      dialog_type: NOTIFICATION
      use_non_blocking: true
      timeout: 5000
      position: TOP_RIGHT
    WARNING:
      dialog_type: NOTIFICATION
      use_non_blocking: true
      timeout: 10000
      position: TOP_RIGHT
    ERROR:
      dialog_type: MODAL
      use_non_blocking: false
      timeout: null
      position: null
    CRITICAL:
      dialog_type: MODAL
      use_non_blocking: false
      timeout: null
      position: null
```

### Error Aggregation

```yaml
error_handler:
  error_aggregation:
    enabled: true
    timeout: 5000
    pattern_matching: false
```

### Rate Limiting

```yaml
error_handler:
  rate_limiting:
    enabled: true
    threshold: 5
    time_window: 60000
    use_exponential_backoff: true
```

### Notification Manager

```yaml
error_handler:
  notification_manager:
    max_notifications: 5
    spacing: 10
    animation_duration: 250
    fade_effect: true
    slide_effect: true
    stacking_order: newest_on_top
    default_timeouts:
      INFO: 5000
      WARNING: 10000
      ERROR: 15000
      CRITICAL: null
```

## Demo

A demo application is provided to showcase the enhanced error handler features. You can run the demo using the following command:

```bash
python -m src.tests.ui.test_enhanced_error_handler_demo
```

The demo allows you to trigger different types of errors and see how they are handled by the enhanced error handler.

## Testing

Unit tests for the enhanced error handler are provided in the `src/tests/ui/test_error_handler_integration.py` file. You can run the tests using the following command:

```bash
python -m unittest src.tests.ui.test_error_handler_integration
```
