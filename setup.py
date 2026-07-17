"""Setuptools metadata for editable installs and source distributions."""

from pathlib import Path

from setuptools import find_packages, setup

from bible_app import __author__, __version__


ROOT = Path(__file__).parent
README = ROOT / "README.md"


setup(
    name="bible-reference-study-tool",
    version=__version__,
    description="Desktop Bible reference, study, hymnal, and document library tool",
    long_description=README.read_text(encoding="utf-8") if README.exists() else "",
    long_description_content_type="text/markdown",
    author=__author__,
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    install_requires=[
        "Pillow>=9.0.0",
        "pypdf>=3.0.0",
        "PyPDF2>=3.0.0",
        "pypdfium2>=4.0.0",
        "PyMuPDF>=1.22.0",
    ],
    extras_require={
        "dev": [
            "black>=22.0",
            "flake8>=4.0",
            "pytest>=7.0",
        ],
        "build": [
            "build>=1.0.0",
            "pyinstaller>=5.0",
            "wheel>=0.37.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bible-app=bible_app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Religion",
    ],
    python_requires=">=3.10",
)
