#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting PyPI publish process for thriftllm..."

# Ensure build tools are installed
echo "Checking for required build tools (build, twine)..."
python3 -m pip install --upgrade build twine

# Clean previous builds
echo "Cleaning up old build artifacts..."
rm -rf dist/ build/ *.egg-info

# Build the package
echo "Building source distribution and wheel..."
python3 -m build

# Upload to PyPI using twine
echo "Uploading to PyPI..."
echo "Note: This will prompt for credentials unless TWINE_USERNAME and TWINE_PASSWORD are set in the environment."
python3 -m twine upload dist/*

echo "Publish process complete."