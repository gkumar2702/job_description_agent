#!/bin/bash

# JD Agent Installation Script
# This script sets up the JD Agent system with all dependencies

set -e  # Exit on any error

echo "🚀 Installing JD Agent - Interview Question Harvester"
echo "=================================================="

# Check if Python 3.10+ is installed
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $python_version is too old. Please install Python 3.10 or higher."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Create necessary directories
echo "Creating directories..."
mkdir -p data/exports

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your API keys:"
    echo "   - Gmail API credentials"
    echo "   - SerpAPI key"
    echo "   - OpenAI API key"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
chmod +x main.py
chmod +x example.py

echo ""
echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Validate configuration: python main.py --validate"
echo "4. Run examples: python example.py"
echo "5. Run full pipeline: python main.py"
echo ""
echo "For more information, see readme/README.md" 