"""
Network Traffic Analyzer - ML-powered network traffic analysis and anomaly detection

This package provides tools for capturing, analyzing, and detecting anomalies
in network traffic using machine learning techniques.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements from requirements.txt
requirements = []
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Development requirements
dev_requirements = []
with open("requirements-dev.txt", "r", encoding="utf-8") as f:
    dev_requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="network-traffic-analyzer",
    version="1.1.0",
    author="Network Traffic Analyzer Contributors",
    author_email="",
    description="ML-powered network traffic analysis and anomaly detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Raoof128/network-traffic-analyzer",
    project_urls={
        "Bug Tracker": "https://github.com/Raoof128/network-traffic-analyzer/issues",
        "Documentation": "https://github.com/Raoof128/network-traffic-analyzer#readme",
        "Source Code": "https://github.com/Raoof128/network-traffic-analyzer",
        "Changelog": "https://github.com/Raoof128/network-traffic-analyzer/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        # Development Status
        "Development Status :: 4 - Beta",

        # Intended Audience
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",

        # License
        "License :: OSI Approved :: MIT License",

        # Programming Language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",

        # Topic
        "Topic :: Security",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",

        # Operating System
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",

        # Environment
        "Environment :: Console",
        "Environment :: Web Environment",

        # Natural Language
        "Natural Language :: English",

        # Typing
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "api": [
            "fastapi>=0.108.0",
            "uvicorn[standard]>=0.25.0",
            "pydantic>=2.5.0",
            "python-multipart>=0.0.6",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "numpy>=1.24.0",
            "pandas>=2.0.0",
        ],
        "viz": [
            "matplotlib>=3.7.0",
            "plotly>=5.14.0",
        ],
        "all": dev_requirements + [
            "fastapi>=0.108.0",
            "uvicorn[standard]>=0.25.0",
            "pydantic>=2.5.0",
            "python-multipart>=0.0.6",
        ],
    },
    entry_points={
        "console_scripts": [
            "network-traffic-analyzer=analyzer:main",
            "nta=analyzer:main",
            "nta-train=train_model:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "config/*.yaml",
            "detection/rules/*.yaml",
            "features/*.yaml",
        ],
    },
    zip_safe=False,
    keywords=[
        "network",
        "traffic",
        "analysis",
        "anomaly-detection",
        "machine-learning",
        "security",
        "monitoring",
        "packet-capture",
        "pcap",
        "scapy",
        "intrusion-detection",
        "cybersecurity",
    ],
    platforms=["any"],
)
