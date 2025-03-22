# RebelSCRIBE Integrations

This directory contains integration modules for RebelSCRIBE with other RebelSUITE components.

## RebelDESK Integration

The RebelDESK integration enables documentation management, editing, publishing, version control, and search capabilities within the RebelDESK IDE.

### Features

- **Documentation Management**: Extract documentation from RebelDESK source code and manage it within RebelDESK.
- **Documentation Editing**: Edit documentation within RebelDESK using a WYSIWYG editor.
- **Documentation Publishing**: Generate HTML and Markdown documentation from RebelDESK.
- **Version Control**: Track changes to documentation and restore previous versions.
- **Documentation Search**: Search for documentation within RebelDESK.

### Usage

To use the RebelDESK integration, run the following command from the RebelSCRIBE directory:

```powershell
.\run_rebeldesk_integration.ps1
```

This will extract documentation from RebelDESK source code and integrate RebelSCRIBE with RebelDESK.

### Integration Modules

The RebelDESK integration consists of the following modules:

- **documentation_manager.py**: Manages documentation within RebelDESK.
- **documentation_editor.py**: Provides a WYSIWYG editor for documentation.
- **documentation_browser.py**: Provides a browser for documentation.
- **version_control.py**: Provides version control for documentation.

### Testing

To test the RebelDESK integration, run the following command from the RebelSCRIBE directory:

```powershell
python test_rebeldesk_integration.py
```

This will run unit tests for the RebelDESK integration.

## Other Integrations

Additional integrations with other RebelSUITE components will be added in the future.
