# RebelSCRIBE API Reference

This document provides a reference for the RebelSCRIBE API.

## Main Window

### MainWindowHybrid

The main window for the hybrid version of RebelSCRIBE.

#### Methods

- `__init__()`: Initialize the main window.
- `run()`: Run the application.
- `_init_ui()`: Initialize the UI.
- `_create_menu_bar()`: Create the menu bar.
- `_create_tool_bar()`: Create the tool bar.
- `_init_novel_writing_tab()`: Initialize the novel writing tab.
- `_init_documentation_tab()`: Initialize the documentation tab.
- `_load_settings()`: Load settings.
- `_save_settings()`: Save settings.
- `closeEvent(event)`: Handle close event.
- `_on_new()`: Handle new action.
- `_on_open()`: Handle open action.
- `_on_save()`: Handle save action.
- `_on_save_as()`: Handle save as action.
- `_on_undo()`: Handle undo action.
- `_on_redo()`: Handle redo action.
- `_on_cut()`: Handle cut action.
- `_on_copy()`: Handle copy action.
- `_on_paste()`: Handle paste action.
- `_on_theme_settings()`: Handle theme settings action.
- `_on_ai_settings()`: Handle AI settings action.
- `_on_model_benchmarking()`: Handle model benchmarking action.
- `_on_batch_benchmarking()`: Handle batch benchmarking action.
- `_on_model_finetuning()`: Handle model fine-tuning action.
- `_on_extract_documentation()`: Handle extract documentation action.
- `_on_generate_static_site()`: Handle generate static site action.
- `_on_integrate_with_component()`: Handle integrate with component action.
- `_on_about()`: Handle about action.

## Theme Manager

### ThemeManager

The theme manager for RebelSCRIBE.

#### Methods

- `__init__()`: Initialize the theme manager.
- `apply_theme(app=None)`: Apply the current theme to the application.
- `_apply_light_theme(app)`: Apply light theme to the application.
- `_apply_dark_theme(app)`: Apply dark theme to the application.
- `_apply_system_theme(app)`: Apply system theme to the application.
- `_apply_custom_theme(app)`: Apply custom theme to the application.
- `_apply_editor_settings()`: Apply editor settings.

## Error Handler

### ErrorHandler

The error handler for RebelSCRIBE.

#### Methods

- `__init__()`: Initialize the error handler.
- `set_main_window(main_window)`: Set the main window.
- `show_error(message, title="Error", details=None)`: Show an error message.
- `handle_exception(exc_type, exc_value, exc_traceback)`: Handle an exception.

## Logging Utilities

### Functions

- `setup_logging(log_file="rebelscribe.log", console_output=True, file_output=True, level=logging.DEBUG)`: Set up logging for the application.
- `get_logger(name)`: Get a logger with the specified name.
