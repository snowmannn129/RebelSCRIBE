#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script for TypeScript parser.
"""

import sys
import os
from src.backend.parsers import TypeScriptParser

# Sample TypeScript code from the test
typescript_code = '''/**
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

def main():
    parser = TypeScriptParser()
    result = parser.parse(typescript_code)
    
    print("File node type:", result.type)
    print("File node name:", result.name)
    
    # Print all children
    print("\nAll children:")
    for i, child in enumerate(result.children):
        print(f"{i+1}. {child.type}: {child.name}")
    
    # Print imports
    imports = [node for node in result.children if node.type == "IMPORT"]
    print("\nImports:")
    for i, imp in enumerate(imports):
        print(f"{i+1}. {imp.name}: {imp.content}")
    
    # Print variables
    variables = [node for node in result.children if node.type == "VARIABLE"]
    print("\nVariables:")
    for i, var in enumerate(variables):
        print(f"{i+1}. {var.name}: {var.attributes.get('var_type', '')}")
    
    # Print the line that should match the variable
    print("\nVariable line:")
    for line in typescript_code.split('\n'):
        if "sampleVariable" in line:
            print(f"Line: '{line}'")
            # Test the regex
            import re
            variable_regex = re.compile(r'^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)(?:\s*:\s*([a-zA-Z0-9_$<>[\].,\s|]+))?(?:\s*=\s*[^;]+)?;?\s*$')
            match = variable_regex.match(line)
            if match:
                print(f"Regex match: {match.group(1)}, {match.group(2)}")
            else:
                print("No regex match")

if __name__ == "__main__":
    main()
