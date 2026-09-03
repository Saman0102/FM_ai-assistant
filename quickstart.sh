#!/bin/bash
# Quick Start Script for AI Assistant

set -e

echo "==================================="
echo "AI Assistant - Quick Setup Script"
echo "==================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

echo "✓ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment configuration..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your API keys"
    echo "   Required:"
    echo "   - LLM_PROVIDER (openai or claude)"
    echo "   - API_KEY (your API key)"
    echo ""
    read -p "Press Enter after configuring .env..."
else
    echo "✓ .env file exists"
fi

echo ""
echo "==================================="
echo "Setup Complete! ✅"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Run examples: python examples.py"
echo "3. Check README.md for more options"
echo "4. Try with Docker: docker build -t ai-assistant . && docker run --env-file .env ai-assistant"
echo ""
