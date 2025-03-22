#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE Integration Script for RebelSUITE.

This script demonstrates how to integrate RebelSCRIBE with other RebelSUITE components
by extracting documentation from their source code and generating documentation.
"""

import os
import sys
import argparse
from pathlib import Path

# Add src directory to path to allow imports
src_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(src_dir))

from src.backend.models.documentation import Documentation
from src.backend.services.documentation_manager import DocumentationManager
from src.utils.logging_utils import setup_logging, get_logger

# Set up logging
setup_logging(
    log_file="rebelsuite_integration.log",
    console_output=True,
    file_output=True
)

logger = get_logger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="RebelSCRIBE Integration Script for RebelSUITE")
    
    parser.add_argument(
        "--component",
        type=str,
        choices=[
            "RebelCAD",
            "RebelCODE",
            "RebelENGINE",
            "RebelFLOW",
            "RebelDESK",
            "RebelSCRIBE",
            "all"
        ],
        default="all",
        help="The RebelSUITE component to integrate with"
    )
    
    parser.add_argument(
        "--source-dir",
        type=str,
        default="..",
        help="The root directory containing the RebelSUITE components"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs",
        help="The output directory for the generated documentation"
    )
    
    parser.add_argument(
        "--api-version",
        type=str,
        default="1.0.0",
        help="The API version to use for the documentation"
    )
    
    return parser.parse_args()

def integrate_with_component(component, source_dir, output_dir, api_version):
    """
    Integrate with a RebelSUITE component.
    
    Args:
        component: The component name.
        source_dir: The source directory of the component.
        output_dir: The output directory for the documentation.
        api_version: The API version to use for the documentation.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info(f"Integrating with {component}...")
    
    # Map component name to Documentation component constant
    component_map = {
        "RebelCAD": Documentation.COMPONENT_CAD,
        "RebelCODE": Documentation.COMPONENT_CODE,
        "RebelENGINE": Documentation.COMPONENT_ENGINE,
        "RebelFLOW": Documentation.COMPONENT_FLOW,
        "RebelDESK": Documentation.COMPONENT_DESK,
        "RebelSCRIBE": Documentation.COMPONENT_SCRIBE
    }
    
    doc_component = component_map.get(component)
    if not doc_component:
        logger.error(f"Unknown component: {component}")
        return False
    
    # Create documentation manager
    manager = DocumentationManager()
    
    # Get component source directory
    component_source_dir = os.path.join(source_dir, component, "src")
    if not os.path.exists(component_source_dir):
        logger.error(f"Component source directory not found: {component_source_dir}")
        return False
    
    # Create output directory
    component_output_dir = os.path.join(output_dir, component.lower())
    os.makedirs(component_output_dir, exist_ok=True)
    
    # Integrate with component
    success = manager.integrate_with_component(
        doc_component,
        component_source_dir,
        component_output_dir
    )
    
    if success:
        logger.info(f"Successfully integrated with {component}")
        logger.info(f"Documentation generated in {component_output_dir}")
    else:
        logger.error(f"Failed to integrate with {component}")
    
    return success

def main():
    """Main function."""
    print("=== RebelSCRIBE Integration with RebelSUITE ===")
    
    # Parse arguments
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Integrate with components
    if args.component == "all":
        components = [
            "RebelCAD",
            "RebelCODE",
            "RebelENGINE",
            "RebelFLOW",
            "RebelDESK",
            "RebelSCRIBE"
        ]
        
        success = True
        for component in components:
            component_success = integrate_with_component(
                component,
                args.source_dir,
                args.output_dir,
                args.api_version
            )
            success = success and component_success
        
        # Generate index page
        if success:
            generate_index_page(args.output_dir, components)
    else:
        success = integrate_with_component(
            args.component,
            args.source_dir,
            args.output_dir,
            args.api_version
        )
    
    if success:
        print("\n=== Integration completed successfully ===")
        print(f"Documentation generated in {args.output_dir}")
    else:
        print("\n=== Integration failed ===")
        print("Check the log file for details")

def generate_index_page(output_dir, components):
    """
    Generate an index page for the documentation.
    
    Args:
        output_dir: The output directory.
        components: The list of components.
    """
    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>RebelSUITE Documentation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        
        .component-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .component-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            background-color: #f9f9f9;
        }
        
        .component-card h2 {
            margin-top: 0;
            color: #3498db;
        }
        
        .component-card a {
            display: inline-block;
            margin-top: 10px;
            color: #3498db;
            text-decoration: none;
        }
        
        .component-card a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>RebelSUITE Documentation</h1>
    
    <p>
        This is the documentation for the RebelSUITE ecosystem, generated by RebelSCRIBE.
        Click on a component below to view its documentation.
    </p>
    
    <div class="component-grid">
"""
    
    # Add component cards
    for component in components:
        component_lower = component.lower()
        index_html += f"""
        <div class="component-card">
            <h2>{component}</h2>
            <p>Documentation for the {component} component of RebelSUITE.</p>
            <a href="{component_lower}/index.html">View Documentation</a>
        </div>
"""
    
    index_html += """
    </div>
</body>
</html>
"""
    
    # Write index.html
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(index_html)
    
    logger.info(f"Generated index page in {output_dir}")

if __name__ == "__main__":
    main()
