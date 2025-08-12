#!/bin/bash

# TriAI Production Deployment Script
echo "Deploying TriAI to Production..."
echo "================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "Please do not run as root. Create a dedicated user for TriAI."
   exit 1
fi

# Create application directory
sudo mkdir -p /opt/triai
sudo chown $USER:$USER /opt/triai

# Copy application files
echo "Copying application files..."
cp *.py /opt/triai/
cp -r public /opt/triai/
cp requirements.txt /opt/triai/

# Create configuration from template
if [ ! -f /opt/triai/config.yaml ]; then
    echo "Creating configuration file..."
    cp config.yaml.template /opt/triai/config.yaml
    echo "⚠️  IMPORTANT: Edit /opt/triai/config.yaml with your database settings!"
else
    echo "Configuration file already exists, skipping..."
fi

# Set up Python virtual environment
echo "Setting up Python environment..."
cd /opt/triai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd services
echo "Installing systemd services..."
sudo cp systemd/triai-messaging.service /etc/systemd/system/
sudo cp systemd/triai-agents.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "Deployment completed!"
echo "===================="
echo ""
echo "Next steps:"
echo "1. Run the database schema script: create_database_schema.sql"
echo "2. Edit /opt/triai/config.yaml with your database settings"
echo "3. Test the deployment:"
echo "   cd /opt/triai && source venv/bin/activate && python main.py"
echo "4. If test works, enable services:"
echo "   sudo systemctl enable triai-messaging.service"
echo "   sudo systemctl enable triai-agents.service"  
echo "   sudo systemctl start triai-messaging.service"
echo "   sudo systemctl start triai-agents.service"
echo ""
echo "Access the web interface at: http://your-server:8080"
