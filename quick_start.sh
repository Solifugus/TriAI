#!/bin/bash
# Quick start script for TriAI

echo "🚀 TriAI Quick Start"
echo "==================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install fastapi uvicorn websockets pydantic python-multipart pyyaml requests beautifulsoup4"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first:"
    echo "   ollama serve"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

echo "📋 Available commands:"
echo ""
echo "1. Start Messaging Server:"
echo "   source venv/bin/activate && python main.py"
echo ""
echo "2. Start AI Agents (in new terminal):"
echo "   source venv/bin/activate && python start_agents.py"
echo ""
echo "3. Test single agent:"
echo "   source venv/bin/activate && python test_agent_basic.py"
echo ""
echo "4. Access web interface:"
echo "   Open http://localhost:8080 in your browser"
echo ""
echo "🎯 To start everything now:"
echo "   1. Run: source venv/bin/activate && python main.py"
echo "   2. Open new terminal and run: source venv/bin/activate && python start_agents.py"
echo "   3. Open http://localhost:8080"