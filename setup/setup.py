#!/usr/bin/env python3
"""
Setup script for JD Agent - Interview Question Harvester
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("readme/README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="jd-agent",
    version="1.0.0",
    author="Atlas",
    author_email="atlas@jd-agent.com",
    description="An intelligent system that automatically harvests interview questions tailored to candidates from job description emails",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/gkumar2702/job_description_agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Human Resources",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
    
        ],
    },
    entry_points={
        "console_scripts": [
            "jd-agent=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "jd_agent": ["*.md", "*.txt"],
    },
    keywords="interview questions job description email parsing AI machine learning",
    project_urls={
        "Bug Reports": "https://github.com/gkumar2702/job_description_agent/issues",
        "Source": "https://github.com/gkumar2702/job_description_agent",
        "Documentation": "https://github.com/gkumar2702/job_description_agent#readme",
    },
) 