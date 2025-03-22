#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Setup Script

This script is used to install RebelSCRIBE.
"""

from setuptools import setup, find_packages

setup(
    name="rebelscribe",
    version="1.0.0",
    description="A hybrid documentation and novel writing program",
    author="RebelSUITE",
    author_email="info@rebelsuite.com",
    url="https://github.com/rebelsuite/rebelscribe",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "markdown>=3.4.1",
        "pymdown-extensions>=9.5",
        "docutils>=0.18.1",
        "sphinx>=5.0.2",
        "openai>=0.27.0",
        "anthropic>=0.2.8",
        "llama-cpp-python>=0.1.65",
    ],
    entry_points={
        "console_scripts": [
            "rebelscribe=rebelscribe.run_hybrid:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Documentation",
        "Topic :: Text Editors",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
)
