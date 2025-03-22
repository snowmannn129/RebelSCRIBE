#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for RebelSCRIBE documentation functionality.

This script demonstrates the use of the Documentation model and DocumentationManager
to extract documentation from source code, generate documentation, and integrate
with other RebelSUITE components.
"""

import os
import sys
from pathlib import Path

# Add src directory to path to allow imports
src_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(src_dir))

from src.backend.models.documentation import Documentation
from src.backend.services.documentation_manager import DocumentationManager
from src.utils.logging_utils import setup_logging, get_logger

# Set up logging
setup_logging(
    log_file="test_documentation.log",
    console_output=True,
    file_output=True
)

logger = get_logger(__name__)

def test_documentation_model():
    """Test the Documentation model."""
    print("\n=== Testing Documentation Model ===")
    
    # Create a documentation object
    doc = Documentation(
        title="Test Documentation",
        type=Documentation.TYPE_API,
        content="This is a test documentation.",
        component=Documentation.COMPONENT_SCRIBE,
        api_version="1.0.0"
    )
    
    # Add some parameters
    doc.add_parameter("param1", "The first parameter", "string")
    doc.add_parameter("param2", "The second parameter", "number")
    
    # Set return value
    doc.set_returns("The return value", "boolean")
    
    # Add exceptions
    doc.add_exception("ValueError", "If the input is invalid")
    doc.add_exception("TypeError", "If the input is of the wrong type")
    
    # Add examples
    doc.add_example("const result = testFunction('test', 42);")
    
    # Add see also references
    doc.add_see_also("Another API")
    doc.add_see_also("Related Function")
    
    # Add authors
    doc.add_author("John Doe")
    doc.add_author("Jane Smith")
    
    # Generate Markdown
    markdown = doc.generate_markdown()
    print("\nGenerated Markdown:")
    print(markdown)
    
    # Generate HTML
    html = doc.generate_html()
    print("\nGenerated HTML (truncated):")
    print(html[:500] + "...\n")
    
    return doc

def test_documentation_extraction():
    """Test documentation extraction from source code."""
    print("\n=== Testing Documentation Extraction ===")
    
    # Create a temporary Python file with documentation
    temp_file = "temp_test.py"
    with open(temp_file, "w") as f:
        f.write('''"""
This is a test module.

This module demonstrates documentation extraction.
"""

def test_function(param1, param2=None):
    """
    A test function that demonstrates documentation extraction.
    
    This function doesn't do anything useful, but it has a well-documented
    docstring that can be extracted by the documentation system.
    
    Args:
        param1: The first parameter.
        param2: The second parameter, which is optional.
    
    Returns:
        A boolean indicating success or failure.
    
    Raises:
        ValueError: If param1 is invalid.
        TypeError: If param1 is not a string.
    """
    return True

class TestClass:
    """
    A test class that demonstrates documentation extraction.
    
    This class doesn't do anything useful, but it has a well-documented
    docstring that can be extracted by the documentation system.
    """
    
    def __init__(self, name):
        """
        Initialize the TestClass.
        
        Args:
            name: The name of the instance.
        """
        self.name = name
    
    def test_method(self, value):
        """
        A test method that demonstrates documentation extraction.
        
        Args:
            value: The value to test.
        
        Returns:
            The result of the test.
        """
        return value
''')
    
    # Create a documentation manager
    manager = DocumentationManager()
    
    # Extract documentation from the file
    doc = manager.extract_documentation_from_file(temp_file, Documentation.COMPONENT_SCRIBE, "1.0.0")
    
    if doc:
        print(f"\nExtracted documentation from {temp_file}:")
        print(f"Title: {doc.title}")
        print(f"Type: {doc.type}")
        print(f"Content: {doc.content}")
        
        # Generate Markdown
        markdown = manager.generate_markdown_documentation(doc.id)
        print("\nGenerated Markdown:")
        print(markdown)
        
        # Export Markdown
        markdown_file = "temp_test.md"
        success = manager.export_markdown_documentation(doc.id, markdown_file)
        if success:
            print(f"\nExported Markdown to {markdown_file}")
        
        # Export HTML
        html_file = "temp_test.html"
        success = manager.export_html_documentation(doc.id, html_file)
        if success:
            print(f"Exported HTML to {html_file}")
    
    # Clean up
    try:
        os.remove(temp_file)
        os.remove("temp_test.md")
        os.remove("temp_test.html")
    except:
        pass
    
    return doc

def test_static_site_generation():
    """Test static site generation."""
    print("\n=== Testing Static Site Generation ===")
    
    # Create a documentation manager
    manager = DocumentationManager()
    
    # Create some documentation
    doc1 = manager.create_documentation(
        title="API Documentation",
        doc_type=Documentation.TYPE_API,
        content="This is API documentation.",
        component=Documentation.COMPONENT_SCRIBE,
        api_version="1.0.0"
    )
    
    doc2 = manager.create_documentation(
        title="User Guide",
        doc_type=Documentation.TYPE_GUIDE,
        content="This is a user guide.",
        component=Documentation.COMPONENT_SCRIBE,
        api_version="1.0.0"
    )
    
    doc3 = manager.create_documentation(
        title="Tutorial",
        doc_type=Documentation.TYPE_TUTORIAL,
        content="This is a tutorial.",
        component=Documentation.COMPONENT_CAD,
        api_version="1.0.0"
    )
    
    # Generate static site
    output_dir = "docs_site"
    success = manager.generate_static_site(output_dir)
    
    if success:
        print(f"\nGenerated static site in {output_dir}")
        print(f"Files in {output_dir}:")
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                print(f"  {os.path.join(root, file)}")
    
    # Clean up
    try:
        import shutil
        shutil.rmtree(output_dir)
    except:
        pass

def test_integration():
    """Test integration with RebelSUITE components."""
    print("\n=== Testing Integration with RebelSUITE Components ===")
    
    # Create a documentation manager
    manager = DocumentationManager()
    
    # Create a temporary directory structure for a component
    component_dir = "temp_component"
    os.makedirs(os.path.join(component_dir, "src"), exist_ok=True)
    
    # Create a temporary Python file with documentation
    with open(os.path.join(component_dir, "src", "main.py"), "w") as f:
        f.write('''"""
Main module for the component.

This module contains the main functionality of the component.
"""

def main():
    """
    Main function for the component.
    
    This function initializes the component and starts its execution.
    
    Returns:
        An integer exit code.
    """
    return 0
''')
    
    # Create a temporary C++ file with documentation
    with open(os.path.join(component_dir, "src", "core.cpp"), "w") as f:
        f.write('''/**
 * Core functionality for the component.
 *
 * This file contains the core functionality of the component.
 */

/**
 * Initialize the component.
 *
 * @param name The name of the component.
 * @return True if initialization was successful, false otherwise.
 */
bool initialize(const char* name) {
    return true;
}
''')
    
    # Create output directory
    output_dir = "component_docs"
    
    # Integrate with the component
    success = manager.integrate_with_component(
        Documentation.COMPONENT_CAD,
        component_dir,
        output_dir
    )
    
    if success:
        print(f"\nIntegrated with component in {component_dir}")
        print(f"Generated documentation in {output_dir}")
        print(f"Files in {output_dir}:")
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                print(f"  {os.path.join(root, file)}")
    
    # Clean up
    try:
        import shutil
        shutil.rmtree(component_dir)
        shutil.rmtree(output_dir)
    except:
        pass

def main():
    """Main function."""
    print("=== RebelSCRIBE Documentation Test ===")
    
    # Test Documentation model
    test_documentation_model()
    
    # Test documentation extraction
    test_documentation_extraction()
    
    # Test static site generation
    test_static_site_generation()
    
    # Test integration
    test_integration()
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    main()
