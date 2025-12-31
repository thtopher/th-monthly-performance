#!/usr/bin/env bash
# Build script for Render deployment

# Exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads
mkdir -p outputs
mkdir -p config

echo "Build completed successfully!"
