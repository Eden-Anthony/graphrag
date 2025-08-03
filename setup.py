#!/usr/bin/env python3
"""
Setup script for GraphRAG.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(
    encoding="utf-8") if readme_path.exists() else ""

# Dependencies from pyproject.toml
requirements = [
    "neo4j>=5.0.0",
    "click>=8.0.0",
    "python-magic>=0.4.27",
    "chardet>=5.0.0",
    "pathlib2>=2.3.7",
    "rich>=13.0.0",
    "tqdm>=4.65.0",
]

setup(
    name="graphrag",
    version="0.1.0",
    description="A knowledge graph system using Neo4j for indexing and querying file directories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="GraphRAG Team",
    author_email="",
    url="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "graphrag=graphrag.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
