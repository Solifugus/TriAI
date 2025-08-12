#!/bin/bash
# TriAI Service Installation Script

set -e

echo "🚀 Installing TriAI systemd services"
echo "===================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo "❌ This script should not be run as root."
    echo "   Please run as your regular user - sudo will be used when needed."
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Installing services from: $SCRIPT_DIR"

# Copy service files to systemd directory
echo "📋 Copying service files to /etc/systemd/system/"
sudo cp "$SCRIPT_DIR/triai-messaging.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/triai-agents.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/triai.target" /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/triai-messaging.service
sudo chmod 644 /etc/systemd/system/triai-agents.service
sudo chmod 644 /etc/systemd/system/triai.target

# Reload systemd
echo "🔄 Reloading systemd daemon"
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling TriAI services"
sudo systemctl enable triai-messaging.service
sudo systemctl enable triai-agents.service
sudo systemctl enable triai.target

echo ""
echo "🎉 Services installed successfully!"
echo ""
echo "📋 Available commands:"
echo "  sudo systemctl start triai.target     # Start all TriAI services"
echo "  sudo systemctl stop triai.target      # Stop all TriAI services"
echo "  sudo systemctl status triai.target    # Check status of all services"
echo "  sudo systemctl restart triai.target   # Restart all services"
echo ""
echo "  Individual service commands:"
echo "  sudo systemctl start triai-messaging.service   # Start messaging server"
echo "  sudo systemctl start triai-agents.service      # Start agent server"
echo "  sudo systemctl status triai-messaging.service  # Check messaging server"
echo "  sudo systemctl status triai-agents.service     # Check agent server"
echo ""
echo "📝 View logs:"
echo "  sudo journalctl -u triai-messaging.service -f  # Follow messaging server logs"
echo "  sudo journalctl -u triai-agents.service -f     # Follow agent server logs"
echo "  sudo journalctl -u triai.target -f             # Follow all TriAI logs"
echo ""
echo "⚠️  Prerequisites:"
echo "  - Ensure Ollama is installed and running: systemctl status ollama"
echo "  - Virtual environment is set up in $SCRIPT_DIR/venv"
echo "  - Dependencies are installed in the virtual environment"
echo ""
echo "🚀 To start TriAI now: sudo systemctl start triai.target"