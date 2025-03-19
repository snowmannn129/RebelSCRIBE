#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE setup script.

This file is provided for backward compatibility with older Python packaging tools.
For modern Python packaging, see pyproject.toml.
"""

from setuptools import setup, find_packages

setup(
    name="rebelscribe",
    version="0.1.0",
    description="AI-powered novel writing program inspired by Scrivener",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="RebelSCRIBE Team",
    author_email="info@rebelscribe.com",
    url="https://github.com/rebelscribe/rebelscribe",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.5.0",
        "PyQt6-QScintilla>=2.14.0",
        "anthropic>=0.5.0",
        "openai>=1.0.0",
        "httpx>=0.24.1",
        "backoff>=2.2.1",
        "google-generativeai>=0.3.0",
        "dropbox>=11.36.0",
        "google-auth>=2.22.0",
        "google-auth-oauthlib>=1.0.0",
        "google-api-python-client>=2.100.0",
        "python-docx>=0.8.11",
        "reportlab>=4.0.4",
        "markdown>=3.4.3",
        "beautifulsoup4>=4.12.2",
        "pyyaml>=6.0.0",
        "rich>=13.4.2",
        "tqdm>=4.66.1",
        "pillow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "pytest-qt>=4.2.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Word Processors",
    ],
    entry_points={
        "console_scripts": [
            "rebelscribe=src.main:main",
        ],
    },
)
