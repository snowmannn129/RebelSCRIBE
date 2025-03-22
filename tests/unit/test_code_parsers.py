#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for code parsers.

This module contains unit tests for the code parsers in RebelSCRIBE.
"""

import os
import sys
import unittest
from typing import Dict, List, Any

# Add the RebelSCRIBE directory to the Python path
rebelsuite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if rebelsuite_path not in sys.path:
    sys.path.append(rebelsuite_path)

from src.backend.parsers import CodeParser, CodeNode, PythonParser, CppParser, TypeScriptParser

class TestCodeParsers(unittest.TestCase):
    """
    Test case for code parsers.
    """
    
    def setUp(self):
        """
        Set up the test case.
        """
        self.python_parser = PythonParser()
        self.cpp_parser = CppParser()
        self.typescript_parser = TypeScriptParser()
        
        # Sample code snippets
        self.python_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Python module.

This is a sample Python module for testing the Python parser.
"""

import os
import sys
from typing import Dict, List, Optional, Any

class SampleClass:
    """
    Sample class for testing.
    
    This class demonstrates various Python features.
    """
    
    class_variable = "class variable"
    
    def __init__(self, param1: str, param2: int = 0):
        """
        Initialize the SampleClass.
        
        Args:
            param1: The first parameter.
            param2: The second parameter.
        """
        self.param1 = param1
        self.param2 = param2
    
    def sample_method(self, arg1: str, arg2: Optional[int] = None) -> str:
        """
        Sample method.
        
        Args:
            arg1: The first argument.
            arg2: The second argument.
            
        Returns:
            A string result.
            
        Raises:
            ValueError: If arg1 is empty.
        """
        if not arg1:
            raise ValueError("arg1 cannot be empty")
        
        return f"{arg1} {arg2 or self.param2}"
    
    @property
    def sample_property(self) -> str:
        """
        Sample property.
        
        Returns:
            The property value.
        """
        return self.param1

def sample_function(arg1: str, arg2: int = 0) -> str:
    """
    Sample function.
    
    Args:
        arg1: The first argument.
        arg2: The second argument.
        
    Returns:
        A string result.
    """
    return f"{arg1} {arg2}"

# Sample variable
sample_variable = "sample value"
'''
        
        self.cpp_code = '''/**
 * Sample C++ header file.
 *
 * This is a sample C++ header file for testing the C++ parser.
 */

#include <string>
#include <vector>
#include <iostream>

namespace sample {

/**
 * @brief Sample class for testing.
 *
 * This class demonstrates various C++ features.
 */
class SampleClass {
public:
    /**
     * @brief Constructor.
     *
     * @param param1 The first parameter.
     * @param param2 The second parameter.
     */
    SampleClass(const std::string& param1, int param2 = 0);
    
    /**
     * @brief Sample method.
     *
     * @param arg1 The first argument.
     * @param arg2 The second argument.
     * @return A string result.
     * @throws std::invalid_argument If arg1 is empty.
     */
    std::string sampleMethod(const std::string& arg1, int arg2 = 0) const;
    
    /**
     * @brief Get the sample property.
     *
     * @return The property value.
     */
    std::string getSampleProperty() const;
    
private:
    std::string param1; ///< The first parameter.
    int param2; ///< The second parameter.
};

/**
 * @brief Sample function.
 *
 * @param arg1 The first argument.
 * @param arg2 The second argument.
 * @return A string result.
 */
std::string sampleFunction(const std::string& arg1, int arg2 = 0);

/**
 * @brief Sample enumeration.
 */
enum SampleEnum {
    VALUE1, ///< First value.
    VALUE2, ///< Second value.
    VALUE3  ///< Third value.
};

} // namespace sample
'''
        
        self.typescript_code = '''/**
 * Sample TypeScript module.
 *
 * This is a sample TypeScript module for testing the TypeScript parser.
 */

import { Component } from 'react';
import * as utils from './utils';

/**
 * Sample interface for testing.
 */
export interface SampleInterface {
    /**
     * The first property.
     */
    prop1: string;
    
    /**
     * The second property.
     */
    prop2?: number;
    
    /**
     * Sample method.
     *
     * @param arg1 - The first argument.
     * @param arg2 - The second argument.
     * @returns A string result.
     */
    sampleMethod(arg1: string, arg2?: number): string;
}

/**
 * Sample class for testing.
 *
 * This class demonstrates various TypeScript features.
 */
export class SampleClass implements SampleInterface {
    /**
     * The first property.
     */
    public prop1: string;
    
    /**
     * The second property.
     */
    private prop2: number;
    
    /**
     * Constructor.
     *
     * @param prop1 - The first property.
     * @param prop2 - The second property.
     */
    constructor(prop1: string, prop2: number = 0) {
        this.prop1 = prop1;
        this.prop2 = prop2;
    }
    
    /**
     * Sample method.
     *
     * @param arg1 - The first argument.
     * @param arg2 - The second argument.
     * @returns A string result.
     * @throws Error if arg1 is empty.
     */
    public sampleMethod(arg1: string, arg2?: number): string {
        if (!arg1) {
            throw new Error('arg1 cannot be empty');
        }
        
        return `${arg1} ${arg2 || this.prop2}`;
    }
    
    /**
     * Sample getter.
     *
     * @returns The property value.
     */
    public get sampleProperty(): string {
        return this.prop1;
    }
}

/**
 * Sample function.
 *
 * @param arg1 - The first argument.
 * @param arg2 - The second argument.
 * @returns A string result.
 */
export function sampleFunction(arg1: string, arg2: number = 0): string {
    return `${arg1} ${arg2}`;
}

/**
 * Sample enumeration.
 */
export enum SampleEnum {
    VALUE1, // First value.
    VALUE2, // Second value.
    VALUE3  // Third value.
}

/**
 * Sample variable.
 */
export const sampleVariable: string = 'sample value';

/**
 * Sample arrow function.
 *
 * @param arg1 - The first argument.
 * @param arg2 - The second argument.
 * @returns A string result.
 */
export const sampleArrowFunction = (arg1: string, arg2: number = 0): string => {
    return `${arg1} ${arg2}`;
};
'''
    
    def test_python_parser(self):
        """
        Test the Python parser.
        """
        # Parse the Python code
        result = self.python_parser.parse(self.python_code)
        
        # Check the result
        self.assertEqual(result.type, CodeNode.TYPE_FILE)
        
        # Check for module docstring
        self.assertIn("Sample Python module", result.content)
        
        # Check for imports
        imports = [node for node in result.children if node.type == CodeNode.TYPE_IMPORT]
        self.assertGreaterEqual(len(imports), 2)
        
        # Check for class
        classes = [node for node in result.children if node.type == CodeNode.TYPE_CLASS]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, "SampleClass")
        
        # Check for class methods
        methods = [node for node in classes[0].children if node.type == CodeNode.TYPE_METHOD]
        self.assertGreaterEqual(len(methods), 1)
        
        # Check for function
        functions = [node for node in result.children if node.type == CodeNode.TYPE_FUNCTION]
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].name, "sample_function")
        
        # Check for variable
        variables = [node for node in result.children if node.type == CodeNode.TYPE_VARIABLE]
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0].name, "sample_variable")
    
    def test_cpp_parser(self):
        """
        Test the C++ parser.
        """
        # Parse the C++ code
        result = self.cpp_parser.parse(self.cpp_code)
        
        # Check the result
        self.assertEqual(result.type, CodeNode.TYPE_FILE)
        
        # Check for includes
        includes = [node for node in result.children if node.type == CodeNode.TYPE_IMPORT]
        self.assertGreaterEqual(len(includes), 3)
        
        # Check for namespace
        namespaces = [node for node in result.children if node.type == CodeNode.TYPE_NAMESPACE]
        self.assertEqual(len(namespaces), 1)
        self.assertEqual(namespaces[0].name, "sample")
        
        # Check for class
        classes = [node for node in namespaces[0].children if node.type == CodeNode.TYPE_CLASS]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, "SampleClass")
        
        # Check for class methods
        methods = [node for node in classes[0].children if node.type == CodeNode.TYPE_METHOD]
        self.assertGreaterEqual(len(methods), 2)
        
        # Check for function
        functions = [node for node in namespaces[0].children if node.type == CodeNode.TYPE_FUNCTION]
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].name, "sampleFunction")
        
        # Check for enum
        enums = [node for node in namespaces[0].children if node.type == CodeNode.TYPE_ENUM]
        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0].name, "SampleEnum")
    
    def test_typescript_parser(self):
        """
        Test the TypeScript parser.
        """
        # Parse the TypeScript code
        result = self.typescript_parser.parse(self.typescript_code)
        
        # Check the result
        self.assertEqual(result.type, CodeNode.TYPE_FILE)
        
        # Check for imports
        imports = [node for node in result.children if node.type == CodeNode.TYPE_IMPORT]
        self.assertGreaterEqual(len(imports), 2)
        
        # Check for interface
        interfaces = [node for node in result.children if node.type == CodeNode.TYPE_INTERFACE]
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0].name, "SampleInterface")
        
        # Check for class
        classes = [node for node in result.children if node.type == CodeNode.TYPE_CLASS]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, "SampleClass")
        
        # Check for class methods
        methods = [node for node in classes[0].children if node.type == CodeNode.TYPE_METHOD]
        self.assertGreaterEqual(len(methods), 1)
        
        # Check for function
        functions = [node for node in result.children if node.type == CodeNode.TYPE_FUNCTION]
        self.assertGreaterEqual(len(functions), 1)
        self.assertTrue(any(func.name == "sampleFunction" for func in functions))
        
        # Check for enum
        enums = [node for node in result.children if node.type == CodeNode.TYPE_ENUM]
        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0].name, "SampleEnum")
        
        # Check for variable
        variables = [node for node in result.children if node.type == CodeNode.TYPE_VARIABLE]
        self.assertGreaterEqual(len(variables), 1)
        self.assertTrue(any(var.name == "sampleVariable" for var in variables))
    
    def test_to_html(self):
        """
        Test the to_html method.
        """
        # Parse the Python code
        result = self.python_parser.parse(self.python_code)
        
        # Convert to HTML
        html = result.to_html()
        
        # Check the HTML
        self.assertIsInstance(html, str)
        self.assertIn("<div class=\"code-file\">", html)
        self.assertIn("<h1>", html)
        self.assertIn("<div class=\"code-class\">", html)
        self.assertIn("<h2 class=\"class-name\">", html)
        self.assertIn("<div class=\"code-function\">", html)
        self.assertIn("<h3 class=\"function-name\">", html)
    
    def test_to_markdown(self):
        """
        Test the to_markdown method.
        """
        # Parse the Python code
        result = self.python_parser.parse(self.python_code)
        
        # Convert to Markdown
        markdown = result.to_markdown()
        
        # Check the Markdown
        self.assertIsInstance(markdown, str)
        self.assertIn("# ", markdown)
        self.assertIn("## Class: ", markdown)
        self.assertIn("### Method: ", markdown)
        self.assertIn("### Function: ", markdown)

if __name__ == '__main__':
    unittest.main()
