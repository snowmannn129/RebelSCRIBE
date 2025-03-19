# RebelSCRIBE Error Handling Guidelines

## Overview

This document provides guidelines for using the enhanced error handling framework in RebelSCRIBE. The framework provides a comprehensive approach to error management, including error categorization, UI treatments, error history tracking, and error reporting.

## Table of Contents

1. [Error Severity Levels](#error-severity-levels)
2. [Basic Error Handling](#basic-error-handling)
3. [Exception Handling](#exception-handling)
4. [Component Registration](#component-registration)
5. [Error Callbacks](#error-callbacks)
6. [Error History and Filtering](#error-history-and-filtering)
7. [Error Aggregation and Rate Limiting](#error-aggregation-and-rate-limiting)
8. [Error Reporting and Export](#error-reporting-and-export)
9. [Configuration](#configuration)
10. [Best Practices](#best-practices)

## Error Severity Levels

The error handling framework categorizes errors into four severity levels:

| Severity | Description | Default UI Treatment |
|----------|-------------|---------------------|
| INFO | Informational messages that don't indicate a problem | Non-blocking notification |
| WARNING | Potential issues that don't prevent the application from functioning | Non-blocking notification |
| ERROR | Issues that prevent a specific operation from completing | Modal dialog |
| CRITICAL | Severe issues that may affect application stability | Modal dialog |

## Basic Error Handling

### Getting the Error Handler

```python
from src.ui.error_handler_integration import get_integrated_error_handler

# In a UI component
self.error_handler = get_integrated_error_handler(self)

# In a non-UI component
from src.ui.error_handler_integration import get_error_handler
self.error_handler = get_error_handler()
```

### Handling Errors

```python
# Basic error handling
error_id = self.error_handler.handle_error(
    error_type="FileError",
    error_message="Failed to open file: example.txt",
    severity=ErrorSeverity.ERROR,
    component="ui.file_manager",
    parent=self  # UI parent for dialogs, optional
)

# Log an error without showing a dialog
self.error_handler.log_error(
    error_type="NetworkWarning",
    error_message="Network connection is slow",
    severity=ErrorSeverity.WARNING,
    component="backend.network"
)
```

## Exception Handling

```python
try:
    # Code that might raise an exception
    result = 1 / 0
except Exception as e:
    # Handle the exception
    self.error_handler.handle_exception(
        exception=e,
        context="Division operation in calculate_ratio",
        severity=ErrorSeverity.ERROR,  # Optional, will be auto-detected if not provided
        component="backend.calculator",
        parent=self  # Optional
    )
```

## Component Registration

Registering components helps organize errors and provides better context for error tracking.

```python
# Register main component
self.error_handler.register_component(
    component_name="ui.main_window",
    metadata={"description": "Main application window"}
)

# Register sub-component
self.error_handler.register_component(
    component_name="ui.main_window.editor",
    parent_component="ui.main_window",
    metadata={"description": "Document editor"}
)
```

## Error Callbacks

You can register callbacks to be notified when specific errors occur.

```python
# Register a callback for network errors
def on_network_error(error_record):
    # Handle network error
    print(f"Network error occurred: {error_record.error_message}")
    # Attempt to reconnect
    reconnect_to_network()

callback_id = self.error_handler.set_error_callback(
    error_type="NetworkError",
    callback=on_network_error,
    priority=2  # Higher priority callbacks are executed first
)

# Remove the callback when no longer needed
self.error_handler.remove_error_callback(callback_id)
```

## Error History and Filtering

```python
# Get all errors
all_errors = self.error_handler.get_error_history()

# Get errors with specific severity
error_errors = self.error_handler.get_error_history(severity=ErrorSeverity.ERROR)

# Get errors from a specific component
ui_errors = self.error_handler.get_error_history(component="ui")

# Get errors with a specific type
network_errors = self.error_handler.get_error_history(error_type="NetworkError")

# Get errors within a time range
from datetime import datetime, timedelta
now = datetime.now()
recent_errors = self.error_handler.get_error_history(
    time_range=(now - timedelta(hours=1), now)
)

# Combine filters
recent_ui_errors = self.error_handler.get_error_history(
    component="ui",
    time_range=(now - timedelta(hours=1), now)
)

# Limit the number of errors returned
last_10_errors = self.error_handler.get_error_history(limit=10)

# Clear error history
self.error_handler.clear_error_history()
```

## Error Aggregation and Rate Limiting

Error aggregation and rate limiting help prevent error flooding and improve the user experience.

```python
# Enable error aggregation
self.error_handler.enable_error_aggregation(
    enabled=True,
    timeout=5000,  # 5 seconds
    pattern_matching=True  # Use pattern matching to group similar errors
)

# Configure rate limiting
self.error_handler.configure_rate_limiting(
    threshold=5,  # Maximum number of errors in the time window
    time_window=60000,  # 60 seconds
    use_exponential_backoff=True  # Use exponential backoff for repeated errors
)
```

## Error Reporting and Export

```python
# Export error history to a file
self.error_handler.export_error_history(
    file_path="error_history.json",
    format="json",  # "json", "csv", or "txt"
    include_system_info=True,
    anonymize=False
)

# Report a specific error
self.error_handler.report_error(
    error_id="error-id",
    include_system_info=True,
    anonymize=True,
    additional_info={"user_action": "clicking save button"},
    report_service="email"  # Optional, defaults to configured service
)
```

## Configuration

The error handling framework can be configured through the `config.yaml` file:

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
  error_aggregation:
    enabled: true
    timeout: 5000
    pattern_matching: false
  rate_limiting:
    enabled: true
    threshold: 5
    time_window: 60000
    use_exponential_backoff: true
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
  error_reporting:
    service: local
    endpoint_url: ''
    api_key: ''
    smtp_server: ''
    smtp_port: 587
    smtp_username: ''
    smtp_password: ''
    from_email: ''
    to_email: ''
```

## Best Practices

1. **Use Appropriate Severity Levels**
   - Use INFO for informational messages that don't indicate a problem
   - Use WARNING for potential issues that don't prevent the application from functioning
   - Use ERROR for issues that prevent a specific operation from completing
   - Use CRITICAL for severe issues that may affect application stability

2. **Provide Meaningful Error Messages**
   - Include specific details about what went wrong
   - Avoid technical jargon in user-facing error messages
   - Suggest possible solutions when appropriate

3. **Register Components**
   - Register components to provide better context for error tracking
   - Use a consistent naming convention for components (e.g., `module.component.subcomponent`)

4. **Handle Exceptions Properly**
   - Use try-except blocks to catch exceptions
   - Provide context when handling exceptions
   - Let the error handler determine the severity when possible

5. **Use Error Callbacks for Specialized Handling**
   - Register callbacks for errors that require special handling
   - Use callbacks to implement automatic recovery mechanisms

6. **Monitor Error History**
   - Periodically review error history to identify recurring issues
   - Use error filtering to focus on specific types of errors

7. **Configure Error Aggregation and Rate Limiting**
   - Enable error aggregation to prevent error flooding
   - Configure rate limiting to improve the user experience

8. **Export Error History for Analysis**
   - Export error history to analyze patterns and trends
   - Include system information for better context

9. **Report Critical Errors**
   - Report critical errors to the development team
   - Include additional information to help diagnose the issue

10. **Update Configuration as Needed**
    - Adjust configuration based on user feedback and error patterns
    - Consider different configurations for development and production environments

## Testing the Error Handler

A test script is available to demonstrate the error handler's features:

```powershell
# Run the error handler test script
.\run_error_handler_test.ps1
```

This script demonstrates:
- Triggering errors with different severity levels
- Handling exceptions
- Triggering multiple errors
- Triggering errors in different components
- Exporting error history
- Clearing error history

## Conclusion

The enhanced error handling framework provides a comprehensive approach to error management in RebelSCRIBE. By following these guidelines, you can ensure consistent error handling throughout the application and provide a better user experience.
