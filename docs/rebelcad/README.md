# RebelCAD Documentation

This directory contains the generated documentation for the RebelCAD component of RebelSUITE. The documentation is generated from the RebelCAD source code using the RebelSCRIBE documentation generation system.

## Latest Updates

- **2025-03-19**: Improved documentation extraction with enhanced regex patterns for better comment parsing
- **2025-03-19**: Added HTML generation with proper formatting and styling
- **2025-03-19**: Implemented search functionality in the documentation browser
- **2025-03-19**: Fixed issues with documentation extraction for classes, enums, and structs

## Documentation Structure

- `index.html`: The main entry point for the documentation
- `*.html`: HTML documentation files for individual classes, functions, and modules
- `*.md`: Markdown documentation files for individual classes, functions, and modules

## Generating Documentation

To generate or update the documentation, run the RebelCAD integration script:

```bash
cd RebelSUITE/RebelSCRIBE
python run_rebelcad_integration.py
```

This will extract documentation from the RebelCAD source code and generate HTML and Markdown documentation in this directory.

## Documentation Content

The documentation includes:

- Class documentation
- Function and method documentation
- Module documentation
- Code examples
- Cross-references between related documentation

## Viewing Documentation

To view the documentation, open the `index.html` file in a web browser. The documentation includes a search function to help you find specific information.

## Integration with RebelSUITE

This documentation is part of the RebelSUITE documentation system, which provides integrated documentation for all RebelSUITE components. The documentation is designed to be cross-linked with documentation for other components, providing a seamless documentation experience.

## Contributing

To contribute to the documentation:

1. Update the source code documentation in the RebelCAD source files
2. Run the documentation generation script to update the documentation
3. Review the generated documentation for accuracy and completeness
4. Submit a pull request with your changes

## License

The documentation is licensed under the same license as the RebelCAD source code.
