#!/bin/bash
# TriAI Setup Script
# Run this after cloning the repository to set up the development environment

set -e  # Exit on any error

echo "🔧 TriAI Setup Script"
echo "===================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
echo "✅ Python3 found"
echo ""

# Create virtual environment
echo "🐍 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate

# Upgrade pip first
echo "   Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements with better error handling
echo "   Installing packages from requirements.txt..."
if [ -f "requirements.txt" ]; then
    # Install core packages first to resolve conflicts
    echo "   Installing FastAPI and core dependencies..."
    pip install fastapi uvicorn[standard] websockets pydantic python-multipart pyyaml
    
    echo "   Installing database drivers..."
    pip install pyodbc
    
    echo "   Installing MCP (this may upgrade some packages)..."
    pip install mcp
    
    echo "   Checking for dependency conflicts..."
    pip check
    
    echo "✅ All dependencies installed successfully"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi
echo ""

# Check configuration
echo "⚙️  Checking configuration..."
if [ -f "config.yaml" ]; then
    echo "✅ Configuration file found"
    
    # Check if using mock database
    if grep -q 'type: "mock"' config.yaml && grep -q 'use_mock_db: true' config.yaml; then
        echo "✅ Mock database configuration detected - good for initial testing"
    else
        echo "⚠️  Real database configuration detected"
        echo "   For initial testing, consider setting:"
        echo "   - database.type: 'mock'"  
        echo "   - server.use_mock_db: true"
    fi
else
    echo "❌ config.yaml not found!"
    exit 1
fi
echo ""

# Check if Ollama is available (optional)
echo "🤖 Checking AI model availability..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running and accessible"
else
    echo "⚠️  Ollama is not running or not accessible"
    echo "   This is OK for testing, but you'll need Ollama for AI agents"
    echo "   Install with: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   Then run: ollama pull qwen2.5-coder"
fi
echo ""

echo "🎉 Setup Complete!"
echo "================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the messaging server:"
echo "   python main.py"
echo ""
echo "3. In a new terminal, start the agents:"
echo "   source venv/bin/activate && python start_agents.py"
echo ""
echo "4. Open your browser to:"
echo "   http://localhost:8080"
echo ""
echo "📚 For more information, see README.md or run ./quick_start.sh"