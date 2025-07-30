#!/usr/bin/env python3
"""Setup script for CrossPLC compiler."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crossplc",
    version="2.0.0",
    author="Original Author + Modernization",
    description="Cross-vendor semantic toolkit for PLC codebases with multi-platform support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Compilers",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "crossplc=crossplc.cli:main",
            "l5x2st=crossplc.cli:l5x2st_main",
            "st2l5x=crossplc.cli:st2l5x_main",
            "export-ir=crossplc.cli:export_ir_main",
            "analyze-multi=crossplc.cli:analyze_multi_main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 